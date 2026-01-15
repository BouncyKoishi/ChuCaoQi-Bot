import datetime
import re
import os
import time
import json
import openai
import asyncio

import dbConnection.chat as db
from kusa_base import isSuperAdmin, config, sendLog
from nonebot import on_command, CommandSession, scheduler
from utils import nameDetailSplit, imgUrlTobase64
from openai import OpenAI

os.environ["http_proxy"] = config['web']['proxy']
os.environ["https_proxy"] = config['web']['proxy']
HISTORY_PATH = u"chatHistory/"

openai.api_key = config['web']['openai']['key']
deepseekApiKey = config['web']['deepseek']['key']
geminiApiKey = config['web']['gemini']['key']
deepseekBaseUrl = "https://api.deepseek.com"
geminiBaseUrl = "https://generativelanguage.googleapis.com/v1beta/openai/"
openaiClient = OpenAI(api_key=config['web']['openai']['key'])
deepseekClient = OpenAI(api_key=deepseekApiKey, base_url=deepseekBaseUrl)
geminiClient = OpenAI(api_key=geminiApiKey, base_url=geminiBaseUrl)

sensitiveWords = config['sensitiveWords']


@on_command(name='chat', only_to_me=False)
async def chatNew(session: CommandSession):
    if not await permissionCheck(session, 'chat'):
        return
    userId = session.event.user_id
    content = await getChatContent(session)
    await session.send("已开启新对话，等待回复……")
    reply = await chat(userId, content, isNewConversation=True)
    await session.send(reply)


@on_command(name='chat5', only_to_me=False, aliases='chat4')
async def chatNewGPT(session: CommandSession):
    if not await permissionCheck(session, 'chat'):
        return
    if not await permissionCheck(session, 'model'):
        return
    userId = session.event.user_id
    content = await getChatContent(session)
    await session.send("已开启新对话，等待回复……")
    reply = await chat(userId, content, isNewConversation=True, useGPT5=True)
    await session.send(reply)


@on_command(name='chatn', only_to_me=False)
async def chatNewWithoutRole(session: CommandSession):
    if not await permissionCheck(session, 'chat'):
        return
    userId = session.event.user_id
    content = await getChatContent(session)
    await session.send("已开启新对话，等待回复……")
    reply = await chat(userId, content, isNewConversation=True, useDefaultRole=True)
    await session.send(reply)


@on_command(name='chatn5', only_to_me=False, aliases='chatn4')
async def chatNewWithoutRoleGPT(session: CommandSession):
    if not await permissionCheck(session, 'chat'):
        return
    if not await permissionCheck(session, 'model'):
        return
    userId = session.event.user_id
    content = await getChatContent(session)
    await session.send("已开启新对话，等待回复……")
    reply = await chat(userId, content, isNewConversation=True, useDefaultRole=True, useGPT5=True)
    await session.send(reply)


@on_command(name='chatc', only_to_me=False)
async def chatContinue(session: CommandSession):
    if not await permissionCheck(session, 'chat'):
        return
    userId = session.event.user_id
    content = await getChatContent(session)
    await session.send("继续进行对话，等待回复……")
    reply = await chat(userId, content, isNewConversation=False)
    await session.send(reply)


@on_command(name='chatc5', only_to_me=False, aliases='chatc4')
async def chatContinueGPT(session: CommandSession):
    if not await permissionCheck(session, 'chat'):
        return
    if not await permissionCheck(session, 'model'):
        return
    userId = session.event.user_id
    content = await getChatContent(session)
    await session.send("继续进行对话，等待回复……")
    reply = await chat(userId, content, isNewConversation=False, useGPT5=True)
    await session.send(reply)


@on_command(name='chatb', only_to_me=False)
async def chatUndo(session: CommandSession):
    if not await permissionCheck(session, 'chat'):
        return
    lastMessage = await undo(session.event.user_id)
    if lastMessage is None:
        await session.send("没有可撤回的对话。")
        return
    await session.send("已撤回最后一轮对话。")


@on_command(name='chatr', only_to_me=False)
async def chatRetry(session: CommandSession):
    if not await permissionCheck(session, 'chat'):
        return
    userId = session.event.user_id
    content = await getChatContent(session)
    lastMessage = await undo(userId)
    if lastMessage is None:
        await session.send("没有可撤回的对话，无法重新生成。")
        return
    inputContent = content if session.current_arg_text else lastMessage['content']
    await session.send("已撤回最后一轮对话，重新生成回复中……")
    reply = await chat(userId, inputContent, isNewConversation=False)
    await session.send(reply)


@on_command(name='chatr5', only_to_me=False, aliases='chatr4')
async def chatRetryGPT(session: CommandSession):
    if not await permissionCheck(session, 'chat'):
        return
    if not await permissionCheck(session, 'model'):
        return
    userId = session.event.user_id
    content = await getChatContent(session)
    lastMessage = await undo(userId)
    if lastMessage is None:
        await session.send("没有可撤回的对话，无法重新生成。")
        return
    inputContent = content if session.current_arg_text else lastMessage['content']
    await session.send("已撤回最后一轮对话，重新生成回复中……")
    reply = await chat(userId, inputContent, isNewConversation=False, useGPT5=True)
    await session.send(reply)


@on_command(name='chat_user', only_to_me=False)
async def chatUserInfo(session: CommandSession):
    userId = session.event.user_id
    chatUser = await db.getChatUser(userId)
    if chatUser is None:
        await session.send("你尚未激活大模型对话功能。")
        return

    output = f"你总计使用的token量: {chatUser.tokenUse}\n"
    output += f"当日token用量：{chatUser.todayTokenUse} / {int(chatUser.dailyTokenLimit)}\n"
    output += "在群聊内进行大模型对话无需权限。\n"
    output += f"你的进阶chat功能使用权限："
    output += f"私聊 " if chatUser.allowPrivate else ""
    output += f"角色切换 " if chatUser.allowRole else ""
    output += f"进阶模型 " if chatUser.allowAdvancedModel else ""
    output += f"\n当前使用模型：{chatUser.chosenModel}\n"

    if chatUser.allowRole:
        nowRole = await db.getChatRoleById(chatUser.chosenRoleId)
        createdRoleList = await db.getChatRoleList(userId)
        publicRoleList = await db.getPublicRoleList()
        output += f"\n当前使用角色：{nowRole.name}"
        if createdRoleList:
            output += f"\n当前可选择的自建角色列表："
            for role in createdRoleList:
                output += f"{role.name} "
        if publicRoleList:
            output += f"\n当前可选择的公共角色列表："
            for role in publicRoleList:
                output += f"{role.name} "
    await session.send(output)


@on_command(name='chat_user_update', only_to_me=False)
async def chatUserUpdate(session: CommandSession):
    if not await permissionCheck(session, 'admin'):
        return
    # get number from text as userId, get params after -
    strippedText = session.current_arg_text.strip()
    if strippedText is None or strippedText == "":
        await session.send('需要指定用户qq号！')
        return
    userId = int(''.join([c for c in strippedText if c.isdigit()]))
    params = strippedText.split('-')[1] if '-' in strippedText else ""
    await db.updateChatUser(userId, params)
    await session.send(f"已更新{userId}的chat权限")


@on_command(name='role_detail', only_to_me=False)
async def roleDetail(session: CommandSession):
    if not await permissionCheck(session, "role"):
        return
    userId = session.event.user_id
    strippedText = session.current_arg_text.strip()
    role = await db.getChatRoleByUserAndRoleName(userId, strippedText, True)
    if role is None:
        await session.send("无相关该角色信息（无法查看他人的私人角色）。")
        return
    await session.send(role.detail)


@on_command(name='role_change', only_to_me=False)
async def changeRole(session: CommandSession):
    if not await permissionCheck(session, "role"):
        return
    userId = session.event.user_id
    strippedText = session.current_arg_text.strip()
    success = await db.changeUsingRole(userId, strippedText)
    if not success:
        await session.send("无相关角色信息（无法切换到他人的私人角色）。")
    else:
        strippedText = "default" if not strippedText else strippedText
        await session.send(f"已切换到{strippedText}角色")


@on_command(name='role_update', only_to_me=False)
async def updateRole(session: CommandSession):
    if not await permissionCheck(session, "role"):
        return
    userId = session.event.user_id
    strippedText = session.current_arg_text.strip()
    isPublicRole = strippedText.startswith("-p ") or strippedText.startswith("-public ")
    strippedText = re.sub("^(-p|-public) ", "", strippedText)
    name, detail = nameDetailSplit(strippedText)
    if not name:
        await session.send('至少需要一个角色名称！')
        return
    if isPublicRole:
        publicRoleList = await db.getPublicRoleList()
        for role in publicRoleList:
            if role.name == name:
                await session.send("已经有一个公共角色叫这个名称了！")
                return
    await db.updateRoleDetail(userId, name, detail, isPublicRole)
    await session.send(f"已更新角色 {name} 的描述信息")


@on_command(name='role_delete', only_to_me=False)
async def deleteRole(session: CommandSession):
    if not await permissionCheck(session, "role"):
        return
    userId = session.event.user_id
    strippedText = session.current_arg_text.strip()
    if not strippedText:
        await session.send('需要角色名称！')
        return
    role = await db.getChatRoleByUserAndRoleName(userId, strippedText, False)
    if role is None:
        await session.send("无相关角色信息，或者你没有权限删除该角色。")
        return
    chatUsersUsingThisRole = await db.getChatUserListByNowRoleId(role.id)
    for chatUser in chatUsersUsingThisRole:
        await db.changeUsingRole(chatUser.qq, None)
    await db.deleteRole(role)
    await session.send(f"已删除角色 {strippedText}")


@on_command(name='model_change', only_to_me=False)
async def changeModel(session: CommandSession):
    userId = session.event.user_id
    strippedText = session.current_arg_text.strip()
    if strippedText:
        if "gpt" in strippedText:
            if strippedText in ["gpt-5", "gpt5"]:
                if not await permissionCheck(session, "model"):
                    await session.send("需要高级模型权限！")
                    return
                newModel = "gpt-5"
            else:
                newModel = "gpt-5-mini"
        elif "gemini" in strippedText:
            # gemini暂时自用
            if not await permissionCheck(session, "admin"):
                return
            if "pro" in strippedText:
                newModel = "gemini-2.5-pro"
            else:
                newModel = "gemini-2.5-flash"
        elif "deepseek-r" in strippedText:
            newModel = "deepseek-reasoner"
        elif "deepseek" in strippedText:
            newModel = "deepseek-chat"
        else:
            newModel = strippedText
            await session.send("注意，你定义的模型名称不在预设列表，chat可能报错！")
    else:
        newModel = "deepseek-chat"
    await db.updateUsingModel(userId, newModel)
    output = f"已切换到{newModel}模型"
    await session.send(output)


@on_command(name='chat_save', aliases='save_conversation', only_to_me=False)
async def _(session: CommandSession):
    if not await permissionCheck(session, 'chat'):
        return
    userId = session.event.user_id
    strippedArg = session.current_arg_text.strip()
    history = await readDefaultConversation(userId)
    fileName = re.sub(r'[\\/:*?"<>|]', '', strippedArg)
    if fileName == "":
        timeStr = time.strftime('%Y%m%d%H%M', time.localtime())
        systemPrompt = history[0] if history and len(history) > 0 else None
        roleName = systemPrompt.get('botRoleName', '') if systemPrompt else ''
        fileName = f"{roleName}_{timeStr}" if roleName else timeStr
    saveConversation(userId, fileName, history)
    await session.send(f"已保存当前对话记录，记录名称为 {fileName} ")


@on_command(name='chat_load', aliases='load_conversation', only_to_me=False)
async def _(session: CommandSession):
    if not await permissionCheck(session, 'chat'):
        return
    userId = session.event.user_id

    loadableFiles = []  # 存储(文件名, 修改时间)的元组列表
    for file in os.listdir(HISTORY_PATH):
        if file.startswith(f"{userId}_") and file.endswith(".json"):
            file_path = os.path.join(HISTORY_PATH, file)
            display_name = file[len(f"{userId}_"):-5]  # 去掉前缀和后缀的文件名
            mtime = os.path.getmtime(file_path) # 获取文件修改时间
            loadableFiles.append((display_name, mtime))
    if not loadableFiles:
        await session.send("没有可加载的对话记录。")
        return
    loadableFiles.sort(key=lambda x: x[1], reverse=True)  # 按修改时间倒序排序（最新的在前）

    loadableFileNames = [file[0] for file in loadableFiles]
    selectListStr = "请选择要加载的对话记录(输入序号)：\n"
    for idx, fileName in enumerate(loadableFileNames):
        selectListStr += f"{idx + 1}. {fileName}\n"
        if idx >= 9:
            break   # 最多显示10个选项

    replyMsg = await session.aget(prompt=selectListStr, arg_filters=[str.strip])
    if not replyMsg.isdigit() or not (1 <= int(replyMsg) <= len(loadableFileNames)):
        await session.send("无效的选择，取消加载。")
        return
    # 先加载选中的记录，把Default覆盖掉，再把之前的Default对话保存为备份，
    history = await readDefaultConversation(userId)
    selectedFileName = loadableFileNames[int(replyMsg) - 1]
    loadedHistory = readConversation(userId, selectedFileName)
    saveDefaultConversation(userId, loadedHistory)
    saveConversation(userId, '[上个对话自动存档]', history)

    latestCycleStr = ""
    if len(loadedHistory) >= 2:
        latestCycle = loadedHistory[-2:]
        for message in latestCycle:
            role = "User" if message['role'] == 'user' else "Bot"
            contentText = ""
            for contentPart in message['content']:
                if isinstance(contentPart, str):
                    contentText += contentPart
                elif isinstance(contentPart, dict) and contentPart.get('type') == 'text':
                    contentText += contentPart.get('text', '')
                elif isinstance(contentPart, dict) and contentPart.get('type') == 'image_url':
                    contentText += "[图片]"
            latestCycleStr += f"{role}: {contentText}\n"
    output = f"已加载对话记录 {selectedFileName}。"
    output += "以下是该对话最后一轮对话内容：\n" + latestCycleStr if latestCycleStr else "该对话暂无内容。"
    await session.send(output)


@on_command(name='chat_help', only_to_me=False)
async def chatHelp(session: CommandSession):
    userId = session.event.user_id
    chatUser = await db.getChatUser(userId)
    if chatUser is None:
        await session.send("你尚未激活大模型对话功能。可使用!chat开启一个对话以激活。")
        return

    output = "chat_user: 查看chat权限等相关信息\nchat: 开始一个新对话"
    output += "\nchatc: 继续上一轮对话\nchatb: 撤回上一轮对话\nchatr: 撤回上一轮对话并重新生成"
    output += "\nchat_save: 手动保存当前对话记录"
    output += "\nchat_load: 加载已保存的对话记录文件"
    if chatUser.allowRole:
        output += "\nchatn: 无视当前角色设定，开始一个新对话"
        output += ("\nrole_change: 切换当前角色\nrole_detail: 查看角色描述信息\n"
                   "role_update: 新增/更新角色描述信息(-g 设置为全局角色)\nrole_delete: 删除角色")
    if chatUser.allowAdvancedModel:
        output += "\nmodel_change: 切换语言模型（deepseek/deepseek-r/gpt-5/gpt-5-mini）"
    else:
        output += "\nmodel_change: 切换语言模型（deepseek/deepseek-r/gpt-5-mini）"
    if await isSuperAdmin(session.event.user_id):
        output += "\nchat_user_update: 更改指定人员chat权限(-p私聊 -r角色 -m进阶模型 -v更高上限 -u无限使用)"
    output += "\n\n当前默认使用的模型：deepseek-chat\n对话使用的是收费api，请勿滥用！"
    await session.send(output)


async def getChatContent(session: CommandSession):
    inputText = session.current_arg_text
    inputPicUrls = session.current_arg_images
    userContent = [{"type": "text", "text": inputText}]
    if not inputPicUrls:
        return userContent
    for picUrl in inputPicUrls:
        picBase64 = "data:image/jpeg;base64," + await imgUrlTobase64(picUrl)
        userContent.append({"type": "image_url", "image_url": {"url": picBase64}})
    return userContent


async def chat(userId, content, isNewConversation: bool, useDefaultRole=False, useGPT5=False, retryCount=0):
    chatUser = await db.getChatUser(userId)
    model = "gpt-5" if useGPT5 else chatUser.chosenModel
    roleId = 0 if useDefaultRole else chatUser.chosenRoleId
    history = await getNewConversation(userId, roleId) if isNewConversation else await readDefaultConversation(userId)
    history.append({"role": "user", "content": content})

    try:
        reply, tokenUsage = await getChatReply(model, history)
        for word in sensitiveWords:
            reply = reply.replace(word, '')
        await db.addTokenUsage(chatUser, model, tokenUsage)
        saveDefaultConversation(userId, history)

        role = await db.getChatRoleById(roleId)
        roleSign = f"\nRole: {role.name}" if role.id != 0 and isNewConversation else ""
        modelSign = "(GPT-5)" if model == "gpt-5" else ("(deepseek)" if "deepseek" in model else "")
        tokenSign = f"\nTokens{modelSign}: {tokenUsage}"
        return reply + "\n" + roleSign + tokenSign
    except Exception as e:
        reason = str(e) if str(e) else "Timeout"
        await sendLog(f"userId: {userId} 的 {model} api调用出现异常，异常原因为：{reason}\nRetry次数：{retryCount}")
        # print(traceback.format_exc())
        print(f"Catch Time: {datetime.datetime.now().timestamp()}")
        if retryCount < 1:
            return await chat(userId, content, isNewConversation, useDefaultRole, useGPT5, retryCount + 1)
        else:
            return "对话出错了，请稍后再试。"


async def getChatReply(model, history):
    startTimeStamp = datetime.datetime.now().timestamp()
    print(f"Start Time: {startTimeStamp}")
    response = await getResponseAsync(model, history)
    endTimeStamp = datetime.datetime.now().timestamp()
    print(f"Response Time: {endTimeStamp}, Used Time: {endTimeStamp - startTimeStamp}")
    print(f"Response: {response}")
    response = response.to_dict()
    reply = response['choices'][0]['message']['content']
    finishReason = response['choices'][0]['finish_reason']
    tokenUsage = response['usage']['total_tokens']
    history.append({"role": "assistant", "content": reply})
    if "deepseek" in model and 'reasoning_content' in response['choices'][0]['message']:
        print(f"Reasoning Content:{response['choices'][0]['message']['reasoning_content']}")
    if finishReason != "stop":
        print(f"Finish Reason: {finishReason}")
    return reply, tokenUsage


async def getResponseAsync(model, history):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, getResponse, model, history)


def getResponse(model, history):
    if 'deepseek' in model:
        return deepseekClient.chat.completions.create(model=model, messages=history, timeout=120)
    if 'gemini' in model:
        return geminiClient.chat.completions.create(model=model, messages=history, timeout=120)
    if 'gpt-5' in model:
        return openaiClient.chat.completions.create(model=model, messages=history, timeout=120, reasoning_effort="low")
    return openaiClient.chat.completions.create(model=model, messages=history, timeout=120)


async def undo(userId):
    history = await readDefaultConversation(userId)
    if len(history) < 2:
        return None
    history.pop()
    latestWord = history.pop()
    saveDefaultConversation(userId, history)
    return latestWord


async def getNewConversation(userId, roleId):
    history = await readDefaultConversation(userId, forceToGetResult=False)
    if history and len(history) > 0:
        saveConversation(userId, '[上个对话自动存档]', history)
    role = await db.getChatRoleById(roleId)
    return [{"role": "system", "botRoleName": role.name, "content": [{"type": "text", "text": role.detail}]}] \
        if role.detail else []


async def readDefaultConversation(userId, forceToGetResult=True):
    result = readConversation(userId, None)
    if result is None and forceToGetResult:
        chatUser = await db.getChatUser(userId)
        return await getNewConversation(userId, chatUser.chosenRoleId)
    return result


def saveDefaultConversation(userId, history):
    saveConversation(userId, None, history)


def readConversation(userId, fileName):
    fullFileName = f"{userId}_{fileName}" if fileName else f"{userId}"
    savePath = HISTORY_PATH + fullFileName + ".json"
    if not os.path.exists(savePath):
        return None
    with open(savePath, encoding="utf-8") as f:
        return json.load(f)


def saveConversation(userId, fileName, history):
    fullFileName = f"{userId}_{fileName}" if fileName else f"{userId}"
    savePath = HISTORY_PATH + fullFileName + ".json"
    with open(savePath, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=4)


async def permissionCheck(session: CommandSession, checker: str):
    userId = session.event.user_id
    if checker == 'admin':
        return await isSuperAdmin(userId)

    isGroupCall = session.ctx['message_type'] == 'group'
    chatUser = await db.getChatUser(userId)
    if chatUser is None:
        await db.updateChatUser(userId, '')

    if checker == 'chat':
        if 0 < chatUser.dailyTokenLimit <= chatUser.todayTokenUse:
            return False
        if not isGroupCall:
            return chatUser.allowPrivate
        return True
    if checker == 'role':
        return chatUser.allowRole
    if checker == 'model':
        return chatUser.allowAdvancedModel
    return False


@scheduler.scheduled_job('cron', hour=3, minute=1, misfire_grace_time=None)
async def resetTodayTokenUseRunner():
    await db.resetTodayTokenUse()
    print("已重置所有用户的todayTokenUse")
