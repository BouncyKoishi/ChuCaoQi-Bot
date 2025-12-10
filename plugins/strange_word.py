import math
import random
import os
import re
import nonebot
import asyncio
from nonebot import on_natural_language, NLPSession
from nonebot import on_command, CommandSession, on_startup
from kusa_base import config, sendLog, isSuperAdmin
from plugins.chatGPT_api import getChatReply

sentenceListDict, modelSentenceListDict = {}, {}
notRecordWords = config['guaihua']['notRecordWords'] + config['sensitiveWords']
notRecordMembers = config['guaihua']['notRecordMembers']
recordGroups = config['guaihua']['recordGroups']
defaultGroupNum = config['group']['sysu']
receiveFreeze = False
allowModel = True


async def setModelSentenceList():
    global modelSentenceListDict
    for groupNum, sList in sentenceListDict.items():
        modelSentenceList = []
        for sentence in sList:
            if len(sentence) <= 2:
                continue
            if '[CQ:' in sentence:
                continue
            # 过滤纯符号
            if re.match(r'^[\s!@#$%^&*()_+\-=\[\]{};:\'",.<>/?\\|`~]*$', sentence):
                continue
            modelSentenceList.append(sentence)
        print(f'群聊{groupNum}模型怪话条目数：{len(modelSentenceList)}')
        modelSentenceListDict[groupNum] = modelSentenceList


@on_command(name='gh_receive_freeze', only_to_me=False)
async def gh_frozen(session: CommandSession):
    if not await isSuperAdmin(session.ctx['user_id']):
        return

    global receiveFreeze
    receiveFreeze = not receiveFreeze
    await session.send(f'怪话接收已{"冻结" if receiveFreeze else "解冻"}')


@on_command(name='gh_model_freeze', only_to_me=False)
async def gh_model_frozen(session: CommandSession):
    if not await isSuperAdmin(session.ctx['user_id']):
        return

    global allowModel
    allowModel = not allowModel
    await session.send(f'大模型怪话已{"启用" if allowModel else "禁用"}')


@on_command(name='说点怪话', only_to_me=False)
async def say(session: CommandSession):
    strippedText = session.current_arg_text.strip()
    if strippedText and allowModel and random.random() < .5 :
        reply = await getSentenceAdvance(session.ctx['group_id'], strippedText)
        await session.send(reply)
    else:
        await session.send(getRandomSentence(defaultGroupNum))


@on_command(name='话怪点说', only_to_me=False)
async def _(session: CommandSession):
    msg = getRandomSentence(defaultGroupNum)
    await session.send(msg if '[CQ:' in msg else msg[::-1])


@on_command(name='说话怪点', only_to_me=False, aliases=('怪点说话',))
async def _(session: CommandSession):
    msg = getRandomSentence(defaultGroupNum)
    if '[CQ:' in msg:
        await session.send(msg)
    else:
        msgList = list(msg)
        random.shuffle(msgList)
        await session.send(''.join(msgList))


@on_command(name='说些怪话', only_to_me=False)
async def _(session: CommandSession):
    strippedText = session.current_arg_text.strip()
    groupId = session.ctx['group_id']
    if strippedText and allowModel and random.random() < .35:
        replyList = await getSentenceListAdvance(groupId, strippedText)
    else:
        replyList = []
        while len(replyList) < 3:
            msg = getRandomSentence(defaultGroupNum)
            if '[CQ:' not in msg and msg not in replyList:
                replyList.append(msg)
    for msg in replyList:
        await session.send(msg)
        await asyncio.sleep(1)


def getSentenceList(groupNum):
    return sentenceListDict[groupNum] if groupNum in sentenceListDict else sentenceListDict[defaultGroupNum]


def getRandomSentence(groupNum):
    sentenceList = getSentenceList(groupNum)
    return sentenceList[int(random.random() * len(sentenceList))]


def getModelSentenceList(groupNum):
    return modelSentenceListDict[groupNum] if groupNum in modelSentenceListDict else modelSentenceListDict[defaultGroupNum]


async def getSentenceAdvance(groupNum, inputStr: str):
    modelSentenceList = getModelSentenceList(groupNum)
    systemPrompt = '你需要从以下怪话中选择一句语义最适宜的话来回答用户说的内容。你的回答内容只能是怪话列表中的某一句话，不包括任何其它内容。\n'
    userPrompt = f"用户发言：{inputStr}\n\n怪话列表：\n"
    for i in range(10):
        userPrompt += random.choice(modelSentenceList) + '\n'
    prompt = [{"role": "system", "content": systemPrompt}, {"role": "user", "content": userPrompt}]
    reply, tokenUsage = await getChatReply("deepseek-chat", prompt)
    if reply not in modelSentenceList:
        print(f'输出内容为:"{reply}" 匹配怪话库失败，输出随机怪话')
        reply = random.choice(modelSentenceList)
    print(f'Deepseek TokenUsage: {tokenUsage}')
    return reply


async def getSentenceListAdvance(groupNum, inputStr: str):
    modelSentenceList = getModelSentenceList(groupNum)
    systemPrompt = ('你需要从以下怪话中选择三句话，组成一个尽可能语义适宜且内容连贯的段落来回答用户说的内容。'
                    '你的回答内容按以下格式输出：["A", "B", "C"]'
                    '其中A、B、C只能是怪话列表中的某一句话，不包括任何其它内容。')
    userPrompt = f"用户发言：{inputStr}\n\n怪话列表：\n"
    for i in range(40):
        userPrompt += random.choice(modelSentenceList) + '\n'
    prompt = [{"role": "system", "content": systemPrompt}, {"role": "user", "content": userPrompt}]
    reply, tokenUsage = await getChatReply("deepseek-chat", prompt)
    print(f'Deepseek TokenUsage: {tokenUsage}')
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
    sentenceList = getSentenceList(groupNum)
    return [random.choice(sentenceList) for _ in range(3)]


@on_natural_language(keywords=None, only_to_me=False)
async def record(session: NLPSession):
    if 'group_id' not in session.ctx:
        return

    global sentenceListDict

    msg = session.msg
    userId = session.ctx['user_id']
    groupNum = session.ctx['group_id']
    if groupNum not in recordGroups:
        return

    sentenceList = sentenceListDict.get(groupNum, [])

    # 不录入条件
    if receiveFreeze:
        return
    if msg in sentenceList:
        return
    if '\n' in msg:
        return
    if userId in notRecordMembers:
        return
    for word in notRecordWords:
        if word in msg:
            return
    # 小伞的东方原曲挑战相关
    if re.search(
            r'(?:hmx|yym|yyc|hyz|fsl|dld|xlc|slm|hzc|gzz|tkz|gxs|hld|swy|wht(?:ds)?|dzz|txg|(?:mf)?emrj|dmk|fxtz?|sml|xql|pyh|gyyw|红魔乡|妖妖梦|永夜抄|花映[冢塚]|风神录|地灵殿|星莲船|神灵庙|辉针城|绀珠传|天空璋|鬼形兽|虹龙洞|兽王园|文花帖(?:ds)?|大战争|天邪鬼|(?:秘封)?噩梦日记|弹幕狂|绯想天|非想天则|深秘录|心绮楼|凭依华|刚欲异闻)(?:[1-6]|ex|ph)(?:dz|boss|道中)|^(?:这首曲目(?:出自|不?是道中曲$)|(?:当前分数榜|提示)$|正确答案是)',
            msg, re.I | re.M):
        return

    # 概率录入
    listLen = len(sentenceList)
    recordRisk = 175 - (listLen / 4)
    if '[CQ' in msg:
        recordRisk *= 0.25
    else:
        msgLength = len(msg.replace(' ', ''))
        recordRisk /= (0.12 * msgLength + 1.5 / msgLength)
    print(f'RecordRisk: {recordRisk}')

    if random.random() * 100 <= recordRisk:
        sentenceList.append(msg)
        await sendLog(f'群聊{groupNum}录入了来自{userId}的怪话：{msg}')
        if listLen >= 600:
            delMsgIndex = math.floor(1.1 ** (random.random() * 66) - 1)
            delMsg = sentenceList[delMsgIndex]
            print(f'DelMsgIndex={delMsgIndex}, Delete:{delMsg}')
            del sentenceList[delMsgIndex]
        sentenceListDict[groupNum] = sentenceList

    # 接下来的功能只在SYSU群启用
    if groupNum != defaultGroupNum:
        return

    # 主动怪话
    if random.random() < .002 and allowModel:
        output = await getSentenceAdvance(groupNum, msg)
        await session.send(output)

    # 拳击
    if random.random() < .002:
        msgId = session.ctx['message_id']
        await session.bot.set_msg_emoji_like(message_id=msgId, emoji_id=128074)
        print(f'已对消息{msgId}设置表情：👊')


@nonebot.scheduler.scheduled_job('interval', minutes=2, misfire_grace_time=120)
async def strangeWordSavingRunner():
    os.makedirs('database/strangeWord', exist_ok=True)
    for groupNum in sentenceListDict:
        with open(f'database/strangeWord/{groupNum}.txt', 'w', encoding='utf-8') as file:
            for sentence in sentenceListDict[groupNum]:
                file.write(sentence + '\n')


@nonebot.scheduler.scheduled_job('interval', hours=3, misfire_grace_time=600)
async def setModelSentenceListRunner():
    await setModelSentenceList()


@on_startup
async def _():
    global sentenceListDict
    folderPath = 'database/strangeWord'
    for filename in os.listdir(folderPath):
        if filename.endswith('.txt'):
            groupNum = int(filename[:-4])
            sentenceList = []
            with open(os.path.join(folderPath, filename), 'r', encoding='utf-8') as f:
                for sentence in f.readlines():
                    sentence = sentence.strip()
                    if sentence:
                        sentenceList.append(sentence)
            print(f'群聊{groupNum}当前怪话条目数：{len(sentenceList)}')
            sentenceListDict[groupNum] = sentenceList
    await setModelSentenceList()
