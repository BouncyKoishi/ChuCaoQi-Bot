import math
import random
import nonebot
import dbConnection.db as baseDB
import dbConnection.kusa_item as itemDB
import dbConnection.kusa_field as fieldDB
from nonebot import on_command, CommandSession
from kusa_base import config, sendGroupMsg, sendLog


async def buyingKusaFactory(session: CommandSession, increaseAmount: int):
    if increaseAmount > 100:
        await session.send("一次最多新建100个工厂！")
        return

    userId = session.ctx['user_id']
    cheapLevel = await getFactoryVipLevel(userId)
    factoryAmount = await itemDB.getItemAmount(userId, '生草工厂')
    coreAmount = await itemDB.getItemAmount(userId, '自动化核心')
    coreCost = getFactoriesCost(cheapLevel, factoryAmount, increaseAmount)
    costSign = f'新建{increaseAmount}个工厂需要：自动化核心 * {coreCost}，'
    if coreAmount < coreCost:
        await session.send(costSign + '你不够核心^ ^')
        return
    confirm = await session.aget(prompt=costSign + '是否继续建厂？(y/n)')
    if confirm.lower() != 'y':
        return

    await itemDB.changeItemAmount(userId, '自动化核心', -coreCost)
    await itemDB.changeItemAmount(userId, '生草工厂', increaseAmount)
    await session.send(f'建造成功！新建了{increaseAmount}个工厂，消耗了{coreCost}个自动化核心，你的当前工厂数为{factoryAmount + increaseAmount}。')
    tradeDetail = f'购买前已有生草工厂{factoryAmount}个，购买时等效信息员等级为{cheapLevel}'
    await baseDB.setTradeRecord(operator=userId, tradeType='商店(买)', detail=tradeDetail,
                                gainItemName='生草工厂', gainItemAmount=increaseAmount,
                                costItemName='自动化核心', costItemAmount=coreCost)


def getFactoriesCost(cheapLevelAll, nowFactory, newFactory):
    base = 1 + 0.5 * math.exp(-0.255 * cheapLevelAll)
    return int((base ** nowFactory) * (base ** newFactory - 1) / (base - 1))


async def getNextFactoryCost(userId):
    cheapLevel = await getFactoryVipLevel(userId)
    factoryAmount = await itemDB.getItemAmount(userId, '生草工厂')
    return getFactoriesCost(cheapLevel, factoryAmount, 1)


async def getFactoryVipLevel(userId):
    user = await baseDB.getUser(userId)
    return user.vipLevel + await itemDB.getTechLevel(userId, '生草工厂自动工艺')


async def buyingAdvFactory(session: CommandSession, increaseAmount: int):
    userId = session.ctx['user_id']
    bluePrintExist = await itemDB.getItemAmount(userId, '生草工业园区蓝图')
    if bluePrintExist == 0:
        await session.send('你没有工业园区蓝图，无法建设草精炼厂^ ^')
        return

    baseFactoryAmount = await itemDB.getItemAmount(userId, '生草工厂')
    mobileFactoryAmount = await itemDB.getItemAmount(userId, '流动生草工厂')
    totalBaseFactoryAmount = baseFactoryAmount + mobileFactoryAmount
    amountLimitImproved = await itemDB.getItemAmount(userId, '产业链优化')
    advFactoryAmountLimit = totalBaseFactoryAmount // 8 if amountLimitImproved else totalBaseFactoryAmount // 10
    oldAdvFactoryAmount = await itemDB.getItemAmount(userId, '草精炼厂')
    if oldAdvFactoryAmount >= advFactoryAmountLimit:
        await session.send('你的草精炼厂数量已到达上限！')
        return
    newAdvFactoryAmount = min(increaseAmount, advFactoryAmountLimit - oldAdvFactoryAmount)
    needCoreAmount = newAdvFactoryAmount * 500
    coreAmount = await itemDB.getItemAmount(userId, '自动化核心')
    if coreAmount >= needCoreAmount:
        await itemDB.changeItemAmount(userId, '草精炼厂', newAdvFactoryAmount)
        await itemDB.changeItemAmount(userId, '自动化核心', -needCoreAmount)
        await session.send(f'{newAdvFactoryAmount}个草精炼厂建造成功！消耗了{needCoreAmount}个自动化核心。')
        await baseDB.setTradeRecord(operator=userId, tradeType='商店(买)',
                                    gainItemName='草精炼厂', gainItemAmount=newAdvFactoryAmount,
                                    costItemName='自动化核心', costItemAmount=needCoreAmount)
    else:
        await session.send(f"你不够核心^ ^")


@on_command(name='生草工厂', only_to_me=False)
async def _(session: CommandSession):
    await session.send('本物品已集成到商店，请使用“!购买 生草工厂 [数量]”进行购买。')


@on_command(name='草精炼厂', only_to_me=False)
async def _(session: CommandSession):
    await session.send('本物品已集成到商店，请使用“!购买 草精炼厂 [数量]”进行购买。')


@on_command(name='扭秤装置', only_to_me=False)
async def _(session: CommandSession):
    await session.send('本物品已集成到建筑商店，请使用“!购买 扭秤装置 [数量]”进行购买。')


@on_command(name='草压缩基地', only_to_me=False)
async def _(session: CommandSession):
    await session.send('本物品已集成到建筑商店，请使用“!购买 草压缩基地”进行购买。”')


@on_command(name='每日产量', only_to_me=False)
async def dailyStatistics(session: CommandSession):
    userId = session.ctx['user_id']
    user = await baseDB.getUser(userId)
    userName = user.name if user.name else user.qq
    newKusaAmount = await getDailyKusaNum(userId, 8)
    newAdvKusaAmount = await getDailyAdvKusaNum(user.qq)
    newCoreAmount = await getDailyCoreNum(user.qq, 8)
    outputStr = f'{userName}的每日工业期望产量：{newKusaAmount}草，'
    outputStr += f'{newAdvKusaAmount}草之精华，' if newAdvKusaAmount else ''
    outputStr += f'{newCoreAmount}自动化核心，' if newCoreAmount else ''
    outputStr = outputStr[:-1]
    remiProductionInfo = await itemDB.getItemStorageInfo(user.qq, '蕾米球的生产魔法')
    if remiProductionInfo and remiProductionInfo.allowUse:
        kusaField = await fieldDB.getKusaField(user.qq)
        extraMagnification = 0.04 * (kusaField.soilCapacity - 20)
        if extraMagnification > 0:
            outputStr += f'\n由于蕾米球的生产魔法，你将额外获得：{math.ceil(newKusaAmount * extraMagnification)}草，'
            outputStr += f'{math.ceil(newAdvKusaAmount * extraMagnification)}草之精华，' if newAdvKusaAmount else ''
            outputStr += f'{math.ceil(newCoreAmount * extraMagnification)}自动化核心，' if newCoreAmount else ''
            outputStr = outputStr[:-1]
    await session.send(outputStr)


# 生草工业运作
@nonebot.scheduler.scheduled_job('cron', hour=0)
async def _():
    await dailyIndustrial()


async def dailyIndustrial():
    kusaRandInt = random.randint(4, 12)
    coreRandInt = random.randint(4, 12)
    signStr = f'今日工业运作开始！\n生草机器产量：{kusaRandInt}\n核心装配工厂产量：{coreRandInt}'
    await sendGroupMsg(config['group']['main'], signStr)

    userList = await baseDB.getAllUser()
    for user in userList:
        print(f'{user.qq}的每日工业开始运作！')
        newKusaAmount = await getDailyKusaNum(user.qq, kusaRandInt)
        newAdvKusaAmount = await getDailyAdvKusaNum(user.qq)
        newCoreAmount = await getDailyCoreNum(user.qq, coreRandInt)
        newBlackTeaAmount = await getDailyBlackTeaNum(user.qq)
        remiProductionInfo = await itemDB.getItemStorageInfo(user.qq, '蕾米球的生产魔法')
        if remiProductionInfo and remiProductionInfo.allowUse:
            kusaField = await fieldDB.getKusaField(user.qq)
            extraMagnification = max(0.04 * (kusaField.soilCapacity - 20), 0)
            newKusaAmount = math.ceil(newKusaAmount * (1 + extraMagnification))
            newAdvKusaAmount = math.ceil(newAdvKusaAmount * (1 + extraMagnification))
            newCoreAmount = math.ceil(newAdvKusaAmount * (1 + extraMagnification))
            newBlackTeaAmount = math.ceil(newAdvKusaAmount * (1 + extraMagnification))
            await itemDB.updateTimeLimitedItem(user.qq, '过载标记', 12 * 3600)
            await fieldDB.kusaSoilUseUp(user.qq)
        await baseDB.changeKusa(user.qq, newKusaAmount)
        await baseDB.changeAdvKusa(user.qq, newAdvKusaAmount)
        await itemDB.changeItemAmount(user.qq, '自动化核心', newCoreAmount)
        await itemDB.changeItemAmount(user.qq, '红茶', newBlackTeaAmount)
        await createLotteryTicket(user.qq)
    print('所有每日工业运作完成！')
    await sendLog('所有每日工业运作完成！')


async def getDailyKusaNum(userId, machineRandInt):
    machineAmount = await itemDB.getItemAmount(userId, '生草机器')
    machineTechLevel = await itemDB.getTechLevel(userId, '试做型机器')
    machineAddKusa = machineRandInt * machineAmount
    machineAddKusa *= {0: 1, 1: 8, 2: 40}.get(machineTechLevel)

    factoryAmount = await itemDB.getItemAmount(userId, '生草工厂')
    mobileFactoryAmount = await itemDB.getItemAmount(userId, '流动生草工厂')
    factoryNewDevice = await itemDB.getItemAmount(userId, '生草工厂新型设备I')
    factoryTechLevel = await itemDB.getTechLevel(userId, '生草工厂效率')
    factoryAddKusa = 640 * (factoryAmount + mobileFactoryAmount)
    factoryAddKusa *= 2 if factoryNewDevice else 1
    factoryAddKusa *= (2 ** factoryTechLevel)

    advFactoryInfo = await itemDB.getItemStorageInfo(userId, '草精炼厂')
    advFactoryCostKusa = 5000 * advFactoryInfo.amount if advFactoryInfo and advFactoryInfo.allowUse else 0

    return math.ceil(machineAddKusa + factoryAddKusa - advFactoryCostKusa)


async def getDailyAdvKusaNum(userId):
    advFactoryInfo = await itemDB.getItemStorageInfo(userId, '草精炼厂')
    if not advFactoryInfo or not advFactoryInfo.allowUse:
        return 0
    advKusaBaseAddition = await itemDB.getItemAmount(userId, '高效草精炼指南')
    sevenPlanetMagic = await itemDB.getItemAmount(userId, '七曜精炼术')
    advKusaAdditionI = await itemDB.getItemAmount(userId, '草精炼厂效率I')
    advKusaAdditionII = await itemDB.getItemAmount(userId, '草精炼厂效率II')
    advKusa = advFactoryInfo.amount
    advKusa += (advFactoryInfo.amount // 7) * 4 if sevenPlanetMagic else 0
    advKusa += (advFactoryInfo.amount - 7) if advKusaAdditionI and advFactoryInfo.amount > 7 else 0
    if advKusaBaseAddition:
        additionCount = min(advKusaBaseAddition, advFactoryInfo.amount)
        advKusa += additionCount
        if advKusaAdditionII:
            advKusa += (additionCount * (additionCount - 1))  # 通项为2n-2，前n项和为n(n-1)
    return advKusa


async def getDailyCoreNum(userId, coreFactoryRandInt):
    coreFactoryAmount = await itemDB.getItemAmount(userId, '核心装配工厂')
    coreTechLevel = await itemDB.getTechLevel(userId, '核心工厂效率')
    addCore = coreFactoryRandInt * coreFactoryAmount
    addCore *= {0: 1, 1: 2, 2: 4, 3: 8, 4: 12}.get(coreTechLevel)
    return math.ceil(addCore)


async def getDailyBlackTeaNum(userId):
    blackTeaPool = await itemDB.getItemAmount(userId, '红茶池')
    return 15 * blackTeaPool


# 奖券印刷机生产十连券
async def createLotteryTicket(userId):
    machineAmount = await itemDB.getItemAmount(userId, '奖券印刷机')
    if machineAmount == 0:
        return
    normalTicket, rareTicket, superTicket = 0, 0, 0
    for _ in range(machineAmount):
        randInt = random.randint(1, 8)
        if randInt <= 5:
            normalTicket += 1
        elif randInt <= 7:
            rareTicket += 1
        else:
            superTicket += 1
    await itemDB.changeItemAmount(userId, '十连券', normalTicket)
    await itemDB.changeItemAmount(userId, '高级十连券', rareTicket)
    await itemDB.changeItemAmount(userId, '特级十连券', superTicket)

