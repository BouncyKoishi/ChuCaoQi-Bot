from kusa_base import isSuperAdmin, config
from nonebot import on_natural_language, NLPSession
from nonebot import on_command, CommandSession

banMode = 0
messageHistory = ['', '', '', '']
fourRepeatingBanList = []
fourRepeatingSign = False


@on_command(name='ban_mode_change', only_to_me=False)
async def _(session: CommandSession):
    global banMode
    if await isSuperAdmin(session.ctx['user_id']):
        banMode = 0 if banMode == 1 else 1
        await session.send(f'Succeed! banMode = {banMode}')


@on_natural_language(keywords=None, only_to_me=False)
async def ban_repeat(session: NLPSession):
    global fourRepeatingBanList
    if 'group_id' not in session.ctx:
        return
    groupNum = session.ctx['group_id']
    if banMode and groupNum == config['group']['sysu']:
        set_history(session.msg)
        repeatFour = isRepeatFourTimes()
        repeatSelf = isRepeatSelf()
        if banJudge(repeatFour):
            await session.bot.set_group_ban(group_id=groupNum, user_id=fourRepeatingBanList[-2], duration=120)
        if repeatSelf:
            if session.ctx['user_id'] in fourRepeatingBanList:
                await session.bot.set_group_ban(group_id=groupNum, user_id=session.ctx['user_id'], duration=60)
        else:
            fourRepeatingBanList = []
        setRepeatingBannedName(session.ctx['user_id'])
        setFourRepeatingSign(repeatFour)


def set_history(message):
    global messageHistory
    messageHistory[0] = messageHistory[1]
    messageHistory[1] = messageHistory[2]
    messageHistory[2] = messageHistory[3]
    messageHistory[3] = message


def setRepeatingBannedName(qq):
    global fourRepeatingBanList
    fourRepeatingBanList.append(qq)


def setFourRepeatingSign(r):
    global fourRepeatingSign
    fourRepeatingSign = r


def banJudge(repeat):
    if fourRepeatingSign and not repeat:
        return True
    return False


def isRepeatFourTimes():
    if messageHistory[3] != '':
        if messageHistory[0] == messageHistory[1] and messageHistory[0] == messageHistory[2] and messageHistory[0] == messageHistory[3]:
            return True
    return False


def isRepeatSelf():
    if messageHistory[3] != '':
        if messageHistory[2] == messageHistory[3]:
            return True
    return False
