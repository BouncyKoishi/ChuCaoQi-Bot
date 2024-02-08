import yaml
import nonebot
import dbConnection.db as baseDB
import dbConnection.kusa_item as itemDB

configFile = open("config/plugin_config.yaml", 'r', encoding='utf-8')
config = yaml.load(configFile.read(), Loader=yaml.FullLoader)


async def isUserExist(qqNum) -> bool:
    user = await baseDB.getUser(qqNum)
    if user is None:
        return False
    return True


async def isSuperAdmin(qqNum) -> bool:
    user = await baseDB.getUser(qqNum)
    if user is None:
        return False
    if user.isSuperAdmin:
        return True
    return False


# 基础交易模块
async def buying(qqNum, itemNameBuying, itemAmountBuying, totalPrice, isUsingAdvKusa=False) -> bool:
    user = await baseDB.getUser(qqNum)
    item = await itemDB.getItem(itemNameBuying)
    if itemAmountBuying < 0:
        return False
    if user is None or item is None:
        return False
    if isUsingAdvKusa and user.advKusa < totalPrice:
        return False
    if not isUsingAdvKusa and user.kusa < totalPrice:
        return False

    await itemDB.changeItemAmount(qqNum, itemNameBuying, itemAmountBuying)
    if isUsingAdvKusa:
        await baseDB.changeAdvKusa(qqNum, -totalPrice)
        await baseDB.changeAdvKusa(config['qq']['bot'], totalPrice)
    else:
        await baseDB.changeKusa(qqNum, -totalPrice)
        await baseDB.changeKusa(config['qq']['bot'], totalPrice)
    return True


async def selling(qqNum, itemNameSelling, itemAmountSelling, totalPrice, isUsingAdvKusa=False) -> bool:
    user = await baseDB.getUser(qqNum)
    item = await itemDB.getItem(itemNameSelling)
    itemAmount = await itemDB.getItemAmount(qqNum, itemNameSelling)
    if itemAmountSelling < 0:
        return False
    if user is None or item is None:
        return False
    if itemAmount < itemAmountSelling:
        return False
    await itemDB.changeItemAmount(qqNum, itemNameSelling, -itemAmountSelling)
    if isUsingAdvKusa:
        await baseDB.changeAdvKusa(qqNum, totalPrice)
        await baseDB.changeAdvKusa(config['qq']['bot'], -totalPrice)
    else:
        await baseDB.changeKusa(qqNum, totalPrice)
        await baseDB.changeKusa(config['qq']['bot'], -totalPrice)
    return True


async def itemCharging(qqNum, itemNameGain, itemAmountGain, itemNameCost, itemAmountCost) -> bool:
    user = await baseDB.getUser(qqNum)
    itemGain = await itemDB.getItem(itemNameGain)
    itemCost = await itemDB.getItem(itemNameCost)
    if itemAmountGain < 0 or itemAmountCost < 0:
        return False
    if user is None or itemGain is None or itemCost is None:
        return False
    itemCostNowAmount = await itemDB.getItemAmount(qqNum, itemNameCost)
    if itemCostNowAmount < itemAmountCost:
        return False

    await itemDB.changeItemAmount(qqNum, itemNameGain, itemAmountGain)
    await itemDB.changeItemAmount(qqNum, itemNameCost, -itemAmountCost)
    return True


# Group logger
async def sendLog(message):
    await sendGroupMsg(config['group']['log'], message)


async def sendGroupMsg(groupId, message):
    try:
        bot = nonebot.get_bot()
        await bot.send_group_msg(group_id=groupId, message=message)
    except Exception as e:
        print(f'对群聊{groupId}发送GroupMsg失败：' + str(e))


async def sendPrivateMsg(userId, message):
    try:
        bot = nonebot.get_bot()
        await bot.send_private_msg(user_id=userId, message=message)
    except Exception as e:
        print(f'对用户{userId}发送PrivateMsg失败：' + str(e))
