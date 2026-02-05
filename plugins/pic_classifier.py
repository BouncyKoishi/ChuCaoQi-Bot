import random
import httpx
import aiohttp
import time
from io import BytesIO
from PIL import Image
from decorator import on_reply_command
from nonebot import on_natural_language, NLPSession
from kusa_base import config
from utils import extractImgUrls, checkBanAvailable

nailongModel = None
modelPath = './model_best.pth'
RUN_NAILONG_MODEL_FLAG = (config['env'] == 'prod')  # 测试环境不加载奶龙模型

if RUN_NAILONG_MODEL_FLAG:
    import torch
    from torch import nn
    from torchsampler.imbalanced import torchvision
    from torchvision import transforms

    device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
    img_transform = transforms.Compose([
        transforms.Resize([224, 224]),
        transforms.ToTensor(),
    ])
    try:
        nailongModel = torchvision.models.resnet50()
        nailongModel.fc = torch.nn.Linear(nailongModel.fc.in_features, 2)
        nailongModel.load_state_dict(torch.load(modelPath, map_location=device, weights_only=True)['model'])
        nailongModel = nailongModel.to(device)
        nailongModel.eval()
        print("奶龙检测模型加载成功")
    except Exception as e:
        print(f"奶龙检测模型加载失败: {e}")
else:
    print("当前环境不加载奶龙检测模型")

confirmations = {}
lastUsedTime = {}


@on_natural_language(keywords=None, only_to_me=False)
@on_reply_command(commands=['#nsfw', '#nailong'])
async def picClassifierReplyNLP(session: NLPSession, replyMessageCtx):
    global confirmations
    strippedText = session.ctx['message'][-1].data.get('text', '').strip()

    timeCheckResult, sign = timeCheck(strippedText, session.ctx)
    if not timeCheckResult:
        await session.send(sign)
        return
    imgUrls = extractImgUrls(replyMessageCtx['message'])
    if not imgUrls or len(imgUrls) == 0:
        return
    isNsfw = strippedText == '#nsfw'
    duelRand = random.random()
    userId, targetId = session.ctx['user_id'], replyMessageCtx['user_id']
    if userId != replyMessageCtx['user_id'] and duelRand < 1/8:
        nsfwMsg = f"你触发了黑暗决斗。\n如果这张图片是色图，发图的人将会被口球，否则你会被口球。口球的秒数等于adult/everyone的分值×10。\n输入y继续检测，输入其他表示取消。"
        nailongMsg = "你触发了奶龙决斗。\n如果这张图片的奶龙指数大于50，发图的人将会被口球。否则你会被口球。口球的秒数等于abs(奶龙指数-50)×40。\n输入y继续检测，输入其他表示取消。"
        await session.send(f'[CQ:reply,id={session.ctx["message_id"]}]{nsfwMsg if isNsfw else nailongMsg}')
        confirmations[userId] = {'sender': replyMessageCtx['user_id'], 'imgUrl': imgUrls[0],
                                 'imgMsgId': replyMessageCtx['message_id'], 'commandMsgId': session.ctx['message_id'],
                                 'type': strippedText[1:]}
        return
    if isNsfw:
        await session.send("正在检测……")
    checkResultStr, _ = await nsfwChecker(imgUrls[0]) if isNsfw else await nailongChecker(imgUrls[0])
    await session.send(f'[CQ:reply,id={session.ctx["message_id"]}]{checkResultStr}')
    timeUpdater(strippedText, session.ctx.get('group_id', 0), session.ctx['user_id'])


@on_natural_language(keywords=None, only_to_me=False)
async def picClassifierContinueNLP(session: NLPSession):
    global confirmations
    userId = session.ctx['user_id']
    if userId not in confirmations:
        return
    if session.msg_text.strip().lower() != 'y':
        del confirmations[userId]
        await session.send("已取消决斗。")
        return

    info = confirmations[userId]
    if info['type'] == 'nsfw':
        await session.send("正在启动黑暗决斗……")
        checkResultStr, resultDict = await nsfwChecker(info['imgUrl'])
        if resultDict:
            adultScore = resultDict.get('adult', 0)
            everyoneScore = resultDict.get('everyone', 0)
            isAdult = adultScore > everyoneScore
            targetId = info['sender'] if isAdult else userId
            fightResultStr = (f'决斗成功！图片发送者' if isAdult else '决斗失败！检测者')
            canBanTarget = await checkBanAvailable(targetId, session.ctx['group_id'])
            if canBanTarget:
                muteDuration = int(max(adultScore, everyoneScore) * 10)
                await session.bot.set_group_ban(group_id=session.ctx['group_id'], user_id=targetId,
                                                duration=muteDuration)
                fightResultStr += f'获得了{muteDuration}秒的口球！'
            else:
                msgId = info['imgMsgId'] if isAdult else info['commandMsgId']
                await session.bot.set_msg_emoji_like(message_id=msgId, emoji_id=128074)
                fightResultStr += f'无法被口球，获得了除草器的一拳！'
            await session.send(f'[CQ:reply,id={session.ctx["message_id"]}]{checkResultStr}\n{fightResultStr}')
        else:
            await session.send(f'[CQ:reply,id={session.ctx["message_id"]}]{checkResultStr}')
        timeUpdater('nsfw', session.ctx.get('group_id', 0), userId)
    if info['type'] == 'nailong':
        await session.send("正在启动奶龙决斗……")
        checkResultStr, nailongScore = await nailongChecker(info['imgUrl'])
        if nailongScore is not None:
            isNailong = nailongScore > 50
            targetId = info['sender'] if isNailong else userId
            fightResultStr = (f'决斗成功！图片发送者' if isNailong else '决斗失败！检测者')
            canBanTarget = await checkBanAvailable(targetId, session.ctx['group_id'])
            if canBanTarget:
                muteDuration = int(abs(nailongScore - 50) * 40)
                await session.bot.set_group_ban(group_id=session.ctx['group_id'], user_id=targetId,
                                                duration=muteDuration)
                fightResultStr += f'获得了{muteDuration}秒的口球！'
            else:
                msgId = info['imgMsgId'] if isNailong else info['commandMsgId']
                await session.bot.set_msg_emoji_like(message_id=msgId, emoji_id=128074)
                fightResultStr += f'无法被口球，获得了除草器的一拳！'
            await session.send(f'[CQ:reply,id={session.ctx["message_id"]}]{checkResultStr}\n{fightResultStr}')
        else:
            await session.send(f'[CQ:reply,id={session.ctx["message_id"]}]{checkResultStr}')
        timeUpdater('nailong', session.ctx.get('group_id', 0), userId)
    del confirmations[userId]
    return


def timeCheck(command: str, ctx: dict) -> (bool, str):
    # 目前仅对SYSU大群进行timeCheck
    if 'group_id' not in ctx or ctx['group_id'] != config['group']['sysu']:
        return True, None

    command = command.replace('#', '')
    key = f'{ctx["user_id"]}_{command}'
    if key in lastUsedTime:
        nowTime = int(time.time())
        endTime = lastUsedTime[key] + 3 * 3600
        if nowTime < endTime:
            timeStrf = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(endTime))
            sign = f'冷却时间还没结束，请在{timeStrf}以后再来。'
            return False, sign
    return True, None


def timeUpdater(command: str, groupId: int, userId: int):
    global lastUsedTime
    if groupId != config['group']['sysu']:
        return
    command = command.replace('#', '')
    key = f'{userId}_{command}'
    lastUsedTime[key] = int(time.time())


async def nsfwChecker(imgUrl: str) -> [str, dict]:
    moderateContentApiKey = config['web']['moderateContent']['key']
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(imgUrl)
            image = Image.open(BytesIO(response.content))
            image = image.resize((600, 600), Image.LANCZOS)
            buffer = BytesIO()
            image.save(buffer, format='WEBP', quality=80)
            buffer.seek(0)

            files = {'file': ('image.webp', buffer, 'image/webp')}
            data = {'key': moderateContentApiKey}
            r = await client.post('https://api.moderatecontent.com/moderate/', data=data, files=files)
            result = r.json()
            print(f'NSFW检测结果：{result}')

            if 'predictions' not in result:
                return f'API没有返回检测结果，请稍后再来…_φ(･ω･` )\n{result.get("error")}', None
            else:
                outputStr = '检测结果：\n' + '\n'.join([f'{k} {v:.4f}' for k, v in result['predictions'].items()])
                return outputStr, result['predictions']
    except Exception as e:
        print(f"处理图片失败 {imgUrl}: {e}")
        return f'检测失败了…_φ(･ω･` )', None


async def nailongChecker(imgUrl: str) -> [str, float]:
    if nailongModel is None:
        return '奶龙模型未加载，暂无法使用…_φ(･ω･` )', None
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(imgUrl, timeout=25) as response:
                if response.status == 200:
                    content = await response.read()
                    img = Image.open(BytesIO(content)).convert('RGB')
                    img_tensor = img_transform(img).unsqueeze(0)

                    with torch.no_grad():
                        img_tensor = img_tensor.to(device)
                        outputs = nailongModel(img_tensor)
                        prob = nn.Softmax(dim=1)(outputs)
                        result = float(prob[0, 1]) * 100

                    return f'奶龙指数：{result:.4f}', result
    except Exception as e:
        print(f"处理图片失败 {imgUrl}: {e}")
        return f'检测失败了…_φ(･ω･` )', None
