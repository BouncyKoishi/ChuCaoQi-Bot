import math
import dbConnection.db as baseDB
import dbConnection.kusa_item as itemDB
from nonebot import on_command, CommandSession


@on_command(name='生草工厂', only_to_me=False)
async def kusaFactory(session: CommandSession):
    userId = session.ctx['user_id']
    user = await baseDB.getUser(userId)
    argText = session.current_arg_text.strip()
    newFactoryAmount = abs(int(argText)) if argText else 1
    if newFactoryAmount > 100:
        await session.send("一次最多新建100个工厂！")
        return

    machineCost = 80 * newFactoryAmount
    cheapLevel = await getCheapLevelByItem(userId)
    factoryAmount = await itemDB.getItemAmount(userId, '生草工厂')
    coreCost = getFactoryCoreCost(user.vipLevel + cheapLevel, factoryAmount, newFactoryAmount)
    machineAmount = await itemDB.getItemAmount(userId, '生草机器')
    coreAmount = await itemDB.getItemAmount(userId, '自动化核心')
    costSign = f'新建{newFactoryAmount}个工厂需要：生草机器 * {machineCost}，自动化核心 * {coreCost}，'
    if machineAmount < machineCost or coreAmount < coreCost:
        await session.send(costSign + '你不够机器或不够核心^ ^')
        return

    confirm = await session.aget(prompt=costSign + '是否继续建厂？(y/n)')
    if confirm.lower() != 'y':
        return

    await itemDB.changeItemAmount(userId, '生草机器', -machineCost)
    await itemDB.changeItemAmount(userId, '自动化核心', -coreCost)
    await itemDB.changeItemAmount(userId, '生草工厂', newFactoryAmount)
    await session.send(f'建造成功！新建了{newFactoryAmount}个工厂，消耗了{machineCost}台生草机器和{coreCost}个自动化核心，你的当前工厂数为{factoryAmount + newFactoryAmount}。')


def getFactoryCoreCost(cheapLevelAll, nowFactory, newFactory):
    base = 1 + 0.5 * math.exp(-0.255 * cheapLevelAll)
    return int((base ** nowFactory) * (base ** newFactory - 1) / (base - 1))


async def getCheapLevelByItem(userId):
    cheapLevel = 0
    cheapLevel += await itemDB.getItemAmount(userId, '生草工厂自动工艺I')
    cheapLevel += await itemDB.getItemAmount(userId, '生草工厂自动工艺II')
    return cheapLevel


@on_command(name='草精炼厂', only_to_me=False)
async def _(session: CommandSession):
    userId = session.ctx['user_id']
    bluePrintExist = await itemDB.getItemAmount(userId, '生草工业园区蓝图')
    if bluePrintExist == 0:
        await session.send('你没有工业园区蓝图，不知道如何建设草精炼厂^ ^')
        return

    argText = session.current_arg_text.strip()
    if not argText:
        await session.send('建设每个草精炼厂需要消耗500个自动化核心，你每有10个生草工厂，可以建设一个草精炼厂。输入“!草精炼厂 [数量]”来建设草精炼厂。\n'
                           '注意：每个草精炼厂每天消耗5000草，这会严重影响你的生草工厂产量，建设前请注意！')
        return
    baseFactoryAmount = await itemDB.getItemAmount(userId, '生草工厂')
    mobileFactoryAmount = await itemDB.getItemAmount(userId, '流动生草工厂')
    totalBaseFactoryAmount = baseFactoryAmount + mobileFactoryAmount
    amountLimitImproved = await itemDB.getItemAmount(userId, '产业链优化')
    advFactoryAmountLimit = totalBaseFactoryAmount // 8 if amountLimitImproved else totalBaseFactoryAmount // 10
    oldAdvFactoryAmount = await itemDB.getItemAmount(userId, '草精炼厂')
    newAdvFactoryAmount = int(argText)
    if oldAdvFactoryAmount >= advFactoryAmountLimit:
        await session.send('你的草精炼厂数量已到达上限！')
        return
    newAdvFactoryAmount = min(newAdvFactoryAmount, advFactoryAmountLimit - oldAdvFactoryAmount)
    needCoreAmount = newAdvFactoryAmount * 500
    coreAmount = await itemDB.getItemAmount(userId, '自动化核心')
    if coreAmount >= needCoreAmount:
        await itemDB.changeItemAmount(userId, '草精炼厂', newAdvFactoryAmount)
        await itemDB.changeItemAmount(userId, '自动化核心', -needCoreAmount)
        await session.send(f'{newAdvFactoryAmount}个草精炼厂建造成功！消耗了{needCoreAmount}个自动化核心。')
    else:
        await session.send(f"你不够核心^ ^")


@on_command(name='扭秤装置', only_to_me=False)
async def _(session: CommandSession):
    await session.send('本物品已集成到建筑商店，请使用“!购买 扭秤装置 [数量]进行购买。”')


@on_command(name='草压缩基地', only_to_me=False)
async def _(session: CommandSession):
    userId = session.ctx['user_id']
    bluePrintExist = await itemDB.getItemAmount(userId, '草之精华构造图')
    if bluePrintExist == 0:
        await session.send('你尚不了解草之精华的内部构造，无法建设草压缩基地^ ^')
        return
    baseExist = await itemDB.getItemAmount(userId, '草压缩基地')
    if baseExist > 0:
        await session.send('你已经建设过草压缩基地了，无需重复建设！')
        return

    needCoreAmount = 10000
    coreAmount = await itemDB.getItemAmount(userId, '自动化核心')
    if coreAmount >= needCoreAmount:
        await itemDB.changeItemAmount(userId, '草压缩基地', 1)
        await itemDB.changeItemAmount(userId, '自动化核心', -needCoreAmount)
        await session.send(f'草压缩基地建造成功！消耗了{needCoreAmount}个自动化核心。')
    else:
        await session.send(f"草压缩基地共计需要10000个核心，你不够核心^ ^")

