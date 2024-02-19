import math
import random
import nonebot
import dbConnection.db as baseDB
import dbConnection.kusa_item as itemDB
from nonebot import on_command, CommandSession
from kusa_base import config, sendGroupMsg


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


def getFactoriesCost(cheapLevelAll, nowFactory, newFactory):
    base = 1 + 0.5 * math.exp(-0.255 * cheapLevelAll)
    return int((base ** nowFactory) * (base ** newFactory - 1) / (base - 1))


async def getNextFactoryCost(userId):
    cheapLevel = await getFactoryVipLevel(userId)
    factoryAmount = await itemDB.getItemAmount(userId, '生草工厂')
    return getFactoriesCost(cheapLevel, factoryAmount, 1)


async def getFactoryVipLevel(userId):
    user = await baseDB.getUser(userId)
    cheapLevel = user.vipLevel
    cheapLevel += await itemDB.getItemAmount(userId, '生草工厂自动工艺I')
    cheapLevel += await itemDB.getItemAmount(userId, '生草工厂自动工艺II')
    return cheapLevel


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
    outputStr = f'{userName}的每日工业期望产量：'
    outputStr += f'{await getDailyKusaNum(userId, 8)}草，'
    newAdvKusaAmount = await getDailyAdvKusaNum(userId)
    outputStr += f'{newAdvKusaAmount}草之精华，' if newAdvKusaAmount else ''
    newCoreAmount = await getDailyCoreNum(userId, 8)
    outputStr += f'{newCoreAmount}自动化核心，' if newCoreAmount else ''
    await session.send(outputStr[:-1])


# 生草工业运作
@nonebot.scheduler.scheduled_job('cron', hour=0)
async def daily():
    kusaRandInt = random.randint(4, 12)
    coreRandInt = random.randint(4, 12)
    signStr = f'今日工业运作开始！\n生草机器产量：{kusaRandInt}\n核心装配工厂产量：{coreRandInt}'
    await sendGroupMsg(config['group']['main'], signStr)

    userList = await baseDB.getAllUser()
    for user in userList:
        newKusaAmount = await getDailyKusaNum(user.qq, kusaRandInt)
        await baseDB.changeKusa(user.qq, newKusaAmount)
        newAdvKusaAmount = await getDailyAdvKusaNum(user.qq)
        await baseDB.changeAdvKusa(user.qq, newAdvKusaAmount)
        newCoreAmount = await getDailyCoreNum(user.qq, coreRandInt)
        await itemDB.changeItemAmount(user.qq, '自动化核心', newCoreAmount)
        newBlackTeaAmount = await getDailyBlackTeaNum(user.qq)
        await itemDB.changeItemAmount(user.qq, '红茶', newBlackTeaAmount)
        await createLotteryTicket(user.qq)


async def getDailyKusaNum(userId, machineRandInt):
    machineAmount = await itemDB.getItemAmount(userId, '生草机器')
    factoryAmount = await itemDB.getItemAmount(userId, '生草工厂')
    mobileFactoryAmount = await itemDB.getItemAmount(userId, '流动生草工厂')
    advFactoryInfo = await itemDB.getItemStorageInfo(userId, '草精炼厂')
    factoryNewDeviceI = await itemDB.getItemAmount(userId, '生草工厂新型设备I')
    factoryAdditionI = await itemDB.getItemAmount(userId, '生草工厂效率I')
    factoryAdditionII = await itemDB.getItemAmount(userId, '生草工厂效率II')
    factoryAdditionIII = await itemDB.getItemAmount(userId, '生草工厂效率III')
    factoryAdditionIV = await itemDB.getItemAmount(userId, '生草工厂效率IV')
    machineAdditionI = await itemDB.getItemAmount(userId, '试做型机器I')
    machineAdditionII = await itemDB.getItemAmount(userId, '试做型机器II')
    machineAddKusa = machineRandInt * machineAmount
    machineAddKusa *= 8 if machineAdditionI else 1
    machineAddKusa *= 5 if machineAdditionII else 1
    factoryAddKusa = 640 * (factoryAmount + mobileFactoryAmount)
    factoryAddKusa *= 2 if factoryNewDeviceI else 1
    factoryAddKusa *= 2 if factoryAdditionI else 1
    factoryAddKusa *= 2 if factoryAdditionII else 1
    factoryAddKusa *= 2 if factoryAdditionIII else 1
    factoryAddKusa *= 2 if factoryAdditionIV else 1
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
    coreFactoryAdditionI = await itemDB.getItemAmount(userId, '核心工厂效率I')
    coreFactoryAdditionII = await itemDB.getItemAmount(userId, '核心工厂效率II')
    coreFactoryAdditionIII = await itemDB.getItemAmount(userId, '核心工厂效率III')
    coreFactoryAdditionIV = await itemDB.getItemAmount(userId, '核心工厂效率IV')
    addCore = coreFactoryRandInt * coreFactoryAmount
    addCore *= 2 if coreFactoryAdditionI else 1
    addCore *= 2 if coreFactoryAdditionII else 1
    addCore *= 2 if coreFactoryAdditionIII else 1
    addCore *= 2 if coreFactoryAdditionIV else 1
    addCore = math.ceil(addCore)
    return addCore


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

