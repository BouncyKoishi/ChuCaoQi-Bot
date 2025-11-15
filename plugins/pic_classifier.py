import random
import httpx
import aiohttp
import torch
from io import BytesIO
from PIL import Image
from torch import nn
from torchsampler.imbalanced import torchvision
from torchvision import transforms
from nonebot import on_natural_language, NLPSession
from kusa_base import config
from utils import extractImgUrls, checkBanAvailable

nailongModel = None
modelPath = './model_best.pth'
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

confirmations = {}


@on_natural_language(keywords=None, only_to_me=False)
async def picClassifierReplyNLP(session: NLPSession):
    if session.ctx['message'][0].type != 'reply':
        return

    global confirmations
    strippedText = session.ctx['message'][-1].data.get('text', '').strip()
    replyId = str(session.ctx['message'][0].data['id'])
    if not strippedText.startswith('#'):
        return

    if strippedText in ['#nsfw', '#nailong']:
        replyMessageCtx = await session.bot.get_msg(message_id=replyId)
        imgUrls = extractImgUrls(replyMessageCtx['message'])
        if not imgUrls or len(imgUrls) == 0:
            return
        isNsfw = strippedText == '#nsfw'
        duelRand = random.random()
        userId, targetId = session.ctx['user_id'], replyMessageCtx['user_id']
        if userId != replyMessageCtx['user_id'] and duelRand < 1/8:
            canBanSender = await checkBanAvailable(targetId, session.ctx['group_id'])
            canBanChecker = await checkBanAvailable(userId, session.ctx['group_id'])
            if canBanSender and canBanChecker:
                nsfwMsg = f"你触发了黑暗决斗。\n如果这张图片是色图，发图的人将会被口球，否则你会被口球。口球的秒数等于adult/everyone的分值×10。\n输入y继续检测，输入其他表示取消。"
                nailongMsg = "你触发了奶龙决斗。\n如果这张图片的奶龙指数大于50，发图的人将会被口球。否则你会被口球。口球的秒数等于abs(奶龙指数-50)×40。\n输入y继续检测，输入其他表示取消。"
                await session.send(f'[CQ:reply,id={session.ctx["message_id"]}]{nsfwMsg if isNsfw else nailongMsg}')
                confirmations[userId] = {'sender': replyMessageCtx['user_id'], 'imgUrl': imgUrls[0], 'type': strippedText[1:]}
            return
        await session.send("正在检测……")
        checkResultStr, _ = await nsfwChecker(imgUrls[0]) if isNsfw else await nailongChecker(imgUrls[0])
        await session.send(f'[CQ:reply,id={session.ctx["message_id"]}]{checkResultStr}')


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
            muteDuration = int(max(adultScore, everyoneScore) * 10)
            await session.bot.set_group_ban(group_id=session.ctx['group_id'], user_id=targetId,
                                            duration=muteDuration)
            fightResultStr = (f'决斗成功！图片发送者' if isAdult else '决斗失败！检测者') + f'获得了{muteDuration}秒的口球！'
            await session.send(f'[CQ:reply,id={session.ctx["message_id"]}]{checkResultStr}\n{fightResultStr}')
        else:
            await session.send(f'[CQ:reply,id={session.ctx["message_id"]}]{checkResultStr}')
    if info['type'] == 'nailong':
        await session.send("正在启动奶龙决斗……")
        checkResultStr, nailongScore = await nailongChecker(info['imgUrl'])
        if nailongScore is not None:
            isNailong = nailongScore > 50
            targetId = info['sender'] if isNailong else userId
            muteDuration = int(abs(nailongScore - 50) * 40)
            await session.bot.set_group_ban(group_id=session.ctx['group_id'], user_id=targetId,
                                            duration=muteDuration)
            fightResultStr = (f'决斗成功！图片发送者' if isNailong else '决斗失败！检测者') + f'获得了{muteDuration}秒的口球！'
            await session.send(f'[CQ:reply,id={session.ctx["message_id"]}]{checkResultStr}\n{fightResultStr}')
        else:
            await session.send(f'[CQ:reply,id={session.ctx["message_id"]}]{checkResultStr}')
    del confirmations[userId]
    return


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


