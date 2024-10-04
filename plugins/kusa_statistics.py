import dbConnection.db as baseDB
import dbConnection.kusa_item as itemDB
from nonebot import on_command, CommandSession
from kusa_base import isSuperAdmin, config


@on_command(name="admin_help", only_to_me=False)
async def _(session: CommandSession):
    if not await isSuperAdmin(session.ctx['user_id']):
        return
    outputStr = "管理员命令列表：\n"
    outputStr += "TOTAL_KUSA 系统总草数\n"
    outputStr += "KUSA_RANK 草排行榜\n"
    outputStr += "FACTORY_RANK 工厂数排行榜\n"
    outputStr += "KUSA_ADV [qq号] 总草精数统计\n"
    outputStr += "KUSA_ADV_RANK 总草精排行榜\n"
    outputStr += "TITLE_LIST 系统称号列表\n"
    outputStr += "GIVE_TITLE [qq号] [称号] 给予称号\n"
    outputStr += "SET_DONATION [qq号] [金额] (ifd) 设置捐赠金额\n"
    await session.send(outputStr)


@on_command(name='TOTAL_KUSA', only_to_me=False)
async def _(session: CommandSession):
    userList = await baseDB.getAllUser()
    totalKusa, totalKusaAdv, availableKusa, availableKusaAdv = 0, 0, 0, 0
    for user in userList:
        totalKusa += user.kusa
        totalKusaAdv += user.advKusa
        if str(user.qq) != str(config['qq']['bot']):
            availableKusa += user.kusa
            availableKusaAdv += user.advKusa
    await session.send(f'系统总草数: {totalKusa}\n可流通草数: {availableKusa}\n'
                       f'系统总草精数: {totalKusaAdv}\n可流通草精数: {availableKusaAdv}')


@on_command(name='KUSA_RANK', only_to_me=False)
async def _(session: CommandSession):
    if not await permissionCheck(session):
        return

    userList = await baseDB.getAllUser()
    userList = sorted(userList, key=lambda x: x.kusa, reverse=True)
    outputStr = "草排行榜：\n"
    for i in range(25):
        if i >= len(userList):
            break
        user = userList[i]
        userName = user.name if user.name else user.qq
        outputStr += f'{i + 1}. {userName}: {user.kusa}\n'
    await session.send(outputStr)


@on_command(name='FACTORY_RANK', only_to_me=False)
async def _(session: CommandSession):
    if not await permissionCheck(session):
        return

    factoryList = await itemDB.getStoragesOrderByAmountDesc("生草工厂")
    outputStr = "工厂数排行榜：\n"
    for i in range(25):
        if i >= len(factoryList):
            break
        info = factoryList[i]
        user = await baseDB.getUser(info.qq)
        userName = user.name if user.name else user.qq
        outputStr += f'{i + 1}. {userName}: {info.amount}\n'
    await session.send(outputStr)


@on_command(name='KUSA_ADV', only_to_me=False)
async def _(session: CommandSession):
    if not await isSuperAdmin(session.ctx['user_id']):
        return

    qqNum = session.current_arg_text.strip()
    qqNum = session.ctx['user_id'] if not qqNum else qqNum
    user = await baseDB.getUser(qqNum)
    if not user:
        await session.send("用户不存在")
        return

    advShopItemList = await itemDB.getShopItemList(priceType="草之精华")
    total, now, title, item = await getKusaAdv(user, advShopItemList)
    outputStr = f"{user.qq}草精情况：\n现有 {now}\n信息员等级消费 {title}\n道具消费 {item}\n总计 {total}"
    await session.send(outputStr)


@on_command(name='KUSA_ADV_RANK', only_to_me=False)
async def _(session: CommandSession):
    if not await permissionCheck(session):
        return
    outputStr = await getKusaAdvRank()
    await session.send(outputStr)


async def permissionCheck(session: CommandSession) -> bool:
    userId = session.ctx['user_id']
    if await isSuperAdmin(userId):
        return True
    amount = await itemDB.getItemAmount(userId, "侦察凭证")
    if amount >= 10:
        await itemDB.changeItemAmount(userId, '侦察凭证', -10)
        return True
    else:
        await session.send("查看排行榜需要消耗10个侦察凭证，你的侦察凭证不足")
        return False


async def getKusaAdvRank():
    userList = await baseDB.getAllUser()
    advShopItemList = await itemDB.getShopItemList(priceType="草之精华")
    userAdvKusaDict = {}
    for user in userList:
        bluePrintExist = await itemDB.getItemAmount(user.qq, '生草工业园区蓝图')
        if not bluePrintExist:
            continue
        total, _, _, _ = await getKusaAdv(user, advShopItemList)
        userAdvKusaDict[user] = total
    userAdvKusaDict = sorted(userAdvKusaDict.items(), key=lambda x: x[1], reverse=True)
    outputStr = "草精排行榜：\n"
    for i in range(min(25, len(userAdvKusaDict))):
        user = userAdvKusaDict[i][0]
        userName = user.name if user.name else user.qq
        outputStr += f'{i + 1}. {userName}: {userAdvKusaDict[i][1]}\n'
    return outputStr


async def getKusaAdv(user, advShopItemList):
    nowKusaAdv = user.advKusa
    titleKusaAdv = sum(10 ** (i - 4) for i in range(5, user.vipLevel + 1)) if user.vipLevel > 4 else 0
    itemKusaAdv = 0
    for item in advShopItemList:
        itemAmount = await itemDB.getItemAmount(user.qq, item.name)
        itemKusaAdv += item.shopPrice * itemAmount
    return nowKusaAdv + titleKusaAdv + itemKusaAdv, nowKusaAdv, titleKusaAdv, itemKusaAdv


@on_command(name='TITLE_LIST', only_to_me=False)
async def _(session: CommandSession):
    if not await isSuperAdmin(session.ctx['user_id']):
        return

    itemTitle = await itemDB.getItemsByType("称号")
    outputStr = "系统称号列表：\n"
    outputStr += "\n".join([f"{item.name}" for item in itemTitle])
    await session.send(outputStr)


@on_command(name='GIVE_TITLE', only_to_me=False)
async def _(session: CommandSession):
    if not await isSuperAdmin(session.ctx['user_id']):
        return

    stripped_arg = session.current_arg_text.strip()
    qqNum, title = stripped_arg.split(" ")
    user = await baseDB.getUser(qqNum)
    if not user:
        await session.send("用户不存在")
        return
    item = await itemDB.getItem(title)
    if not item or item.type != '称号':
        await session.send('你想给出的称号不存在')
        return
    await itemDB.changeItemAmount(user.qq, title, 1)
    await session.send(f'成功赠送{user.qq}称号{title}')


@on_command(name='SET_DONATION', only_to_me=False)
async def _(session: CommandSession):
    if not await isSuperAdmin(session.ctx['user_id']):
        return

    stripped_arg = session.current_arg_text.strip()
    qqNum, amount, source = stripped_arg.split(" ")
    source = source if source else "qq"
    user = await baseDB.getUser(qqNum)
    if not user:
        await session.send("用户不存在")
        return
    await baseDB.setDonateRecord(qqNum, amount, source)
    await session.send(f'成功添加{qqNum}通过{source}捐赠{amount}元的记录')
