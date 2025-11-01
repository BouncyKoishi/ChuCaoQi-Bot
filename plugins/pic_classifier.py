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
from utils import extractImgUrls

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
async def _(session: NLPSession):
    if session.ctx['message'][0].type != 'reply':
        return

    global confirmations
    strippedText = session.ctx['message'][-1].data.get('text', '').strip()
    replyId = str(session.ctx['message'][0].data['id'])
    if not strippedText.startswith('#') and replyId not in confirmations:
        return

    if replyId in confirmations and confirmations[replyId]['triggeredBy'] == session.ctx['user_id']:
        info = confirmations[replyId]
        if info['type'] == 'nsfw':
            await session.send("正在启动黑暗决斗……")
            checkResultStr, resultDict = await nsfwChecker(confirmations[replyId]['imgUrl'])
            if resultDict:
                adultScore = resultDict.get('adult', 0)
                everyoneScore = resultDict.get('everyone', 0)
                isAdult = adultScore > everyoneScore
                targetId = confirmations[replyId]['owner'] if isAdult else confirmations[replyId]['triggeredBy']
                muteDuration = int(max(adultScore, everyoneScore) * 10)
                await session.bot.set_group_ban(group_id=session.ctx['group_id'], user_id=targetId,
                                                duration=muteDuration)
                fightResultStr = f'决斗成功！图片发送者' if isAdult else '决斗失败！检测者' + f'获得了{muteDuration}秒的口球！'
                await session.send(f'[CQ:reply,id={session.ctx["message_id"]}]{checkResultStr}\n\n{fightResultStr}')
            else:
                await session.send(f'[CQ:reply,id={session.ctx["message_id"]}]{checkResultStr}')
        if info['type'] == 'nailong':
            await session.send("正在启动奶龙决斗……")
            checkResultStr, nailongScore = await nailongChecker(confirmations[replyId]['imgUrl'])
            if nailongScore is not None:
                isNailong = nailongScore > 0.5
                targetId = confirmations[replyId]['owner'] if isNailong else confirmations[replyId]['triggeredBy']
                muteDuration = int(abs(nailongScore - 50) * 20)
                await session.bot.set_group_ban(group_id=session.ctx['group_id'], user_id=targetId,
                                                duration=muteDuration)
                fightResultStr = f'决斗成功！图片发送者' if isNailong else '决斗失败！检测者' + f'获得了{muteDuration}秒的口球！'
                await session.send(f'[CQ:reply,id={session.ctx["message_id"]}]{checkResultStr}\n\n{fightResultStr}')
            else:
                await session.send(f'[CQ:reply,id={session.ctx["message_id"]}]{checkResultStr}')
        del confirmations[replyId]
        return
    if strippedText in ['#nsfw', '#nailong']:
        replyMessageCtx = await session.bot.get_msg(message_id=replyId)
        imgUrls = extractImgUrls(replyMessageCtx['message'])
        if not imgUrls or len(imgUrls) == 0:
            return
        isNsfw = strippedText == '#nsfw'
        if session.ctx['user_id'] != replyMessageCtx['user_id']:
            nsfwMsg = f"你触发了黑暗决斗。\n如果这张图片是色图，发图的人将会被口球，否则你会被口球。口球的秒数等于adult/everyone的分值×10。\n回复此消息并输入y以继续检测。"
            nailongMsg = "你触发了奶龙决斗。\n如果这张图片的奶龙指数大于0.5，发图的人将会被口球。否则你会被口球。口球的秒数等于abs(奶龙指数-50)×20。\n回复此消息并输入y以继续检测。"
            sendMsgInfo = await session.send(
                f'[CQ:reply,id={session.ctx["message_id"]}]{nsfwMsg if isNsfw else nailongMsg}')
            confirmations[str(sendMsgInfo['message_id'])] = {'triggeredBy': session.ctx['user_id'],
                                                             'owner': replyMessageCtx['user_id'],
                                                             'imgUrl': imgUrls[0], 'type': strippedText[1:]}
            return
        await session.send("正在检测……")
        checkResultStr, _ = await nsfwChecker(imgUrls[0]) if isNsfw else await nailongChecker(imgUrls[0])
        await session.send(f'[CQ:reply,id={session.ctx["message_id"]}]{checkResultStr}')


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



# @on_natural_language(only_to_me=False, allow_empty_message=False)
# async def handle_function(session: NLPSession):
#     groupId = session.event.group_id
#     strippedArg = session.msg
#
#     if groupId != config['group']['main']:
#         return
#     if '[CQ:image' not in strippedArg:
#         return
#
#     imageUrls = extractImgUrls(strippedArg)
#     if not imageUrls:
#         return
#     results = await nailongCheckUrlsAsync(imageUrls)
#     output = ""
#     for result in results.values():
#         output += f"奶龙指数：{result:.8f}\n"
#     print(results)
#     await session.send(output[:-1])

