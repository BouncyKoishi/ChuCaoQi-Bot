import re
import time
import codecs
import random
import nonebot
from nonebot import on_command, CommandSession
from decorator import CQ_injection_check_command
from functools import reduce

junWifeList = []


@on_command(name='roll_help', only_to_me=False)
async def roll_help(session: CommandSession):
    with codecs.open(u'text/随机化功能帮助.txt', 'r', 'utf-8') as f:
        await session.send(f.read().strip())


@on_command(name='roll', only_to_me=False)
async def roll_point(session: CommandSession):
    stripped_arg = session.current_arg_text.strip()
    diceInfo = re.search(r'(\d{1,4})d((\d{1,12})-(\d{1,12})|\d{1,12})', stripped_arg)
    if diceInfo:
        result, _ = runDice(diceInfo, 'n')
        await session.send(f'Roll点结果为：{result}')


@on_command(name='rollx', only_to_me=False)
async def roll_point_detail(session: CommandSession):
    stripped_arg = session.current_arg_text.strip()
    diceInfo = re.search(r'(\d)d((\d{1,12})-(\d{1,12})|\d{1,12})', stripped_arg)
    if diceInfo:
        result, numList = runDice(diceInfo, 'n')
        numListStr = reduce(lambda a, b: str(a) + '+' + str(b), numList)
        await session.send(f'Roll点结果为：{numListStr}={result}')


@on_command(name='rollf', only_to_me=False)
async def roll_point_float(session: CommandSession):
    stripped_arg = session.current_arg_text.strip()
    regex = r'(\d{1,4})d((\d{1,12}\.\d{1,12}|\d{1,12})-(\d{1,12}\.\d{1,12}|\d{1,12})|(\d{1,12}\.\d{1,12}|\d{1,12}))'
    diceInfo = re.search(regex, stripped_arg)
    if diceInfo:
        result, _ = runDice(diceInfo, 'f')
        await session.send(f'Roll点结果为：{result}')


def runDice(dice_infor, stage):
    amount = int(dice_infor.group(1))
    point_range = dice_infor.group(2)
    min_point = 1
    result = 0
    num_list = []

    if stage == 'f':
        min_point = 0
        if '-' in point_range:
            min_point = float(dice_infor.group(3))
            max_point = float(dice_infor.group(4))
            if max_point - min_point < 0:
                return result, num_list
        else:
            max_point = float(dice_infor.group(2))

        while amount:
            result += random.uniform(min_point, max_point)
            amount -= 1

        return result, num_list

    else:
        if '-' in point_range:
            min_point = int(dice_infor.group(3))
            max_point = int(dice_infor.group(4))
            if max_point - min_point < 0:
                return 0
        else:
            max_point = int(dice_infor.group(2))

        while amount:
            num = random.randint(min_point, max_point)
            result += num
            if amount <= 9:
                num_list.append(num)
            amount -= 1

        return result, num_list


@on_command(name='选择', only_to_me=False)
@CQ_injection_check_command
async def _(session: CommandSession):
    argList = session.current_arg.strip().split(' ')
    if not argList:
        return
    userId = session.ctx['user_id']
    hashingStr = str(argList) + str(userId) + time.strftime("%Y-%m-%d", time.localtime()) + 'confounding'
    st = "选择：" + argList[hash(hashingStr) % len(argList)]
    await session.send(st)


@on_command(name='判断', only_to_me=False)
@CQ_injection_check_command
async def _(session: CommandSession):
    stripped_arg = session.current_arg_text.strip().replace('\n', '')
    answer = ['是', '否']
    userId = session.ctx['user_id']
    hashingStr = stripped_arg + str(userId) + time.strftime("%Y-%m-%d", time.localtime()) + 'confounding'
    st = stripped_arg + '\n判断：' + answer[hash(hashingStr) % 2]
    await session.send(st)


@on_command(name='rollwife', only_to_me=False)
async def _(session: CommandSession):
    if "group_id" in session.ctx:
        groupId = session.ctx['group_id']
        userId = session.ctx['user_id']
        member_list = await session.bot.get_group_member_list(group_id=groupId)

        outputStr = '你的老婆是：'
        if luojunJudge(userId):
            outputStr += '罗俊'
        else:
            nickname_list = []
            for member in member_list:
                nickname_list.append(member['nickname'])
            outputStr += nickname_list[int(random.random() * len(nickname_list))]
        await session.send(outputStr)
        luojunCount(userId)


def luojunCount(userId):
    global junWifeList
    for member in junWifeList:
        if member[0] == userId:
            member[1] += 1
            return
    junWifeList.append([userId, 0])


def luojunJudge(userId):
    for member in junWifeList:
        if member[0] == userId:
            x = member[1]
            if x > 10 or random.random() < 1.1 ** x - 1:
                return True
    return False


@nonebot.scheduler.scheduled_job('interval', minutes=6)
async def luojun_del():
    global junWifeList
    newJunList = []
    for member in newJunList:
        member[1] -= 1
        if member[1] > 0:
            newJunList.append(member)
    junWifeList = newJunList
