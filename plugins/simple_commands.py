import json
import codecs
import nonebot
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
    output = ''
    donateList = await db.getUserListOrderByDonate()
    selfDonate = await db.getUser(session.ctx['user_id'])

    if selfDonate and selfDonate.donateAmount > 0:
        output += '感谢您对生草系统的支援！\n'
        output += f"您的捐助金额为：{selfDonate.donateAmount}元\n\n"

    output += '感谢所有生草系统的资助者！\n篇幅所限，仅展示部分捐助信息。\n'
    for row in donateList:
        displayName = row.name if row.name else row.qq
        output += f'{displayName}：{row.donateAmount}元\n'
    output += 'and you...'
    await session.send(output)


@on_command(name='爆柠檬', only_to_me=False)
async def _(session: CommandSession):
    await session.send('🍋')


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
