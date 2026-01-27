import traceback
from io import BytesIO

import PIL
import httpx
import urllib
import asyncio
from lxml import etree
from PicImageSearch import Network, SauceNAO, Ascii2D, Yandex
from PIL import Image, ImageFont, ImageDraw, ImageFilter

from utils import imgLocalPathToBase64, extractImgUrls
from kusa_base import config
from decorator import on_reply_command
from nonebot import on_command, CommandSession
from nonebot import on_natural_language, NLPSession

proxy = config['web']['proxy']
saucenaoApiKey = config['web']['saucenao']['key']
fontPath = config['basePath'] + r'\font'
generalHeader = {
    "sec-ch-ua": '"Chromium";v="104", " Not A;Brand";v="99", "Google Chrome";v="104"',
    "user-agent": config['web']['userAgent']
}
picSearchResults = {}


@on_command(name='搜图', aliases='picsearch', only_to_me=False)
async def _(session: CommandSession):
    global picSearchResults
    imgCq = await session.aget(prompt='已启用图片搜索，请发送图片')
    imgUrls = extractImgUrls(imgCq)
    if not imgUrls:
        await session.send("非图片，取消搜图")
        return
    await session.send("正在搜索……")
    resultDict = await getSearchResult(imgUrls[0])
    if not resultDict or not resultDict["info"]:
        await session.send('没有搜索到结果^ ^')
        return
    sendMsgInfo = await session.send(imgLocalPathToBase64('picsearch.jpg'))
    picSearchResults[str(sendMsgInfo['message_id'])] = resultDict['info']


async def getSearchResult(imgUrl):
    async with httpx.AsyncClient() as client:
        search = ImgExploration(pic_url=imgUrl, client=client, proxies=proxy, header=generalHeader)
        await search.doSearch()
    return search.getResultDict()


@on_command(name='saucenao', aliases=('yandex', 'google'), only_to_me=False)
async def _(session: CommandSession):
    await session.send('搜图指令已整合，请使用“!搜图”或“!picsearch”')


@on_command(name='picurl', only_to_me=False)
async def picUrlGet(session: CommandSession):
    imgCq = await session.aget(prompt='请发送图片')
    imgUrls = extractImgUrls(imgCq)
    if not imgUrls:
        await session.send("非图片，取消图片链接获取")
        return
    await session.send('\n'.join(imgUrls))


@on_natural_language(keywords=None, only_to_me=False)
@on_reply_command(commands=['#picurl'])
async def picUrlNLP(session: NLPSession, replyMessageCtx):
    imgUrls = extractImgUrls(replyMessageCtx['message'])
    if not imgUrls:
        return
    await session.send('\n'.join(imgUrls))


@on_natural_language(keywords=None, only_to_me=False)
@on_reply_command(commands=['#picsearch', '#搜图'])
async def picSearchNLP(session: NLPSession, replyMessageCtx):
    global picSearchResults

    imgUrls = extractImgUrls(replyMessageCtx['message'])
    if not imgUrls:
        return
    await session.send("正在搜索……")
    resultDict = await getSearchResult(imgUrls[0])
    if not resultDict or not resultDict["info"]:
        await session.send('没有搜索到结果^ ^')
        return
    sendMsgInfo = await session.send(imgLocalPathToBase64('picsearch.jpg'))
    picSearchResults[str(sendMsgInfo['message_id'])] = resultDict['info']


@on_natural_language(keywords=None, only_to_me=False)
async def picSearchContinueNLP(session: NLPSession):
    if session.ctx['message'][0].type != 'reply':
        return

    strippedText = session.ctx['message'][-1].data.get('text', '').strip()
    replyId = str(session.ctx['message'][0].data['id'])
    isRecordedReply = replyId in picSearchResults
    if not strippedText.startswith('#') and not isRecordedReply:
        return

    if replyId in picSearchResults:
        resultDict = picSearchResults[replyId]
        try:
            args = list(set(map(int, strippedText.split())))
            args = [arg for arg in args if 1 <= arg <= len(resultDict)]
            msg = "\n".join(f"{index} - {resultDict[index - 1]['url']}" for index in args)
            await session.send(drawTextToImage(msg) if msg else "未找到对应图片链接")
        except (IndexError, ValueError):
            await session.send("未找到对应图片链接, 请检查输入是否正确")
            return


def drawTextToImage(text: str):
    splitText = text.split('\n')
    fontSize, splitSize = 20, 15
    width = max([len(i) for i in splitText]) * int(fontSize * 0.6) + 50
    height = len(splitText) * fontSize + (len(splitText) - 1) * splitSize + 50

    img = Image.new('RGB', (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype(rf"{fontPath}\HarmonyOS_Sans_SC_Regular.ttf", fontSize)
    for i, line in enumerate(splitText):
        y = 25 + i * fontSize + i * splitSize
        draw.text((25, y), line, font=font, fill=(0, 0, 0))

    img.save("picsearchUrl.jpg", format="JPEG", quality=95)
    return imgLocalPathToBase64('picsearchUrl.jpg')


class ImgExploration:
    def __init__(self, pic_url, client: httpx.AsyncClient, proxies, header):
        self.__result_info = None
        self.__picNinfo = None
        self.client = client
        self.__proxy = proxies
        self.__pic_url = pic_url
        self.__generalHeader = header
        self.setFont(big_size=25, normal_size=20, small_size=15)

    def setFont(self, big_size: int, normal_size: int, small_size: int):
        self.__font_b_size = big_size
        self.__font_b = ImageFont.truetype(rf"{fontPath}\HarmonyOS_Sans_SC_Regular.ttf", big_size)
        self.__font_n = ImageFont.truetype(rf"{fontPath}\HarmonyOS_Sans_SC_Bold.ttf", normal_size)
        self.__font_s = ImageFont.truetype(rf"{fontPath}\HarmonyOS_Sans_SC_Light.ttf", small_size)

    @staticmethod
    async def ImageBatchDownload(urls: list, client: httpx.AsyncClient) -> list:
        tasks = [asyncio.create_task(client.get(url)) for url in urls]
        return [(await task).content for task in tasks]

    async def __draw(self) -> bytes:
        try:
            font_size = self.__font_b_size
            font = self.__font_b
            font2 = self.__font_n
            font3 = self.__font_s
            num = len(self.__result_info)
            width = 900
            height = 200
            total_height = height * num if num != 0 else 10
            line_width = 2
            line_fill = (200, 200, 200)
            text_x = 300
            img = Image.new(mode="RGB", size=(width, total_height + 75), color=(255, 255, 255))

            draw = ImageDraw.Draw(img)
            margin = 20
            for i in range(1, num):
                draw.line(
                    (margin, i * height, width - margin, i * height),
                    fill=line_fill,
                    width=line_width,
                )

            vernier = 0
            seat = 0

            for single in self.__result_info:
                seat += 1

                if "thumbnail_bytes" in single:
                    thumbnail = single["thumbnail_bytes"]
                    try:
                        thumbnail = Image.open(fp=BytesIO(thumbnail)).convert("RGB")
                    except PIL.UnidentifiedImageError:
                        thumbnail = Image.new(mode="RGB", size=(200, 200), color=(255, 255, 255))

                    thumbnail = thumbnail.resize(
                        (int((height - 2 * margin) * thumbnail.width / thumbnail.height), height - 2 * margin))
                    if single["source"] == "ascii2d":
                        thumbnail = thumbnail.filter(ImageFilter.GaussianBlur(radius=3))

                    if thumbnail.width > text_x - 2 * margin:
                        thumbnail = thumbnail.crop((0, 0, text_x - 2 * margin, thumbnail.height))
                        img.paste(im=thumbnail, box=(margin, vernier + margin))
                    else:
                        img.paste(im=thumbnail, box=(text_x - thumbnail.width - margin, vernier + margin))

                text_ver = 2 * margin
                draw.text(
                    xy=(width - margin, vernier + 10),
                    text=f"NO.{seat} from {single['source']}",
                    fill=(150, 150, 150),
                    font=font2,
                    anchor="ra",
                )

                if single["title"]:
                    text = single["title"].replace("\n", "")
                    draw.text(xy=(text_x, vernier + text_ver), text="Title: ", fill=(160, 160, 160), font=font,
                              anchor="la")
                    draw.text(xy=(text_x + 60, vernier + text_ver),
                              text=f"{text[:20]}{'...' if len(text) >= 20 else ''}", fill=(0, 0, 0), font=font,
                              anchor="la")
                    text_ver = text_ver + font_size + margin / 2

                if ("similarity" in single) and single["similarity"]:  # saucenao
                    text = single["similarity"]
                    draw.text(xy=(text_x, vernier + text_ver), text="similarity: ", fill=(160, 160, 160), font=font,
                              anchor="la")
                    draw.text(xy=(text_x + 115, vernier + text_ver), text=f"{text}", fill=(0, 0, 0), font=font,
                              anchor="la")
                    text_ver = text_ver + font_size + margin / 2

                if ("description" in single) and single["description"]:
                    text = single["description"]
                    draw.text(xy=(text_x, vernier + text_ver), text=f"{text[:30]}{'...' if len(text) >= 30 else ''}",
                              fill=(0, 0, 0), font=font, anchor="la")
                    text_ver = text_ver + font_size + margin / 2

                if ("domain" in single) and single["domain"]:  # Yandex
                    text = single["domain"]
                    draw.text(xy=(text_x, vernier + text_ver), text="Source: ", fill=(160, 160, 160), font=font,
                              anchor="la")
                    draw.text(xy=(text_x + 86, vernier + text_ver), text=f"{text}", fill=(0, 0, 0), font=font,
                              anchor="la")
                    text_ver = text_ver + font_size + margin / 2

                if single["url"]:
                    url = single["url"]
                    draw.text(xy=(text_x, vernier + text_ver), text=f"{url[:80]}{'......' if len(url) >= 80 else ''}",
                              fill=(100, 100, 100), font=font3, anchor="la")
                vernier += height

            bottom_text = "若需要提取url，请回复此消息，在回复中输入[图片编号] ，如：1 2"
            draw.text(xy=(width // 2, total_height + 25), text=bottom_text,
                      fill=(0, 0, 0), font=font, anchor="mm",
                      )

            save = BytesIO()
            img.save("picsearch.jpg", format="JPEG", quality=95)
            return save.getvalue()
        except Exception as e:
            raise e

    async def __saucenao_build_result(self, result_num=5, minSim=65) -> list:
        resList = []
        try:
            async with Network(proxies=self.__proxy, timeout=100) as client:
                saucenao = SauceNAO(client=client, api_key=saucenaoApiKey, numres=result_num)
                saucenao_result = await saucenao.search(url=self.__pic_url)

                thumbnail_urls = []
                for single in saucenao_result.raw:
                    if single.similarity < minSim or single.url == "" or single.thumbnail == "":
                        continue
                    thumbnail_urls.append(single.thumbnail)
                thumbnail_bytes = await self.ImageBatchDownload(thumbnail_urls, self.client)
                i = 0
                for single in saucenao_result.raw:
                    if single.similarity < minSim or single.url == "" or single.thumbnail == "":
                        continue
                    sin_di = {
                        "title": single.title,  # 标题
                        "thumbnail": single.thumbnail,  # 缩略图url
                        "url": urllib.parse.unquote(single.url),
                        "similarity": single.similarity,
                        "source": "saucenao",
                        "thumbnail_bytes": thumbnail_bytes[i],
                    }
                    i += 1
                    resList.append(sin_di)
                return resList
        except IndexError as e:
            print(f"saucenao: {e}")
            return []
        finally:
            print(f"saucenao result:{len(resList)}")
            return resList

    def __ascii2d_get_external_url(self, rawHtml):
        rawHtml = str(rawHtml)
        external_url_li = etree.HTML(rawHtml).xpath('//div[@class="external"]/a[1]/@href')
        if external_url_li:
            return external_url_li[0]  # 可能的手动登记结果:list
        else:
            return False

    async def __ascii2d_build_result(self, sh_num: int = 1, tz_num: int = 1) -> list:
        """
        Parameters
        ----------
            * sh_num : 色和搜索获取结果数量
            * tz_num : 特征搜索获取结果数量

        """
        result_li = []
        try:
            async with Network(proxies=self.__proxy, timeout=100) as client:
                ascii2d_sh = Ascii2D(client=client, bovw=False)
                ascii2d_tz = Ascii2D(client=client, bovw=True)

                ascii2d_sh_result = await asyncio.create_task(ascii2d_sh.search(url=self.__pic_url))
                ascii2d_tz_result = await asyncio.create_task(ascii2d_tz.search(url=self.__pic_url))

                thumbnail_urls = []
                for single in ascii2d_tz_result.raw[0:tz_num] + ascii2d_sh_result.raw[0:sh_num]:
                    external_url_li = self.__ascii2d_get_external_url(single.origin)
                    if not external_url_li and not single.url:
                        continue
                    elif single.url:
                        url = single.url
                    else:
                        url = external_url_li
                    sin_di = {
                        "title": single.title,
                        "thumbnail": single.thumbnail,
                        "url": urllib.parse.unquote(url),
                        "source": "ascii2d",
                    }
                    thumbnail_urls.append(single.thumbnail)
                    result_li.append(sin_di)
                thumbnail_bytes = await self.ImageBatchDownload(thumbnail_urls, self.client)
                for i, single in enumerate(result_li):
                    single["thumbnail_bytes"] = thumbnail_bytes[i]
        except Exception as e:
            print(f"ascii2d: {e}")
            return []
        finally:
            print(f"ascii2d result:{len(result_li)}")
            return result_li

    async def __yandex_build_result(self, result_num=4) -> list:
        """
        Parameter:
        ---------
            * result_num : 需要的结果数量
        """
        result_li = []
        try:
            async with Network(proxies=self.__proxy, timeout=100) as client:
                yandex = Yandex(client=client)
                yandex_result = await yandex.search(url=self.__pic_url)
                thumbnail_urls = []
                for single in yandex_result.raw[:result_num]:
                    if single.url == "" or single.thumbnail == "":
                        continue
                    thumbnail_urls.append(single.thumbnail)
                thumbnail_bytes = await self.ImageBatchDownload(thumbnail_urls, self.client)
                i = 0
                for single in yandex_result.raw[:result_num]:
                    if single.url == "" or single.thumbnail == "":
                        continue
                    sin_di = {
                        "title": single.title,
                        "thumbnail": single.thumbnail,
                        "url": urllib.parse.unquote(single.url),
                        "domain": single.source,
                        "source": "Yandex",
                        "thumbnail_bytes": thumbnail_bytes[i],
                    }
                    i += 1
                    result_li.append(sin_di)
        except Exception as e:
            print(f"yandex: {e}")
            traceback.print_exc()
            return []
        finally:
            print(f"yandex result:{len(result_li)}")
            return result_li

    async def doSearch(self):
        task_saucenao = asyncio.create_task(self.__saucenao_build_result())
        task_yandex = asyncio.create_task(self.__yandex_build_result())
        task_ascii2d = asyncio.create_task(self.__ascii2d_build_result())

        self.__result_info = (await task_saucenao) + (await task_yandex) + (await task_ascii2d)
        result_pic = await self.__draw()

        self.__picNinfo = {
            "pic": result_pic,
            "info": self.__result_info,
        }

    def getResultDict(self):
        """
        Returns
        ----------
        {
            "pic": bytes,
            "info": list,
        }
        """
        return self.__picNinfo
