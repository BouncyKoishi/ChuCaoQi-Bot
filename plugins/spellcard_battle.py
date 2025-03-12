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
    await session.send('已创建单机对战，请选择对战符卡。\n')
    await arenaCardSelection(session, newBattle, True)


async def arenaCardSelection(session: CommandSession, battle: Battle, singleMode=False):
    userId = session.ctx['user_id']

    selectedCards = []
    for cost in range(0, 5):
        # cardOptions = getRandomCardsWithSameCost(cost // 2 + 1)
        cardOptions = getRandomCardsWithSameCost(0)
        cardDescriptions = [
            f"{i + 1}. {card.name}: HP{card.cardHp} 攻击{card.atkPoint} 命中{card.hitPoint} 回避{card.dodPoint} 特殊效果：{card.describe}"
            for i, card in enumerate(cardOptions)]
        print(f"请选择一张符卡:\n" + "\n".join(cardDescriptions))
        userResponse = await session.aget(prompt=f"请选择一张符卡:\n" + "\n".join(cardDescriptions))
        if not re.match(r'^\d+$', userResponse):
            await session.send('非序号：符卡选择失败，请重新选择。')
            cost -= 1
            continue
        selectedIndex = int(userResponse) - 1
        if selectedIndex < 0 or selectedIndex >= len(cardOptions):
            await session.send('无效的序号：符卡选择失败，请重新选择。')
            cost -= 1
            continue
        selectedCard = cardOptions[selectedIndex]
        selectedCards.append(selectedCard)

    battler = battle.creator if userId == battle.creatorId else battle.joiner
    battler.chosenCard = selectedCards
    cardInfos = [f"{i + 1}. {card.name}" for i, card in enumerate(selectedCards)]
    await session.send(f'竞技场符卡选择成功！您选择的五张符卡为: {cardInfos}')

    if userId not in battle.spellCardSettled:
        battle.spellCardSettled.append(userId)
    if len(battle.spellCardSettled) == 1 and not singleMode:
        info = '你完成了符卡配置！等待另一位玩家进行配置。'
        await bot.send_group_msg(group_id=battle.groupId, message=info)
    else:
        info = '已完成符卡配置，对战启动中……\n请使用!符卡选择 [序号]指令选择第一张需要宣言的符卡。'
        await bot.send_group_msg(group_id=battle.groupId, message=info)


def getRandomCardsWithSameCost(cardCost: int) -> list:
    allCards = utils.getAllCards()
    sameCostCards = [card for card in allCards if card.cost == cardCost]
    return random.sample(sameCostCards, 3)


@on_command(name='对战信息', only_to_me=False)
async def _(session: CommandSession):
    userId = session.ctx['user_id']
    battle = inBattle(userId)
    if not battle:
        await session.send('您不在一场符卡对战中！')
        return
    # 需要展示的信息：己方剩余可选符卡、对方剩余可选符卡、己方状态、对方当前符卡和状态、当前回合信息
    # todo


@on_command(name='符卡选择', only_to_me=False)
async def spellCardSelect(session: CommandSession):
    global battleList
    userId = session.ctx['user_id']
    battle = inBattle(userId)
    if not battle:
        await session.send('您不在一场符卡对战中！')
        return
    if userId not in battle.spellCardSettled:
        await session.send('您还未选择符卡！')
        return

    cardIndex = int(session.current_arg_text.strip()) - 1
    battler = battle.creator if userId == battle.creatorId else battle.joiner
    success, failReason = battler.setNewMainCard(cardIndex)
    if not success:
        await session.send(f'{failReason}')
        return

    selectedCard = battler.chosenCard[cardIndex]
    battler.nowCard = selectedCard
    await session.send(f'已选择符卡：{selectedCard.name}。')
    if battle.creator.nowCard and battle.joiner.nowCard:
        await battleMain(battle)


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
