import re
import codecs
from nonebot import on_command, CommandSession
from kusa_base import buying, selling, itemCharging, isUserExist
import dbConnection.db as baseDB
import dbConnection.kusa_item as itemDB


@on_command(name='商店', only_to_me=False)
async def _(session: CommandSession):
    await shop(session, '草')


@on_command(name='进阶商店', only_to_me=False)
async def _(session: CommandSession):
    await shop(session, '草之精华')


@on_command(name='建筑商店', only_to_me=False)
async def _(session: CommandSession):
    await shop(session, '自动化核心')


async def shop(session: CommandSession, priceType):
    shopItemList = await itemDB.getShopItemList(priceType)
    argText = session.current_arg_text.strip()
    showAll = True if '全部' in argText or 'all' in argText else False
    itemPriceDict = {}
    for item in shopItemList:
        itemCount = await itemDB.getItemAmount(session.ctx['user_id'], item.name)
        if not showAll:
            if not await preItemCheck(item, session.ctx['user_id']):
                continue
            if item.amountLimit and itemCount >= item.amountLimit:
                continue
        itemPriceDict[item.name] = getItemPrice(item, itemCount)
    print(itemPriceDict)
    sortedPriceDict = sorted(itemPriceDict.items(), key=lambda x: x[1])
    if not sortedPriceDict:
        await session.send('当前商店暂无你可以购买的物品！')

        return
    output = '全部物品列表：\n' if showAll else '您可以购买的物品：\n'
    output += '\n'.join([f'{name}：{price}{priceType}' for name, price in sortedPriceDict])
    output += '\n可输入"!商店帮助"来查看商店和道具的相关说明'
    await session.send(output)


@on_command(name='商店帮助', only_to_me=False)
async def shopHelp(session: CommandSession):
    with codecs.open(u'text/生草系统-商店帮助.txt', 'r', 'utf-8') as f:
        await session.send(f.read().strip())


@on_command(name='查询', only_to_me=False)
async def usefulItemQuery(session: CommandSession):
    itemName = session.current_arg_text.strip()
    item = await itemDB.getItem(itemName)
    if not item:
        await session.send('此物品不存在!')
        return
    ownItemAmount = await itemDB.getItemAmount(session.ctx['user_id'], itemName)
    output = f'{item.name}\n'
    output += f'拥有数量：{ownItemAmount}\n'
    output += f'最大数量限制：{item.amountLimit}\n' if item.amountLimit else ''
    output += f'基础价格：{item.shopPrice}{item.priceType}\n' if item.shopPrice else '不可从商店购买\n'
    output += f'价格倍率：{item.priceRate}\n' if item.priceRate else ''
    output += f'商店售价：{item.sellingPrice}{item.priceType}\n' if item.sellingPrice else ''
    output += '不可转让 ' if not item.isTransferable else ''
    output += '不可禁用 ' if not item.isControllable else ''
    output += '\n'
    output += f'物品说明：{item.detail}\n' if item.detail else '暂无物品说明= =\n'

    output = output[:-1] if output[-1] == '\n' else output
    await session.send(output)


@on_command(name='购买', only_to_me=False)
async def shopBuy(session: CommandSession):
    userId = session.ctx['user_id']
    argText = session.current_arg_text.strip()
    getNameSuccess, itemName, buyingAmount = getItemNameAndAmount(argText)
    if not getNameSuccess:
        await session.send('需要物品名！')
        return

    item = await itemDB.getItem(itemName)
    nowAmount = await itemDB.getItemAmount(userId, itemName)
    if not item:
        await session.send('此物品不存在!')
        return
    if item.shopPrice is None:
        await session.send('此物品不能通过商店购买!')
        return
    if item.amountLimit:
        if nowAmount >= item.amountLimit:
            await session.send('你已达到此物品的最大数量限制!')
            return
        buyingAmount = min(buyingAmount, item.amountLimit - nowAmount)
    if item.priceRate and buyingAmount > 10000:
        await session.send('暂不支持大量购买浮动价格物品!')
        return
    if not await preItemCheck(item, userId):
        await session.send('你不满足购买此物品的前置条件!')
        return

    totalPrice = getMultiItemPrice(item, nowAmount, buyingAmount)
    if item.priceRate and buyingAmount > 0:
        priceInfo = f'本物品价格随购买数量上升，购买{buyingAmount}个{itemName}共计消耗{totalPrice}{item.priceType}。是否继续购买？(y/n)'
        confirm = await session.aget(prompt=priceInfo)
        if confirm.lower() != 'y':
            return

    buyingSuccess = await buyingByCostType(userId, itemName, buyingAmount, totalPrice, item.priceType)
    if buyingSuccess:
        await session.send(f'购买成功！购买了{buyingAmount}个{itemName}。')
    else:
        output = f'你不够{item.priceType}^ ^'
        await session.send(output)


async def buyingByCostType(userId, itemName, buyingAmount, totalPrice, priceType):
    if priceType == '草' or priceType == '草之精华':
        isUsingAdvKusa = (priceType == '草之精华')
        return await buying(userId, itemName, buyingAmount, totalPrice, isUsingAdvKusa)
    else:
        return await itemCharging(userId, itemName, buyingAmount, priceType, totalPrice)


@on_command(name='出售', only_to_me=False)
async def shopSell(session: CommandSession):
    userId = session.ctx['user_id']
    argText = session.current_arg_text.strip()
    getNameSuccess, itemName, sellingAmount = getItemNameAndAmount(argText)
    if not getNameSuccess:
        await session.send('需要物品名！')
        return

    item = await itemDB.getItem(itemName)
    if not item:
        await session.send('此物品不存在!')
        return
    if item.sellingPrice is None:
        await session.send('此物品不能通过商店出售!')
        return
    if item.priceRate:
        # 这个分支在实际使用中不应出现，若出现应检查商品配置是否有误
        await session.send('此物品的价格不固定，不能通过商店出售!')
        return

    totalPrice = sellingAmount * item.sellingPrice
    sellingSuccess = await sellingByCostType(userId, itemName, sellingAmount, totalPrice, item.priceType)
    if sellingSuccess:
        await session.send(f'出售成功！出售了{sellingAmount}个{itemName}。')
    else:
        await session.send(f'你不够{itemName}^ ^')


async def sellingByCostType(userId, itemName, buyingAmount, totalPrice, priceType):
    if priceType == '草' or priceType == '草之精华':
        isUsingAdvKusa = (priceType == '草之精华')
        return await selling(userId, itemName, buyingAmount, totalPrice, isUsingAdvKusa)
    else:
        # 暂不支持非草/草精物品的出售
        return False


@on_command(name='道具转让', aliases='物品转让', only_to_me=False)
async def usefulItemTransfer(session: CommandSession):
    userId = session.ctx['user_id']
    argText = session.current_arg_text.strip()
    getNameSuccess, itemName, transferAmount = getItemNameAndAmount(argText)
    qqNumberList = re.search(r'(?<=(QQ|qq)=)\d+', argText)
    qqNumber = qqNumberList.group(0) if qqNumberList else None
    if not getNameSuccess:
        await session.send('需要物品名！')
        return
    if not qqNumber:
        await session.send('需要被转让人的QQ号！')
        return
    if not await isUserExist(qqNumber):
        await session.send('你想转让的对象并没有生草账户！')
        return

    item = await itemDB.getItem(itemName)
    if not item:
        await session.send('此物品不存在!')
        return
    if not item.isTransferable:
        await session.send('此物品不能转让!')
        return

    itemAmount = await itemDB.getItemAmount(userId, itemName)
    if itemAmount < transferAmount:
        await session.send(f'你不够{itemName}^ ^')
        return
    await itemDB.changeItemAmount(userId, itemName, -transferAmount)
    await itemDB.changeItemAmount(qqNumber, itemName, transferAmount)
    await session.send(f'转让成功！转让了{transferAmount}个{itemName}给{qqNumber}。')


@on_command(name='启用', aliases='道具启用', only_to_me=False)
async def usefulItemEnable(session: CommandSession):
    await usefulItemEnableOrDisable(session, True)


@on_command(name='禁用', aliases='道具禁用', only_to_me=False)
async def usefulItemDisable(session: CommandSession):
    await usefulItemEnableOrDisable(session, False)


async def usefulItemEnableOrDisable(session: CommandSession, enable: bool):
    userId = session.ctx['user_id']
    argText = session.current_arg_text.strip()
    getNameSuccess, itemName, _ = getItemNameAndAmount(argText)
    if not getNameSuccess:
        await session.send('需要道具名！')
        return

    item = await itemDB.getItem(itemName)
    itemStorageInfo = await itemDB.getItemStorageInfo(userId, itemName)
    if not item:
        await session.send('此道具不存在!')
        return
    if not item.isControllable:
        await session.send('此道具不能手动启用或禁用!')
        return
    if not itemStorageInfo:
        await session.send('你没有此道具!')
        return

    await itemDB.changeItemAllowUse(userId, itemName, enable)
    await session.send(f'已{"启用" if enable else "禁用"}你的 {itemName}')


def getItemNameAndAmount(argText: str):
    # 名字匹配中文字符
    itemNameResult = re.search(r'[\u4e00-\u9fa5G]+[IVX]*', argText)
    itemAmountResult = re.search(r'(?<!(QQ|qq)=)\b\d+\b', argText)
    if not itemNameResult:
        return False, None, None
    itemName = itemNameResult.group(0)
    itemAmount = int(itemAmountResult.group(0)) if itemAmountResult else 1
    return True, itemName, itemAmount


async def preItemCheck(item, userId):
    if not item.shopPreItems:
        return True
    preItemNames = item.shopPreItems.split(',')
    for preItemName in preItemNames:
        # 信息员等级限制
        if preItemName.startswith('Lv'):
            needLevel = int(preItemName[2:])
            user = await baseDB.getUser(userId)
            if user.vipLevel < needLevel:
                return False
            continue
        # 前置物品限制
        preItem = await itemDB.getItem(preItemName)
        if not preItem:
            return False
        if not await itemDB.getItemAmount(userId, preItemName):
            return False
    return True


def getMultiItemPrice(item, ownItemAmount, newItemAmount):
    return sum(getItemPrice(item, ownItemAmount + i) for i in range(newItemAmount))


def getItemPrice(item, itemAmount):
    if not item.priceRate:
        return item.shopPrice
    return int(item.shopPrice * (item.priceRate ** itemAmount))
