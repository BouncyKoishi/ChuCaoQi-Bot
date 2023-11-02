import math
import random
import nonebot
import asyncio
from nonebot import on_natural_language, NLPSession
from nonebot import on_command, CommandSession
from kusa_base import config, sendLog, isSuperAdmin


sentenceList = []
notRecordWords = config['guaihua']['notRecordWords']
notRecordMembers = config['guaihua']['notRecordMembers']
previousSentence = ''
freeze = False

with open(u'database/guaihua.txt', 'r', encoding='utf-8') as f:
    for sentence in f.readlines():
        sentence = sentence.strip()
        if sentence:
            sentenceList.append(sentence)
print(f'怪话条目数：{len(sentenceList)}')


@on_command(name='gh_freeze', only_to_me=False)
async def gh_frozen(session: CommandSession):
    if not await isSuperAdmin(session.ctx['user_id']):
        return
        
    global freeze
    freeze = not freeze
    await session.send(f'怪话接收已{"冻结" if freeze else "解冻"}')


@on_command(name='说点怪话', only_to_me=False)
async def say(session: CommandSession):
    await session.send(getRandomSentence())


@on_command(name='话怪点说', only_to_me=False)
async def _(session: CommandSession):
    msg = getRandomSentence()
    await session.send(msg if '[CQ:' in msg else msg[::-1])


@on_command(name='说话怪点', only_to_me=False)
async def _(session: CommandSession):
    await saySentenceShuffle(session)


@on_command(name='怪点说话', only_to_me=False)
async def _(session: CommandSession):
    await saySentenceShuffle(session)


@on_command(name='说些怪话', only_to_me=False)
async def _(session: CommandSession):
    outputList = []
    while len(outputList) < 3:
        msg = getRandomSentence()
        if '[CQ:' in msg:
            continue
        if msg not in outputList:
            outputList.append(msg)
    for msg in outputList:
        await session.send(msg)
        await asyncio.sleep(1)


def getRandomSentence():
    listLen = len(sentenceList)
    msg = sentenceList[int(random.random() * listLen)]
    return msg


async def saySentenceShuffle(session: CommandSession):
    msg = getRandomSentence()
    if '[CQ:' in msg:
        await session.send(msg)
    else:
        msg_list = list(msg)
        random.shuffle(msg_list)
        msg_shuffle = ''.join(msg_list)
        await session.send(msg_shuffle)
        

@on_natural_language(keywords=None, only_to_me=False)
async def record(session: NLPSession):
    if 'group_id' not in session.ctx:
        return
        
    global sentenceList
    listLen = len(sentenceList)
    msg = session.msg
    userId = session.ctx['user_id']
    groupNum = session.ctx['group_id']
    
    if groupNum != config['group']['sysu']:
        return
    
    # 主动怪话
    if random.random() < config['guaihua']['risk'] / 100:
        msg = sentenceList[int(random.random() * listLen)]
        await session.send(msg)
        return
    
    # 不录入条件
    if freeze:
        return
    if repeat(msg) or msg in sentenceList:
        return
    if '\n' in msg:
        return
    if userId in notRecordMembers:
        return
    for nrm in notRecordWords:
        if nrm in msg:
            return

    # 概率录入
    record_risk = 200 - (listLen / 2)
    if 'CQ' in msg:
        record_risk *= 0.25
    else:
        msgLength = len(msg.replace(' ', ''))
        record_risk /= (0.12 * msgLength + 1.5 / msgLength)
    print(f'RecordRisk: {record_risk}')

    if random.random() * 100 <= record_risk:
        sentenceList.append(msg)
        await sendLog(f'录入了来自{userId}的怪话：{msg}')
        if listLen >= 360:
            delMsgIndex = math.floor(1.1 ** (random.random() * 60) - 1)
            delMsg = sentenceList[delMsgIndex]
            print(f'DelMsgIndex={delMsgIndex}, Delete:{delMsg}')
            del sentenceList[delMsgIndex]
        

def repeat(latestSentence):
    global previousSentence
    if previousSentence == latestSentence:
        return True
    previousSentence = latestSentence
    return False


@nonebot.scheduler.scheduled_job('interval', minutes=1)
async def saveToFile():
    with open(u'database/guaihua.txt', 'w', encoding='utf-8') as file:
        for sentence in sentenceList:
            file.write(sentence + '\n')

