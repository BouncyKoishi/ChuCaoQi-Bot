import asyncio
import dataclasses
import math
import random
import re
import string
import typing
import nonebot
import dbConnection.db as baseDB
import dbConnection.kusa_field as fieldDB
import dbConnection.kusa_item as itemDB
from nonebot import on_command, CommandSession
from datetime import datetime, timedelta, date, time
from kusa_base import config, sendGroupMsg, sendPrivateMsg
from utils import intToRomanNum


@dataclasses.dataclass
class RobInfo:
    targetId: str
    participantIds: set
    robCount: int
    robLimit: int
    extraKusaAdv: bool = False


systemRandom = random.SystemRandom()
robDict: typing.Dict[str, RobInfo] = {}
advKusaProbabilityDict = {0: 0, 1: 0.15, 2: 0.5, 3: 0.5, 4: 0.6}
kusaTypeEffectMap = {'巨草': 2, '巨巨草': 3, '巨灵草': 4, '速草': 0.75, '速速草': 0.5,
                     '灵草': 2, '不灵草': 0, '灵草II': 3, '灵草III': 4, '灵草IV': 5,
                     '灵草V': 6, '灵草VI': 7, '灵草VII': 8, '灵草VIII': 9, '神灵草': 10}
advKusaTypeEffectMap = {'巨草': 2, '巨巨草': 3, '巨灵草': 4, '灵草': 2, '灵草II': 3,
                        '灵草III': 4, '灵草IV': 5, '灵草V': 6, '灵草VI': 7, '灵草VII': 8,
                        '灵草VIII': 9, '神灵草': 10}


@on_command(name='生草', only_to_me=False)
async def _(session: CommandSession):
    await plantKusa(session)


@on_command(name='过载生草', only_to_me=False)
async def _(session: CommandSession):
    userId = session.ctx['user_id']
    overloadMagic = await itemDB.getItemAmount(userId, '奈奈的过载魔法')
    if not overloadMagic:
        await session.send('你未学会过载魔法，无法进行过载生草^ ^')
        return
    await plantKusa(session, True)


async def plantKusa(session: CommandSession, overloadOnHarvest: bool = False):
    userId = session.ctx['user_id']
    field = await fieldDB.getKusaField(userId)
    if field.kusaFinishTs:
        predictTime = datetime.fromtimestamp(field.kusaFinishTs) + timedelta(minutes=1)
        restTime = predictTime - datetime.now()
        if restTime.total_seconds() > 60:
            outputStr = f'你的{field.kusaType}还在生。剩余时间：{int(restTime.total_seconds() // 60)}min'
            outputStr += f'\n预计生草完成时间：{predictTime.hour:02}:{predictTime.minute:02}'
            await session.send(outputStr)
        else:
            await session.send(f'你的{field.kusaType}将在一分钟内长成！')
        return

    overload = await itemDB.getItemStorageInfo(userId, '过载标记')
    if overload:
        overloadEndTime = datetime.fromtimestamp(overload.timeLimitTs).strftime('%H:%M')
        await session.send(f'土地过载中，无法生草！过载结束时间：{overloadEndTime}')
        return

    soilSaver = await itemDB.getItemStorageInfo(userId, '土壤保护装置')
    if soilSaver and soilSaver.allowUse and field.soilCapacity <= 10:
        await session.send(f'当前承载力为{field.soilCapacity}，强制土壤保护启用中，不允许生草。\n如果需要强制生草，请先禁用土壤保护装置。')
        return
    if field.soilCapacity <= 0:
        await session.send(f'当前承载力为{field.soilCapacity}，不允许生草。')
        return

    kusaType, success, errMsg = await getKusaType(userId, session.current_arg_text, field.defaultKusaType)
    if not success:
        await session.send(errMsg)
        return
    kusaType = "草" if not kusaType else kusaType

    # 原始生长时间和金坷垃、沼气池效果
    growTime = systemRandom.randint(40, 80)
    isUsingKela, bioGasEffect = False, 1
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

    # 神灵草替换
    divinePlugin = await itemDB.getItemStorageInfo(userId, '神灵草基因模块')
    if divinePlugin and divinePlugin.allowUse and kusaType != '不灵草':
        if random.random() < 0.05:
            kusaType = '神灵草'

    # 灵草相关处理
    if kusaType == "半灵草":
        kusaType = "灵草" if systemRandom.random() < 0.5 else "草"
    if kusaType == "半灵巨草":
        kusaType = "巨灵草" if systemRandom.random() < 0.5 else "巨草"
    if kusaType == "灵灵草":
        spiritTypeName = ['草', '灵草', '灵草II', '灵草III', '灵草IV', '灵草V', '灵草VI', '灵草VII', '灵草VIII']
        spiritLevel = min(8, int(-math.log2(systemRandom.random())))
        kusaType = spiritTypeName[spiritLevel]

    # 草种影响生长时间
    growTimeMultiplierMap = {'巨草': 2, '巨灵草': 2, '巨巨草': 4, '速草': 0.5}
    growTime = math.ceil(growTime * growTimeMultiplierMap[kusaType]) if kusaType in growTimeMultiplierMap else growTime
    growTime = systemRandom.randint(1, 5) if kusaType == "速速草" else growTime

    # 奈奈的时光魔法影响生长时间
    kusaSpeedMagic = await itemDB.getItemAmount(userId, '奈奈的时光魔法')
    magicImmediate = kusaSpeedMagic and random.random() < 0.007
    magicQuick = kusaSpeedMagic and random.random() < 0.07 and not magicImmediate
    if magicImmediate:
        growTime = 1
        await itemDB.updateTimeLimitedItem(userId, '时光胶囊标记', 60)
    if magicQuick:
        growTime = math.ceil(growTime * (1 - 0.777))

    # 生草预知判断
    juniorPrescient = await itemDB.getItemStorageInfo(userId, '初级生草预知')
    seniorPrescient = await itemDB.getItemStorageInfo(userId, '生草预知')
    isPrescient = True if (juniorPrescient and juniorPrescient.allowUse) or (
            seniorPrescient and seniorPrescient.allowUse) else False

    # 生草、除草消耗承载力计算
    plantCostingMap = {'巨草': 2, '巨灵草': 2, '巨巨草': 4}
    plantCosting = plantCostingMap[kusaType] if kusaType in plantCostingMap else 1
    weedCosting = 2 if ((juniorPrescient and juniorPrescient.allowUse) and
                        not (seniorPrescient and seniorPrescient.allowUse)) else 0

    kusaFinishTs = datetime.timestamp(datetime.now() + timedelta(minutes=growTime))
    await fieldDB.kusaStartGrowing(userId, kusaFinishTs, isUsingKela, bioGasEffect, kusaType,
                                   plantCosting, weedCosting, isPrescient, overloadOnHarvest)

    # 生草产量计算
    newField = await fieldDB.getKusaField(userId)
    baseKusaNum = 10 * systemRandom.random()
    finalKusaNum = await getCreateKusaNum(newField, baseKusaNum)
    finalAdvKusaNum = await getCreateAdvKusaNum(newField)
    await fieldDB.updateKusaResult(userId, finalKusaNum, finalAdvKusaNum)

    outputStr = f"开始生{kusaType}。"
    if magicImmediate:
        outputStr += '\n时光魔法吟唱中……\n(ﾉ≧∀≦)ﾉ ‥…━━━★\n'
    elif magicQuick:
        outputStr += f'剩余时间：{growTime}min(-77.7%)\n'
    else:
        outputStr += f'剩余时间：{growTime}min\n'
    if not magicImmediate:
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
    if not field.kusaFinishTs:
        await session.send('当前没有生草，无法除草^ ^')
        return
    await fieldDB.kusaStopGrowing(field, True)
    await itemDB.removeTimeLimitedItem(field.qq, '灵性标记')
    await session.send('除草成功^ ^')

    if await baseDB.getFlagValue(userId, '除草后自动生草'):
        await plantKusa(session)


@on_command(name='百草园', only_to_me=False)
async def _(session: CommandSession):
    userId = session.ctx['user_id']
    user = await baseDB.getUser(userId)
    field = await fieldDB.getKusaField(userId)
    st = '百草园：\n'
    if field.kusaFinishTs:
        predictTime = datetime.fromtimestamp(field.kusaFinishTs) + timedelta(minutes=1)
        restTime = predictTime - datetime.now()
        if restTime.total_seconds() > 60:
            st += f'距离{field.kusaType}长成还有{int(restTime.total_seconds() // 60)}min\n'
            st += f'预计生草完成时间：{predictTime.hour:02}:{predictTime.minute:02}\n'
        else:
            st += f'你的{field.kusaType}将在一分钟内长成！\n'
        if field.isPrescient:
            st += f"预知：生草量为{field.kusaResult}"
            st += f"，草之精华获取量为{field.advKusaResult}" if field.advKusaResult else ""
            if field.overloadOnHarvest:
                st += f"\n过载！本次生草额外获得{getOverloadBonusAmount(field)}草之精华，并过载{getOverloadHour(field)}小时！"
        else:
            minPredict, maxPredict = await getKusaPredict(field)
            st += f'预估生草量：{minPredict} ~ {maxPredict}'
        st += '\n\n'
    else:
        overload = await itemDB.getItemStorageInfo(userId, '过载标记')
        if overload:
            overloadEndTime = datetime.fromtimestamp(overload.timeLimitTs).strftime('%H:%M')
            st += f'土地过载中，无法生草！\n过载结束时间：{overloadEndTime}\n'
        else:
            st += '当前没有生草。\n'
    st += f'你选择的默认草种为：{field.defaultKusaType}\n' if field.defaultKusaType else '草'
    st += f'当前的土壤承载力为：{field.soilCapacity}\n'

    isDetailShown = await baseDB.getFlagValue(field.qq, '生草预估详情展示')
    if isDetailShown:
        kusaOffset = 0.5 * (2 ** (user.vipLevel - 1)) if user.vipLevel >= 1 else 0
        fieldAmount = await itemDB.getItemAmount(field.qq, '草地')
        doubleMagic = await itemDB.getItemAmount(field.qq, '双生法术卷轴')
        kusaTechEffect = await getKusaTechEffect(field.qq)
        soilEffect = 1 - 0.1 * (10 - field.soilCapacity) if field.soilCapacity <= 10 else 1
        spiritualSign = await itemDB.getItemAmount(field.qq, '灵性标记')
        spiritualEffect = 2 if spiritualSign else 1

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
        st += f'灵性保留 * {spiritualEffect}\n' if spiritualSign else ''
        st += f'土壤承载力影响 * {soilEffect:.1f}\n' if soilEffect != 1 else ''

    await session.send(st[:-1])


@on_command(name='默认草种', only_to_me=False)
async def _(session: CommandSession):
    userId = session.ctx['user_id']
    kusaType, success, errMsg = await getKusaType(userId, session.current_arg_text, '草')
    if not success:
        await session.send(errMsg)
        return
    await fieldDB.updateDefaultKusaType(userId, kusaType)
    output = f'你的生草默认草种已经设置为{kusaType}' if kusaType else '你的生草默认草种已经设置为普通草'
    await session.send(output)


async def getKusaType(userId, strippedArg, defaultType=None):
    if not strippedArg or strippedArg == defaultType:
        return defaultType, True, None

    kusaTypeName = strippedArg + "基因图谱"
    kusaItemExist = await itemDB.getItem(kusaTypeName)
    if not kusaItemExist:
        return '', False, '你选择的草种类不存在^ ^'
    kusaItemAmount = await itemDB.getItemStorageInfo(userId, kusaTypeName)
    if not kusaItemAmount:
        return '', False, '你无法种植这种类型的草^ ^'

    return strippedArg, True, None


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
@nonebot.scheduler.scheduled_job('interval', minutes=1, max_instances=10)
async def save():
    finishedFields = await fieldDB.getAllKusaField(onlyFinished=True)
    timeCapsuleUserIds = await itemDB.getUserIdListByItem('时光胶囊标记')
    for field in finishedFields:
        # 时光魔法收获逻辑
        if field.qq in timeCapsuleUserIds:
            await sendPrivateMsg(field.qq,
                                 '时光胶囊启动！奈奈发动了时光魔法，使本次生草立即完成且不消耗承载力喵(⑅˘̤ ᵕ˘̤)*♡*')
            await itemDB.removeTimeLimitedItem(field.qq, '时光胶囊标记')
            await kusaHarvest(field)
            recoverToFull = await fieldDB.kusaSoilRecover(field.qq)
            if recoverToFull:
                await sendFieldRecoverInfo(field.qq)
        # 普通收获逻辑
        else:
            await kusaHarvest(field)


async def kusaHarvest(field):
    if not field.kusaFinishTs:
        return
    await baseDB.changeKusa(field.qq, field.kusaResult)
    await baseDB.changeAdvKusa(field.qq, field.advKusaResult)
    outputMsg = f'你的{field.kusaType}生了出来！获得了{field.kusaResult}草。'
    outputMsg += f'额外获得{field.advKusaResult}草之精华！' if field.advKusaResult else ''
    await sendPrivateMsg(field.qq, outputMsg)
    if field.advKusaResult > 0:
        await goodNewsReport(field)
    if await itemDB.getItemAmount(field.qq, '纯酱的生草魔法'):
        await getChainBonus(field)
    if field.overloadOnHarvest:
        await getOverloadBonus(field)
    if field.kusaType == "不灵草":
        await itemDB.updateTimeLimitedItem(field.qq, '灵性标记', 24 * 3600)
    else:
        await itemDB.removeTimeLimitedItem(field.qq, '灵性标记')
    await fieldDB.kusaHistoryAdd(field)
    await fieldDB.kusaStopGrowing(field, False)


@nonebot.scheduler.scheduled_job('interval', minutes=90)
async def soilCapacityIncreaseBase():
    badSoilFields = await fieldDB.getAllKusaField(onlySoilNotBest=True)
    for field in badSoilFields:
        recoverToFull = await fieldDB.kusaSoilRecover(field.qq)
        if recoverToFull:
            await sendFieldRecoverInfo(field.qq)


@nonebot.scheduler.scheduled_job('cron', minute=33, second=33)
async def soilCapacityIncreaseForInactive():
    badSoilFields = await fieldDB.getAllKusaField(onlySoilNotBest=True)
    for field in badSoilFields:
        if field.kusaFinishTs:
            continue
        overload = await itemDB.getItemAmount(field.qq, '过载标记')
        if overload:
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
    spiritualSign = await itemDB.getItemAmount(field.qq, '灵性标记')
    kusaTechEffect = await getKusaTechEffect(field.qq)
    soilEffect = 1 - 0.1 * (10 - field.soilCapacity) if field.soilCapacity <= 10 else 1

    kusaNum = baseKusa
    kusaNum += 0.5 * (2 ** (user.vipLevel - 1)) if user.vipLevel > 0 else 0
    kusaNum *= kusaTypeEffectMap[field.kusaType] if field.kusaType in kusaTypeEffectMap else 1
    kusaNum *= 2 if field.isUsingKela else 1
    kusaNum *= 2 if doubleMagic else 1
    kusaNum *= 2 if spiritualSign else 1
    kusaNum *= field.biogasEffect
    kusaNum *= fieldAmount
    kusaNum *= soilEffect
    kusaNum *= kusaTechEffect
    kusaNum = math.ceil(kusaNum)
    return kusaNum


async def getCreateAdvKusaNum(field):
    advKusaTechLevel = await itemDB.getTechLevel(field.qq, '生草质量')
    soilEffect = 1 - 0.1 * (10 - field.soilCapacity) if field.soilCapacity <= 10 else 1
    advKusaProbability = advKusaProbabilityDict[advKusaTechLevel]
    advKusaProbability *= soilEffect

    advKusaNum = 0
    if advKusaTechLevel >= 3:
        while systemRandom.random() < advKusaProbability:
            advKusaNum += 1
    else:
        if systemRandom.random() < advKusaProbability:
            advKusaNum = 1

    mustGrowAdv = await itemDB.getItemAmount(field.qq, '生草控制论')
    spiritualSign = await itemDB.getItemStorageInfo(field.qq, '灵性标记')
    advKusaNum = 1 if mustGrowAdv and advKusaNum == 0 else advKusaNum
    advKusaNum *= advKusaTypeEffectMap[field.kusaType] if field.kusaType in advKusaTypeEffectMap else 1
    advKusaNum *= 2 if spiritualSign and field.kusaType != '不灵草' else 1

    return advKusaNum


async def getKusaTechEffect(userId):
    # 数量1 *2.5，数量2 *1.6，数量3 *1.5，数量4 *1.4
    levelEffectDict = {0: 1, 1: 2.5, 2: 4, 3: 6, 4: 8.4}
    kusaTechLevel = await itemDB.getTechLevel(userId, '生草数量')
    return levelEffectDict[kusaTechLevel]


async def goodNewsReport(field):
    qualityLevel = await itemDB.getTechLevel(field.qq, '生草质量')
    # 悲报：连续X次生草未获得草之精华
    if qualityLevel >= 2:
        history = await fieldDB.noKusaAdvHistory(field.qq, 40)
        noKusaAdvCount = next((i for i, h in enumerate(history) if h.advKusaResult > 0), len(history))
        countThresholds = math.log(1 / 200, 1 - advKusaProbabilityDict[qualityLevel])  # 质量2、3为8，质量4为6
        if noKusaAdvCount > countThresholds:
            await sendReportMsg(field, '悲报', sadNewsCount=noKusaAdvCount)
    # 生草质量喜报：基础草精大于等于X
    if qualityLevel >= 3:
        advKusaEffect = advKusaTypeEffectMap[field.kusaType] if field.kusaType in advKusaTypeEffectMap else 1
        spiritualSign = await itemDB.getItemAmount(field.qq, '灵性标记')
        spiritualEffect = 2 if spiritualSign else 1
        baseAdvKusa = field.advKusaResult / advKusaEffect / spiritualEffect
        advKusaThresholds = math.log(1 / 200, advKusaProbabilityDict[qualityLevel])  # 质量3为8，质量4为11
        if baseAdvKusa >= advKusaThresholds:
            await sendReportMsg(field, '质量喜报')
    # 总草精数喜报：最终草精大于等于50
    if field.advKusaResult >= 50:
        await sendReportMsg(field, '草精喜报')


async def getChainBonus(field):
    # 连号与连号喜报逻辑
    chains = re.findall(r'0{3,}|1{3,}|2{3,}|3{3,}|4{3,}|5{3,}|6{3,}|7{3,}|8{3,}|9{3,}', str(field.kusaResult))
    chainBonusTotal = 0
    for chainStr in chains:
        chainBonus = getChainBonusAmount(chainStr)
        chainBonusTotal += chainBonus
        await sendPrivateMsg(field.qq,
                             f'{getChainLengthStr(chainStr)}！魔法少女纯酱召唤了额外的{chainBonus}个草之精华喵(*^▽^)/★*☆')
        if len(chainStr) >= 4:
            await sendReportMsg(field, '连号喜报', chainStr=chainStr)
    await baseDB.changeAdvKusa(field.qq, chainBonusTotal)
    field.advKusaResult += chainBonusTotal


async def sendReportMsg(field, reportType, sadNewsCount=0, chainStr=""):
    user = await baseDB.getUser(field.qq)
    userName = user.name if user.name else user.qq
    reportStr = ""
    if reportType == '悲报':
        qualityLevel = await itemDB.getTechLevel(field.qq, '生草质量')
        itemName = "生草质量" + intToRomanNum(qualityLevel)
        reportStr = f"喜报\n[CQ:face,id=144]玩家 {userName} 使用 {itemName} 在连续{sadNewsCount}次生草中未获得草之精华！[CQ:face,id=144]"
    if reportType in ['质量喜报', '草精喜报']:
        kusaType = field.kusaType if field.kusaType else "普通草"
        reportStr = f"喜报\n[CQ:face,id=144]玩家 {userName} 使用 {kusaType} 获得了{field.advKusaResult}个草之精华！大家快来围殴他吧！[CQ:face,id=144]"
    if reportType == '连号喜报':
        chainBonus = getChainBonusAmount(chainStr)
        reportStr = f"喜报\n魔法少女纯酱为生{field.kusaType}达成{getChainLengthStr(chainStr)}的玩家 {userName} 召唤了额外的{chainBonus}草之精华喵(*^▽^)/★*☆"
    if not reportStr:
        return

    # 群聊喜报发送
    await sendGroupMsg(config['group']['main'], reportStr)
    # 小礼炮通知发送
    cannonUserIdList = await itemDB.getUserIdListByItem('小礼炮')
    for userId in cannonUserIdList:
        if userId == field.qq:
            continue
        await itemDB.changeItemAmount(userId, '小礼炮', -1)
        await sendPrivateMsg(userId, f'[CQ:face,id=144]一个喜报产生了！[CQ:face,id=144]')
    # 分享魔法额外奖励效果
    if '喜报' in reportType:
        await activateRobbing(field)
        shareUserIdList = await itemDB.getUserIdListByItem('除草器的共享魔法')
        for userId in shareUserIdList:
            if reportType in ['质量喜报', '草精喜报']:
                await baseDB.changeAdvKusa(userId, 1)
            if reportType == '连号喜报':
                await baseDB.changeKusa(userId, int(chainStr))


def getChainLengthStr(chainStr: str):
    chainLength = len(chainStr)
    return "零一二三四五六七八九十"[chainLength] + "连" if chainLength <= 10 else f"{chainLength}连"


def getChainBonusAmount(chainStr: str):
    chainNumber = int(chainStr[0])
    chainLength = len(chainStr)
    return int((chainNumber // 3 + 1) * (3 ** (chainLength - 2)))


async def getOverloadBonus(field):
    advKusaNum = getOverloadBonusAmount(field)
    overLoadHour = getOverloadHour(field)
    await baseDB.changeAdvKusa(field.qq, advKusaNum)
    await itemDB.updateTimeLimitedItem(field.qq, '过载标记', overLoadHour * 3600)
    overloadMsg = f'注意：你的草地进入了{overLoadHour}小时的过载。你通过过载生草额外获得了{advKusaNum}个草之精华！'
    await sendPrivateMsg(field.qq, overloadMsg)


def getOverloadBonusAmount(field):
    distinctDigitsCount = len(set(str(field.kusaResult)))
    return distinctDigitsCount * 2


def getOverloadHour(field):
    distinctDigitsCount = len(set(str(field.kusaResult)))
    return 3 * distinctDigitsCount


@on_command(name='围殴', only_to_me=False)
async def _(session: CommandSession):
    global robDict
    userId = session.ctx['user_id']
    if "group_id" not in session.ctx:
        await session.send('只能在群聊中进行围殴^ ^')
        return
    if not robDict:
        await session.send('当前没有可围殴对象^ ^')
        return

    selfRobFlag, hasRobbedFlag, robRecords, stopRobbingIds = False, False, [], []
    for robId, robInfo in robDict.items():
        print(robId, robInfo)
        if str(userId) == robInfo.targetId:
            selfRobFlag = True
            continue
        if str(userId) in robInfo.participantIds:
            hasRobbedFlag = True
            continue
        kusaRobbed = random.randint(round(robInfo.robLimit * .05), round(robInfo.robLimit * .3))
        await baseDB.changeKusa(userId, kusaRobbed)
        await baseDB.changeKusa(robInfo.targetId, -kusaRobbed)
        robInfo.robCount += kusaRobbed
        robInfo.participantIds.add(str(userId))
        targetUser = await baseDB.getUser(robInfo.targetId)
        targetUserName = targetUser.name if targetUser.name else targetUser.qq
        record = f'围殴 {targetUserName} 成功！你获得了{kusaRobbed}草！'
        user = await baseDB.getUser(userId)
        if robInfo.extraKusaAdv and user.vipLevel >= 5:
            await baseDB.changeAdvKusa(userId, 1)
            record += '额外获得了1草之精华！'
        robRecords.append(record)
        if robInfo.robCount >= robInfo.robLimit:
            stopRobbingIds.append(robId)

    if robRecords:
        await session.send('\n'.join(robRecords))
    elif hasRobbedFlag:
        await session.send('你已经围殴过了^ ^')
    elif selfRobFlag:
        await session.send('不能围殴自己^ ^')

    for robId in stopRobbingIds:
        await stopRobbing(robId)


async def activateRobbing(field):
    global robDict
    duration = random.randint(60, 300)
    shareMagic = await itemDB.getItemAmount(field.qq, '除草器的共享魔法')
    shareMagicExist = True if shareMagic else False
    robInfo = RobInfo(targetId=field.qq, participantIds=set(),
                      robCount=0, robLimit=field.kusaResult, extraKusaAdv=shareMagicExist)
    robId = field.qq + "_" + ''.join(random.choice(string.ascii_letters) for _ in range(8))
    stopTask = asyncio.create_task(stopRobbingTimer(duration, robId))
    print(f'robInfo: {robInfo}, taskDuration: {duration}s, stopTask: {stopTask}')
    robDict[robId] = robInfo


async def stopRobbingTimer(duration: int, robId: str):
    await asyncio.sleep(duration)
    await stopRobbing(robId)


async def stopRobbing(robId: str):
    global robDict
    if robId not in robDict:
        return
    robInfo = robDict.pop(robId)
    user = await baseDB.getUser(robInfo.targetId)
    userName = user.name if user.name else user.qq
    await sendGroupMsg(config['group']['main'], f'本次围殴结束，玩家 {userName} 一共损失{robInfo.robCount}草！')
