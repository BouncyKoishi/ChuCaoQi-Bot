import dbConnection.db as baseDB
import dbConnection.kusa_item as itemDB
import dbConnection.kusa_field as fieldDB
from datetime import datetime
from nonebot import on_command, CommandSession, get_bot
from kusa_base import isSuperAdmin, config
from functools import wraps


def permissionCheck(onlyAdmin=False, costCredentials=0):
    def decorator(func):
        @wraps(func)
        async def wrapper(session: CommandSession, *args, **kwargs):
            userId = session.ctx['user_id']
            superAdmin = await isSuperAdmin(userId)
            if superAdmin:
                return await func(session, *args, **kwargs)
            if onlyAdmin and not superAdmin:
                return
            amount = await itemDB.getItemAmount(userId, "侦察凭证")
            if amount >= costCredentials:
                await itemDB.changeItemAmount(userId, '侦察凭证', -costCredentials)
                return await func(session, *args, **kwargs)
            else:
                await session.send(f'查看该信息需要消耗{costCredentials}个侦察凭证，你的侦察凭证不足^ ^')
                return
        return wrapper
    return decorator


@on_command(name="admin_help", only_to_me=False)
@permissionCheck(onlyAdmin=True)
async def _(session: CommandSession):
    outputStr = "管理员命令列表：\n"
    outputStr += "TOTAL_KUSA 系统总草数\n"
    outputStr += "KUSA_RANK 草排行榜\n"
    outputStr += "FACTORY_RANK 工厂数排行榜\n"
    outputStr += "KUSA_ADV [qq号] 总草精数统计\n"
    outputStr += "KUSA_ADV_RANK 总草精排行榜\n"
    outputStr += "TITLE_LIST 系统称号列表\n"
    outputStr += "GIVE_TITLE [qq号] [称号] 给予称号\n"
    outputStr += "SET_DONATION [qq号] [金额] (qq/ifd) 设置捐赠金额\n"
    outputStr += "SET_NAME [qq号] (名字) 设置名称（默认从昵称取）\n"
    await session.send(outputStr)


@on_command(name='TOTAL_KUSA', only_to_me=False)
@permissionCheck(onlyAdmin=False, costCredentials=1)
async def _(session: CommandSession):
    userList = await baseDB.getAllUser()
    totalKusa, totalKusaAdv, availableKusa, availableKusaAdv = 0, 0, 0, 0
    for user in userList:
        totalKusa += user.kusa
        totalKusaAdv += user.advKusa
        if str(user.qq) != str(config['qq']['bot']):
            availableKusa += user.kusa
            availableKusaAdv += user.advKusa
    await session.send(f'系统总草数: {totalKusa}\n可用总草数: {availableKusa}\n'
                       f'历史总草精数: {totalKusaAdv}\n可用总草精数: {availableKusaAdv}')


@on_command(name='KUSA_RANK', only_to_me=False)
@permissionCheck(onlyAdmin=False, costCredentials=1)
async def _(session: CommandSession):
    userList = await baseDB.getAllUser()
    userList = [user for user in userList if str(user.qq) != str(config['qq']['bot'])]
    userList = sorted(userList, key=lambda x: x.kusa, reverse=True)
    outputStr = "草排行榜：\n"
    for i, user in enumerate(userList[:25]):
        userName = user.name if user.name else user.qq
        outputStr += f'{i + 1}. {userName}: {user.kusa:,}\n'
    await session.send(outputStr[:-1])


@on_command(name='FACTORY_RANK', only_to_me=False)
@permissionCheck(onlyAdmin=False, costCredentials=1)
async def _(session: CommandSession):
    factoryList = await itemDB.getStoragesOrderByAmountDesc("生草工厂")
    outputStr = "工厂数排行榜：\n"
    for i, info in enumerate(factoryList[:25]):
        user = await baseDB.getUser(info.qq)
        userName = user.name if user.name else user.qq
        outputStr += f'{i + 1}. {userName}: {info.amount}\n'
    await session.send(outputStr[:-1])


@on_command(name='KUSA_ADV', only_to_me=False)
@permissionCheck(onlyAdmin=False, costCredentials=1)
async def _(session: CommandSession):
    qqNum = session.current_arg_text.strip()
    qqNum = session.ctx['user_id'] if not qqNum else qqNum
    user = await baseDB.getUser(qqNum)
    if not user:
        await session.send("用户不存在")
        return

    total, now, title, item = await getKusaAdv(user)
    outputStr = f"{user.qq}草精情况：\n现有 {now}\n信息员等级消费 {title}\n道具消费 {item}\n总计 {total}"
    await session.send(outputStr)


@on_command(name='草精排行榜', only_to_me=False)
@permissionCheck(onlyAdmin=False, costCredentials=10)
async def _(session: CommandSession):
    outputStr = '总草精排行榜：' + await getKusaAdvRank(userId=session.ctx['user_id'])
    await session.send(outputStr)


@on_command(name='草精新星榜', only_to_me=False)
@permissionCheck(onlyAdmin=False, costCredentials=10)
async def _(session: CommandSession):
    outputStr = '草精新星排行榜：' + await getKusaAdvRank(userId=session.ctx['user_id'], levelMax=6)
    await session.send(outputStr)


@on_command(name='KUSA_ADV_RANK', only_to_me=False)
@permissionCheck(onlyAdmin=True)
async def _(session: CommandSession):
    userId = session.ctx['user_id']
    strippedArg = session.current_arg_text.strip()
    showInactiveUsers = True if '-i' in strippedArg else False
    showSubAccount = True if '-s' in strippedArg else False
    levelMax = 10
    if '--l' in strippedArg:
        try:
            levelMax = int(strippedArg.split('--l')[1].strip().split()[0])
        except (IndexError, ValueError):
            await session.send("Invalid levelMax value. Please provide a valid integer after --l.")
            return
    outputStr = '草精排行榜（自定义）：' + await getKusaAdvRank(userId, levelMax, showInactiveUsers, showSubAccount)
    await session.send(outputStr)


async def getKusaAdvRank(userId=None, levelMax: int = 10, showInactiveUsers: bool = False, showSubAccount: bool = True) -> str:
    userList = await baseDB.getAllUser()
    userAdvKusaDict = {}
    for user in userList:
        if user.vipLevel > levelMax:
            continue
        if not showSubAccount and user.relatedQQ:
            continue
        bluePrintExist = await itemDB.getItemAmount(user.qq, '生草工业园区蓝图')
        if not bluePrintExist:
            continue
        if not showInactiveUsers:
            # 近90天无生草记录，则不显示在排行榜
            kusaRecordRow = await fieldDB.kusaHistoryReport(user.qq, datetime.now(), 7776000)
            if kusaRecordRow["count"] == 0:
                continue
        total, _, _, _ = await getKusaAdv(user)
        userAdvKusaDict[user] = total
    userAdvKusaDict = sorted(userAdvKusaDict.items(), key=lambda x: x[1], reverse=True)
    outputStr = "\n"

    for i in range(min(len(userAdvKusaDict), 25)):
        user = userAdvKusaDict[i][0]
        userName = user.name if user.name else user.qq
        outputStr += f'{i + 1}. {userName}: {userAdvKusaDict[i][1]}\n'
    if userId:
        # 获取个人排名，上一名及草精差距，下一名及草精差距
        userRank, userKusaAdv, prevInfo, nextInfo = -1, 0, None, None
        for i, (user, kusaAdv) in enumerate(userAdvKusaDict):
            if str(user.qq) == str(userId):
                userRank, userKusaAdv = i + 1, kusaAdv
                if i > 0:
                    prevInfo = (userAdvKusaDict[i - 1][0], userAdvKusaDict[i - 1][1])
                if i < len(userAdvKusaDict) - 1:
                    nextInfo = (userAdvKusaDict[i + 1][0], userAdvKusaDict[i + 1][1])
                break

        if userRank != -1:
            outputStr += f"\n您的排名：{userRank}\n"
            if prevInfo:
                prevName = prevInfo[0].name if prevInfo[0].name else prevInfo[0].qq
                outputStr += f"距上一名 {prevName} 还差 {prevInfo[1] - userKusaAdv}草精\n"
            if nextInfo:
                nextName = nextInfo[0].name if nextInfo[0].name else nextInfo[0].qq
                outputStr += f"下一名 {nextName} 距您 {userKusaAdv - nextInfo[1]}草精\n"
        else:
            outputStr += "\n您不在这个排行榜上^ ^\n"
    return outputStr[:-1]


async def getKusaAdv(user):
    nowKusaAdv = user.advKusa
    titleKusaAdv = sum(10 ** (i - 4) for i in range(5, user.vipLevel + 1)) if user.vipLevel > 4 else 0
    advItemTradeRecord = await baseDB.getTradeRecord(operator=user.qq, costItemName='草之精华')
    itemKusaAdv = sum(record.costItemAmount for record in advItemTradeRecord)
    return nowKusaAdv + titleKusaAdv + itemKusaAdv, nowKusaAdv, titleKusaAdv, itemKusaAdv


@on_command(name='生草打分榜', only_to_me=False)
@permissionCheck(onlyAdmin=False, costCredentials=5)
async def _(session: CommandSession):
    userId = session.ctx['user_id']
    selfMode = '-self' in session.current_arg_text
    if selfMode:
        rankList = await fieldDB.kusaOnceRanking(userId=userId)
        user = await baseDB.getUser(userId)
        userName = user.name if user.name else user.qq
        outputStr = f"生草打分榜({userName})：\n"
    else:
        rankList = await fieldDB.kusaOnceRanking()
        outputStr = "生草打分榜：\n"
    for i, rank in enumerate(rankList):
        createTime = datetime.fromtimestamp(rank.createTimeTs)
        timeStr = createTime.strftime("%Y-%m-%d %H:%M")
        if selfMode:
            outputStr += f"{i + 1}. {rank.kusaResult}草({timeStr})\n"
        else:
            rankUser = await baseDB.getUser(rank.qq)
            userName = rankUser.name if rankUser.name else rankUser.qq
            outputStr += f"{i + 1}. {userName}：{rank.kusaResult}草({timeStr})\n"
    await session.send(outputStr[:-1])


@on_command(name='草精打分榜', only_to_me=False)
@permissionCheck(onlyAdmin=False, costCredentials=5)
async def _(session: CommandSession):
    userId = session.ctx['user_id']
    selfMode = '-self' in session.current_arg_text
    if selfMode:
        rankList = await fieldDB.kusaAdvOnceRanking(userId=userId)
        user = await baseDB.getUser(userId)
        userName = user.name if user.name else user.qq
        outputStr = f"草精打分榜({userName})：\n"
    else:
        rankList = await fieldDB.kusaAdvOnceRanking()
        outputStr = "草精打分榜：\n"
    for i, rank in enumerate(rankList):
        createTime = datetime.fromtimestamp(rank.createTimeTs)
        timeStr = createTime.strftime("%Y-%m-%d %H:%M")
        if selfMode:
            outputStr += f"{i + 1}. {rank.advKusaResult}草精({timeStr})\n"
        else:
            rankUser = await baseDB.getUser(rank.qq)
            userName = rankUser.name if rankUser.name else rankUser.qq
            outputStr += f"{i + 1}. {userName}：{rank.advKusaResult}草精({timeStr})\n"
    await session.send(outputStr[:-1])


@on_command(name='TITLE_LIST', only_to_me=False)
@permissionCheck(onlyAdmin=True)
async def _(session: CommandSession):
    itemTitle = await itemDB.getItemsByType("称号")
    outputStr = "系统称号列表：\n"
    outputStr += "\n".join([f"{item.name}" for item in itemTitle])
    await session.send(outputStr)


@on_command(name='GIVE_TITLE', only_to_me=False)
@permissionCheck(onlyAdmin=True)
async def _(session: CommandSession):
    strippedArg = session.current_arg_text.strip()
    qqNum, title = strippedArg.split(" ")
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
@permissionCheck(onlyAdmin=True)
async def _(session: CommandSession):
    strippedArg = session.current_arg_text.strip()
    qqNum, amount, source = strippedArg.split(" ")
    source = source if source else "qq"
    user = await baseDB.getUser(qqNum)
    if not user:
        await session.send("用户不存在")
        return
    await baseDB.setDonateRecord(qqNum, amount, source)
    await session.send(f'成功添加{qqNum}通过{source}捐赠{amount}元的记录')
    # 关联称号系统，总金额大于20时自动添加‘投喂者’称号
    totalDonateAmount = await baseDB.getDonateAmount(qqNum)
    if totalDonateAmount >= 20:
        haveTitle = await itemDB.getItemAmount(qqNum, "投喂者")
        if not haveTitle:
            await itemDB.changeItemAmount(qqNum, "投喂者", 1)
            await session.send(f'为{qqNum}自动添加了称号“投喂者”')


@on_command(name='SET_NAME', only_to_me=False)
@permissionCheck(onlyAdmin=True)
async def _(session: CommandSession):
    strippedArg = session.current_arg_text.strip()
    qqNum, name = strippedArg.split(" ") if " " in strippedArg else (strippedArg, None)
    if not name:
        bot = get_bot()
        try:
            qqInfo = await bot.get_stranger_info(user_id=qqNum)
            name = qqInfo['nickname']
        except:
            await session.send("获取用户信息失败")
            return

    user = await baseDB.getUser(qqNum)
    if not user:
        await session.send("用户不存在")
        return
    await baseDB.changeName(qqNum, name)
    await session.send(f'成功修改{qqNum}的名字为{name}')
