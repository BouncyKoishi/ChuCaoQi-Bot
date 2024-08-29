from plugins.scBattle.scBattleObj import Battle
from plugins.scBattle.scBattlerObj import Battler
import plugins.scBattle.scBattleUtils as utils
import re
import random
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
    await session.send('已创建对战，请选择对战符卡。其他人可使用 !加入符卡对战 [对方qq号] 指令加入本场对战。')
    print('OnOpen:' + str(battleList))
    await arenaCardSelection(session, newBattle)


@on_command(name='退出符卡对战', only_to_me=False)
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
    if battle.creatorId == userId:
        battleList.pop(userId)
        await session.send('已取消你创建的对战。')
    if battle.joinerId == userId:
        await battle.leaveBattle()
        await session.send('已退出当前对战。')


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
    await session.send(f'加入对战成功！请选择对战符卡。')
    battleList[int(argId)] = battle
    print('OnJoin:' + str(battleList))
    await arenaCardSelection(session, battle)


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
    await session.send('已创建单机对战，请选择对战符卡。\n当前所有符卡列表：https://docs.qq.com/sheet/DSHNYTW9mWEhTVWJx')
    await arenaCardSelection(session, newBattle, True)


async def arenaCardSelection(session: CommandSession, battle: Battle, singleMode=False):
    userId = session.ctx['user_id']

    selectedCards = []
    for cost in range(0, 5):
        cardOptions = getRandomCardsWithSameCost(cost // 2 + 1)
        cardDescriptions = [f"{i + 1}. {card.name}: ATK{card.atkPoint} DEF{card.defPoint} DOD{card.dodPoint} 特殊效果：{card.describe}" for i, card in enumerate(cardOptions)]
        print(f"请选择一张符卡:\n" + "\n".join(cardDescriptions))
        userResponse = await session.aget(prompt=f"请选择一张符卡:\n" + "\n".join(cardDescriptions))
        selectedIndex = int(userResponse) - 1
        if selectedIndex < 0 or selectedIndex >= len(cardOptions):
            await session.send('无效的序号：符卡选择失败。')
            return
        selectedCard = cardOptions[selectedIndex].id
        if selectedCard:
            selectedCards.append(selectedCard)

    battler = battle.creator if userId == battle.creatorId else battle.joiner
    battler.cardIdList = selectedCards
    await session.send(f'竞技场符卡选择成功！选择的符卡ID为: {selectedCards}')

    if userId not in battle.spellCardSettled:
        battle.spellCardSettled.append(userId)
    if len(battle.spellCardSettled) == 1 and not singleMode:
        info = '你完成了符卡配置！等待另一位玩家进行配置。'
        await bot.send_group_msg(group_id=battle.groupId, message=info)
        print('OnSetCard1:' + str(battleList))
    else:
        info = '所有玩家已完成符卡配置，对战启动中……'
        await bot.send_group_msg(group_id=battle.groupId, message=info)
        print('OnSetCard2:' + str(battleList))
        await battleMain(battle)


def getRandomCardsWithSameCost(cardCost: int):
    allCards = utils.getAllCards()
    sameCostCards = [card for card in allCards if card.cost == cardCost]
    print(sameCostCards)
    return random.sample(sameCostCards, 3)


async def battleMain(battle: Battle):
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


