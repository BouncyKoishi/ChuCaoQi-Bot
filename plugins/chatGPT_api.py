import os
import json
import openai
import asyncio
import dbConnection.chat as db
from kusa_base import isSuperAdmin, config
from nonebot import on_command, CommandSession
from utils import nameDetailSplit

os.environ["http_proxy"] = config['web']['proxy']
os.environ["https_proxy"] = config['web']['proxy']
openai.api_key = config['web']['openai']['key']
HISTORY_PATH = u"chatHistory/"


@on_command(name='chat', only_to_me=False)
async def chatNew(session: CommandSession):
    if not await permissionCheck(session, 'chat'):
        return
    userId = session.event.user_id
    content = session.current_arg_text.strip()
    await session.send("已开启新对话，等待回复……")
    reply = await chat(userId, content, True)
    await session.send(reply)


@on_command(name='chatn', only_to_me=False)
async def chatNewWithoutRole(session: CommandSession):
    if not await permissionCheck(session, 'chat'):
        return
    userId = session.event.user_id
    content = session.current_arg_text.strip()
    await session.send("已开启新对话，等待回复……")
    reply = await chat(userId, content, True, True)
    await session.send(reply)


@on_command(name='chatc', only_to_me=False)
async def chatContinue(session: CommandSession):
    if not await permissionCheck(session, 'chatc'):
        return
    userId = session.event.user_id
    content = session.current_arg_text.strip()
    await session.send("继续进行对话，等待回复……")
    reply = await chat(userId, content, False)
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
    content = session.current_arg_text.strip()
    lastMessage = await undo(userId)
    await session.send("已撤回一次对话，重新生成回复中……")
    reply = await chat(userId, content if content else lastMessage['content'], False)
    await session.send(reply)


@on_command(name='chat_user', only_to_me=False)
async def chatUserInfo(session: CommandSession):
    userId = session.event.user_id
    chatUser = await db.getChatUser(userId)
    if chatUser is None:
        await session.send("你没有chat功能的使用权限。")
        return

    output = f"你已使用的token量: {chatUser.tokenUse}\n"
    output += f"你已使用的token量(GPT4): {chatUser.tokenUseGPT4}\n" if chatUser.allowModel else ""
    output += f"当前chat功能使用权限：\n"
    output += f"连续对话：{'可用' if chatUser.allowContinue else '不可用'}\n"
    output += f"私聊：{'可用' if chatUser.allowPrivate else '不可用'}\n"
    output += f"群聊：{'可用' if chatUser.allowGroup else '不可用'}\n"
    output += f"角色切换：{'可用' if chatUser.allowRole else '不可用'}\n"
    output += f"GPT4模型：{'可用' if chatUser.allowModel else '不可用'}\n"

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
    userId = int(''.join(filter(str.isdigit, strippedText)))
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
        await session.send("无相关角色信息，或者你没有权限查看该角色。")
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
        await session.send("无相关角色信息，或者你没有权限使用该角色。")
    else:
        strippedText = "default" if not strippedText else strippedText
        await session.send(f"已切换到{strippedText}角色")


@on_command(name='role_update', only_to_me=False)
async def updateRole(session: CommandSession):
    if not await permissionCheck(session, "role"):
        return
    userId = session.event.user_id
    strippedText = session.current_arg_text.strip()
    isPublicRole = strippedText.startswith("-p") or strippedText.startswith("-public")
    strippedText = strippedText.strip("-public").strip("-p").strip()
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
    chatUser = await db.getChatUser(userId)
    newModel = "gpt-4-1106-preview" if "gpt-3.5-turbo" in chatUser.chosenModel else "gpt-3.5-turbo"
    await db.updateUsingModel(userId, newModel)
    output = f"已切换到{newModel}模型"
    output += "\nGPT4 token的价格比普通token高出一个数量级，请勿用于娱乐！" if "gpt-4" in newModel else ""
    await session.send(output)


@on_command(name='chat_help', only_to_me=False)
async def chatHelp(session: CommandSession):
    if not await permissionCheck(session, "base"):
        await session.send("你没有chat功能的使用权限。")
        return
    userId = session.event.user_id
    chatUser = await db.getChatUser(userId)
    output = "chat_user: 查看chat权限等相关信息\nchat: 开始一个新对话"
    if chatUser.allowContinue:
        output += "\nchatc: 继续上一轮对话\nchatb: 撤回上一轮对话\nchatr: 撤回上一轮对话并重新生成"
    if chatUser.allowRole:
        output += "\nchatn: 无视当前角色设定，开始一个新对话"
        output += "\nrole_change: 切换当前角色\nrole_detail: 查看角色描述信息\nrole_update: 更新角色描述信息(-g)\nrole_delete: 删除角色"
    if chatUser.allowModel:
        output += "\nmodel_change: 切换语言模型（gpt3.5/gpt4）"
    if await isSuperAdmin(session.event.user_id):
        output += "\nchat_user_update: 更改指定人员chat权限(-c -p -g -r -m)"
    output += "\n\n当前默认使用的模型：gpt-3.5-turbo\n当前使用的是收费api，请勿滥用！"
    await session.send(output)


async def chat(userId, content: str, isNewConversation: bool, useDefaultRole: bool = False):
    chatUser = await db.getChatUser(userId)
    roleId = 0 if useDefaultRole else chatUser.chosenRoleId
    role = await db.getChatRoleById(roleId)
    model = chatUser.chosenModel
    if isNewConversation:
        history = await getNewConversation(roleId)
    else:
        history = await readOldConversation(userId)

    history.append({"role": "user", "content": content})

    try:
        response = await getResponseAsync(model, history)
        reply = response['choices'][0]['message']['content']
        usage = response['usage']

        history.append({"role": "assistant", "content": reply})
        await db.addTokenUsage(chatUser, usage['total_tokens'])
        saveConversation(userId, history)

        roleSign = f"\nRole: {role.name}" if role.id != 0 else ""
        gpt4Sign = f"\nModel: GPT-4" if "gpt-4" in model else ""
        tokenSign = f"\nTokens: {usage['total_tokens']}"
        return reply + "\n" + roleSign + gpt4Sign + tokenSign
    except Exception as e:
        print(e)
        return "对话出错了，请稍后再试。"


async def undo(userId):
    history = await readOldConversation(userId)
    history.pop()
    latestWord = history.pop()
    saveConversation(userId, history)
    return latestWord


async def getResponseAsync(model, history):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, getResponse, model, history)


def getResponse(model, history):
    return openai.ChatCompletion.create(model=model, messages=history)


async def getNewConversation(roleId):
    role = await db.getChatRoleById(roleId)
    return [{"role": "system", "content": role.detail}]


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

    chatUser = await db.getChatUser(userId)
    if chatUser is None:
        return False
    if checker == 'base':
        return True
    if checker == 'chat':
        if session.ctx['message_type'] == 'private':
            return chatUser.allowPrivate
        if session.ctx['message_type'] == 'group':
            return chatUser.allowGroup
    if checker == 'chatc':
        if session.ctx['message_type'] == 'private':
            return chatUser.allowPrivate and chatUser.allowContinue
        if session.ctx['message_type'] == 'group':
            return chatUser.allowGroup and chatUser.allowContinue
    if checker == 'role':
        return chatUser.allowRole
    if checker == 'model':
        return chatUser.allowModel

    return False
