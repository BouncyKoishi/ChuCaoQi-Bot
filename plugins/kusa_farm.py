import math
import random
import nonebot
import dbConnection.db as baseDB
import dbConnection.kusa_field as fieldDB
import dbConnection.kusa_item as itemDB
from nonebot import on_command, CommandSession
from datetime import datetime, timedelta


@on_command(name='生草', only_to_me=False)
async def kusa_born(session: CommandSession):
    userId = session.ctx['user_id']
    field = await fieldDB.getKusaField(userId)
    if field.kusaIsGrowing:
        kusaTypeName = field.kusaType if field.kusaType else '草'
        outputStr = f'你的{kusaTypeName}还在生。剩余时间：{field.kusaRestTime}min'
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
        await session.send(f'当前承载力为{field.soilCapacity}，强制土壤保护启用中，不允许生草。\n如果需要强制生草，请先禁用土壤保护装置。')
        return

    growTime = 40 + int(40 * random.random())
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
    if kusaType == "巨草":
        growTime = growTime * 2
    if kusaType == "速草":
        growTime = math.ceil(growTime / 2)
    if kusaType == "半灵草":
        if random.random() < 0.5:
            kusaType = "灵草"
        else:
            kusaType = ""
    juniorPrescient = await itemDB.getItemStorageInfo(userId, '初级生草预知')
    seniorPrescient = await itemDB.getItemStorageInfo(userId, '生草预知')
    weedCosting = 2 if juniorPrescient and juniorPrescient.allowUse else 0
    isPrescient = True if (juniorPrescient and juniorPrescient.allowUse) or (seniorPrescient and seniorPrescient.allowUse) else False
    await fieldDB.kusaStartGrowing(userId, growTime, isUsingKela, bioGasEffect, kusaType, weedCosting, isPrescient)

    newField = await fieldDB.getKusaField(userId)
    baseKusaNum = 10 * random.random()
    finalKusaNum = await getCreateKusaNum(newField, baseKusaNum)
    finalAdvKusaNum = await getCreateAdvKusaNum(newField)
    await fieldDB.updateKusaResult(userId, finalKusaNum, finalAdvKusaNum)

    kusaTypeName = kusaType if kusaType else '草'
    outputStr = f"开始生{kusaTypeName}。剩余时间：{growTime}min\n"
    predictTime = datetime.now() + timedelta(minutes=growTime + 1)
    outputStr += f'预计生草完成时间：{predictTime.hour:02}:{predictTime.minute:02}\n'
    if isPrescient:
        outputStr += f"预知：生草量为{finalKusaNum}"
        outputStr += f"，草之精华获取量为{finalAdvKusaNum}" if finalAdvKusaNum else ""
    else:
        minPredict, maxPredict = await getKusaPredict(newField)
        outputStr += f"预估生草量：{minPredict} ~ {maxPredict}"
    outputStr += f' (*2)' if newField.kusaType == '灵草' else ''
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
    await fieldDB.kusaStopGrowing(userId, True)
    await session.send('除草成功^ ^')


@on_command(name='百草园', only_to_me=False)
async def _(session: CommandSession):
    userId = session.ctx['user_id']
    user = await baseDB.getUser(userId)
    field = await fieldDB.getKusaField(userId)
    st = '百草园：\n'
    if field.kusaIsGrowing:
        kusaTypeName = field.kusaType if field.kusaType else '草'
        st += f'距离{kusaTypeName}长成还有{field.kusaRestTime}min\n'
        predictTime = datetime.now() + timedelta(minutes=field.kusaRestTime + 1)
        st += f'预计生草完成时间：{predictTime.hour:02}:{predictTime.minute:02}\n'
        if field.isPrescient:
            st += f"预知：生草量为{field.kusaResult}"
            st += f"，草之精华获取量为{field.advKusaResult}" if field.advKusaResult else ""
        else:
            minPredict, maxPredict = await getKusaPredict(field)
            st += f'预估生草量：{minPredict} ~ {maxPredict}'
        st += f' (*2)' if field.kusaType == '灵草' else ''
        st += '\n\n'
    else:
        st += f'当前没有生草。\n'
    st += f'你选择的默认草种为：{field.defaultKusaType}\n' if field.defaultKusaType else ''
    st += f'当前的土壤承载力为：{field.soilCapacity}\n'

    isDetailShown = await baseDB.getFlagValue(field.qq, '生草预估详情展示')
    if isDetailShown:
        kusaOffset = 0.5 * (2 ** (user.vipLevel - 1)) if user.vipLevel >= 1 else 0
        fieldAmount = await itemDB.getItemAmount(field.qq, '草地')
        doubleMagic = await itemDB.getItemAmount(field.qq, '双生法术卷轴')
        kusaAmountGrowthI = await itemDB.getItemAmount(field.qq, '生草数量I')
        soilEffect = 1 - 0.1 * (10 - field.soilCapacity) if field.soilCapacity <= 10 else 1
        kusaTypeEffectMap = {'巨草': 2, '速草': 0.75}
        kusaTypeEffect = kusaTypeEffectMap[field.kusaType] if field.kusaType in kusaTypeEffectMap else 1
        st += '\n生草数量计算详情:\n'
        st += f'基础生草量：0 ~ 10\n'
        st += f'信息员等级加成：{kusaOffset}\n'
        st += f'草地数量 * {fieldAmount}\n'
        st += f'施用金坷垃 * 2\n' if field.isUsingKela else ''
        st += f'沼气影响 * {field.biogasEffect}\n' if field.biogasEffect != 1 else ''
        st += f'已掌握双生法术 * 2\n' if doubleMagic else ''
        st += f'已掌握生草数量I * 2.5\n' if kusaAmountGrowthI else ''
        st += f'当前草种影响 * {kusaTypeEffect}\n' if kusaTypeEffect != 1 else ''
        st += f'土壤承载力影响 * {soilEffect}\n' if soilEffect != 1 else ''
        st += f'灵草：你可以收获两次！\n' if field.kusaType == '灵草' else ''

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
        kusaType = ''
    await fieldDB.updateDefaultKusaType(userId, kusaType)
    output = f'你的生草默认草种已经设置为{kusaType}' if kusaType else '你的生草默认草种已经设置为普通草'
    await session.send(output)


@on_command(name='生草简报', only_to_me=False)
async def _(session: CommandSession):
    userId = session.ctx['user_id']
    row = await fieldDB.kusaHistoryReport(userId)
    if not row["count"]:
        await session.send('最近24小时未生出草！')
        return
    await session.send(f'最近24小时共生草{row["count"]}次\n'
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
            outputMsg = f'你的草生了出来！获得草*{field.kusaResult}'
            outputMsg += f'\n你还获得了额外的{field.advKusaResult}个草之精华！' if field.advKusaResult else ''
            if field.kusaType == '灵草':
                await baseDB.changeKusa(field.qq, field.kusaResult)
                await baseDB.changeAdvKusa(field.qq, field.advKusaResult)
                outputMsg += f'\n本次额外收获了草的灵体，以上草/草之精华获取两次！'
            try:
                bot = nonebot.get_bot()
                await bot.send_private_msg(user_id=field.qq, message=outputMsg)
            except:
                print(f'错误：sendmsg api not available，qq={field.qq}')
            await fieldDB.kusaHistoryAdd(field.qq)
            await fieldDB.kusaStopGrowing(field.qq, False)
        else:
            await fieldDB.kusaTimePass(field.qq)


@nonebot.scheduler.scheduled_job('interval', minutes=90)
async def soilCapacityIncreaseBase():
    badSoilFields = await fieldDB.getAllKusaField(onlySoilNotBest=True)
    for field in badSoilFields:
        recoverToFull = await fieldDB.kusaSoilRecover(field.qq)
        if recoverToFull:
            await sendFieldRecoverInfo(field.qq)


@nonebot.scheduler.scheduled_job('cron', minute='55')
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
    try:
        bot = nonebot.get_bot()
        await bot.send_private_msg(user_id=userId, message='你的草地承载力已回满！')
    except:
        print(f'错误：sendmsg api not available，qq={userId}')


async def getKusaPredict(fieldInfo):
    minPredict = await getCreateKusaNum(fieldInfo, 0)
    maxPredict = await getCreateKusaNum(fieldInfo, 10)
    return minPredict, maxPredict


async def getCreateKusaNum(field, baseKusa):
    user = await baseDB.getUser(field.qq)
    fieldAmount = await itemDB.getItemAmount(field.qq, '草地')
    doubleMagic = await itemDB.getItemAmount(field.qq, '双生法术卷轴')
    kusaAmountGrowthI = await itemDB.getItemAmount(field.qq, '生草数量I')
    soilCapacity = field.soilCapacity
    soilEffect = 1 - 0.1 * (10 - soilCapacity) if soilCapacity <= 10 else 1
    kusaNum = baseKusa
    kusaNum += 0.5 * (2 ** (user.vipLevel - 1)) if user.vipLevel > 0 else 0
    kusaNum *= 2 if field.isUsingKela else 1
    kusaNum *= 2 if doubleMagic else 1
    kusaNum *= 2.5 if kusaAmountGrowthI else 1
    kusaNum *= 2 if field.kusaType == "巨草" else 1
    kusaNum *= 0.75 if field.kusaType == "速草" else 1
    kusaNum *= field.biogasEffect
    kusaNum *= fieldAmount
    kusaNum *= soilEffect
    kusaNum = math.ceil(kusaNum)
    return kusaNum


async def getCreateAdvKusaNum(field):
    advKusaNum = 0
    advKusaGetRisk = 0
    advKusaCreateI = await itemDB.getItemAmount(field.qq, '生草质量I')
    advKusaCreateII = await itemDB.getItemAmount(field.qq, '生草质量II')
    advKusaCreateIII = await itemDB.getItemAmount(field.qq, '生草质量III')
    soilEffect = 1 - 0.1 * (10 - field.soilCapacity) if field.soilCapacity <= 10 else 1
    advKusaGetRisk += 0.1 if advKusaCreateI else 0
    advKusaGetRisk += 0.3 if advKusaCreateII else 0
    advKusaGetRisk += 0.1 if advKusaCreateIII else 0
    advKusaGetRisk *= soilEffect

    if advKusaCreateIII:
        newRandom = random.random()
        while newRandom < advKusaGetRisk:
            advKusaNum += 1
            newRandom = random.random()
    else:
        if random.random() < advKusaGetRisk:
            advKusaNum = 1
    if field.kusaType == "巨草":
        advKusaNum *= 2
    return advKusaNum

