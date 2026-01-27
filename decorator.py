import time
from functools import wraps
from typing import Optional, List, Callable

from nonebot import CommandSession, NLPSession
from kusa_base import sendLog
from utils import getUserAndGroupMsg


def CQ_injection_check_command(func):
    @wraps(func)
    def check(session: CommandSession):
        if 'CQ:' in session.current_arg:
            return CQInjectionHolder(session)
        return func(session)

    return check


async def CQInjectionHolder(session):
    nowTime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    groupId = session.ctx['group_id'] if 'group_id' in session.ctx else None
    userMsg, groupMsg = await getUserAndGroupMsg(session.ctx['user_id'], groupId)
    await sendLog(f"{userMsg} 在 {groupMsg} 触发了CQ Injection风控！触发时间：{nowTime}")
    await session.send("[风控]取消本指令响应。")


def on_reply_command(commands: Optional[List[str]] = None):
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(session: NLPSession):
            if not session.ctx['message'] or session.ctx['message'][0].type != 'reply':
                return

            strippedText = session.ctx['message'][-1].data.get('text', '').strip()
            if not strippedText.startswith('#'):
                return

            # 检查是否是有效的指令（支持带空格的情况，如"#nsfw"）
            if commands is not None:
                commandMatch = False
                for cmd in commands:
                    if strippedText == cmd or strippedText.startswith(cmd + ' '):
                        commandMatch = True
                        break
                if not commandMatch:
                    return

            replyId = str(session.ctx['message'][0].data['id'])
            replyMessageCtx = await session.bot.get_msg(message_id=replyId)
            return await func(session, replyMessageCtx=replyMessageCtx)

        return wrapper

    return decorator

