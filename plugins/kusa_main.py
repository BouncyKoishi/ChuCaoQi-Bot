import re
import nonebot
import dbConnection.db as baseDB
import dbConnection.kusa_item as itemDB
import dbConnection.kusa_field as fieldDB
from utils import convertNumStrToInt
from nonebot import on_command, CommandSession
from kusa_base import config, isUserExist, sendPrivateMsg
from .kusa_statistics import getKusaAdvRank

vipTitleName = ['用户', '信息员', '高级信息员', '特级信息员', '后浪信息员', '天琴信息员', '天琴信息节点',
                '天琴信息矩阵', '天琴信息网络', '???', '???', '???', '???']


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
            output += f'{item.name} * {itemAmount}, ' if item.amountLimit != 1 else f'{item.name}, '
    for item in itemsG:
        itemAmount = await itemDB.getItemAmount(userId, item.name)
        if itemAmount != 0:
            output += f'{item.name} * {itemAmount}, '
    output = output[:-2]

    output += '\n\n当前道具：\n'
    itemsUse = await itemDB.getItemsByType("道具")
    for item in itemsUse:
        itemAmount = await itemDB.getItemAmount(userId, item.name)
        if itemAmount != 0:
            output += f'{item.name} * {itemAmount}, ' if item.amountLimit != 1 else f'{item.name}, '
    if output.endswith("当前道具：\n"):
        output = output[:-6]

    return output[:-2]


async def getItemAmountStr(userId, item):
    itemAmount = await itemDB.getItemAmount(userId, item.name)
    if itemAmount != 0:
        return f'{item.name} * {itemAmount}, ' if itemAmount != 1 else f'{item.name}, '
    return ''


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


@on_command(name='草转让', only_to_me=False)
async def give(session: CommandSession):
    userId = session.ctx['user_id']

    stripped_arg = session.current_arg_text.strip()
    qqNumberList = re.search(r'(?<=(QQ|qq)=)\d+', stripped_arg)
    transferKusaStr = re.search(r'(?<=(kusa|Kusa|KUSA)=)\d+[kmbKMB]?', stripped_arg)

    receiverQQ = qqNumberList.group(0) if qqNumberList else None
    transferKusa = convertNumStrToInt(transferKusaStr.group(0)) if transferKusaStr else 0
    if not receiverQQ:
        await session.send('需要被转让人的QQ号！')
        return
    if not transferKusa:
        await session.send('待转让的草数不合法！')
        return
    if not await isUserExist(receiverQQ):
        await session.send('你想转让的对象并没有生草账户！')
        return

    user = await baseDB.getUser(userId)
    if user.kusa < transferKusa:
        await session.send('你不够草^ ^')
        return
    await baseDB.changeKusa(receiverQQ, transferKusa)
    await baseDB.changeKusa(userId, -transferKusa)

    nickname = session.ctx['sender']['nickname']
    announce = f'{nickname}({userId})转让了{transferKusa}个草给你！'
    hasSendPrivate = sendPrivateMsg(receiverQQ, announce) if transferKusa >= 10000 else False
    st = '转让成功！' if hasSendPrivate else '转让成功！(未私聊通知被转让者)'

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
        await session.send(
            '你已经是后浪信息员了，不能使用本指令提升信息员等级！如果需要进一步升级，请使用“!进阶信息员升级”。')
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


# 生草日报运作
@nonebot.scheduler.scheduled_job('cron', hour=4)
async def dailyReport():
    row = await fieldDB.kusaHistoryTotalReport(86400)
    maxTimes, maxKusa, maxAdvKusa, maxAvgAdvKusa, maxOnceAdvKusa = await fieldDB.kusaFarmChampion()
    outputStr = f"最近24h生草统计:\n" \
                f"总生草次数: {row['count']}\n" \
                f"总草产量: {round(row['sumKusa'] / 1000000, 2)}m\n" \
                f"总草之精华产量: {row['sumAdvKusa']}\n"
    if maxTimes['count']:
        user1 = await baseDB.getUser(maxTimes['qq'])
        userName1 = user1.name if user1.name else user1.qq
        user2 = await baseDB.getUser(maxKusa['qq'])
        userName2 = user2.name if user2.name else user2.qq
        user3 = await baseDB.getUser(maxAdvKusa['qq'])
        userName3 = user3.name if user3.name else user3.qq
        user4 = await baseDB.getUser(maxAvgAdvKusa['qq'])
        userName4 = user4.name if user4.name else user4.qq
        user5 = await baseDB.getUser(maxOnceAdvKusa['qq'])
        userName5 = user5.name if user5.name else user5.qq
        outputStr += f"\n" \
                     f"生草次数最多: {userName1}({maxTimes['count']}次)\n" \
                     f"获得草最多: {userName2}(共{round(maxKusa['sumKusa'] / 1000000, 2)}m草)\n" \
                     f"获得草之精华最多: {userName3}(共{maxAdvKusa['sumAdvKusa']}草精)\n" \
                     f"平均草之精华最多: {userName4}(平均{round(maxAvgAdvKusa['avgAdvKusa'], 2)}草精)\n" \
                     f"单次草之精华最多: {userName5}({maxOnceAdvKusa['maxAdvKusa']}草精)"
    await nonebot.get_bot().send_group_msg(group_id=config['group']['main'], message=outputStr)


# 生草周报运作
@nonebot.scheduler.scheduled_job('cron', hour=4, minute=1, day_of_week='mon')
async def weeklyReport():
    row = await fieldDB.kusaHistoryTotalReport(604800)
    outputStr = f"最近一周生草统计:\n" \
                f"总生草次数: {row['count']}\n" \
                f"总草产量: {round(row['sumKusa'] / 1000000)}m\n" \
                f"总草之精华产量: {row['sumAdvKusa']}"
    await nonebot.get_bot().send_group_msg(group_id=config['group']['main'], message=outputStr)


# 每周草精总榜
@nonebot.scheduler.scheduled_job('cron', hour=4, minute=2, day_of_week='mon')
async def weeklyReport():
    outputStr = await getKusaAdvRank()
    await nonebot.get_bot().send_group_msg(group_id=config['group']['main'], message=outputStr)
