import nonebot
from nonebot import on_notice, NoticeSession
from nonebot import on_request, RequestSession
from nonebot import on_command, CommandSession
from kusa_base import config, sendLog, isSuperAdmin
from utils import getUserAndGroupMsg


@on_request('group')
async def newMemberHandle(session: RequestSession):
    groupNum = session.event.group_id
    allow_list = config['group']['adminAuthGroup']
    if groupNum not in allow_list:
        return

    adder_id = session.event.user_id
    bot = nonebot.get_bot()
    st = f"{adder_id}申请进群。加群备注为：\n" + session.event.comment
    await bot.send_group_msg(group_id=groupNum, message=st)
    await sendLog(f'群聊{groupNum}:' + st)
    if session.event.sub_type == 'add':
        for keyword in ('交流学习', '通过一下', '管理员你好', '朋友推荐', ):
            if keyword in session.event.comment:
                await bot.set_group_add_request(
                    flag=session.event.flag,
                    sub_type=session.event.sub_type,
                    approve=False,
                    reason='触发风控，已自动拒绝加群申请',
                )
                await bot.send_group_msg(
                    group_id=groupNum,
                    message='触发关键词风控，已自动拒绝加群申请。如有需要，请联系该用户通过邀请方式进群。',
                )
                await sendLog(f'群聊{groupNum}触发关键词风控（{keyword}），已拒绝{adder_id}的申请')
                return
        stranger_info = await bot.get_stranger_info(user_id=adder_id)
        if 0 < stranger_info['level'] < 8:
            await bot.set_group_add_request(
                flag=session.event.flag,
                sub_type=session.event.sub_type,
                approve=False,
                reason='触发风控，已自动拒绝加群申请',
            )
            await bot.send_group_msg(
                group_id=groupNum,
                message='触发等级风控，已自动拒绝加群申请。如有需要，请联系该用户通过邀请方式进群。',
            )
            await sendLog(f'群聊{groupNum}触发等级风控（{stranger_info["level"]}），已拒绝{adder_id}的申请')
        if stranger_info['level'] == 0:
            await bot.send_group_msg(
                group_id=groupNum,
                message='注意：该用户隐藏了QQ等级，请注意分辨。',
            )


@on_request('friend')
async def newFriendHandle(session: RequestSession):
    # 因不明原因一次好友申请会收到多条消息，加个防抖
    global friendHandleTimestamp
    if session.event.time - friendHandleTimestamp < 2:
        return
    friendHandleTimestamp = session.event.time

    adderId = session.event.user_id
    friendCode = getFriendAddCode(str(adderId))
    logInfo = f'收到一个来自{adderId}的好友申请，'
    if friendCode == session.event.comment:
        await session.approve()
        await sendLog(logInfo + '已自动通过')
    else:
        await session.reject(reason='好友码错误，请向维护者申请好友码')
        await sendLog(logInfo + '因好友码错误已自动拒绝')


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



