import asyncio
import math
import random
import re
import nonebot
import dbConnection.db as baseDB
import dbConnection.kusa_field as fieldDB
import dbConnection.kusa_item as itemDB
from nonebot import on_command, CommandSession
from datetime import datetime, timedelta, date, time
from kusa_base import config, sendGroupMsg, sendPrivateMsg

systemRandom = random.SystemRandom()
# robTarget = ""
# robParticipant = set()
# robCount = 0
# robLimit = 0


@on_command(name='生草', only_to_me=False)
async def _(session: CommandSession):
    await plantKusa(session)


async def plantKusa(session: CommandSession):
    userId = session.ctx['user_id']
    field = await fieldDB.getKusaField(userId)
    if field.kusaIsGrowing:
        outputStr = f'你的{field.kusaType}还在生。剩余时间：{field.kusaRestTime}min'
        predictTime = datetime.now() + timedelta(minutes=field.kusaRestTime + 1)
        outputStr += f'\n预计生草完成时间：{predictTime.hour:02}:{predictTime.minute:02}'
        await session.send(outputStr)
        return

    kusaType = session.current_arg_text.strip()
    if kusaType:
        kusaTypeName = kusaType + "基因图谱"
        kusaItemExist = await itemDB.getItem(kusaTypeName)
        if not kusaItemExist:
            await session.send('你选择的草种类不存在^ ^')
            return
        kusaItemAmount = await itemDB.getItemStorageInfo(userId, kusaTypeName)
        if not kusaItemAmount:
            await session.send('你无法种植这种类型的草^ ^')
            return
    else:
        kusaType = field.defaultKusaType

    soilSaver = await itemDB.getItemStorageInfo(userId, '土壤保护装置')
    if soilSaver and soilSaver.allowUse and field.soilCapacity <= 10:
        await session.send(
            f'当前承载力为{field.soilCapacity}，强制土壤保护启用中，不允许生草。\n如果需要强制生草，请先禁用土壤保护装置。')
        return
    if field.soilCapacity <= 0:
        await session.send(
            f'当前承载力为{field.soilCapacity}，不允许生草。')
        return

    growTime = 40 + int(40 * systemRandom.random())
    isUsingKela = False
    bioGasEffect = 1
    kelaStorage = await itemDB.getItemStorageInfo(userId, '金坷垃')
    biogasStorage = await itemDB.getItemStorageInfo(userId, '沼气池')
    fieldAmount = await itemDB.getItemAmount(userId, '草地')
    if kelaStorage and kelaStorage.allowUse and kelaStorage.amount >= fieldAmount:
        isUsingKela = True
        growTime = math.ceil(growTime / 2)
        await itemDB.changeItemAmount(userId, '金坷垃', -fieldAmount)
    if biogasStorage and biogasStorage.allowUse:
        bioGasEffect = round(random.uniform(0.5, 2), 2)
        blackTeaStorage = await itemDB.getItemStorageInfo(userId, '红茶')
        if blackTeaStorage and blackTeaStorage.allowUse:
            bioGasEffect = round(random.uniform(1.2, 2), 2)
            await itemDB.changeItemAmount(userId, '红茶', -1)

    growTime = growTime * 2 if kusaType == "巨草" else growTime
    growTime = math.ceil(growTime / 2) if kusaType == "速草" else growTime
    if kusaType == "半灵草":
        kusaType = "灵草" if systemRandom.random() < 0.5 else ""

    juniorPrescient = await itemDB.getItemStorageInfo(userId, '初级生草预知')
    seniorPrescient = await itemDB.getItemStorageInfo(userId, '生草预知')
    weedCosting = 2 if juniorPrescient and juniorPrescient.allowUse and not (
                seniorPrescient and seniorPrescient.allowUse) else 0
    isPrescient = True if (juniorPrescient and juniorPrescient.allowUse) or (
                seniorPrescient and seniorPrescient.allowUse) else False
    kusaType = "草" if not kusaType else kusaType
    await fieldDB.kusaStartGrowing(userId, growTime, isUsingKela, bioGasEffect, kusaType, weedCosting, isPrescient)

    newField = await fieldDB.getKusaField(userId)
    baseKusaNum = 10 * systemRandom.random()
    finalKusaNum = await getCreateKusaNum(newField, baseKusaNum)
    finalAdvKusaNum = await getCreateAdvKusaNum(newField)
    await fieldDB.updateKusaResult(userId, finalKusaNum, finalAdvKusaNum)

    outputStr = f"开始生{kusaType}。剩余时间：{growTime}min\n"
    predictTime = datetime.now() + timedelta(minutes=growTime + 1)
    outputStr += f'预计生草完成时间：{predictTime.hour:02}:{predictTime.minute:02}\n'
    if isPrescient:
        outputStr += f"预知：生草量为{finalKusaNum}"
        outputStr += f"，草之精华获取量为{finalAdvKusaNum}" if finalAdvKusaNum else ""
    else:
        minPredict, maxPredict = await getKusaPredict(newField)
        outputStr += f"预估生草量：{minPredict} ~ {maxPredict}"
    outputStr += f'\n当前承载力低！目前承载力：{newField.soilCapacity}' if newField.soilCapacity <= 12 else ""
    await session.send(outputStr)


@on_command(name='除草', only_to_me=False)
async def _(session: CommandSession):
    userId = session.ctx['user_id']
    weeder = await itemDB.getItemAmount(userId, '除草机')
    if not weeder:
        await session.send('你没有除草机，无法除草^ ^')
        return
    field = await fieldDB.getKusaField(userId)
    if not field.kusaIsGrowing:
        await session.send('当前没有生草，无法除草^ ^')
        return
    await fieldDB.kusaStopGrowing(field, True)
    await session.send('除草成功^ ^')

    if await baseDB.getFlagValue(userId, '除草后自动生草'):
        await plantKusa(session)


@on_command(name='百草园', only_to_me=False)
async def _(session: CommandSession):
    userId = session.ctx['user_id']
    user = await baseDB.getUser(userId)
    field = await fieldDB.getKusaField(userId)
    st = '百草园：\n'
    if field.kusaIsGrowing:
        st += f'距离{field.kusaType}长成还有{field.kusaRestTime}min\n'
        predictTime = datetime.now() + timedelta(minutes=field.kusaRestTime + 1)
        st += f'预计生草完成时间：{predictTime.hour:02}:{predictTime.minute:02}\n'
        if field.isPrescient:
            st += f"预知：生草量为{field.kusaResult}"
            st += f"，草之精华获取量为{field.advKusaResult}" if field.advKusaResult else ""
        else:
            minPredict, maxPredict = await getKusaPredict(field)
            st += f'预估生草量：{minPredict} ~ {maxPredict}'
        st += '\n\n'
    else:
        st += f'当前没有生草。\n'
    st += f'你选择的默认草种为：{field.defaultKusaType}\n' if field.defaultKusaType else '草'
    st += f'当前的土壤承载力为：{field.soilCapacity}\n'

    isDetailShown = await baseDB.getFlagValue(field.qq, '生草预估详情展示')
    if isDetailShown:
        kusaOffset = 0.5 * (2 ** (user.vipLevel - 1)) if user.vipLevel >= 1 else 0
        fieldAmount = await itemDB.getItemAmount(field.qq, '草地')
        doubleMagic = await itemDB.getItemAmount(field.qq, '双生法术卷轴')
        kusaTechEffect = await getKusaTechEffect(field.qq)
        soilEffect = 1 - 0.1 * (10 - field.soilCapacity) if field.soilCapacity <= 10 else 1
        kusaTypeEffectMap = {'巨草': 2, '灵草': 2, '速草': 0.75}
        kusaTypeEffect = kusaTypeEffectMap[field.kusaType] if field.kusaType in kusaTypeEffectMap else 1
        st += '\n生草数量计算详情:\n'
        st += f'基础生草量：0 ~ 10\n'
        st += f'信息员等级加成：{kusaOffset}\n'
        st += f'草地数量 * {fieldAmount}\n'
        st += f'施用金坷垃 * 2\n' if field.isUsingKela else ''
        st += f'沼气影响 * {field.biogasEffect}\n' if field.biogasEffect != 1 else ''
        st += f'已掌握双生法术 * 2\n' if doubleMagic else ''
        st += f'生草科技影响 * {kusaTechEffect}\n' if kusaTechEffect != 1 else ''
        st += f'当前草种影响 * {kusaTypeEffect}\n' if kusaTypeEffect != 1 else ''
        st += f'土壤承载力影响 * {soilEffect}\n' if soilEffect != 1 else ''

    await session.send(st[:-1])


@on_command(name='默认草种', only_to_me=False)
async def _(session: CommandSession):
    userId = session.ctx['user_id']
    kusaType = session.current_arg_text.strip()
    if kusaType:
        kusaTypeName = kusaType + "基因图谱"
        kusaItemExist = await itemDB.getItem(kusaTypeName)
        if not kusaItemExist:
            await session.send('你选择的草种类不存在^ ^')
            return
        kusaItemAmount = await itemDB.getItemStorageInfo(userId, kusaTypeName)
        if not kusaItemAmount:
            await session.send('你无法种植这种类型的草^ ^')
            return
    else:
        kusaType = '草'
    await fieldDB.updateDefaultKusaType(userId, kusaType)
    output = f'你的生草默认草种已经设置为{kusaType}' if kusaType else '你的生草默认草种已经设置为普通草'
    await session.send(output)


@on_command(name='生草简报', only_to_me=False)
async def _(session: CommandSession):
    userId = session.ctx['user_id']
    row = await fieldDB.kusaHistoryReport(userId, datetime.now(), 86400)
    if not row["count"]:
        await session.send('最近24小时未生出草！')
        return
    await session.send(f'最近24小时共生草{row["count"]}次\n'
                       f'收获{row["sumKusa"]}草，平均每次{round(row["avgKusa"], 2)}草\n'
                       f'收获{row["sumAdvKusa"]}草之精华，平均每次{round(row["avgAdvKusa"], 2)}草之精华')


@on_command(name='生草日报', only_to_me=False)
async def _(session: CommandSession):
    userId = session.ctx['user_id']
    queryTime = datetime.combine(date.today(), time.min)
    row = await fieldDB.kusaHistoryReport(userId, queryTime, 86400)
    if not row["count"]:
        await session.send('昨日未生出草！')
        return
    await session.send(f'昨日共生草{row["count"]}次\n'
                       f'收获{row["sumKusa"]}草，平均每次{round(row["avgKusa"], 2)}草\n'
                       f'收获{row["sumAdvKusa"]}草之精华，平均每次{round(row["avgAdvKusa"], 2)}草之精华')


@on_command(name='生草周报', only_to_me=False)
async def _(session: CommandSession):
    userId = session.ctx['user_id']
    queryTime = datetime.combine(date.today(), time.min) - timedelta(days=date.today().weekday())
    row = await fieldDB.kusaHistoryReport(userId, queryTime, 604800)
    if not row["count"]:
        await session.send('上周未生出草！')
        return
    await session.send(f'上周共生草{row["count"]}次\n'
                       f'收获{row["sumKusa"]}草，平均每次{round(row["avgKusa"], 2)}草\n'
                       f'收获{row["sumAdvKusa"]}草之精华，平均每次{round(row["avgAdvKusa"], 2)}草之精华')


# 生草结算
@nonebot.scheduler.scheduled_job('interval', minutes=1)
async def save():
    activeFields = await fieldDB.getAllKusaField(onlyGrowing=True)
    for field in activeFields:
        if field.kusaRestTime <= 1:
            await baseDB.changeKusa(field.qq, field.kusaResult)
            await baseDB.changeAdvKusa(field.qq, field.advKusaResult)
            outputMsg = f'你的{field.kusaType}生了出来！获得了{field.kusaResult}草。'
            outputMsg += f'额外获得{field.advKusaResult}草之精华！' if field.advKusaResult else ''
            await sendPrivateMsg(field.qq, outputMsg)
            await goodNewsReport(field)

            if await itemDB.getItemAmount(field.qq, '纯酱的生草魔法'):
                chains = tuple(
                    (int(x[0]), len(x))
                    for x in
                    re.findall(r'0{3,}|1{3,}|2{3,}|3{3,}|4{3,}|5{3,}|6{3,}|7{3,}|8{3,}|9{3,}', str(field.kusaResult))
                )
                chainBonusTotal = 0
                for chainNumber, chainLength in chains:
                    chainBonus = int((chainNumber // 3 + 1) * (3 ** (chainLength - 2)))
                    chainBonusTotal += chainBonus
                    await sendPrivateMsg(field.qq, f'{getChainStr(chainLength)}！魔法少女纯酱召唤了额外的{chainBonus}个草之精华喵(*^▽^)/★*☆')
                    if chainLength >= 4:
                        user = await baseDB.getUser(field.qq)
                        userName = user.name if user.name else user.qq
                        reportMsg = f"喜报\n魔法少女纯酱为生{field.kusaType}达成{getChainStr(chainLength)}的玩家 {userName} 召唤了额外的{chainBonus}草之精华喵(*^▽^)/★*☆"
                        await sendGroupMsg(config['group']['main'], reportMsg)
                await baseDB.changeAdvKusa(field.qq, chainBonusTotal)
                field.advKusaResult += chainBonusTotal

            await fieldDB.kusaHistoryAdd(field)
            await fieldDB.kusaStopGrowing(field, False)
        else:
            await fieldDB.kusaTimePass(field)


def getChainStr(chainLength: int):
    return "零一二三四五六七八九十"[chainLength] + "连" if chainLength <= 10 else chainLength


@nonebot.scheduler.scheduled_job('interval', minutes=90)
async def soilCapacityIncreaseBase():
    badSoilFields = await fieldDB.getAllKusaField(onlySoilNotBest=True)
    for field in badSoilFields:
        recoverToFull = await fieldDB.kusaSoilRecover(field.qq)
        if recoverToFull:
            await sendFieldRecoverInfo(field.qq)


@nonebot.scheduler.scheduled_job('cron', minute=33)
async def soilCapacityIncreaseForInactive():
    badSoilFields = await fieldDB.getAllKusaField(onlySoilNotBest=True)
    for field in badSoilFields:
        if field.kusaIsGrowing:
            continue
        recoverToFull = await fieldDB.kusaSoilRecover(field.qq)
        if recoverToFull:
            await sendFieldRecoverInfo(field.qq)


async def sendFieldRecoverInfo(userId):
    isRecoverMsgSend = await baseDB.getFlagValue(userId, '发送承载力回满信息')
    if not isRecoverMsgSend:
        return
    await sendPrivateMsg(userId, '你的草地承载力已回满！')


async def getKusaPredict(fieldInfo):
    minPredict = await getCreateKusaNum(fieldInfo, 0)
    maxPredict = await getCreateKusaNum(fieldInfo, 10)
    return minPredict, maxPredict


async def getCreateKusaNum(field, baseKusa):
    user = await baseDB.getUser(field.qq)
    fieldAmount = await itemDB.getItemAmount(field.qq, '草地')
    doubleMagic = await itemDB.getItemAmount(field.qq, '双生法术卷轴')
    kusaTechEffect = await getKusaTechEffect(field.qq)
    soilCapacity = field.soilCapacity
    soilEffect = 1 - 0.1 * (10 - soilCapacity) if soilCapacity <= 10 else 1
    kusaNum = baseKusa
    kusaNum += 0.5 * (2 ** (user.vipLevel - 1)) if user.vipLevel > 0 else 0
    kusaNum *= 2 if field.isUsingKela else 1
    kusaNum *= 2 if doubleMagic else 1
    kusaNum *= 2 if field.kusaType == "巨草" or field.kusaType == "灵草" else 1
    kusaNum *= 0.75 if field.kusaType == "速草" else 1
    kusaNum *= field.biogasEffect
    kusaNum *= fieldAmount
    kusaNum *= soilEffect
    kusaNum *= kusaTechEffect
    kusaNum = math.ceil(kusaNum)
    return kusaNum


async def getCreateAdvKusaNum(field):
    advKusaNum = 0
    advKusaGetRisk = 0
    advKusaCreateI = await itemDB.getItemAmount(field.qq, '生草质量I')
    advKusaCreateII = await itemDB.getItemAmount(field.qq, '生草质量II')
    advKusaCreateIII = await itemDB.getItemAmount(field.qq, '生草质量III')
    advKusaCreateIV = await itemDB.getItemAmount(field.qq, '生草质量IV')
    soilEffect = 1 - 0.1 * (10 - field.soilCapacity) if field.soilCapacity <= 10 else 1
    advKusaGetRisk += 0.1 if advKusaCreateI else 0
    advKusaGetRisk += 0.3 if advKusaCreateII else 0
    advKusaGetRisk += 0.1 if advKusaCreateIII else 0
    advKusaGetRisk += 0.1 if advKusaCreateIV else 0
    advKusaGetRisk *= soilEffect

    if advKusaCreateIII:
        newRandom = systemRandom.random()
        while newRandom < advKusaGetRisk:
            advKusaNum += 1
            newRandom = systemRandom.random()
    else:
        if systemRandom.random() < advKusaGetRisk:
            advKusaNum = 1

    mustGrowAdv = await itemDB.getItemAmount(field.qq, '生草控制论')
    if mustGrowAdv and advKusaNum == 0:
        advKusaNum = 1

    advKusaNum *= 2 if field.kusaType == "巨草" or field.kusaType == "灵草" else 1

    return advKusaNum


async def getKusaTechEffect(userId):
    kusaAmountGrowthI = await itemDB.getItemAmount(userId, '生草数量I')
    kusaAmountGrowthII = await itemDB.getItemAmount(userId, '生草数量II')
    kusaAmountGrowthIII = await itemDB.getItemAmount(userId, '生草数量III')
    kusaAmountGrowthIV = await itemDB.getItemAmount(userId, '生草数量IV')
    effect = 1
    effect *= 2.5 if kusaAmountGrowthI else 1
    effect *= 1.6 if kusaAmountGrowthII else 1
    effect *= 1.5 if kusaAmountGrowthIII else 1
    effect *= 1.4 if kusaAmountGrowthIV else 1
    return effect


async def goodNewsReport(field):
    if field.advKusaResult > 0:
        # 悲报：连续X次生草未获得草之精华
        quality3 = await itemDB.getItemAmount(field.qq, "生草质量III")
        quality2 = await itemDB.getItemAmount(field.qq, "生草质量II")
        if quality3 or quality2:
            maxLen = 30 if quality3 else 40
            history = await fieldDB.noKusaAdvHistory(field.qq, maxLen)
            cnt = 0
            for i in range(len(history)):
                if history[i].advKusaResult > 0:
                    break
                cnt += 1
            if (quality3 and cnt >= 8) or cnt >= 11:
                user = await baseDB.getUser(field.qq)
                userName = user.name if user.name else user.qq
                itemName = "生草质量III" if quality3 else "生草质量II"
                reportStr = f"喜报\n[CQ:face,id=144]玩家 {userName} 使用 {itemName} 在连续{cnt}次生草中未获得草之精华！[CQ:face,id=144]"
                await sendGroupMsg(config['group']['main'], reportStr)
        # 喜报：基础草精大于等于X
        advKusaMultiple = (field.kusaType == "巨草" or field.kusaType == "灵草")
        baseAdvKusa = field.advKusaResult / 2 if advKusaMultiple else field.advKusaResult
        if baseAdvKusa >= 8:
            user = await baseDB.getUser(field.qq)
            userName = user.name if user.name else user.qq
            kusaType = field.kusaType if field.kusaType else "普通草"
            reportStr = f"喜报\n[CQ:face,id=144]玩家 {userName} 使用 {kusaType} 获得了{field.advKusaResult}个草之精华！大家快来围殴他吧！[CQ:face,id=144]"
            await sendGroupMsg(config['group']['main'], reportStr)
            # await activateRobbing(field, 60)


# @on_command(name='围殴', only_to_me=False)
# async def _(session: CommandSession):
#     global robCount
#     userId = session.ctx['user_id']
#     if not robTarget:
#         return
#     if str(userId) == robTarget:
#         await session.send('不能围殴自己^ ^')
#         return
#     if str(userId) in robParticipant:
#         await session.send('你已经围殴过了！')
#         return
#     kusaRobbed = random.randint(1, round(robLimit * .1))
#     await baseDB.changeKusa(userId, kusaRobbed)
#     await baseDB.changeKusa(robTarget, -kusaRobbed)
#     robCount += kusaRobbed
#     robParticipant.add(str(userId))
#     await session.send(f'围殴成功！你获得了{kusaRobbed}草！')
#     if robCount >= robLimit:
#         await stopRobbing()


# async def activateRobbing(field, duration: int):
#     global robTarget, robLimit, robCount
#     robTarget = field.qq
#     robParticipant.clear()
#     robLimit = field.kusaResult
#     await asyncio.create_task(stopRobbingTimer(duration))
#     print('robName:', robTarget, 'robLimit:', robLimit)
#
#
# async def stopRobbingTimer(duration: int):
#     await asyncio.sleep(duration)
#     await stopRobbing()
#
#
# async def stopRobbing():
#     global robTarget
#     if not robTarget:
#         return
#     user = await baseDB.getUser(robTarget)
#     userName = user.name if user.name else user.qq
#     await sendGroupMsg(config['group']['main'], f'本次围殴结束，玩家 {userName} 一共损失{robCount}草！')
#     robTarget = ""
