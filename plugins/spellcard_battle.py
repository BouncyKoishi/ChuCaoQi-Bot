from plugins.scBattle.scBattleObj import Battle
from plugins.scBattle.scBattlerObj import Battler
import plugins.scBattle.scBattleUtils as utils
import dbConnection.kusa_item as itemDB
import re
import string
import codecs
import nonebot
from nonebot import on_command, CommandSession

bot = nonebot.get_bot()
battleList = {}


def inBattle(qq) -> Battle or None:
    for battle in battleList.values():
        if battle.creatorId == qq or battle.joinerId == qq:
            return battle
    return None


def waitingBattleQQList() -> list:
    waitingList = []
    for battle in battleList.values():
        if not battle.joinerId:
            waitingList.append(battle.creatorId)
    return waitingList


@on_command(name='符卡对战', only_to_me=False)
async def _(session: CommandSession):
    global battleList
    userId = session.ctx['user_id']
    groupId = session.ctx['group_id']
    if inBattle(userId):
        await session.send('您已经在一场符卡对战中！')
        return
    print('BeforeOpen:' + str(battleList))
    newBattle = Battle(userId, groupId)
    await newBattle.setCreator()
    battleList[userId] = newBattle
    await session.send('已创建对战，其他人可使用 !加入符卡对战 [对方qq号] 指令加入本场对战。')
    print('OnOpen:' + str(battleList))


@on_command(name='取消符卡对战', only_to_me=False)
async def _(session: CommandSession):
    global battleList
    userId = session.ctx['user_id']
    battle = inBattle(userId)
    if not battle:
        await session.send('您不在一场符卡对战中！')
        return
    if battle.gameRound:
        await session.send('对战已经开始，无法取消。')
        return
    battleList.pop(userId)
    await session.send('已取消对战。')


@on_command(name='加入符卡对战', only_to_me=False)
async def join(session: CommandSession):
    global battleList
    userId = session.ctx['user_id']
    if inBattle(userId):
        await session.send('您已经在一场符卡对战中！')
        return

    argId = session.current_arg_text.strip()
    if not argId:
        waitingList = waitingBattleQQList()
        if len(waitingList) == 0:
            await session.send('当前没有正在等待加入的对战。')
            return
        if len(waitingList) == 1:
            argId = waitingList[0]
        else:
            await session.send('当前有多场对战正在等待加入，请指定开启对战方的qq号。')
            return
    battle = inBattle(int(argId))
    if not battle:
        await session.send('该符卡对战未开启。')
        return
    if battle.joinerId:
        await session.send('该符卡对战人员已满。')
        return

    print('BeforeJoin:' + str(battleList))
    await battle.joinBattle(userId)
    await session.send(f'加入对战成功！等待双方配置符卡……\n使用“!符卡配置”指令以进行配置，建议私聊配置\n当前所有符卡列表：https://docs.qq.com/sheet/DSHNYTW9mWEhTVWJx')
    battleList[int(argId)] = battle
    print('OnJoin:' + str(battleList))


async def battleMain(battle: Battle):
    await sendTitle(battle.creatorId)
    await sendTitle(battle.joinerId)
    print('BeforeGameStart:' + str(battleList))
    battle.gameStart()
    print('OnGameStart:' + str(battleList))
    gameBreak = False
    while not gameBreak:
        cardBreak, gameBreak = battle.cardBreakJudge()
        if cardBreak:
            await bot.send_group_msg(group_id=battle.groupId, message=battle.lastTurnInfoImg)
            continue
        battle.turnStart()
        cardBreak, gameBreak = battle.cardBreakJudge()
        if cardBreak:
            await bot.send_group_msg(group_id=battle.groupId, message=battle.lastTurnInfoImg)
            continue
        battle.turnGetBasePoint()
        battle.turnHurtValueCalc()
        battle.turnHpChange()
        cardBreak, gameBreak = battle.cardBreakJudge()
        if cardBreak:
            await bot.send_group_msg(group_id=battle.groupId, message=battle.lastTurnInfoImg)
            continue
        battle.turnEnd()
    print('OnMainCycleEnd:' + str(battleList))
    endGame, loserName = battle.endGameCheck()
    await battleEnd(battle, loserName)


async def battleEnd(battle: Battle, loserName):
    global battleList
    message = ''
    if len(loserName) == 1:
        message = f"{loserName[0]} 已被击破！"
    elif len(loserName) == 2:
        message = f"{loserName[0]} 和 {loserName[1]} 同时被对方击破！"
    await bot.send_group_msg(group_id=battle.groupId, message=message)
    print('BeforeEndGame:' + str(battleList))
    battleList.pop(battle.creatorId)


async def sendTitle(userId):
    titleExist = await itemDB.getItemAmount(userId, '早期符卡对战者')
    if titleExist == 0:
        await itemDB.changeItemAmount(userId, '早期符卡对战者', 1)


@on_command(name='符卡查询', only_to_me=False)
async def showCardInfo(session: CommandSession):
    cardId = session.current_arg_text.strip()
    cardId = int(cardId)
    card = utils.getCardObjById(cardId)
    if not card:
        await session.send('没有查询到id对应的符卡信息！')
        return
    await session.send(card.getCardDescribe(cardId))


@on_command(name='符卡配置', only_to_me=False)
async def setCard(session: CommandSession):
    userId = session.ctx['user_id']
    argText = session.current_arg_text.strip()
    isRandom = True if 'random' in argText.lower() else False
    regex = r'\d+ \d+ \d+ \d+ \d+'
    argMatch = re.search(regex, argText)
    if not argMatch and not isRandom:
        with codecs.open(u'text/符卡配置帮助.txt', 'r', 'utf-8') as f:
            await session.send(f.read().strip())
        return

    battle = inBattle(userId)
    if not battle:
        await session.send('您不在一场符卡对战中！')
        return
    if battle.gameRound is not None and battle.gameRound != 0:
        await session.send('对战已开始，不可中途更换符卡！')
        return

    if isRandom:
        setCardSuccess, cost = setCardInRandom(battle, userId)
    else:
        setCardSuccess, cost = setCardByCardString(battle, userId, argText)

    if not setCardSuccess:
        if cost is None:
            await session.send('符卡配置失败：你选择的某个编号不存在对应符卡。')
        else:
            await session.send(f'符卡配置失败：你选择的符卡Cost总和为{cost}, 超出Cost上限：7')
        return
    await session.send(f'符卡配置成功！选择的符卡总Cost为{cost}')

    print('BeforeSetCard:' + str(battleList))
    if userId not in battle.spellCardSettled:
        battle.spellCardSettled.append(userId)
    if len(battle.spellCardSettled) == 1:
        info = '一位玩家完成了符卡配置！等待另一位玩家。'
        await bot.send_group_msg(group_id=battle.groupId, message=info)
        print('OnSetCard1:' + str(battleList))
    elif len(battle.spellCardSettled) == 2:
        info = '所有玩家已完成符卡配置，对战启动中……'
        await bot.send_group_msg(group_id=battle.groupId, message=info)
        print('OnSetCard2:' + str(battleList))
        await battleMain(battle)


def setCardByCardString(battle: Battle, userId: int, argText: string):
    battler = battle.creator if userId == battle.creatorId else battle.joiner
    mainCardList = list(map(lambda x: int(x), argText.split(" ")))
    return setCardByIdList(battler, mainCardList)


def setCardInRandom(battle: Battle, userId: int):
    battler = battle.creator if userId == battle.creatorId else battle.joiner
    cardIdList = utils.getRandomCardIdList()
    return setCardByIdList(battler, cardIdList)


def setCardByIdList(battler: Battler, cardIdList: list):
    if not utils.isCardIdListValid(cardIdList):
        return False, None
    cost = utils.getCardTotalCost(cardIdList)
    if cost > 7:
        return False, cost
    battler.cardIdList = cardIdList
    print(cardIdList)
    return True, cost


@on_command(name="单机对战", only_to_me=False)
async def _(session: CommandSession):
    global battleList
    userId = session.ctx['user_id']
    groupId = session.ctx['group_id']
    if inBattle(userId):
        await session.send('您已经在一场符卡对战中！')
        return
    newBattle = Battle(userId, groupId)
    await newBattle.setCreator()
    await newBattle.setSingleBattleEnemy('Cirno', [14, 14, 14, 14, 14])
    battleList[userId] = newBattle
    await session.send('已创建单机对战，使用“!符卡配置”指令以设置你本次使用的符卡。\n当前所有符卡列表：https://docs.qq.com/sheet/DSHNYTW9mWEhTVWJx')

