import nonebot
import aiocqhttp
from nonebot import on_websocket_connect
from nonebot import on_request, RequestSession
from nonebot import on_command, CommandSession
from kusa_base import config, sendLog, isSuperAdmin, appendFriendList

friendHandleTimestamp = 0


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
        if session.event.comment.strip() == '':
            isSysu = groupNum == config['group']['sysu']
            # 原napcat实现中没有user2_id！这里是修改了napcat的源码后实现的
            if isSysu and hasattr(session.event, 'user2_id') and session.event.user2_id != 0:
                sign = f'这是一个未填写备注信息的邀请进群。请[CQ:at,qq={session.event.user2_id}] 说明入群者的身份。'
                await bot.send_group_msg(group_id=groupNum, message=sign)
                return
            rejectReason = '请填写年级专业东方兴趣方向或说明来意' if isSysu else '加群备注不能为空'
            await bot.set_group_add_request(
                flag=session.event.flag,
                sub_type=session.event.sub_type,
                approve=False,
                reason=rejectReason,
            )
            await bot.send_group_msg(
                group_id=groupNum,
                message='备注信息为空，已自动拒绝加群申请。',
            )
            await sendLog(f'群聊{groupNum}触发空备注风控，已拒绝{adder_id}的申请')
            return
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
        strangerInfo = await bot.get_stranger_info(user_id=adder_id)
        if 0 < strangerInfo['qqLevel'] < 8:
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
            await sendLog(f'群聊{groupNum}触发等级风控（{strangerInfo["level"]}），已拒绝{adder_id}的申请')
        if strangerInfo['qqLevel'] == 0:
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
        await appendFriendList(str(adderId))
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


@on_websocket_connect
async def friendListInit(event: aiocqhttp.Event):
    bot = nonebot.get_bot()
    friendListInfo = await bot.get_friend_list()
    friendListQQ = [str(friend['user_id']) for friend in friendListInfo]
    await appendFriendList(friendListQQ)



