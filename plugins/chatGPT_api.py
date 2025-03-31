import datetime
import re
import os
import time
import json
import openai
import asyncio
import traceback

import dbConnection.chat as db
from kusa_base import isSuperAdmin, config, sendLog
from nonebot import on_command, CommandSession
from utils import nameDetailSplit, imgUrlTobase64
from openai import OpenAI

os.environ["http_proxy"] = config['web']['proxy']
os.environ["https_proxy"] = config['web']['proxy']
HISTORY_PATH = u"chatHistory/"

openai.api_key = config['web']['openai']['key']
deepseekApiKey = config['web']['deepseek']['key']
deepseekBaseUrl = "https://api.deepseek.com"  # tencentDs:"https://api.lkeap.cloud.tencent.com/v1"
openaiClient = OpenAI(api_key=config['web']['openai']['key'])
deepseekClient = OpenAI(api_key=deepseekApiKey, base_url=deepseekBaseUrl)

unlimitedGroup = config['web']['openai']['gpt3AllowGroups']
groupCallCounts = {}

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


@on_command(name='chat4', only_to_me=False)
async def chatNewGPT4(session: CommandSession):
    if not await permissionCheck(session, 'model'):
        return
    userId = session.event.user_id
    content = await getChatContent(session)
    await session.send("已开启新对话，等待回复……")
    reply = await chat(userId, content, isNewConversation=True, useGPT4=True)
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


@on_command(name='chatn4', only_to_me=False)
async def chatNewWithoutRoleGPT4(session: CommandSession):
    if not await permissionCheck(session, 'model'):
        return
    userId = session.event.user_id
    content = await getChatContent(session)
    await session.send("已开启新对话，等待回复……")
    reply = await chat(userId, content, isNewConversation=True, useDefaultRole=True, useGPT4=True)
    await session.send(reply)


@on_command(name='chatc', only_to_me=False)
async def chatContinue(session: CommandSession):
    if not await permissionCheck(session, 'chatc'):
        return
    userId = session.event.user_id
    content = await getChatContent(session)
    await session.send("继续进行对话，等待回复……")
    reply = await chat(userId, content, isNewConversation=False)
    await session.send(reply)


@on_command(name='chatc4', only_to_me=False)
async def chatContinueGPT4(session: CommandSession):
    if not await permissionCheck(session, 'chatc'):
        return
    if not await permissionCheck(session, 'model'):
        return
    userId = session.event.user_id
    content = await getChatContent(session)
    await session.send("继续进行对话，等待回复……")
    reply = await chat(userId, content, isNewConversation=False, useGPT4=True)
    await session.send(reply)


@on_command(name='chatb', only_to_me=False)
async def chatUndo(session: CommandSession):
    if not await permissionCheck(session, 'chatc'):
        return
    await undo(session.event.user_id)
    await session.send("已撤回一次对话")


@on_command(name='chatr', only_to_me=False)
async def chatRetry(session: CommandSession):
    if not await permissionCheck(session, 'chatc'):
        return
    userId = session.event.user_id
    content = await getChatContent(session)
    lastMessage = await undo(userId)
    inputContent = content if session.current_arg_text else lastMessage['content']
    await session.send("已撤回一次对话，重新生成回复中……")
    reply = await chat(userId, inputContent, isNewConversation=False)
    await session.send(reply)


@on_command(name='chatr4', only_to_me=False)
async def chatRetryGPT4(session: CommandSession):
    if not await permissionCheck(session, 'chatc'):
        return
    if not await permissionCheck(session, 'model'):
        return
    userId = session.event.user_id
    content = await getChatContent(session)
    lastMessage = await undo(userId)
    inputContent = content if session.current_arg_text else lastMessage['content']
    await session.send("已撤回一次对话，重新生成回复中……")
    reply = await chat(userId, inputContent, isNewConversation=False, useGPT4=True)
    await session.send(reply)


@on_command(name='chat_user', only_to_me=False)
async def chatUserInfo(session: CommandSession):
    userId = session.event.user_id
    chatUser = await db.getChatUser(userId)
    if chatUser is None:
        await session.send("你没有chat功能的使用权限。")
        return

    output = f"你已使用的token量: {chatUser.tokenUse + chatUser.tokenUseGPT4}\n"
    output += f"当前chat功能使用权限：\n"
    output += f"连续对话：{'可用' if chatUser.allowContinue else '不可用'}\n"
    output += f"任意私聊：{'可用' if chatUser.allowPrivate else '不可用'}\n"
    output += f"任意群聊：{'可用' if chatUser.allowGroup else '不可用'}\n"
    output += f"角色切换：{'可用' if chatUser.allowRole else '不可用'}\n"
    output += f"模型切换：{'可用' if chatUser.allowModel else '不可用'}\n"
    output += f"当前使用模型：{chatUser.chosenModel}\n"

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
    if not await permissionCheck(session, "model"):
        return
    userId = session.event.user_id
    strippedText = session.current_arg_text.strip()
    if strippedText:
        if strippedText == "gpt-4" or strippedText == "gpt4":
            newModel = "gpt-4o"
        elif strippedText == "gpt-4-mini" or strippedText == "gpt4-mini":
            newModel = "gpt-4o-mini"
        elif "deepseek" in strippedText:
            newModel = "deepseek-chat"
        elif "deepseek-r" in strippedText:
            newModel = "deepseek-reasoner"
        else:
            newModel = strippedText
            await session.send("注意，你定义的模型名称不在预设列表，可能无效！")
    else:
        newModel = "gpt-4o-mini"
    await db.updateUsingModel(userId, newModel)
    output = f"已切换到{newModel}模型"
    await session.send(output)


@on_command(name='save_conversation', only_to_me=False)
async def _(session: CommandSession):
    if not await isSuperAdmin(session.event.user_id):
        return
    userId = session.event.user_id
    userInfo = await db.getChatUser(userId)
    history = await readOldConversation(userId)
    timeStr = time.strftime("%Y-%m-%d-%H-%M", time.localtime())
    fileName = f"{userId}_{timeStr}_{userInfo.chosenModel}.json"
    savePath = HISTORY_PATH + fileName
    with open(savePath, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=4)
    await session.send(f"已保存当前对话记录至{fileName}")


@on_command(name='chat_help', only_to_me=False)
async def chatHelp(session: CommandSession):
    if not await permissionCheck(session, "base"):
        await session.send("你没有chat功能的使用权限。（在特定群聊可使用基础功能）")
        return
    userId = session.event.user_id
    chatUser = await db.getChatUser(userId)
    output = "chat_user: 查看chat权限等相关信息\nchat: 开始一个新对话"
    if chatUser.allowContinue:
        output += "\nchatc: 继续上一轮对话\nchatb: 撤回上一轮对话\nchatr: 撤回上一轮对话并重新生成"
    if chatUser.allowRole:
        output += "\nchatn: 无视当前角色设定，开始一个新对话"
        output += "\nrole_change: 切换当前角色\nrole_detail: 查看角色描述信息\nrole_update: 新增/更新角色描述信息(-g)\nrole_delete: 删除角色"
    if chatUser.allowModel:
        output += "\nmodel_change: 切换语言模型（gpt4o-mini/gpt4o/deepseek/deepseek-r）"
    if await isSuperAdmin(session.event.user_id):
        output += "\nchat_user_update: 更改指定人员chat权限(-c -p -g -r -m)"
        output += "\nsave_conversation: 保存当前对话记录"
    output += "\n\n当前默认使用的模型：gpt-4o-mini\n当前使用的是收费api，请勿滥用！"
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


async def chat(userId, content, isNewConversation: bool, useDefaultRole=False, useGPT4=False, retryCount=0):
    chatUser = await db.getChatUser(userId)
    model = "gpt-4o" if useGPT4 else chatUser.chosenModel
    roleId = 0 if useDefaultRole else chatUser.chosenRoleId
    role = await db.getChatRoleById(roleId)
    history = await getNewConversation(roleId) if isNewConversation else await readOldConversation(userId)
    history.append({"role": "user", "content": content})

    try:
        reply, tokenUsage = await getChatReply(model, history)
        for word in sensitiveWords:
            reply = reply.replace(word, "*" * len(word))
        await db.addTokenUsage(chatUser, model, tokenUsage)
        saveConversation(userId, history)

        roleSign = f"\nRole: {role.name}" if role.id != 0 and isNewConversation else ""
        modelSign = "(GPT-4o)" if model == "gpt-4o" else ("(deepseek)" if "deepseek" in model else "")
        tokenSign = f"\nTokens{modelSign}: {tokenUsage}"
        return reply + "\n" + roleSign + tokenSign
    except Exception as e:
        reason = str(e) if str(e) else "Timeout"
        await sendLog(f"userId: {userId} 的 {model} api调用出现异常，异常原因为：{reason}\nRetry次数：{retryCount}")
        # print(traceback.format_exc())
        print(f"Catch Time: {datetime.datetime.now().timestamp()}")
        if retryCount < 1:
            return await chat(userId, content, isNewConversation, useDefaultRole, useGPT4, retryCount + 1)
        else:
            return "对话出错了，请稍后再试。"


async def getChatReply(model, history, maxTokens=None):
    startTimeStamp = datetime.datetime.now().timestamp()
    print(f"Start Time: {startTimeStamp}")
    response = await getResponseAsync(model, history, maxTokens)
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


async def getResponseAsync(model, history, maxTokens=None):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, getResponse, model, history, maxTokens)


def getResponse(model, history, maxTokens):
    if 'deepseek' in model:
        return deepseekClient.chat.completions.create(model=model, messages=history, timeout=59)
    if maxTokens:
        return openaiClient.chat.completions.create(model=model, messages=history, max_tokens=maxTokens, timeout=60)
    else:
        return openaiClient.chat.completions.create(model=model, messages=history, timeout=60)


async def undo(userId):
    history = await readOldConversation(userId)
    history.pop()
    latestWord = history.pop()
    saveConversation(userId, history)
    return latestWord


async def getNewConversation(roleId):
    role = await db.getChatRoleById(roleId)
    return [{"role": "system", "content": [{"type": "text", "text": role.detail}]}] if role.detail else []


async def readOldConversation(userId):
    historyPath = HISTORY_PATH + str(userId) + ".json"
    if not os.path.exists(historyPath):
        chatUser = await db.getChatUser(userId)
        return await getNewConversation(chatUser)
    with open(historyPath, encoding="utf-8") as f:
        return json.load(f)


def saveConversation(userId, history):
    historyPath = HISTORY_PATH + str(userId) + ".json"
    with open(historyPath, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=4)


async def permissionCheck(session: CommandSession, checker: str):
    userId = session.event.user_id
    if checker == 'admin':
        return await isSuperAdmin(userId)

    isGroupCall = session.ctx['message_type'] == 'group'
    groupId = session.event.group_id if isGroupCall else None
    chatUser = await db.getChatUser(userId)
    if chatUser is None:
        if groupId not in unlimitedGroup:
            return False
        await db.updateChatUser(userId, '')

    if checker == 'base':
        return True
    if checker == 'chat':
        if isGroupCall:
            if groupId in unlimitedGroup:
                return True
            return chatUser.allowGroup
        if not isGroupCall:
            return chatUser.allowPrivate
    if checker == 'chatc':
        if isGroupCall:
            if groupId in unlimitedGroup:
                return True
            return chatUser.allowGroup and chatUser.allowContinue
        if not isGroupCall:
            return chatUser.allowPrivate and chatUser.allowContinue
    if checker == 'role':
        return chatUser.allowRole
    if checker == 'model':
        return chatUser.allowModel

    return False
