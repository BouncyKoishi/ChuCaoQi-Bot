import io
import re
import math
import time
import codecs
import random
import asyncio
from typing import Optional, Dict

import nonebot
import datetime
from collections import Counter
from nonebot import on_command, CommandSession
from kusa_base import buying, selling, config, sendGroupMsg
from utils import rd3, imgBytesToBase64
import dbConnection.db as baseDB
import dbConnection.kusa_item as itemDB
import dbConnection.g_value as gValueDB

import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt

systemRandom = random.SystemRandom()
gPicCache: Dict[str, Optional[bytes]] = {
    '东': None,
    '南': None,
    '北': None,
    '珠': None,
    '深': None,
    'all': None,
}


@on_command(name='测G', only_to_me=False)
async def _(session: CommandSession):
    userId = session.ctx['user_id']
    gValues = await gValueDB.getLatestGValues()
    gValuesLast = await gValueDB.getSecondLatestGValues()

    st = f'G市有风险，炒G需谨慎！\n'
    if gValues.turn != 1:
        st += '当前G值为：\n'
        st += formatGValue(gValues.eastValue, gValuesLast.eastValue, '东')
        st += formatGValue(gValues.southValue, gValuesLast.southValue, '南')
        st += formatGValue(gValues.northValue, gValuesLast.northValue, '北')
        st += formatGValue(gValues.zhuhaiValue, gValuesLast.zhuhaiValue, '珠海')
        st += formatGValue(gValues.shenzhenValue, gValuesLast.shenzhenValue, '深圳')
        st += f'当前为本周期第{gValues.turn}期数值。\n\n'
    else:
        st += f'当前为本周期的第一期数值！\n当前G值为：\n'
        st += f'东校区：{areaStartValue("东")}\n南校区：{areaStartValue("南")}\n北校区：{areaStartValue("北")}\n' \
              f'珠海校区：{areaStartValue("珠")}\n深圳校区：{areaStartValue("深")}\n\n'

    eastGAmount, southGAmount, northGAmount, zhuhaiGAmount, shenzhenGAmount = await getAllGAmounts(userId)
    st += f'您拥有的G：\n'
    st += (f'东校区： {eastGAmount}\n' if eastGAmount else '')
    st += (f'南校区： {southGAmount}\n' if southGAmount else '')
    st += (f'北校区： {northGAmount}\n' if northGAmount else '')
    st += (f'珠海校区： {zhuhaiGAmount}\n' if zhuhaiGAmount else '')
    st += (f'深圳校区： {shenzhenGAmount}\n' if shenzhenGAmount else '')
    st += (f'您当前没有任何G!\n' if not (
                eastGAmount or southGAmount or northGAmount or zhuhaiGAmount or shenzhenGAmount) else '')

    st += '\n使用 !G市帮助 可以查看G市交易相关指令。'
    await session.send(st[:-1])


def formatGValue(currentValue, lastValue, campusName):
    change = currentValue - lastValue
    percentageChange = (change / lastValue * 100) if lastValue != 0 else 0
    pChangeSign = '+' if change >= 0 else ''
    return f'{campusName}校区：{currentValue:.3f}({pChangeSign}{percentageChange:.2f}%)\n'


@on_command(name='G市帮助', only_to_me=False)
async def GHelp(session: CommandSession):
    with codecs.open(u'text/生草系统-G市帮助.txt', 'r', 'utf-8') as f:
        await session.send(f.read().strip())


@on_command(name='测F', only_to_me=False)
async def _(session: CommandSession):
    st = '啊，这……'
    await session.send(st)


@on_command(name='测H', only_to_me=False)
async def _(session: CommandSession):
    st = '您不够H^ ^'
    await session.send(st)


@on_command(name='测*', only_to_me=False)
async def _(session: CommandSession):
    st = '*^ ^*'
    await session.send(st)


@on_command(name='交易总结', only_to_me=False)
async def _(session: CommandSession):
    if not await tradingTimeCheck():
        await session.send('请在G市结算完成后再查询交易总结^ ^')
        return
    userId = session.ctx['user_id']
    gValues = await gValueDB.getLatestGValues()
    eastGAmount, southGAmount, northGAmount, zhuhaiGAmount, shenzhenGAmount = await getAllGAmounts(userId)
    gStartTs = getGCycleStartTs(gValues)
    tradeRecordBuying = await baseDB.getTradeRecord(operator=userId, startTime=gStartTs, tradeType='G市(买)')
    tradeRecordSelling = await baseDB.getTradeRecord(operator=userId, startTime=gStartTs, tradeType='G市(卖)')
    nowKusaInG = int(sum([
        eastGAmount * gValues.eastValue, southGAmount * gValues.southValue,
        northGAmount * gValues.northValue, zhuhaiGAmount * gValues.zhuhaiValue,
        shenzhenGAmount * gValues.shenzhenValue
    ]))
    allCostKusa = sum([record.costItemAmount for record in tradeRecordBuying])
    allGainKusa = sum([record.gainItemAmount for record in tradeRecordSelling])
    st = f'您本周期的G市交易总结：\n'
    st += f'当前持仓相当于{nowKusaInG}草，本周期共投入{allCostKusa}草，共取出{allGainKusa}草。\n'
    st += f'本周期盈亏估值：{nowKusaInG + allGainKusa - allCostKusa}草。\n\n'

    if not (eastGAmount or southGAmount or northGAmount or zhuhaiGAmount or shenzhenGAmount):
        st += '您当前在G市暂无持仓。\n'
    else:
        st += f'您的具体持仓如下：\n'
        st += (f'东校区： {eastGAmount}G * {gValues.eastValue:.3f} = {eastGAmount * gValues.eastValue:.0f}草\n' if eastGAmount else '')
        st += (f'南校区： {southGAmount}G * {gValues.southValue:.3f} = {southGAmount * gValues.southValue:.0f}草\n' if southGAmount else '')
        st += (f'北校区： {northGAmount}G * {gValues.northValue:.3f} = {northGAmount * gValues.northValue:.0f}草\n' if northGAmount else '')
        st += (f'珠海校区： {zhuhaiGAmount}G * {gValues.zhuhaiValue:.3f} = {zhuhaiGAmount * gValues.zhuhaiValue:.0f}草\n' if zhuhaiGAmount else '')
        st += (f'深圳校区： {shenzhenGAmount}G * {gValues.shenzhenValue:.3f} = {shenzhenGAmount * gValues.shenzhenValue:.0f}草\n' if shenzhenGAmount else '')

    await session.send(st[:-1])


@on_command(name='上期交易总结', only_to_me=False)
async def _(session: CommandSession):
    if not await tradingTimeCheck():
        await session.send('请在G市结算完成后再查询上期交易总结^ ^')
        return
    userId = session.ctx['user_id']
    gValues = await gValueDB.getLatestGValues()
    gThisCycleStartTs = getGCycleStartTs(gValues)
    gLastCycleStartTs = gThisCycleStartTs - 3 * 86400
    tradeRecordBuying = await baseDB.getTradeRecord(operator=userId, startTime=gLastCycleStartTs, endTime=gThisCycleStartTs, tradeType='G市(买)')
    tradeRecordSelling = await baseDB.getTradeRecord(operator=userId, startTime=gLastCycleStartTs, endTime=gThisCycleStartTs,  tradeType='G市(卖)')
    allCostKusa = sum([record.costItemAmount for record in tradeRecordBuying])
    allGainKusa = sum([record.gainItemAmount for record in tradeRecordSelling])
    st = f'您上周期的G市交易总结：\n'
    st += f'上周期共投入{allCostKusa}草，共取出{allGainKusa}草，总盈亏：{allGainKusa - allCostKusa}草。'
    await session.send(st)


@on_command(name='交易记录', only_to_me=False)
async def _(session: CommandSession):
    userId = session.ctx['user_id']
    gValues = await gValueDB.getLatestGValues()

    gStartTs = getGCycleStartTs(gValues)
    tradeRecordBuying = await baseDB.getTradeRecord(operator=userId, startTime=gStartTs, tradeType='G市(买)')
    tradeRecordSelling = await baseDB.getTradeRecord(operator=userId, startTime=gStartTs, tradeType='G市(卖)')
    if not (tradeRecordBuying or tradeRecordSelling):
        await session.send('您本周期暂无G市交易记录= =')
    allRecords = tradeRecordBuying + tradeRecordSelling
    allRecords.sort(key=lambda tradeRecord: tradeRecord.timestamp, reverse=True)

    pageSize = 10
    totalPages = (len(allRecords) + pageSize - 1) // pageSize

    for currentPage in range(1, totalPages + 1):
        startIndex = (currentPage - 1) * pageSize
        endIndex = startIndex + pageSize
        pageRecords = allRecords[startIndex:endIndex]
        outputStr = f'您本周期的G市交易记录如下：\n'
        for record in pageRecords:
            recordTime = datetime.datetime.fromtimestamp(record.timestamp).strftime('%m-%d %H:%M')
            if record.tradeType == 'G市(买)':
                unitPrice = rd3(record.costItemAmount / record.gainItemAmount)
                outputStr += f'{recordTime}：买入{record.gainItemAmount}{record.gainItemName}，花费{record.costItemAmount}草，等效单价为{unitPrice}\n'
            if record.tradeType == 'G市(卖)':
                unitPrice = rd3(record.gainItemAmount / record.costItemAmount)
                outputStr += f'{recordTime}：卖出{record.costItemAmount}{record.costItemName}，获得{record.gainItemAmount}草，等效单价为{unitPrice}\n'
        if totalPages > 1 and currentPage < totalPages:
            confirm = await session.aget(prompt=outputStr + f'(当前第{currentPage}/{totalPages}页，输入Next显示下一页)')
            if confirm.lower() != 'next':
                break
        else:
            await session.send(outputStr[:-1])


def getGCycleStartTs(gValues):
    # 假设G周期未变动的异常出现小于10次，获取原始gStartTs对应的日期，并重置到当天的23点45分
    gStartTs = datetime.datetime.now().timestamp() - 1800 * (gValues.turn + 10)
    gStartDatetime = datetime.datetime.fromtimestamp(gStartTs)
    gStartTs = datetime.datetime(gStartDatetime.year, gStartDatetime.month, gStartDatetime.day, 23, 50).timestamp()
    return gStartTs


@on_command(name='G买入', only_to_me=False)
async def _(session: CommandSession):
    if not await tradingTimeCheck():
        await session.send('当前是结算时间，无法进行G交易^ ^')
        return

    userId = session.ctx['user_id']
    st = ''
    strippedArg = session.current_arg_text.strip()
    buyingAmount = re.findall(r'\d+', strippedArg)
    buyingAmount = int(buyingAmount[0]) if buyingAmount else 0
    isBuyingAll = re.findall(r'all', strippedArg)
    schoolRatio = Counter()
    schoolRatio.update(re.findall(r'[东南北珠深]', strippedArg))
    gValues = await gValueDB.getLatestGValues()

    if isBuyingAll:
        if not schoolRatio:
            await session.send('参数不正确^ ^')
            return
        user = await baseDB.getUser(userId)
        kusa = user.kusa
        for schoolName in '东南北珠深':
            ratio = schoolRatio.get(schoolName)
            if ratio is None:
                continue
            gType = areaTranslateItem(schoolName)
            valueType = areaTranslateValue(schoolName)
            gValue = getattr(gValues, valueType)
            buyingAmount = math.floor(math.floor(kusa / sum(schoolRatio.values()) * ratio) / gValue)
            totalPrice = int(buyingAmount * gValue)
            if await buying(userId, gType, buyingAmount, totalPrice, 'G市(买)'):
                st += f'花费{totalPrice}草，买入了{buyingAmount}{gType}\n'
        st = st.strip()
        if not st:
            st = '你不够草^ ^'
    elif buyingAmount:
        for schoolName in '东南北珠深':
            ratio = schoolRatio.get(schoolName)
            if ratio is None:
                continue
            gType = areaTranslateItem(schoolName)
            valueType = areaTranslateValue(schoolName)
            gValue = getattr(gValues, valueType)
            totalPrice = int(buyingAmount * ratio * gValue)
            if await buying(userId, gType, buyingAmount * ratio, totalPrice, 'G市(买)'):
                st += f'花费{totalPrice}草，买入了{buyingAmount * ratio}{gType}\n'
        st = st.strip()
        if not st:
            st = '你不够草^ ^'
    else:
        st = '参数不正确^ ^'

    await session.send(st)


@on_command(name='G卖出', only_to_me=False)
async def _(session: CommandSession):
    if not await tradingTimeCheck():
        await session.send('当前是结算时间，无法进行G交易^ ^')
        return

    userId = session.ctx['user_id']
    st = ''
    strippedArg = session.current_arg_text.strip()
    sellingAmount = re.findall(r'\d+', strippedArg)
    sellingAmount = int(sellingAmount[0]) if sellingAmount else 0
    isSellingAll = re.findall(r'all', strippedArg)
    schoolRatio = Counter()
    schoolRatio.update(re.findall(r'[东南北珠深]', strippedArg))
    gValues = await gValueDB.getLatestGValues()

    if isSellingAll:
        if not schoolRatio:
            allKusa = await GSellingAll(userId, gValues)
            await session.send(f'已卖出所有G，获得了{allKusa}草')
            return
        EGAmount, SGAmount, NGAmount, ZGAmount, SZGAmount = await getAllGAmounts(userId)
        for schoolName in '东南北珠深':
            ratio = schoolRatio.get(schoolName)
            if ratio is None:
                continue
            gType = areaTranslateItem(schoolName)
            valueType = areaTranslateValue(schoolName)
            gValue = getattr(gValues, valueType)
            sellingAmount = {'东': EGAmount, '南': SGAmount, '北': NGAmount, '珠': ZGAmount, '深': SZGAmount}[schoolName]
            totalPrice = int(sellingAmount * gValue * (1 - 0.0005))
            if await selling(userId, gType, sellingAmount * ratio, totalPrice, 'G市(卖)'):
                st += f'卖出了{sellingAmount}{gType}，获得了{totalPrice}草\n'
        st = st.strip()
        if not st:
            st = '你没有可卖出的G^ ^'
    elif sellingAmount:
        for schoolName in '东南北珠深':
            ratio = schoolRatio.get(schoolName)
            if ratio is None:
                continue
            gType = areaTranslateItem(schoolName)
            valueType = areaTranslateValue(schoolName)
            gValue = getattr(gValues, valueType)
            totalPrice = int(sellingAmount * ratio * gValue * (1 - 0.0005))
            if await selling(userId, gType, sellingAmount * ratio, totalPrice, 'G市(卖)'):
                st += f'卖出了{sellingAmount * ratio}{gType}，获得了{totalPrice}草\n'
        st = st.strip()
        if not st:
            st = '你不够G^ ^'
    else:
        st = '参数不正确^ ^'
    await session.send(st)


async def GSellingAll(userId, gValues):
    EGAmount, SGAmount, NGAmount, ZGAmount, SZGAmount = await getAllGAmounts(userId)
    allKusa = int(sum([
        EGAmount * gValues.eastValue, SGAmount * gValues.southValue,
        NGAmount * gValues.northValue, ZGAmount * gValues.zhuhaiValue,
        SZGAmount * gValues.shenzhenValue
    ]) * (1 - 0.0005))

    await baseDB.changeKusa(userId, allKusa)
    await baseDB.changeKusa(config['qq']['bot'], -allKusa)
    await itemDB.cleanAllG(userId)
    for amount, area, values in zip(
        [EGAmount, SGAmount, NGAmount, ZGAmount, SZGAmount],
        ['东校区', '南校区', '北校区', '珠海校区', '深圳校区'],
        [gValues.eastValue, gValues.southValue, gValues.northValue, gValues.zhuhaiValue, gValues.shenzhenValue]
    ):
        if amount > 0:
            kusaAmount = math.ceil(amount * values * (1 - 0.0005))
            await baseDB.setTradeRecord(
                operator=userId, tradeType='G市(卖)',
                gainItemName='草', gainItemAmount=kusaAmount,
                costItemName=f'G({area})', costItemAmount=amount
            )
    return allKusa


async def tradingTimeCheck():
    # 非交易周期：当前G值为第一周期，且时间在23：50分之前
    gValues = await gValueDB.getLatestGValues()
    if gValues.turn == 1 and datetime.datetime.now().minute < 50:
        return False
    return True


@on_command(name='G线图', only_to_me=False)
async def G_pic(session: CommandSession):
    stripped_arg = session.current_arg_text.strip()
    school = re.findall(r'[东南北珠深]', stripped_arg)
    school = school[0] if school and school[0] in '东南北珠深' else 'all'
    if gPicCache[school] is None:
        await createGpic()
    pic = imgBytesToBase64(gPicCache[school])
    await session.send(pic)


def getGValuesColMap(gValuesList):
    gValuesColMap = {'eastValue': [], 'southValue': [], 'northValue': [], 'zhuhaiValue': [], 'shenzhenValue': []}
    for gValues in gValuesList:
        gValuesColMap['eastValue'].append(gValues.eastValue)
        gValuesColMap['southValue'].append(gValues.southValue)
        gValuesColMap['northValue'].append(gValues.northValue)
        gValuesColMap['zhuhaiValue'].append(gValues.zhuhaiValue)
        gValuesColMap['shenzhenValue'].append(gValues.shenzhenValue)
    return gValuesColMap


async def createGpic():
    global gPicCache
    startTs = datetime.datetime.now().timestamp()
    gValuesList = await gValueDB.getThisCycleGValues()
    gValuesColMap = getGValuesColMap(gValuesList)
    for school in '东南北珠深':
        gType = areaTranslateValue(school)
        gPicCache[school] = createGpicSingle(gValuesColMap[gType])
    gPicCache['all'] = createGpicAll(gValuesColMap)
    endTs = datetime.datetime.now().timestamp()
    print(f'G线图生成时间：{endTs - startTs}')


def createGpicSingle(gValuesCol):
    buf = io.BytesIO()
    plt.plot(gValuesCol)
    plt.xticks([])
    plt.savefig(buf, format='png')
    plt.close()
    return buf.getvalue()


def createGpicAll(gValuesColMap):
    buf = io.BytesIO()
    plt.plot(list(map(lambda x: x / areaStartValue('东'), gValuesColMap['eastValue'])), label='East')
    plt.plot(list(map(lambda x: x / areaStartValue('南'), gValuesColMap['southValue'])), label='South')
    plt.plot(list(map(lambda x: x / areaStartValue('北'), gValuesColMap['northValue'])), label='North')
    plt.plot(list(map(lambda x: x / areaStartValue('珠'), gValuesColMap['zhuhaiValue'])), label='Zhuhai')
    plt.plot(list(map(lambda x: x / areaStartValue('深'), gValuesColMap['shenzhenValue'])), label='Shenzhen')
    plt.xticks([])
    plt.yscale('log')
    plt.legend()
    plt.savefig(buf, format='png')
    plt.close()
    return buf.getvalue()


@nonebot.scheduler.scheduled_job('cron', minute='*/30', max_instances=3)
async def G_change():
    gValues = await gValueDB.getLatestGValues()
    newEastG = getNewG(gValues.eastValue, 0.1)
    newSouthG = getNewG(gValues.southValue, 0.1)
    newNorthG = getNewG(gValues.northValue, 0.08)
    newZhuhaiG = getNewG(gValues.zhuhaiValue, 0.1)
    newSzG = getNewG(gValues.shenzhenValue, 0.15)
    await gValueDB.addNewGValue(gValues.cycle, gValues.turn + 1, newEastG, newSouthG, newNorthG, newZhuhaiG, newSzG)
    nowTime = datetime.datetime.now().strftime('%H:%M')
    print(f'{nowTime}: G值已更新，新的值为：东{newEastG} 南{newSouthG} 北{newNorthG} 珠{newZhuhaiG} 深{newSzG}')
    await createGpic()


def getNewG(oldG: float, changeRange: float):
    rank = changeRange * (systemRandom.random() - 0.5)
    newG = rd3(oldG * (1 + rank))
    time.sleep(0.001)
    return newG


@nonebot.scheduler.scheduled_job('cron', hour='23', minute='45')
async def G_reset():
    if not resetDateCheck():
        return
    allUsers = await baseDB.getAllUser()
    gValues = await gValueDB.getLatestGValues()
    bot = nonebot.get_bot()
    for user in allUsers:
        allKusaFromG = await GSellingAll(user.qq, gValues)
        if allKusaFromG:
            print(f'用户{user.qq}的G已经兑换为{allKusaFromG}草')
            # if await baseDB.getFlagValue(user.qq, 'G市重置提示'):
            #     await bot.send_private_msg(user_id=user.qq, message=f'G周期已结束，您的所有G已经兑换为{allKusaFromG}草。')
        gCreatorAmount = await itemDB.getItemAmount(user.qq, '扭秤装置')
        gCreatorStable = await itemDB.getItemAmount(user.qq, '扭秤稳定理论')
        if gCreatorAmount:
            schoolName = random.choice(['东', '南', '北', '珠', '深'])
            singleCreatorG = 50 + systemRandom.random() * 450
            createGAmount = int(gCreatorAmount * singleCreatorG)
            if gCreatorStable:
                createGAmount *= (areaStartValue('深') / areaStartValue(schoolName))
                createGAmount = int(createGAmount)
            await itemDB.changeItemAmount(user.qq, areaTranslateItem(schoolName), createGAmount)
            print(f'用户{user.qq}的扭秤装置已运作，创造了{createGAmount}个{schoolName}G')

    await gValueDB.addNewGValue(gValues.cycle + 1, 1, areaStartValue('东'), areaStartValue('南'), areaStartValue('北'),
                                areaStartValue('珠'), areaStartValue('深'))
    await bot.send_group_msg(group_id=config['group']['main'], message=f'新的G周期开始了！上个周期的G已经自动兑换为草。')


@nonebot.scheduler.scheduled_job('cron', hour='23', minute='50')
async def _():
    if not resetDateCheck():
        return
    summary = await getLastCycleSummary()
    await sendGroupMsg(config['group']['main'], summary)


async def getLastCycleSummary():
    gValues = await gValueDB.getLatestGValues()
    gThisCycleStartTs = getGCycleStartTs(gValues)
    gLastCycleStartTs = gThisCycleStartTs - 3 * 86400
    tradeRecordsBuying = await baseDB.getTradeRecord(startTime=gLastCycleStartTs, endTime=gThisCycleStartTs, tradeType='G市(买)')
    tradeRecordsSelling = await baseDB.getTradeRecord(startTime=gLastCycleStartTs, endTime=gThisCycleStartTs, tradeType='G市(卖)')

    allRecords = tradeRecordsBuying + tradeRecordsSelling
    operatorRecordsMap = {}
    for record in allRecords:
        operatorRecordsMap.setdefault(record.operator, []).append(record)

    operatorProfitMap = {}
    for userId, records in operatorRecordsMap.items():
        kusaProfit = 0
        for record in records:
            if record.tradeType == 'G市(买)':
                kusaProfit -= record.costItemAmount
            if record.tradeType == 'G市(卖)':
                kusaProfit += record.gainItemAmount
        operatorProfitMap[userId] = kusaProfit

    maxProfitUserId = max(operatorProfitMap, key=operatorProfitMap.get)
    minProfitUserId = min(operatorProfitMap, key=operatorProfitMap.get)
    nameList = await baseDB.getNameListByQQ([maxProfitUserId, minProfitUserId])
    maxUserName = nameList[maxProfitUserId] if nameList[maxProfitUserId] else maxProfitUserId
    minUserName = nameList[minProfitUserId] if nameList[minProfitUserId] else minProfitUserId
    outputStr = (f'上周期的G神为 {maxUserName} 和 {minUserName}：\n'
                 f'{maxUserName}在G市盈利{operatorProfitMap[maxProfitUserId]}草\n'
                 f'{minUserName}在G市盈利{operatorProfitMap[minProfitUserId]}草\n')

    lastCycleGValue = await gValueDB.getLastCycleGValues()
    endGValues = lastCycleGValue[-1]
    outputStr += '\n上周期各G的收盘价为：\n'
    outputStr += formatGValue(endGValues.eastValue, areaStartValue('东'), '东')
    outputStr += formatGValue(endGValues.southValue, areaStartValue('南'), '南')
    outputStr += formatGValue(endGValues.northValue, areaStartValue('北'), '北')
    outputStr += formatGValue(endGValues.zhuhaiValue, areaStartValue('珠'), '珠海')
    outputStr += formatGValue(endGValues.shenzhenValue, areaStartValue('深'), '深圳')

    outputStr += '\n上周期的G线图：'
    outputStr += imgBytesToBase64(createGpicAll(getGValuesColMap(lastCycleGValue)))

    return outputStr


def resetDateCheck():
    # 以2024年11月1日为基准，每3天重置一次
    resetDate = datetime.datetime(2024, 11, 1)
    delta = datetime.datetime.now() - resetDate
    return delta.days % 3 == 0


def areaTranslateValue(areaName):
    valueMap = {'东': 'eastValue', '南': 'southValue', '北': 'northValue', '珠': 'zhuhaiValue', '深': 'shenzhenValue'}
    return valueMap[areaName]


def areaTranslateItem(areaName):
    valueMap = {'东': 'G(东校区)', '南': 'G(南校区)', '北': 'G(北校区)', '珠': 'G(珠海校区)', '深': 'G(深圳校区)'}
    return valueMap[areaName]


def areaStartValue(areaName):
    valueMap = {'东': 9.8, '南': 9.8, '北': 6.67, '珠': 32.0, '深': 120.0}
    return valueMap[areaName]


async def getAllGAmounts(userId):
    eastGAmount = await itemDB.getItemAmount(userId, 'G(东校区)')
    southGAmount = await itemDB.getItemAmount(userId, 'G(南校区)')
    northGAmount = await itemDB.getItemAmount(userId, 'G(北校区)')
    zhuhaiGAmount = await itemDB.getItemAmount(userId, 'G(珠海校区)')
    shenzhenGAmount = await itemDB.getItemAmount(userId, 'G(深圳校区)')
    return eastGAmount, southGAmount, northGAmount, zhuhaiGAmount, shenzhenGAmount
