import re
import json
import httpx
import urllib
from lxml import etree
from PicImageSearch import Network, SauceNAO
from kusa_base import config
from nonebot import on_command, CommandSession
from nonebot.command.argfilter.extractors import extract_image_urls

proxy = config['web']['proxy']
saucenaoApiKey = config['web']['saucenao']['key']
generalHeader = {
    "sec-ch-ua": '"Chromium";v="104", " Not A;Brand";v="99", "Google Chrome";v="104"',
    "user-agent": config['web']['userAgent']
}
# TODO: 交互不友好，等待调整


@on_command(name='saucenao', only_to_me=False)
async def saucenaoSearch(session: CommandSession):
    imgCq = await session.aget(prompt='已启用saucenao搜索，请发送图片')
    if imgCq is None or '[CQ:image' not in imgCq:
        await session.send("非图片，取消saucenao搜索")
        return
    imgUrl = extract_image_urls(imgCq)[0]
    resList = await saucenaoBuildResult(imgUrl)
    if len(resList) == 0:
        await session.send("未搜索到相似度高的结果")
        return
    resStr = ""
    for single in resList:
        resStr += f"{single['title']}(Similarity:{single['similarity']}%)\n{single['url']}\n\n"
    await session.send(resStr[:-2])


@on_command(name='yandex', only_to_me=False)
async def yandexSearch(session: CommandSession):
    imgCq = await session.aget(prompt='已启用yandex图片搜索，请发送图片')
    if imgCq is None or '[CQ:image' not in imgCq:
        await session.send("非图片，取消yandex搜索")
        return
    imgUrl = extract_image_urls(imgCq)[0]
    resList = await yandexBuildResult(imgUrl)
    if len(resList) == 0:
        await session.send("未搜索到结果")
        return
    resStr = ""
    for single in resList:
        resStr += f"{single['title']}\nURL:{single['url']}\nImgURL:{single['thumbnail']}\n\n"
    await session.send(resStr[:-2])


@on_command(name='google', only_to_me=False)
async def googleSearch(session: CommandSession):
    imgCq = await session.aget(prompt='已启用google图片搜索，请发送图片')
    if imgCq is None or '[CQ:image' not in imgCq:
        await session.send("非图片，取消google搜索")
        return
    imgUrl = extract_image_urls(imgCq)[0]
    resList = await googleBuildResult(imgUrl)
    if len(resList) == 0:
        await session.send("未搜索到结果")
        return
    resStr = ""
    for single in resList:
        resStr += f"{single['title']}\nURL:{single['url']}\nImgURL:{single['thumbnail']}\n\n"
    await session.send(resStr[:-2])


@on_command(name='picurl', only_to_me=False)
async def picUrlGet(session: CommandSession):
    imgCq = await session.aget(prompt='请发送图片')
    if imgCq is None or '[CQ:image' not in imgCq:
        await session.send("非图片，取消图片链接获取")
        return
    imgUrls = extract_image_urls(imgCq)
    await session.send('\n'.join(imgUrls))


async def saucenaoBuildResult(baseImgUrl, resultNum=5, minSim=75):
    resList = []
    try:
        async with Network(proxies=proxy, timeout=50) as client:
            saucenao = SauceNAO(client=client, api_key=saucenaoApiKey, numres=resultNum)
            saucenao_result = await saucenao.search(url=baseImgUrl)

            for single in saucenao_result.raw:
                if single.similarity < minSim or single.url == "" or single.thumbnail == "":
                    continue
                sin_di = {
                    "title": single.title,  # 标题
                    "thumbnail": single.thumbnail,  # 缩略图url
                    "url": urllib.parse.unquote(single.url),
                    "similarity": single.similarity,
                }
                resList.append(sin_di)
            return resList
    except IndexError as e:
        return []


async def yandexBuildResult(baseImgUrl, resultNum=4):
    try:
        yandexUrl = f"https://yandex.com/images/search"
        data = {
            "rpt": "imageview",
            "url": baseImgUrl,
        }
        resList = []

        client = httpx.AsyncClient(proxies=proxy)
        yandexPage = await client.get(url=yandexUrl, params=data, headers=generalHeader, timeout=50)
        yandexHtml = etree.HTML(yandexPage.text)
        InfoJSON = yandexHtml.xpath('//*[@class="cbir-section cbir-section_name_sites"]/div/@data-state')[0]
        result_dict = json.loads(InfoJSON)
        for single in result_dict["sites"][:resultNum]:
            sin_di = {
                "title": single["title"],  # 标题
                "thumbnail": "https:" + single["thumb"]["url"],  # 预览图url
                "url": urllib.parse.unquote(single["url"]),  # 来源网址
                "description": single["description"],  # 描述
                "domain": single["domain"],  # 来源网站域名
            }
            resList.append(sin_di)
        return resList
    except Exception as e:
        return []


async def googleBuildResult(baseImgUrl, result_num=4):
    google_header = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,"
                  "application/signed-exchange;v=b3;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/113.0.0.0 Safari/537.36",
        "Cookie": "",
    }
    post_headers = {
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
        "Sec-Ch-Ua": '"Google Chrome";v="113", "Chromium";v="113", "Not-A.Brand";v="24"',
        "Referer": "https://lens.google.com/",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/113.0.0.0 Safari/537.36",
    }
    resList = []

    try:
        params = {"url": baseImgUrl}
        uploadUrl = f"https://lens.google.com/uploadbyurl"
        client = httpx.AsyncClient(proxies=proxy)
        google_lens_text = (await client.get(uploadUrl, params=params, headers=google_header, follow_redirects=True, timeout=100)).text
        req_tex = re.findall(r"var AF_dataServiceRequests = (.+?); var AF_initDataChunkQueue", google_lens_text)
        if req_tex:
            ds1 = re.findall(r"'ds:1' : (.*)}", req_tex[0])
            if ds1:
                ds = ds1[0]
                ds = (
                    ds.replace("id:", '"id":')
                    .replace("request:", '"request":')
                    .replace("'", '"')
                    .replace("[4,true],null,null,[],null", 'null,null,null,[],"000000"')
                    .replace("true", "1")
                    .replace("false", "0")
                    .replace("Asia/Kuching", "Asia/Hong_Kong")
                    .replace("[5,6,7,2]", "[5,6,2]")
                    .replace("[],[null,5],null,[5]", "[null,null],[null,5],null,[5],[]")
                )
                dic = json.loads(ds)
                try:
                    dic["request"][1][-1].remove(1)
                except Exception as e:
                    pass
                dic["request"][-3].append(dic["request"][1])

        qest = [[[dic["id"], json.dumps(dic["request"]), None, "generic"]]]
        postDate = {"f.req": json.dumps(qest)}
        lensWebStandaloneUrl = "https://lens.google.com/_/LensWebStandaloneUi/data/batchexecute?hl=zh-CN"
        te = await client.post(url=lensWebStandaloneUrl, data=postDate, headers=post_headers)

        res_j = json.loads(te.text.replace(r")]}'", "", 1))
        search_result = json.loads(res_j[0][2])[1][0][1][8][20][0][0]

        for singleDiv in search_result[:result_num]:
            try:
                sin_di = {
                    "title": singleDiv[4],
                    "thumbnail": singleDiv[0][0],
                    "url": singleDiv[2][2][2],
                    "source": "Google",
                    "domain": singleDiv[1][2],
                }
            except IndexError:
                continue
            resList.append(sin_di)
        return resList

    except Exception as e:
        return []
