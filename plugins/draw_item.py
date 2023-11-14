import re
import random
import nonebot
from nonebot import on_command, CommandSession
from kusa_base import config
from utils import nameDetailSplit
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
        await ban(groupId, userId, True)
        return

    banRisk = drawConfig['banRisk']
    banShieldInfo = await usefulItemDB.getItemStorageInfo(userId, '量子护盾')
    if banShieldInfo and banShieldInfo.allowUse:
        await usefulItemDB.changeItemAmount(userId, '量子护盾', -1)
        banRisk = banRisk / 2
    if random.random() < banRisk:
        await ban(groupId, userId, False)
        return

    await getItem(groupId, userId, session.ctx['sender'], 0)


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
    drawTenTicketInfo = await usefulItemDB.getItemStorageInfo(userId, '十连券')
    if not drawTenTicketInfo or not drawTenTicketInfo.allowUse:
        await session.send('你缺少十连券，无法十连抽^ ^')
        return
    await usefulItemDB.changeItemAmount(userId, '十连券', -1)

    itemList = []
    while len(itemList) < 10:
        item = await getItemFromDB(0)
        if item:
            itemList.append(item)
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


async def ban(groupNum, userId, isForceBan=False):
    bot = nonebot.get_bot()
    dur_time = int(1.1 ** (5 + random.random() * 70))
    if isForceBan:
        dur_time = int(1.1 ** (15 + random.random() * 70))

    print(f'抽奖口球-{dur_time}s, id:{userId}, group:{groupNum}')
    msg = f'获得了：口球({dur_time}s)！'
    await bot.set_group_ban(group_id=groupNum, user_id=userId, duration=dur_time)
    await bot.send_group_msg(group_id=groupNum, message=msg)


async def getItem(groupNum, userId, senderInfo, startRareRank):
    item = await getItemFromDB(startRareRank)
    if not item:
        await getCardModify(groupNum, userId, senderInfo)
        return
    existItemStorage = await drawItemDB.getSingleItemStorage(userId, item.id)
    msg = f'获得了：[{itemRareDescribe[item.rareRank]}]{item.name}'
    if not existItemStorage:
        msg += '(New!)'
    if item.detail:
        msg += f'\n物品说明：{item.detail}'
    bot = nonebot.get_bot()
    await bot.send_group_msg(group_id=groupNum, message=msg)
    await drawItemDB.setItemStorage(userId, item.id)


async def getItemFromDB(startRareRank):
    easyRand = 1 if startRareRank > 0 else random.random()
    if easyRand < 0.7:
        return await drawItemDB.getRandomItem(0)
    normalRand = 1 if startRareRank > 1 else random.random()
    if normalRand < 0.7:
        return await drawItemDB.getRandomItem(1)
    hardRand = 1 if startRareRank > 2 else random.random()
    if hardRand < 0.7:
        return await drawItemDB.getRandomItem(2)
    lunaticRand = random.random()
    if lunaticRand < 0.7:
        return await drawItemDB.getRandomItem(3)
    return None


async def getCardModify(groupNum, userId, sender):
    bot = nonebot.get_bot()
    cardName = sender['card']
    if not cardName:
        nickname = sender['nickname']
        new_name = f'[信息员]{nickname}'
    else:
        if '[信息员]' in cardName:
            amount = re.search(r'(?<=\*)(\d+)\s(.*)', cardName)
            if amount:
                new_name = f'[信息员]*{int(amount.group(1)) + 1} {amount.group(2)}'
            else:
                new_name = f'[信息员]*2 {cardName[5:]}'
        else:
            new_name = '[信息员]' + cardName
    await bot.set_group_card(group_id=groupNum, user_id=userId, card=new_name)
    msg = '获得了：*除草器的认证*'
    await bot.send_group_msg(group_id=groupNum, message=msg)


@on_command(name='添加-Easy', only_to_me=False)
@CQ_injection_check_command
async def addItemEasy(session: CommandSession):
    await addItem(session, 0)


@on_command(name='添加-Normal', only_to_me=False)
@CQ_injection_check_command
async def addItemNormal(session: CommandSession):
    await addItem(session, 1)


@on_command(name='添加-Hard', only_to_me=False)
@CQ_injection_check_command
async def addItemHard(session: CommandSession):
    await addItem(session, 2)


@on_command(name='添加-Lunatic', only_to_me=False)
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

    user = await baseDB.getUser(userId)
    costKusa = 1000 * (8**rare)
    if not user.kusa >= costKusa:
        await session.send('你不够草^_^')
        return
    await baseDB.changeKusa(userId, -costKusa)
    await drawItemDB.addItem(itemName, rare, itemDetail, userId)

    output = "添加成功！"
    output += "注意：你添加的物品没有简介。" if not itemDetail else ""
    await session.send(output)


@on_command(name='物品仓库', only_to_me=False)
async def _(session: CommandSession):
    userId = session.ctx['user_id']
    arg = session.current_arg_text.strip()

    if arg in itemRareDescribe:
        itemStorageList = await drawItemDB.getItemsWithStorage(qqNum=userId, rareRank=itemRareDescribe.index(arg))
    else:
        itemStorageList = await drawItemDB.getItemsWithStorage(qqNum=userId, rareRank=None)

    allItemNumList = [0, 0, 0, 0]
    ownItemNumList = [0, 0, 0, 0]
    describeStrList = ['', '', '', '']

    for item in itemStorageList:
        allItemNumList[item.rareRank] += 1
        if not item.storage:
            continue
        ownItemNumList[item.rareRank] += 1
        describeStrList[item.rareRank] += f' {item.name}*{item.storage[0].amount},'

    outputStr = ""
    for i in range(3, -1, -1):
        if ownItemNumList[i]:
            outputStr += f'{itemRareDescribe[i]}({ownItemNumList[i]}/{allItemNumList[i]}):'
            if ownItemNumList[i] > drawConfig['itemHideAmount'] and arg != '展开' and arg not in itemRareDescribe:
                outputStr += ' ---隐藏了过长的物品列表--- \n'
            else:
                outputStr += describeStrList[i] + '\n'
    if outputStr:
        outputStr = outputStr[:-2]
    else:
        outputStr = '暂无任何抽奖物品^ ^'
    await session.send(outputStr)


@on_command(name='物品详情', only_to_me=False)
async def _(session: CommandSession):
    stripped_arg = session.current_arg_text.strip()
    item = await drawItemDB.getItemByName(stripped_arg)
    if not item:
        await itemSearch(session)
        return
    outputStr = f'[{itemRareDescribe[item.rareRank]}]{item.name}'
    personCount, numberCount = await drawItemDB.getItemStorageCount(item.id)
    if item.detail:
        outputStr += f'\n物品说明：{item.detail}'
    else:
        outputStr += '\n暂无物品说明。'

    try:
        sender_infor = await nonebot.get_bot().get_stranger_info(user_id=item.author)
        outputStr += f'\n创作者：{sender_infor["nickname"]}({item.author})'
    except:
        outputStr += f'\n创作者：{item.author}'

    if personCount == 0:
        outputStr += f'\n暂时还没有人抽到这个物品= ='
    else:
        outputStr += f'\n抽到该物品的人数：{personCount}\n被抽到的总次数：{numberCount}'

    await session.send(outputStr)


@on_command(name='物品搜索', only_to_me=False)
async def _(session: CommandSession):
    await itemSearch(session)


async def itemSearch(session: CommandSession):
    stripped_arg = session.current_arg_text.strip()
    if len(stripped_arg) < 2:
        await session.send('搜索关键词至少为两个字^ ^')
        return
    offset = 0
    while True:
        pageSize = 10
        count, items = await drawItemDB.searchItem(stripped_arg, pageSize, offset)
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
    itemStorageList = await drawItemDB.getItemListByAuthor(session.ctx['user_id'])
    rareDescribeFlags = [False, False, False, False]
    outputStr = ""

    for item in itemStorageList:
        if not rareDescribeFlags[item.rareRank]:
            if outputStr:
                outputStr = outputStr[:-2] + '\n'
            outputStr += f'{itemRareDescribe[item.rareRank]}: '
            rareDescribeFlags[item.rareRank] = True
        outputStr += f'{item.name}, '
    if outputStr:
        outputStr = outputStr[:-2]
    else:
        outputStr = '暂未添加任何物品^ ^'
    await session.send(outputStr)
