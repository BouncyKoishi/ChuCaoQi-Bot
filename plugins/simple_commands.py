import json
import codecs
import nonebot
import datetime
import numpy as np
import dbConnection.db as db
from nonebot import Message, on_command, CommandSession
from kusa_base import config
from urllib import request


@on_command(name='help', only_to_me=False)
async def _(session: CommandSession):
    with codecs.open(u'text/指令帮助.txt', 'r', 'utf-8') as f:
        await session.send(f.read().strip())


@on_command(name='生草系统', only_to_me=False)
async def _(session: CommandSession):
    with codecs.open(u'text/生草系统-指令帮助.txt', 'r', 'utf-8') as f:
        await session.send(f.read().strip())


@on_command(name='公告', only_to_me=False)
async def _(session: CommandSession):
    with codecs.open(u'text/公告.txt', 'r', 'utf-8') as f:
        await session.send(f.read().strip())


@on_command(name='晚安', only_to_me=False)
async def _(session: CommandSession):
    msg = f'晚安！你获得的睡眠时间：'
    await sleep(session.ctx, msg, 400, 50, 1)


@on_command(name='午睡', only_to_me=False)
async def _(session: CommandSession):
    msg = f'午安！你获得的睡眠时间：'
    await sleep(session.ctx, msg, 60, 10, 1)


@on_command(name='醒了', only_to_me=False)
async def _(session: CommandSession):
    msg = f'你可以睡个回笼觉。你获得的睡眠时间：'
    await sleep(session.ctx, msg, 60, 10, 1)


async def sleep(ctx, msg, base, summa, size):
    allow_list = config['group']['adminAuthGroup']
    if ctx['group_id'] in allow_list:
        durTime = sleepTimeCalculation(base, summa, size)
        msg += f'{durTime}sec！'
        bot = nonebot.get_bot()
        await bot.set_group_ban(group_id=ctx['group_id'], user_id=ctx['user_id'], duration=durTime)
        await bot.send_group_msg(group_id=ctx['group_id'], message=msg)


def sleepTimeCalculation(base, summa, size):
    x = np.random.uniform(size=size)
    y = np.random.uniform(size=size)
    z = np.sqrt(-2 * np.log(x)) * np.cos(2 * np.pi * y)
    dur_time_min = base + float(z) * summa
    return int(dur_time_min * 60)


@on_command(name='THANKS', only_to_me=False)
async def _(session: CommandSession):
    userId = session.ctx['user_id']
    year = session.current_arg_text.strip()
    year = year if year and year.isdigit() and 2020 <= int(year) <= 2099 else None
    donateAmount = await db.getDonateAmount(userId)
    output = ''

    if donateAmount > 0:
        output += '感谢您对生草系统的支援！\n'
        output += f"您的累计捐助金额为：{donateAmount}元\n"
        if year:
            thisYearAmount = await db.getDonateAmount(userId, year)
            output += f"您的{year}年度捐助金额为：{thisYearAmount}元\n" if thisYearAmount > 0 else ''
        output += '若需要查询您的所有捐助记录，请使用【!捐助记录】指令\n\n'

    output += '感谢所有生草系统的资助者！\n'
    donateRank = await db.getDonateRank(year=year)

    if len(donateRank) == 0:
        output += f'{year}年度暂无捐助信息= ='
        await session.send(output)
        return
    output += f'以下是{year}年度的捐助信息' if year else '以下是累计捐助信息'
    output += f'(篇幅较长，仅展示前25条)：\n' if len(donateRank) > 25 else '：\n'

    nameList = await db.getNameListByQQ(donateRank.keys())
    for qq, amount in list(donateRank.items())[:25]:
        displayName = nameList[qq] if qq in nameList and nameList[qq] else qq
        output += f'{displayName}：{amount:.2f}元\n'
    await session.send(output[:-1])


@on_command(name='捐助记录', aliases='捐赠记录', only_to_me=False)
async def _(session: CommandSession):
    userId = session.ctx['user_id']
    output = ''
    donateRecords = await db.getDonateRecords(userId)
    if not donateRecords:
        output += '您还没有捐助记录哦~'
    else:
        output += '您的捐助记录如下：\n'
        for record in donateRecords:
            output += f"{record.donateDate}：{record.amount}元\n"
    await session.send(output[:-1])


@on_command(name='爆柠檬', only_to_me=False)
async def _(session: CommandSession):
    await session.send('🍋')


@on_command(name='timestamp', only_to_me=False)
async def _(session: CommandSession):
    await session.send(str(datetime.datetime.now().timestamp()))


@nonebot.scheduler.scheduled_job('cron', day='*', hour='9', minute='00')
async def read60s():
    msg = await get60sNewsPic()
    for qq_group in config['sendNews']['group']:
        await nonebot.get_bot().send_group_msg(group_id=qq_group, message=Message(msg))


@on_command(name='news', only_to_me=False)
async def _(session: CommandSession):
    msg = await get60sNewsPic()
    await session.send(msg)


async def get60sNewsPic():
    url = "https://api.2xb.cn/zaob"
    http_req = request.Request(url)
    http_req.add_header('User-Agent', config['web']['userAgent'])
    with request.urlopen(http_req) as req:
        data = req.read().decode('utf-8')
        data = ''.join(x for x in data if x.isprintable())
        retData = json.loads(data)
        lst = retData['imageUrl']
        pic_ti1 = f"[CQ:image,file={lst}]"
        return pic_ti1
