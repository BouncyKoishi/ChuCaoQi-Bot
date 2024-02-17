import random
import nonebot
from nonebot import on_command, CommandSession
from kusa_base import config
from utils import nameDetailSplit
from itertools import groupby
from decorator import CQ_injection_check_command
import dbConnection.db as baseDB
import dbConnection.draw_item as drawItemDB
import dbConnection.kusa_item as usefulItemDB


itemRareDescribe = ['Easy', 'Normal', 'Hard', 'Lunatic']
drawConfig = config['drawItem']


@on_command(name='抽奖', only_to_me=False)
async def itemDraw(session: CommandSession):
    groupId = session.ctx['group_id']
    userId = session.ctx['user_id']
    if not groupId:
        await session.send('暂不支持私聊抽奖^ ^')
        return
    if groupId not in drawConfig['groupAllowDraw']:
        await session.send('本群暂不支持抽奖^ ^')
        return
    if groupId not in drawConfig['groupAllowItem']:
        await ban(groupId, userId)
        return

    banRisk = drawConfig['banRisk']
    banShieldInfo = await usefulItemDB.getItemStorageInfo(userId, '量子护盾')
    if banShieldInfo and banShieldInfo.allowUse:
        await usefulItemDB.changeItemAmount(userId, '量子护盾', -1)
        banRisk = banRisk / 10
    if random.random() < banRisk:
        await ban(groupId, userId)
        return

    strippedArg = session.current_arg_text.strip()
    await getItem(groupId, userId, strippedArg)


@on_command(name='十连抽', only_to_me=False)
async def itemDraw10(session: CommandSession):
    groupId = session.ctx['group_id']
    userId = session.ctx['user_id']

    if not groupId:
        await session.send('暂不支持私聊抽奖^ ^')
        return
    if groupId not in drawConfig['groupAllowItem']:
        await session.send('本群暂不支持十连抽^ ^')
        return

    strippedArg = session.current_arg_text.strip()
    baseLevel, poolName = await getLevelAndPoolName(strippedArg)
    baseLevel = baseLevel if baseLevel is not None else 0
    
    ticketName = ['十连券', '高级十连券', '特级十连券', '天琴十连券'][baseLevel]
    drawTenTicketInfo = await usefulItemDB.getItemStorageInfo(userId, ticketName)
    if not drawTenTicketInfo or not drawTenTicketInfo.allowUse:
        await session.send(f'你缺少{ticketName}，无法十连抽^ ^')
        return
    await usefulItemDB.changeItemAmount(userId, ticketName, -1)

    itemList = [await getItemFromDB(baseLevel, poolName) for i in range(10)]

    outputStr = '十连抽结果：\n'
    for item in itemList:
        existItemStorage = await drawItemDB.getSingleItemStorage(userId, item.id)
        outputStr += f'[{itemRareDescribe[item.rareRank]}]{item.name}'
        if not existItemStorage:
            outputStr += '(New!)'
        outputStr += '\n'
        await drawItemDB.setItemStorage(userId, item.id)
    outputStr = outputStr[:-1]
    await session.send(outputStr)


async def ban(groupNum, userId):
    bot = nonebot.get_bot()
    dur_time = int(1.1 ** (5 + random.random() * 70))

    print(f'抽奖口球-{dur_time}s, id:{userId}, group:{groupNum}')
    msg = f'获得了：口球({dur_time}s)！'
    await bot.set_group_ban(group_id=groupNum, user_id=userId, duration=dur_time)
    await bot.send_group_msg(group_id=groupNum, message=msg)


async def getItem(groupNum, userId, strippedArg):
    _, poolName = await getLevelAndPoolName(strippedArg)
    redrawDice = await usefulItemDB.getItemStorageInfo(userId, '骰子碎片')
    if not redrawDice or not redrawDice.allowUse:
        drawLimit = 1
    else:
        drawLimit = min(51, redrawDice.amount + 1)

    redrawCount, item = 0, None
    for i in range(drawLimit):
        redrawCount = i
        item = await getItemFromDB(poolName=poolName)
        existItemStorage = await drawItemDB.getSingleItemStorage(userId, item.id)
        if not existItemStorage:
            break

    msg = ''
    if redrawCount > 0:
        await usefulItemDB.changeItemAmount(userId, '骰子碎片', -redrawCount)
        msg += f'消耗了骰子碎片*{redrawCount}，'

    existItemStorage = await drawItemDB.getSingleItemStorage(userId, item.id)
    msg += f'获得了：[{itemRareDescribe[item.rareRank]}]{item.name}'
    if not existItemStorage:
        msg += '(New!)'
    if item.detail:
        msg += f'\n物品说明：{item.detail}'
    bot = nonebot.get_bot()
    await bot.send_group_msg(group_id=groupNum, message=msg)
    await drawItemDB.setItemStorage(userId, item.id)


async def getItemFromDB(startRareRank=0, poolName=None):
    easyRand = 1 if startRareRank > 0 else random.random()
    if easyRand < 0.7:
        return await drawItemDB.getRandomItem(0, poolName)
    normalRand = 1 if startRareRank > 1 else random.random()
    if normalRand < 0.7:
        return await drawItemDB.getRandomItem(1, poolName)
    hardRand = 1 if startRareRank > 2 else random.random()
    if hardRand < 0.7:
        return await drawItemDB.getRandomItem(2, poolName)
    lunaticRand = random.random()
    if lunaticRand < 0.7:
        return await drawItemDB.getRandomItem(3, poolName)
    return await getItemFromDB(startRareRank, poolName)


@on_command(name='添加-Easy', aliases='物品添加-Easy', only_to_me=False)
@CQ_injection_check_command
async def addItemEasy(session: CommandSession):
    await addItem(session, 0)


@on_command(name='添加-Normal', aliases='物品添加-Normal', only_to_me=False)
@CQ_injection_check_command
async def addItemNormal(session: CommandSession):
    await addItem(session, 1)


@on_command(name='添加-Hard', aliases='物品添加-Hard', only_to_me=False)
@CQ_injection_check_command
async def addItemHard(session: CommandSession):
    await addItem(session, 2)


@on_command(name='添加-Lunatic', aliases='物品添加-Lunatic', only_to_me=False)
@CQ_injection_check_command
async def addItemLunatic(session: CommandSession):
    await addItem(session, 3)


async def addItem(session, rare):
    stripped_arg = session.current_arg_text.strip()
    userId = session.ctx['user_id']
    itemName, itemDetail = nameDetailSplit(stripped_arg)
    if not itemName:
        await session.send('需要物品名!')
        return

    itemName = itemName.strip()
    if len(itemName) > 32:
        await session.send('物品名太长啦!最多32字')
        return
    if itemDetail and len(itemDetail) > 1024:
        await session.send('物品简介太长啦!最多1024字')
        return
    existItem = await drawItemDB.getItemByName(itemName)
    if existItem:
        await session.send('此物品名已经存在!')
        return

    # 暂时为纯老师写死
    poolName = "宝可梦" if userId == 285698619 else "默认"

    user = await baseDB.getUser(userId)
    costKusa = 1000 * (8 ** rare)
    if not user.kusa >= costKusa:
        await session.send('你不够草^_^')
        return
    await baseDB.changeKusa(userId, -costKusa)
    await drawItemDB.addItem(itemName, rare, poolName, itemDetail, userId)

    output = "添加成功！"
    output += "注意：你添加的物品没有简介。" if not itemDetail else ""
    await session.send(output)


@on_command(name='物品仓库', only_to_me=False)
async def _(session: CommandSession):
    userId = session.ctx['user_id']
    arg = session.current_arg_text.strip()
    level, poolName = await getLevelAndPoolName(arg)
    itemStorageList = await drawItemDB.getItemsWithStorage(qqNum=userId, rareRank=level, poolName=poolName)
    if not itemStorageList:
        poolInfo = f'{poolName}奖池' if poolName else ''
        levelInfo = f'{itemRareDescribe[level]}等级' if level is not None else ''
        await session.send(f'{poolInfo}{levelInfo}暂无可抽取物品^ ^')
        return

    outputStr = ""
    # 展示全部等级的物品
    if level is None:
        groupedData = groupby(itemStorageList, key=lambda x: x.rareRank)
        for nowLevel, levelItemIterator in groupedData:
            levelItems = list(levelItemIterator)
            levelOwnItems = [item for item in levelItems if item.storage]
            if levelOwnItems:
                outputStr += f'{itemRareDescribe[nowLevel]}({len(levelOwnItems)}/{len(levelItems)}):'
                if len(levelOwnItems) > drawConfig['itemHideAmount']:
                    outputStr += ' ---隐藏了过长的物品列表--- \n'
                    continue
                outputStr += ','.join([f' {item.name}*{item.storage[0].amount}' for item in levelOwnItems]) + '\n'
        outputStr = outputStr[:-1]
    # 展示指定等级的物品
    else:
        ownItem = [item for item in itemStorageList if item.storage]
        if ownItem:
            outputStr += f'{itemRareDescribe[level]}({len(ownItem)}/{len(itemStorageList)}):'
            pageSize, offset = 100, 0
            while True:
                displayItems = ownItem[offset: min(offset + pageSize, len(ownItem))]
                outputStr += ','.join([f' {item.name}*{item.storage[0].amount}' for item in displayItems])
                offset += len(displayItems)
                if offset >= len(ownItem):
                    outputStr += f'\n(当前最后一页)' if len(ownItem) > pageSize else ''
                    break
                confirm = await session.aget(prompt=outputStr + f'\n(当前第{offset // pageSize}页，输入Next显示下一页)')
                outputStr = ''
                if confirm.lower() != 'next':
                    break

    if not outputStr:
        argExistInfo = '在' if level is not None or poolName else ''
        poolInfo = f'{poolName}奖池' if poolName else ''
        levelInfo = f'{itemRareDescribe[level]}等级' if level is not None else ''
        outputStr = f'{argExistInfo}{poolInfo}{levelInfo}暂未抽到任何物品^ ^'
    await session.send(outputStr)


@on_command(name='物品详情', only_to_me=False)
async def _(session: CommandSession):
    stripped_arg = session.current_arg_text.strip()
    item = await drawItemDB.getItemByName(stripped_arg)
    if not item:
        await itemSearch(session)
        return

    outputStr = f'[{itemRareDescribe[item.rareRank]}]{item.name}'
    outputStr += f'\n物品说明：{item.detail}' if item.detail else '\n暂无物品说明。'
    try:
        sender_infor = await nonebot.get_bot().get_stranger_info(user_id=item.author)
        outputStr += f'\n创作者：{sender_infor["nickname"]}({item.author})'
    except:
        outputStr += f'\n创作者：{item.author}'

    personCount, numberCount = await drawItemDB.getItemStorageCount(item.id)
    outputStr += f'\n抽到该物品的人数：{personCount}\n被抽到的总次数：{numberCount}' if personCount else '\n还没有人抽到这个物品= ='

    await session.send(outputStr)


@on_command(name='物品搜索', only_to_me=False)
async def _(session: CommandSession):
    await itemSearch(session)


async def itemSearch(session: CommandSession):
    strippedArg = session.current_arg_text.strip()
    if not strippedArg:
        await session.send('没有搜索关键词呢^ ^')
        return
    offset = 0
    while True:
        pageSize = 12
        count, items = await drawItemDB.searchItem(strippedArg, pageSize, offset)
        if not count:
            await session.send('没有找到该物品^ ^')
            return
        outputStr = '' if offset else '你要找的是不是：\n'
        outputStr += '\n'.join(f'[{itemRareDescribe[item["rareRank"]]}]{item["name"]}' for item in items)
        offset += len(items)
        if offset >= count:
            outputStr += f'\n(共{count}件物品，当前最后一页)' if count > pageSize else ''
            await session.send(outputStr)
            return
        confirm = await session.aget(prompt=outputStr + f'\n(共{count}件物品，当前第{offset // pageSize}页，输入Next显示下一页)')
        if confirm.lower() != 'next':
            return


@on_command(name='物品修改', only_to_me=False)
async def _(session: CommandSession):
    userId = session.ctx['user_id']
    stripped_arg = session.current_arg_text.strip()
    itemName, itemDetail = nameDetailSplit(stripped_arg)
    item = await drawItemDB.getItemByName(itemName)
    if not item:
        await session.send('没有找到该物品^ ^')
        return
    if item.author != str(userId):
        await session.send('你不是该物品的作者，无法修改物品说明^ ^')
        return

    await drawItemDB.setItemDetail(item, itemDetail)
    await session.send('修改成功！')


@on_command(name='物品删除', only_to_me=False)
async def _(session: CommandSession):
    userId = session.ctx['user_id']
    itemName = session.current_arg_text.strip()
    item = await drawItemDB.getItemByName(itemName)
    if not item:
        await session.send('没有找到该物品^ ^')
        return
    if item.author != str(userId):
        await session.send('你不是该物品的作者，无法删除物品^ ^')
        return

    await drawItemDB.deleteItem(item)
    await session.send('删除成功！')


@on_command(name='自制物品列表', only_to_me=False)
async def _(session: CommandSession):
    userId = session.ctx['user_id']
    strippedArg = session.current_arg_text.strip()
    level, poolName = await getLevelAndPoolName(strippedArg)
    itemList = await drawItemDB.getItemListByAuthor(userId, level, poolName)
    if not itemList:
        argExistInfo = '在' if level is not None or poolName else ''
        poolInfo = f'{poolName}奖池' if poolName else ''
        levelInfo = f'{itemRareDescribe[level]}等级' if level is not None else ''
        await session.send(f'{argExistInfo}{poolInfo}{levelInfo}暂未添加任何物品^ ^')
        return

    outputStr = ""
    # 展示全部等级的物品
    if level is None:
        groupedData = groupby(itemList, key=lambda x: x.rareRank)
        for nowLevel, levelItemIterator in groupedData:
            levelItems = list(levelItemIterator)
            if levelItems:
                outputStr += f'{itemRareDescribe[nowLevel]}:'
                if len(levelItems) > drawConfig['itemHideAmount'] * 2:
                    outputStr += ' ---隐藏了过长的自制物品列表--- \n'
                    continue
                outputStr += ','.join([f' {item.name}' for item in levelItems]) + '\n'
        outputStr = outputStr[:-1]
    # 展示指定等级的物品
    else:
        outputStr += f'{itemRareDescribe[level]}:'
        pageSize, offset = 150, 0
        while True:
            displayItems = itemList[offset: min(offset + pageSize, len(itemList))]
            outputStr += ','.join([f' {item.name}' for item in displayItems])
            offset += len(displayItems)
            if offset >= len(itemList):
                outputStr += f'\n(当前最后一页)' if len(itemList) > pageSize else ''
                break
            confirm = await session.aget(prompt=outputStr + f'\n(当前第{offset // pageSize}页，输入Next显示下一页)')
            outputStr = ''
            if confirm.lower() != 'next':
                break

    await session.send(outputStr)


async def getLevelAndPoolName(strippedArg):
    if not strippedArg:
        return None, None

    argList = strippedArg.split()
    itemRareList = [rare.lower() for rare in itemRareDescribe]
    if len(argList) == 1:
        if argList[0].lower() in itemRareList:
            levelStr, poolName = argList[0], None
        else:
            poolName, levelStr = argList[0], None
    else:
        if argList[0].lower() in itemRareList:
            levelStr, poolName = argList
        elif argList[1].lower() in itemRareList:
            poolName, levelStr = argList
        else:
            return None, None
    level = itemRareList.index(levelStr.lower()) if levelStr else None
    poolName = poolName if await drawItemDB.isPoolNameExist(poolName) else None
    return level, poolName
