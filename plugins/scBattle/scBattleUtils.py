import re
import os
import random
import nonebot
import inspect
import importlib
import itertools
import dbConnection.db as baseDB


def runDiceByString(diceStr):
    if not diceStr:
        return 0
    diceRegex = r'(\d{1,2})d(\d{1,2})'
    diceInfoList = re.findall(diceRegex, diceStr)
    diceResultList = []
    for diceInfo in diceInfoList:
        amount = int(diceInfo[0])
        maxPoint = int(diceInfo[1])
        diceResultList.append(dice(amount, maxPoint))
    for i in range(0, len(diceResultList)):
        diceStr = re.sub(diceRegex, str(diceResultList[i]), diceStr, 1)
    return eval(diceStr)


def dice(diceNum, maxPoint):
    sumPoint = 0
    while diceNum:
        dicePoint = random.randint(1, maxPoint)
        sumPoint += dicePoint
        diceNum -= 1
    return sumPoint


async def getBattlerName(userId, groupId):
    try:
        bot = nonebot.get_bot()
        user = await baseDB.getUser(userId)
        if user and user.name:
            return user.name
        senderInfor = await bot.get_group_member_info(user_id=userId, group_id=groupId)
        return senderInfor['nickname']
    except:
        return str(userId)


def getClassesDict(path):
    idClassesDict = {}
    costIdDict = {}
    for root, dirs, files in os.walk(path):
        for filename in files:
            name, extension = os.path.splitext(filename)
            if extension == '.py':
                moduleName = os.path.join(root, name).replace(os.sep, '.')
                module = importlib.import_module(moduleName)
                members = inspect.getmembers(module)
                for member_name, member in members:
                    if inspect.isclass(member) and 'Abstract' not in member_name:
                        if hasattr(member, 'id'):
                            idClassesDict[member.id] = member
                            if hasattr(member, 'cost'):
                                if member.cost not in costIdDict:
                                    costIdDict[member.cost] = []
                                costIdDict[member.cost].append(member.id)
    return idClassesDict, costIdDict


def getCostCountList(cardCount, costLimit, costSum):
    # 获取所有可用的符卡cost组合
    result = []
    for singleList in itertools.product(range(cardCount + 1), repeat=costLimit + 1):
        countSum = 0
        indexSum = 0
        for index, count in enumerate(singleList):
            countSum += count
            indexSum += count * index
        if countSum == cardCount and indexSum == costSum:
            result.append(singleList)
    return result


cardDict, cardCostIdDict = getClassesDict(r'plugins\scBattle\cards')
effectDict, _ = getClassesDict(r'plugins\scBattle\effects')
costCountList = getCostCountList(5, 3, 7)   # standard: 5 cards, card <= 5 cost, total cost = 10


def getCardObjById(cardId):
    cardClass = cardDict.get(cardId, None)
    return cardClass() if cardClass else None


def getEffectObjById(effectId, effectAmount):
    effectClass = effectDict.get(effectId, None)
    return effectClass(effectAmount) if effectClass else None


def isCardIdListValid(cardIdList):
    for cardId in cardIdList:
        if cardId not in cardDict:
            return False
    return True


def getCardTotalCost(cardIdList) -> int:
    totalCost = 0
    for cardId in cardIdList:
        card = getCardObjById(cardId)
        totalCost += card.cost
    return totalCost


def getRandomCardIdList():
    chosenCostCount = random.choice(costCountList)
    cardCostList = []
    for index, num in enumerate(chosenCostCount):
        for i in range(0, num):
            cardCostList.append(index)
    random.shuffle(cardCostList)

    outputIdList = []
    for cost in cardCostList:
        cardIdList = cardCostIdDict.get(cost, None)
        if not cardIdList:
            outputIdList.append(0)
        outputIdList.append(random.choice(cardIdList))
    return outputIdList




