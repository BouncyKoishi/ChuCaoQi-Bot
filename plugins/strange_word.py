import math
import random
import re
import nonebot
import asyncio
from nonebot import on_natural_language, NLPSession
from nonebot import on_command, CommandSession, on_startup
from kusa_base import config, sendLog, isSuperAdmin
from plugins.chatGPT_api import getChatReply


sentenceList = []
modelSentenceList = []
notRecordWords = config['guaihua']['notRecordWords']
notRecordMembers = config['guaihua']['notRecordMembers']
freeze = False


@on_startup
async def _():
    global sentenceList
    with open(u'database/guaihua.txt', 'r', encoding='utf-8') as f:
        for sentence in f.readlines():
            sentence = sentence.strip()
            if sentence:
                sentenceList.append(sentence)
    print(f'当前怪话条目数：{len(sentenceList)}')
    await setModelSentenceList()


@on_command(name='gh_freeze', only_to_me=False)
async def gh_frozen(session: CommandSession):
    if not await isSuperAdmin(session.ctx['user_id']):
        return

    global freeze
    freeze = not freeze
    await session.send(f'怪话接收已{"冻结" if freeze else "解冻"}')


@on_command(name='说点怪话', only_to_me=False)
async def say(session: CommandSession):
    strippedText = session.current_arg_text.strip()
    if strippedText and random.random() < .4:
        reply = await getSentenceAdvance(strippedText)
        await session.send(reply)
    else:
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
    strippedText = session.current_arg_text.strip()
    if strippedText and random.random() < .4:
        replyList = await getSentenceListAdvance(strippedText)
    else:
        replyList = []
        while len(replyList) < 3:
            msg = getRandomSentence()
            if '[CQ:' not in msg and msg not in replyList:
                replyList.append(msg)
    for msg in replyList:
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


async def getSentenceAdvance(inputStr: str):
    systemPrompt = '你需要从以下怪话中选择一句语义最适宜的话来回答用户说的内容。你的回答内容只能是怪话列表中的某一句话，不包括任何其它内容。\n'
    userPrompt = f"用户发言：{inputStr}\n\n怪话列表：\n"
    for i in range(10):
        userPrompt += random.choice(modelSentenceList) + '\n'
    prompt = [{"role": "system", "content": systemPrompt}, {"role": "user", "content": userPrompt}]
    reply, tokenUsage = await getChatReply("gpt-4o-mini", prompt)
    if reply not in modelSentenceList:
        print(f'输出内容为:"{reply}" 匹配怪话库失败，输出随机怪话')
        reply = random.choice(modelSentenceList)
    print(f'GPT-4o TokenUsage: {tokenUsage}')
    return reply


async def getSentenceListAdvance(inputStr: str):
    systemPrompt = ('你需要从以下怪话中选择三句语义最适宜的话来回答用户说的内容。'
                    '你需要排列好顺序使得三句话相对连贯。'
                    '你的回答内容按以下格式输出：["A", "B", "C"]'
                    '其中A、B、C只能是怪话列表中的某一句话，不包括任何其它内容。')
    userPrompt = f"用户发言：{inputStr}\n\n怪话列表：\n"
    for i in range(40):
        userPrompt += random.choice(modelSentenceList) + '\n'
    prompt = [{"role": "system", "content": systemPrompt}, {"role": "user", "content": userPrompt}]
    reply, tokenUsage = await getChatReply("gpt-4o-mini", prompt)
    print('Reply:', reply)
    if reply.startswith('[') and reply.endswith(']'):
        reply = reply.replace('“', '"').replace('”', '"').replace('‘', "'").replace('’', "'")
        reply = reply.replace('，', ',').replace('。', '.').replace('：', ':').replace('；', ';')
        try:
            replyList = eval(reply)
            if isinstance(replyList, list):
                for i in range(len(replyList)):
                    if not isinstance(replyList[i], str):
                        print(f'输出内容为:"{reply}" 匹配怪话库失败，输出随机怪话')
                        replyList[i] = random.choice(modelSentenceList)
                return replyList
        except Exception as e:
            print(f'解析输出内容失败，错误信息：{e}')
    print(f'输出内容为:"{reply}" 基本格式匹配失败，输出随机怪话')
    return [random.choice(sentenceList) for _ in range(3)]


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

    # 不录入条件
    if freeze:
        return
    if msg in sentenceList:
        return
    if '\n' in msg:
        return
    if userId in notRecordMembers:
        return
    for nrm in notRecordWords:
        if nrm in msg:
            return
    # 小伞的东方原曲挑战相关
    if re.search(r'(?:(?:hmx|yym|yyc|hyz|fsl|dld|xlc|slm|hzc|gzz|tkz|gxs|hld|swy|wht(?:ds)?|dzz|txg|(?:mf)?emrj|dmk|fxtz?|sml|xql|pyh|gyyw|红魔乡|妖妖梦|永夜抄|花映(?:冢|塚)|风神录|地灵殿|星莲船|神灵庙|辉针城|绀珠传|天空璋|鬼形兽|虹龙洞|兽王园|文花帖(?:ds)?|大战争|天邪鬼|(?:秘封)?噩梦日记|弹幕狂|绯想天|非想天则|深秘录|心绮楼|凭依华|刚欲异闻)(?:[1-6]|ex|ph)(?:dz|boss|道中))|^(?:这首曲目(?:出自|不?是道中曲$)|(?:当前分数榜|提示)$|正确答案是)', msg, re.I | re.M):
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
        print(f'录入了来自{userId}的怪话：{msg}')
        if listLen >= 360:
            delMsgIndex = math.floor(1.1 ** (random.random() * 60) - 1)
            delMsg = sentenceList[delMsgIndex]
            print(f'DelMsgIndex={delMsgIndex}, Delete:{delMsg}')
            del sentenceList[delMsgIndex]

    # 主动怪话
    if random.random() < config['guaihua']['risk'] / 100:
        output = await getSentenceAdvance(msg)
        await session.send(output)
        return


@nonebot.scheduler.scheduled_job('interval', minutes=2)
async def saveToFile():
    with open(u'database/guaihua.txt', 'w', encoding='utf-8') as file:
        for sentence in sentenceList:
            file.write(sentence + '\n')


@nonebot.scheduler.scheduled_job('interval', hours=3)
async def _():
    await setModelSentenceList()


async def setModelSentenceList():
    global modelSentenceList
    modelSentenceList = []
    for sentence in sentenceList:
        if len(sentence) <= 2:
            continue
        if '[CQ:' in sentence:
            continue
        # 过滤纯符号
        if re.match(r'^[\s!@#$%^&*()_+\-=\[\]{};:\'",.<>/?\\|`~]*$', sentence):
            continue
        modelSentenceList.append(sentence)
    print(f'模型怪话条目数：{len(modelSentenceList)}')

