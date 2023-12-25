import os
import re
import math
import time
import random
import nonebot
import datetime
import matplotlib.pylab as plt
from nonebot import on_command, CommandSession
from kusa_base import buying, selling, config
from utils import rd3, getImgBase64
import dbConnection.db as baseDB
import dbConnection.kusa_item as itemDB
import dbConnection.g_value as gValueDB

G_PIC = 'gPic'
systemRandom = random.SystemRandom()


@on_command(name='测G', only_to_me=False)
async def _(session: CommandSession):
    userId = session.ctx['user_id']
    gValues = await gValueDB.getLatestGValues()
    gValuesLast = await gValueDB.getSecondLatestGValues()

    st = f'G市有风险，炒G需谨慎！\n'
    if gValues.turn != 1:
        st += f'当前G值为：\n'
        st += f'东校区：{rd3(gValues.eastValue)}(上期：{rd3(gValuesLast.eastValue)})\n'
        st += f'南校区：{rd3(gValues.southValue)}(上期：{rd3(gValuesLast.southValue)})\n'
        st += f'北校区：{rd3(gValues.northValue)}(上期：{rd3(gValuesLast.northValue)})\n'
        st += f'珠海校区：{rd3(gValues.zhuhaiValue)}(上期：{rd3(gValuesLast.zhuhaiValue)})\n'
        st += f'深圳校区：{rd3(gValues.shenzhenValue)}(上期：{rd3(gValuesLast.shenzhenValue)})\n'
        st += f'当前为本周期第{gValues.turn}期数值。\n\n'
    else:
        st += f'当前为本周期的第一期数值！\n当前G值为：\n'
        st += f'东校区：{areaStartValue("东")}\n南校区：{areaStartValue("南")}\n北校区：{areaStartValue("北")}\n' \
              f'珠海校区：{areaStartValue("珠")}\n深圳校区：{areaStartValue("深")}\n'

    eastGAmount, southGAmount, northGAmount, zhuhaiGAmount, shenzhenGAmount = await getAllGAmounts(userId)
    st += f'您拥有的G：\n'
    st += (f'东校区： {eastGAmount}\n' if eastGAmount else '')
    st += (f'南校区： {southGAmount}\n' if southGAmount else '')
    st += (f'北校区： {northGAmount}\n' if northGAmount else '')
    st += (f'珠海校区： {zhuhaiGAmount}\n' if zhuhaiGAmount else '')
    st += (f'深圳校区： {shenzhenGAmount}\n' if shenzhenGAmount else '')
    st += (f'您当前没有任何G!\n' if not (eastGAmount or southGAmount or northGAmount or zhuhaiGAmount or shenzhenGAmount) else '')
    st += f'\n'
    st += f'您可以选择：\n!G买入 [校区] [数量]\n!G卖出 [校区] [数量]\n!G线图 [校区]\n'
    await session.send(st)


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


@on_command(name='G买入', only_to_me=False)
async def _(session: CommandSession):
    userId = session.ctx['user_id']

    st = '购买成功！'
    stripped_arg = session.current_arg_text.strip()
    buyingAmount = re.findall(r'\d+', stripped_arg)
    schoolName = re.findall(r'[东南北珠深]', stripped_arg)
    isBuyingAll = re.findall(r'all', stripped_arg)

    if (buyingAmount or isBuyingAll) and schoolName:
        schoolName = schoolName[0]
        gValues = await gValueDB.getLatestGValues()
        gType = areaTranslateItem(schoolName)
        valueType = areaTranslateValue(schoolName)
        gValue = getattr(gValues, valueType)
        if buyingAmount:
            buyingAmount = int(buyingAmount[0])
        elif isBuyingAll:
            user = await baseDB.getUser(userId)
            buyingAmount = math.floor(user.kusa / gValue)
            st += f'买入了{buyingAmount}G'
        totalPrice = int(buyingAmount * gValue)
        success = await buying(userId, gType, buyingAmount, totalPrice)
        if not success:
            st = '你不够草^ ^'
    else:
        st = '参数不正确^ ^'
    await session.send(st)


@on_command(name='G卖出', only_to_me=False)
async def _(session: CommandSession):
    userId = session.ctx['user_id']

    st = '卖出成功！'
    stripped_arg = session.current_arg_text.strip()
    sellingAmount = re.findall(r'\d+', stripped_arg)
    schoolName = re.findall(r'[东南北珠深]', stripped_arg)
    isSellingAll = re.findall(r'all', stripped_arg)
    gValues = await gValueDB.getLatestGValues()
    if sellingAmount and schoolName:
        sellingAmount = int(sellingAmount[0])
        schoolName = schoolName[0]
        gType = areaTranslateItem(schoolName)
        valueType = areaTranslateValue(schoolName)
        gValue = getattr(gValues, valueType)
        totalPrice = int(sellingAmount * gValue)
        success = await selling(userId, gType, sellingAmount, totalPrice)
        if not success:
            st = '你不够G^ ^'
    elif isSellingAll:
        allKusa = await GSellingAll(userId, gValues)
        st += f'获得了{allKusa}草'
    else:
        st = '参数不正确^ ^'
    await session.send(st)


async def GSellingAll(userId, gValues):
    eastGAmount, southGAmount, northGAmount, zhuhaiGAmount, shenzhenGAmount = await getAllGAmounts(userId)
    kusaEast = eastGAmount * gValues.eastValue
    kusaSouth = southGAmount * gValues.southValue
    kusaNorth = northGAmount * gValues.northValue
    kusaZhuhai = zhuhaiGAmount * gValues.zhuhaiValue
    kusaShenzhen = shenzhenGAmount * gValues.shenzhenValue
    allKusa = kusaEast + kusaSouth + kusaNorth + kusaZhuhai + kusaShenzhen
    allKusa = int(allKusa)
    await baseDB.changeKusa(userId, allKusa)
    await baseDB.changeKusa(config['qq']['bot'], -allKusa)
    await itemDB.cleanAllG(userId)
    return allKusa


@on_command(name='G线图', only_to_me=False)
async def G_pic(session: CommandSession):
    stripped_arg = session.current_arg_text.strip()
    school = re.findall(r'[东南北珠深]', stripped_arg)
    gValuesList = await gValueDB.getThisCycleGValues()
    gValuesColMap = getGValuesColMap(gValuesList)

    if school:
        school = school[0]
        gType = areaTranslateValue(school)
        gPicPath = G_PIC + f'/G_{gType}.png'
        if not os.path.exists(gPicPath):
            createGpicSingle(gValuesColMap[gType], gPicPath)
    else:
        gPicPath = G_PIC + '/G_all.png'
        createGpicAll(gValuesColMap, gPicPath)

    pic = getImgBase64(gPicPath)
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


def createGpicSingle(gValuesCol, gPicPath):
    plt.plot(gValuesCol)
    plt.xticks([])
    plt.savefig(gPicPath)
    plt.close()


def createGpicAll(gValuesColMap, gPicPath):
    plt.plot(list(map(lambda x: x / areaStartValue('东'), gValuesColMap['eastValue'])), label='East')
    plt.plot(list(map(lambda x: x / areaStartValue('南'), gValuesColMap['southValue'])), label='South')
    plt.plot(list(map(lambda x: x / areaStartValue('北'), gValuesColMap['northValue'])), label='North')
    plt.plot(list(map(lambda x: x / areaStartValue('珠'), gValuesColMap['zhuhaiValue'])), label='Zhuhai')
    plt.plot(list(map(lambda x: x / areaStartValue('深'), gValuesColMap['shenzhenValue'])), label='Shenzhen')
    plt.xticks([])
    plt.yscale('log')
    plt.legend()
    plt.savefig(gPicPath)
    plt.close()


@nonebot.scheduler.scheduled_job('cron', minute='*/30')
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
    removeGPic()


def getNewG(oldG: float, changeRange: float):
    rank = changeRange * (systemRandom.random() - 0.498)
    newG = rd3(oldG * (1 + rank))
    time.sleep(0.001)
    return newG


def removeGPic():
    ls = os.listdir(G_PIC)
    for fileName in ls:
        cPath = os.path.join(G_PIC, fileName)
        os.remove(cPath)


@nonebot.scheduler.scheduled_job('cron', day='*/3', hour='23', minute='45')
async def G_reset():
    allUsers = await baseDB.getAllUser()
    gValues = await gValueDB.getLatestGValues()
    bot = nonebot.get_bot()
    for user in allUsers:
        allKusaFromG = await GSellingAll(user.qq, gValues)
        if allKusaFromG:
            print(f'用户{user.qq}的G已经兑换为草，数量为{allKusaFromG}')
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
