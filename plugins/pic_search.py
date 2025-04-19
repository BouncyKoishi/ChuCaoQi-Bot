import base64
import re
import json
import traceback
from io import BytesIO
from typing import Dict

import PIL
import httpx
import urllib
import asyncio
from lxml import etree
from PicImageSearch import Network, SauceNAO, Ascii2D
from PIL import Image, ImageFont, ImageDraw, ImageFilter

from utils import imgLocalPathToBase64, extractImgUrls
from kusa_base import config
from nonebot import on_command, CommandSession
from nonebot import on_natural_language, NLPSession

proxy = config['web']['proxy']
saucenaoApiKey = config['web']['saucenao']['key']
googleCookiesFilepath = config['web']['google']['cookiesPath']
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
    async with httpx.AsyncClient(proxies=proxy) as client:
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
async def _(session: NLPSession):
    if session.ctx['message'][0].type != 'reply':
        return

    global picSearchResults
    strippedText = session.ctx['message'][-1].data['text'].strip()
    replyId = session.ctx['message'][0].data['id']
    if not strippedText.startswith('#') and str(replyId) not in picSearchResults:
        return

    replyMessageCtx = await session.bot.get_msg(message_id=replyId)
    # print(replyId, replyMessageCtx)

    if str(replyId) in picSearchResults:
        resultDict = picSearchResults[str(replyId)]
        try:
            args = list(set(map(int, strippedText.split())))
            args = [arg for arg in args if 1 <= arg <= len(resultDict)]
            msg = "\n".join(f"{index} - {resultDict[index - 1]['url']}" for index in args)
            await session.send(drawTextToImage(msg) if msg else "未找到对应图片链接")
        except (IndexError, ValueError):
            await session.send("未找到对应图片链接, 请检查输入是否正确")
            return
    if strippedText == '#picurl':
        imgUrls = extractImgUrls(replyMessageCtx['message'])
        await session.send('\n'.join(imgUrls))
    if strippedText in ['#picsearch', '#搜图']:
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
        # print(picSearchResults.keys())
    if strippedText == '#nsfw':
        imgUrls = extractImgUrls(replyMessageCtx['message'])
        if not imgUrls:
            return
        await session.send("正在检测……")
        moderateContentApiKey = config['web']['moderateContent']['key']
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(imgUrls[0])
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
                    await session.send(
                        f'[CQ:reply,id={session.ctx["message_id"]}]API没有返回检测结果，请稍后再来…_φ(･ω･` )\n{result.get("error")}')
                else:
                    await session.send(
                        f'[CQ:reply,id={session.ctx["message_id"]}]检测结果：\n' + '\n'.join(
                            [f'{k} {v:.4f}' for k, v in result['predictions'].items()]))
        except Exception as e:
            await session.send(
                f'[CQ:reply,id={session.ctx["message_id"]}]检测失败了…_φ(･ω･` )\n{str(e)}')


def drawTextToImage(text: str):
    splitText = text.split('\n')
    fontSize, splitSize = 20, 15
    width = max([len(i) for i in splitText]) * int(fontSize * 0.6) + 50
    height = len(splitText) * fontSize + (len(splitText) - 1) * splitSize + 50

    img = Image.new('RGB', (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype("HarmonyOS_Sans_SC_Regular", fontSize)
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
        self.__google_cookies = Cookies(googleCookiesFilepath)
        self.setFont(big_size=25, normal_size=20, small_size=15)

    def setFont(self, big_size: int, normal_size: int, small_size: int):
        self.__font_b_size = big_size
        self.__font_b = ImageFont.truetype("HarmonyOS_Sans_SC_Regular", big_size)
        self.__font_n = ImageFont.truetype("HarmonyOS_Sans_SC_Bold", normal_size)
        self.__font_s = ImageFont.truetype("HarmonyOS_Sans_SC_Light", small_size)

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

    async def __saucenao_build_result(self, result_num=5, minSim=68) -> list:
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

    async def __google_build_result(self, result_num=4) -> list:
        google_header = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-encoding": "gzip, deflate, br, zstd:gzip, deflate, br, zstd",
            "accept-language": "zh-CN,zh-HK;q=0.9,zh;q=0.8,en-US;q=0.7,en;q=0.6:zh-CN,zh-HK;q=0.9,zh;q=0.8,en-US;q=0.7,en;q=0.6",
            "cache-control": "no-cache:no-cache",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36:Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        }
        resList = []
        try:
            params = {
                "url": self.__pic_url,
            }
            google_lens = await self.client.get(f"https://lens.google.com/uploadbyurl", params=params,
                                                headers=google_header, timeout=10,
                                                cookies=self.__google_cookies.cookies)
            self.__google_cookies.update(google_lens.headers)
            redirect_url = google_lens.headers.get("location")
            google_header["referer"] = str(google_lens.url)
            google_lens = await self.client.get(redirect_url, headers=google_header, timeout=10,
                                                cookies=self.__google_cookies.cookies)
            self.__google_cookies.update(google_lens.headers)
            google_lens_text = google_lens.text
            print("google_lens_text", google_lens_text)
            main_page = etree.HTML(google_lens_text)
            print("main_page", main_page)
            elements = main_page.xpath("//span[text()='查看完全匹配的结果']/ancestor::a[1]")
            print("elements", elements)
            if elements:
                href = "https://www.google.com" + elements[0].get("href")
                google_lens = await self.client.get(href, headers=google_header, timeout=50,
                                                    cookies=self.__google_cookies.cookies)
                full_match_page = etree.HTML(google_lens.text)
                print("full_match_page", full_match_page)
                id_base64_mapping = parseBase64Image(full_match_page)
                with open("Googlelens_test.html", "w+", encoding="utf-8") as file:
                    file.write(google_lens.text)
                res_items = full_match_page.xpath("//div[@id='search']/div/div/div")
                for item in res_items:
                    link = item.xpath(".//a")[0].get("href")
                    img_id = item.xpath(".//a//img")[0].get("id")
                    title = item.xpath(".//a/div/div[2]/div[1]/text()")[0]
                    img_base64 = id_base64_mapping[img_id] if img_id in id_base64_mapping.keys() else None
                    img_bytes = base64.b64decode(img_base64) if img_base64 else None
                    if img_bytes is not None:
                        sin_di = {
                            "title": title,
                            "thumbnail_bytes": img_bytes,
                            "url": link,
                            "source": "Google",
                        }
                        resList.append(sin_di)
            else:
                pass
            return resList
        except Exception as e:
            print(f"google: {e}")
            print(traceback.format_exc())
        finally:
            print(f"google result:{len(resList)}")
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
            yandexurl = f"https://yandex.com/images/search"
            data = {
                "rpt": "imageview",
                "url": self.__pic_url,
            }

            yandexPage = await self.client.get(url=yandexurl, params=data, headers=self.__generalHeader, timeout=50)
            # yandexPage可能会返回一个302重定向
            if yandexPage.has_redirect_location:
                redirectUrl = yandexPage.headers["location"]
                yandexPage = await self.client.get(url=redirectUrl, params=data, headers=self.__generalHeader,
                                                   timeout=50)
            yandexHtml = etree.HTML(yandexPage.text)
            InfoJSON = yandexHtml.xpath('//*[@class="cbir-section cbir-section_name_sites"]/div/@data-state')[0]
            result_dict = json.loads(InfoJSON)
            thumbnail_urls = []
            for single in result_dict["sites"][:result_num]:
                thumbnail_urls.append("https:" + single["thumb"]["url"])
            thumbnail_bytes = await self.ImageBatchDownload(thumbnail_urls, self.client)
            i = 0
            for single in result_dict["sites"][:result_num]:
                sin_di = {
                    "source": "Yandex",
                    "title": single["title"],  # 标题
                    "thumbnail": "https:" + single["thumb"]["url"],  # 预览图url
                    "url": urllib.parse.unquote(single["url"]),  # 来源网址
                    "description": single["description"],  # 描述
                    "domain": single["domain"],  # 来源网站域名
                    "thumbnail_bytes": thumbnail_bytes[i],
                }
                i += 1
                result_li.append(sin_di)
        except Exception as e:
            print(f"yandex: {e}")
        finally:
            print(f"yandex result:{len(result_li)}")
            return result_li

    async def doSearch(self):
        task_saucenao = asyncio.create_task(self.__saucenao_build_result())
        task_google = asyncio.create_task(self.__google_build_result())
        task_yandex = asyncio.create_task(self.__yandex_build_result())
        task_ascii2d = asyncio.create_task(self.__ascii2d_build_result())

        self.__result_info = (await task_saucenao) + (await task_google) + (await task_yandex) + (await task_ascii2d)
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


class Cookies:
    filepath: str
    cookies_json: list
    cookies: httpx.Cookies

    def __init__(self, filepath: str):
        self.filepath = filepath
        self.cookies_json = []
        self.cookies = httpx.Cookies()
        self.load_cookies()

    def load_cookies(self):
        with open(self.filepath, "r") as f:
            self.cookies_json = json.loads(f.read())
        for cookie in self.cookies_json:
            self.cookies.set(cookie["name"], cookie["value"], cookie["domain"])

    def update(self, response_headers: httpx.Headers):
        set_cookies = response_headers.get_list("set-cookie")
        if not set_cookies:
            return self.cookies
        new_cookies = httpx.Cookies()
        for cookie in self.cookies.jar:
            new_cookies.set(cookie.name, cookie.value, cookie.domain)
        for cookie_str in set_cookies:
            cookie_parts = cookie_str.split(";")
            if not cookie_parts:
                continue
            name_value = cookie_parts[0].strip().split("=", 1)
            if len(name_value) != 2:
                continue
            name, value = name_value
            domain = 'google.com'
            for part in cookie_parts[1:]:
                if part.strip().lower().startswith("domain="):
                    domain = part.split("=", 1)[1].strip()
                    break
            new_cookies.set(name, value, domain)
            for cookie in self.cookies_json:
                if cookie["name"] == name:
                    cookie = {"domain": domain, "name": name, "value": value}
        self.cookies = new_cookies
        self.save()

    def save(self):
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(self.cookies_json, f, ensure_ascii=False, indent=4)


def parseBase64Image(document: etree.Element) -> Dict[str, str]:
    """从HTML文档中解析id和对应的图片base64
    """
    res_dic = {}
    for script in document.xpath("//script[@nonce]"):
        func = script.xpath("./text()")
        func_text: str = func[0] if func and len(func) > 0 else ""
        id_match = re.search(r"\['(.*?)'\]", func_text)
        id = id_match.group(1) if id_match else None
        base64_match = re.search(r"data:image/jpeg;base64,(.*?)'", func_text)
        b64 = base64_match.group(1).replace(r"\x3d", "=") if base64_match else None
        if id != None and b64 != None:
            if "','" in id:
                for dimg in id.split("','"):
                    res_dic[dimg] = b64
            else:
                res_dic[id] = b64
    return res_dic
