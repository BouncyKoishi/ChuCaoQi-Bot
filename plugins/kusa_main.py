import re
import math
import random
import nonebot
import dbConnection.db as baseDB
import dbConnection.kusa_item as itemDB
import dbConnection.kusa_field as fieldDB
from nonebot import on_command, CommandSession
from kusa_base import isUserExist, config

vipTitleName = ['用户', '信息员', '高级信息员', '特级信息员', '后浪信息员', '天琴信息员', '天琴信息节点', '天琴信息矩阵', '天琴信息网络',
                '???', '???', '???', '???']


@on_command(name='仓库', only_to_me=False)
async def warehouse(session: CommandSession):
    stripped_arg = session.current_arg_text.strip()
    targetQQList = re.search(r'(?<=(QQ|qq)=)\d+', stripped_arg)
    if targetQQList:
        watcherQQ = session.ctx['user_id']
        recceItemAmount = await itemDB.getItemAmount(watcherQQ, '侦察凭证')
        if not recceItemAmount:
            await session.send('你当前不能查看别人的仓库！请到商店购买侦察凭证。')
            return
        targetQQ = int(targetQQList.group(0))
        if not await isUserExist(targetQQ):
            await session.send('你想查看的对象并没有生草账户！')
            return
        user = await baseDB.getUser(targetQQ)
        nickname = user.name if user.name else user.qq
        output = '[侦察卫星使用中]\n'
        output += f'{nickname}的仓库状况如下：\n'
        output += await getWarehouseInfoStr(user)
        await session.send(output)
        await itemDB.changeItemAmount(watcherQQ, '侦察凭证', -1)
    else:
        userId = session.ctx['user_id']
        user = await baseDB.getUser(userId)
        nickname = user.name if user.name else session.ctx['sender']['nickname']

        output = ''
        if user.donateAmount:
            output += f'感谢您，生草系统的捐助者!\n'
        output += f'Lv{user.vipLevel} ' if user.vipLevel else ''
        output += f'{user.title} ' if user.title else f'{vipTitleName[user.vipLevel]} '
        output += f'{nickname}({userId})\n'
        output += await getWarehouseInfoStr(user)
        await session.send(output)


async def getWarehouseInfoStr(user):
    userId = user.qq
    output = f'当前拥有草: {user.kusa}\n'
    output += (f'当前拥有草之精华: {user.advKusa}\n' if user.advKusa else '')

    output += f'\n当前财产：\n'
    itemsWorth = await itemDB.getItemsByType("财产")
    itemsG = await itemDB.getItemsByType("G")
    for item in itemsWorth:
        itemAmount = await itemDB.getItemAmount(userId, item.name)
        if itemAmount != 0:
            output += f'{item.name} * {itemAmount}, ' if not item.isSingle else f'{item.name}, '
    for item in itemsG:
        itemAmount = await itemDB.getItemAmount(userId, item.name)
        if itemAmount != 0:
            output += f'{item.name} * {itemAmount}, ' if not item.isSingle else f'{item.name}, '
    output = output[:-2]

    output += '\n\n当前道具：\n'
    itemsUse = await itemDB.getItemsByType("道具")
    for item in itemsUse:
        itemAmount = await itemDB.getItemAmount(userId, item.name)
        if itemAmount != 0:
            output += f'{item.name} * {itemAmount}, ' if not item.isSingle else f'{item.name}, '
    if output.endswith("当前道具：\n"):
        output = output[:-6]

    return output[:-2]


@on_command(name='能力', only_to_me=False)
async def _(session: CommandSession):
    userId = session.ctx['user_id']
    itemsSkill = await itemDB.getItemsByType("能力")
    itemsDrawing = await itemDB.getItemsByType("图纸")
    if not itemsSkill and not itemsDrawing:
        await session.send('当前没有任何能力或图纸！')
        return

    output = ''
    if itemsSkill:
        output += f'你当前所拥有的能力：\n'
        for item in itemsSkill:
            itemAmount = await itemDB.getItemAmount(userId, item.name)
            if itemAmount != 0:
                output += f'{item.name}, '
        output = output[:-2]
        
    if itemsDrawing:
        output += '\n\n' if output else ''
        output += f'你当前所拥有的图纸：\n'
        for item in itemsDrawing:
            itemAmount = await itemDB.getItemAmount(userId, item.name)
            if itemAmount != 0:
                output += f'{item.name}, '
        output = output[:-2]
    await session.send(output)


@on_command(name='改名', only_to_me=False)
async def change_name(session: CommandSession):
    userId = session.ctx['user_id']
    stripped_arg = session.current_arg_text.strip()
    if stripped_arg:
        if len(stripped_arg) <= 25:
            await baseDB.changeName(userId, stripped_arg)
            await session.send(f'已经将您的名字改为 {stripped_arg}')
        else:
            await session.send('名字太长了^ ^')


@on_command(name='称号', only_to_me=False)
async def _(session: CommandSession):
    userId = session.ctx['user_id']
    itemTitle = await itemDB.getItemsByType("称号")
    if not itemTitle:
        await session.send('当前没有任何称号！')
        return

    ownTitle = []
    for item in itemTitle:
        itemAmount = await itemDB.getItemAmount(userId, item.name)
        if itemAmount != 0:
            ownTitle.append(item.name)
    if not ownTitle:
        await session.send('当前没有任何可用称号！')
        return
    output = f'你当前可用的称号：\n'
    output += f'{", ".join(ownTitle)}'
    await session.send(output)


@on_command(name='修改称号', only_to_me=False)
async def change_title(session: CommandSession):
    userId = session.ctx['user_id']
    stripped_arg = session.current_arg_text.strip()
    if not stripped_arg:
        await baseDB.changeTitle(userId, None)
        await session.send('修改成功！当前不展示任何称号')
        return
    item = await itemDB.getItem(stripped_arg)
    if not item or item.type != '称号':
        await session.send('你想使用的称号不存在^ ^')
        return
    itemAmount = await itemDB.getItemAmount(userId, stripped_arg)
    if not itemAmount:
        await session.send('你没有这个称号^ ^')
        return
    await baseDB.changeTitle(userId, stripped_arg)
    await session.send(f'修改成功！当前称号为 {stripped_arg}')


@on_command(name='配置列表', only_to_me=False)
async def flag_list(session: CommandSession):
    userId = session.ctx['user_id']
    flagList = await baseDB.getFlagList()
    output = ""
    for flag in flagList:
        flagValue = await baseDB.getFlagValue(userId, flag.name)
        flagType = 'on' if flagValue else 'off'
        output += f'{flag.name}: {flagType}\n'
    await session.send(output[:-1])


@on_command(name='配置', only_to_me=False)
async def flag_set(session: CommandSession):
    userId = session.ctx['user_id']
    stripped_arg = session.current_arg_text.strip()
    flagName, flagType = stripped_arg.split()
    if flagType.lower() != 'on' and flagType.lower() != 'off':
        return
    flagValue = 1 if flagType.lower() == 'on' else 0
    await baseDB.setFlag(userId, flagName, flagValue)
    await session.send('设置成功！')


@on_command(name='口球', only_to_me=False)
async def kusa_ban(session: CommandSession):
    groupNum = session.ctx['group_id']
    userId = session.ctx['user_id']

    st = '已经送出^ ^'
    stripped_arg = session.current_arg_text.strip()
    receiverQQ = re.search(r'(?<=(QQ|qq)=)\d+', stripped_arg)
    seconds = re.search(r'(?<=(sec|SEC)=)\d+', stripped_arg)
    if receiverQQ and seconds:
        receiverQQ = int(receiverQQ.group(0))
        seconds = int(seconds.group(0))
        if seconds > 0:
            user = await baseDB.getUser(userId)
            costKusa = seconds
            if user.kusa >= costKusa:
                await nonebot.get_bot().set_group_ban(group_id=groupNum, user_id=receiverQQ, duration=seconds)
                await baseDB.changeKusa(userId, -costKusa)
                await baseDB.changeKusa(config['qq']['bot'], costKusa)
            else:
                st = '你不够草^ ^'
        else:
            await nonebot.get_bot().set_group_ban(group_id=groupNum, user_id=receiverQQ, duration=seconds)
            st = '已解除相关人员的口球(如果有的话)'
    else:
        st = '参数不正确^ ^'
    await session.send(st)


@on_command(name='解除口球', only_to_me=False)
async def _(session: CommandSession):
    await session.send("本指令已经废弃。使用“!口球 qq=[qq号] sec=0”即可解除任意口球。")


@on_command(name='草转让', only_to_me=False)
async def give(session: CommandSession):
    userId = session.ctx['user_id']

    st = '转让成功！'
    stripped_arg = session.current_arg_text.strip()
    receiverQQ = re.search(r'(?<=(QQ|qq)=)\d+', stripped_arg)
    transferKusa = re.search(r'(?<=(kusa|Kusa|KUSA)=)\d+', stripped_arg)
    if receiverQQ and transferKusa:
        receiverQQ = int(receiverQQ.group(0))
        transferKusa = int(transferKusa.group(0))

        if transferKusa == 0:
            return
        if await isUserExist(receiverQQ):
            user = await baseDB.getUser(userId)
            if user.kusa >= transferKusa:
                await baseDB.changeKusa(receiverQQ, transferKusa)
                await baseDB.changeKusa(userId, -transferKusa)

                bot = nonebot.get_bot()
                nickname = session.ctx['sender']['nickname']
                announce = f'{nickname}({userId})转让了{transferKusa}个草给你！'
                if transferKusa >= 10000:
                    try:
                        await bot.send_private_msg(user_id=receiverQQ, message=announce)
                    except:
                        st += '（未能私聊通知被转让者）'
            else:
                st = '你不够草^ ^'
        else:
            st = '你想转让的对象并没有生草账户！'
    else:
        st = '参数不正确^ ^'
    await session.send(st)


@on_command(name='草压缩', only_to_me=False)
async def kusa_compress(session: CommandSession):
    userId = session.ctx['user_id']
    baseExist = await itemDB.getItemAmount(userId, '草压缩基地')
    if not baseExist:
        await session.send('你没有草压缩基地，无法使用本指令！')
        return

    user = await baseDB.getUser(userId)
    stripped_arg = session.current_arg_text.strip()
    kusaAdvGain = int(stripped_arg) if stripped_arg else 1
    kusaUse = 1000000 * kusaAdvGain
    if user.kusa >= kusaUse:
        await baseDB.changeAdvKusa(userId, kusaAdvGain)
        await baseDB.changeKusa(userId, -kusaUse)
        await session.send(f'压缩成功！你的草压缩基地消耗了{kusaUse}草，产出了{kusaAdvGain}个草之精华！')
    else:
        await session.send('你不够草^ ^')


@on_command(name='信息员升级', only_to_me=False)
async def vip_upgrade(session: CommandSession):
    userId = session.ctx['user_id']
    user = await baseDB.getUser(userId)
    if user.vipLevel >= 4:
        await session.send('你已经是后浪信息员了，不能使用本指令提升信息员等级！如果需要进一步升级，请使用“!进阶信息员升级”。')
        return
    newLevel = user.vipLevel + 1
    costKusa = 50 * (10 ** newLevel)
    if user.kusa >= costKusa:
        user.vipLevel = newLevel
        await user.save()
        await baseDB.changeKusa(userId, -costKusa)
        await baseDB.changeKusa(config['qq']['bot'], costKusa)
        await session.send(f'获取成功！你成为了{vipTitleName[newLevel]}！')
    else:
        await session.send(f'成为{vipTitleName[newLevel]}需要消耗{costKusa}草，你不够草^ ^')


@on_command(name='进阶信息员升级', only_to_me=False)
async def vip_upgrade_2(session: CommandSession):
    userId = session.ctx['user_id']
    user = await baseDB.getUser(userId)
    if user.vipLevel < 4:
        await session.send('你还不是后浪信息员，不能使用本指令提升信息员等级！如果需要升级，请使用“!信息员升级”。')
        return
    if user.vipLevel >= 8:
        await session.send('你已经是当前最高级的信息员了！')
        return
    newLevel = user.vipLevel + 1
    costAdvPoint = 10 ** (newLevel - 4)
    if user.advKusa >= costAdvPoint:
        user.vipLevel = newLevel
        await user.save()
        await baseDB.changeAdvKusa(userId, -costAdvPoint)
        await baseDB.changeAdvKusa(config['qq']['bot'], costAdvPoint)
        await session.send(f'获取成功！你成为了{vipTitleName[newLevel]}！')
    else:
        await session.send(f'成为{vipTitleName[newLevel]}需要消耗{costAdvPoint}个草之精华，你的草之精华不够^ ^')


# 生草工业运作
@nonebot.scheduler.scheduled_job('cron', hour=0)
async def daily():
    bot = nonebot.get_bot()
    randomKusa = int(4 + 8 * random.random())
    randomCore = int(4 + 8 * random.random())
    stKusa = f'生草机器 正在运作中……\n今日生草机器产量:{randomKusa}'
    stCore = f'核心装配工厂 正在运作中……\n今日核心装配工厂产量:{randomCore}'
    try:
        await bot.send_group_msg(group_id=config['group']['main'], message=stKusa)
        await bot.send_group_msg(group_id=config['group']['main'], message=stCore)
    except:
        pass

    userList = await baseDB.getAllUser()
    for user in userList:
        machineAmount = await itemDB.getItemAmount(user.qq, '生草机器')
        factoryAmount = await itemDB.getItemAmount(user.qq, '生草工厂')
        mobileFactoryAmount = await itemDB.getItemAmount(user.qq, '流动生草工厂')
        advFactoryInfo = await itemDB.getItemStorageInfo(user.qq, '草精炼厂')
        factoryNewDeviceI = await itemDB.getItemAmount(user.qq, '生草工厂新型设备I')
        factoryAdditionI = await itemDB.getItemAmount(user.qq, '生草工厂效率I')
        factoryAdditionII = await itemDB.getItemAmount(user.qq, '生草工厂效率II')
        machineAddition = await itemDB.getItemAmount(user.qq, '试做型机器I')
        machineAddKusa = randomKusa * machineAmount
        machineAddKusa *= 10 if machineAddition else 1
        factoryAddKusa = 640 * (factoryAmount + mobileFactoryAmount)
        factoryAddKusa *= 2 if factoryNewDeviceI else 1
        factoryAddKusa *= 2 if factoryAdditionI else 1
        factoryAddKusa *= 2 if factoryAdditionII else 1
        advFactoryCostKusa = 5000 * advFactoryInfo.amount if advFactoryInfo and advFactoryInfo.allowUse else 0
        addKusa = machineAddKusa + factoryAddKusa - advFactoryCostKusa
        addKusa = math.ceil(addKusa)
        await baseDB.changeKusa(user.qq, addKusa)
        if advFactoryInfo and advFactoryInfo.allowUse:
            advKusaBaseAddition = await itemDB.getItemAmount(user.qq, '高效草精炼指南')
            sevenPlanetMagic = await itemDB.getItemAmount(user.qq, '七曜精炼术')
            advKusaAdditionI = await itemDB.getItemAmount(user.qq, '草精炼厂效率I')
            advKusa = advFactoryInfo.amount
            advKusa += min(advKusaBaseAddition, advFactoryInfo.amount)
            advKusa += (advFactoryInfo.amount // 7) * 4 if sevenPlanetMagic else 0
            advKusa += (advFactoryInfo.amount - 7) if advKusaAdditionI and advFactoryInfo.amount > 7 else 0
            await baseDB.changeAdvKusa(user.qq, advKusa)

        coreFactoryAmount = await itemDB.getItemAmount(user.qq, '核心装配工厂')
        coreFactoryAdditionI = await itemDB.getItemAmount(user.qq, '核心工厂效率I')
        addCore = randomCore * coreFactoryAmount
        addCore *= 2 if coreFactoryAdditionI else 1
        addCore = math.ceil(addCore)
        await itemDB.changeItemAmount(user.qq, '自动化核心', addCore)

        blackTeaPool = await itemDB.getItemAmount(user.qq, '红茶池')
        if blackTeaPool:
            await itemDB.changeItemAmount(user.qq, '红茶', 15)
            print(f'用户{user.qq}的红茶池已补充')

        print(f'用户{user.qq}的每日工厂运作完毕。增加了{addKusa}草，{addCore}个自动化核心，'
              f'{advFactoryInfo.amount if advFactoryInfo else 0}个草之精华。')
    print(f'每日生草机器、生草工厂、核心工厂、草精炼厂运作完毕。草随机值为{randomKusa}，核心随机值为{randomCore}。')


# 生草冠军运作
@nonebot.scheduler.scheduled_job('cron', hour=4)
async def dailyChampion():
    row = await fieldDB.kusaHistoryDailyReport()
    maxTimes, maxKusa, maxAdvKusa, maxAvgAdvKusa = await fieldDB.kusaFarmChampion()
    user1 = await baseDB.getUser(maxTimes['qq'])
    userName1 = user1.name if user1.name else user1.qq
    user2 = await baseDB.getUser(maxKusa['qq'])
    userName2 = user2.name if user2.name else user2.qq
    user3 = await baseDB.getUser(maxAdvKusa['qq'])
    userName3 = user3.name if user3.name else user3.qq
    user4 = await baseDB.getUser(maxAvgAdvKusa['qq'])
    userName4 = user4.name if user4.name else user4.qq
    outputStr = f"最近24h生草统计:\n" \
                f"总生草次数: {row['count']}\n" \
                f"总草产量: {round(row['sumKusa'] / 1000000, 2)}m\n" \
                f"总草之精华产量: {row['sumAdvKusa']}\n" \
                f"\n" \
                f"生草次数最多: {userName1}({maxTimes['count']}次)\n" \
                f"获得草最多: {userName2}(共{round(maxKusa['sumKusa'] / 1000000, 2)}m草)\n" \
                f"获得草之精华最多: {userName3}(共{maxAdvKusa['sumAdvKusa']}草精)\n" \
                f"平均草之精华最多: {userName4}(平均{round(maxAvgAdvKusa['avgAdvKusa'], 2)}草精)"
    await nonebot.get_bot().send_group_msg(group_id=config['group']['main'], message=outputStr)
