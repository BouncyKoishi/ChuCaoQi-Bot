import nonebot
from nonebot import on_notice, NoticeSession
from nonebot import on_request, RequestSession
from nonebot import on_command, CommandSession
from kusa_base import config, sendLog, isSuperAdmin
from utils import getUserAndGroupMsg


@on_request('group')
async def newMemberHandle(session: RequestSession):
    groupNum = session.event.group_id
    adder_id = session.event.user_id
    allow_list = config['group']['adminAuthGroup']
    if groupNum in allow_list:
        bot = nonebot.get_bot()
        st = f"{adder_id}申请进群。加群备注为：\n" + session.event.comment
        await bot.send_group_msg(group_id=groupNum, message=st)
        await sendLog(f'群聊{groupNum}:' + st)


@on_request('friend')
async def newFriendHandle(session: RequestSession):
    adderId = session.event.user_id
    friendCode = getFriendAddCode(str(adderId))
    logInfo = f'收到一个来自{adderId}的好友申请，'
    if friendCode == session.event.comment:
        await session.approve()
        await sendLog(logInfo + '已自动通过')
    else:
        # await session.reject(reason='Code Error')
        await sendLog(logInfo + '好友码错误，待手动处理')


@on_command(name='friend_code', only_to_me=False)
async def friendCodeOutput(session: CommandSession):
    userId = session.event.user_id
    if not await isSuperAdmin(userId):
        return
    friendCode = getFriendAddCode(session.current_arg_text.strip())
    await session.send(f"此QQ号的FriendCode为: {friendCode}")


def getFriendAddCode(friendId):
    hashingStr = friendId + 'confounding'
    return f'{hash(hashingStr) % 100000000 :0>8}'


@on_notice('group_recall')
async def recallHandle(session: NoticeSession):
    bot = nonebot.get_bot()
    event = session.event
    if event.notice_type == "group_recall":
        recall_message_id = event.message_id
        recall_message_content = await bot.get_msg(message_id=recall_message_id)
        print("Recall Message: " + recall_message_content["message"])

        userMsg, groupMsg = await getUserAndGroupMsg(event.user_id, event.group_id)
        logInfo = f"{userMsg} 在群聊 {groupMsg} 撤回了一条消息\n消息内容: {recall_message_content['message']}"
        await sendLog(logInfo)

