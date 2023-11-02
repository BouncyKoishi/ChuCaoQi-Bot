import time
from functools import wraps

from nonebot import CommandSession
from kusa_base import sendLog
from utils import getUserAndGroupMsg


def CQ_injection_check_command(func):
    @wraps(func)
    def check(session: CommandSession):
        if 'CQ:' in session.current_arg:
            return holder(session)
        return func(session)

    return check


async def holder(session):
    nowTime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    groupId = session.ctx['group_id'] if 'group_id' in session.ctx else None
    userMsg, groupMsg = await getUserAndGroupMsg(session.ctx['user_id'], groupId)
    await sendLog(f"{userMsg} 在 {groupMsg} 触发了CQ Injection风控！触发时间：{nowTime}")
    await session.send("[风控]取消本指令响应。")
