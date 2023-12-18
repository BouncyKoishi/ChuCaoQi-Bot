import re
import json
from io import BytesIO

import PIL
import httpx
import urllib
import asyncio
from lxml import etree
from PicImageSearch import Network, SauceNAO, Ascii2D
from PIL import Image, ImageFont, ImageDraw, ImageFilter

from utils import getImgBase64
from kusa_base import config
from nonebot import on_command, CommandSession
from nonebot.command.argfilter.extractors import extract_image_urls

proxy = config['web']['proxy']
saucenaoApiKey = config['web']['saucenao']['key']
generalHeader = {
    "sec-ch-ua": '"Chromium";v="104", " Not A;Brand";v="99", "Google Chrome";v="104"',
    "user-agent": config['web']['userAgent']
}


@on_command(name='搜图', aliases='picsearch', only_to_me=False)
async def _(session: CommandSession):
    imgCq = await session.aget(prompt='已启用图片搜索，请发送图片')
    if imgCq is None or not imgCq.startswith('[CQ:image'):
        await session.send("非图片，取消saucenao搜索")
        return
    await session.send("正在搜索……")
    imgUrl = extract_image_urls(imgCq)[0]
    async with httpx.AsyncClient(proxies=proxy) as client:
        search = ImgExploration(pic_url=imgUrl, client=client, proxies=proxy,
                                saucenao_apikey=saucenaoApiKey, header=generalHeader)
        await search.doSearch()
    resultDict = search.getResultDict()
    if not resultDict or not resultDict["info"]:
        await session.send('没有搜索到结果^ ^')
        return
    await session.send(getImgBase64('picsearch.jpg'))
    imgNum = await session.aget(prompt="若需要提取图片链接，请在60s内发送对应结果的序号\n注: danbooru等敏感网站链接直接发送会被吞，请自行图片转文字提取")
    try:
        args = list(map(int, str(imgNum).split()))
        args = list(set(args))
        for arg in args:
            if arg > len(resultDict["info"]) or arg < 1:
                args.remove(arg)
        msg = ""
        for index in args:
            url = resultDict["info"][index - 1]["url"]
            msg += f"{index} - {url}\n"
        await session.send(msg)
    except (IndexError, ValueError):
        return


@on_command(name='saucenao', aliases=('yandex', 'google'), only_to_me=False)
async def _(session: CommandSession):
    await session.send('搜图指令已整合，请使用“!搜图”或“!picsearch”')


@on_command(name='picurl', only_to_me=False)
async def picUrlGet(session: CommandSession):
    imgCq = await session.aget(prompt='请发送图片')
    if imgCq is None or '[CQ:image' not in imgCq:
        await session.send("非图片，取消图片链接获取")
        return
    imgUrls = extract_image_urls(imgCq)
    await session.send('\n'.join(imgUrls))


class ImgExploration:
    def __init__(self, pic_url, client: httpx.AsyncClient, proxies, saucenao_apikey, header):
        self.__result_info = None
        self.__picNinfo = None
        self.client = client
        self.__proxy = proxies
        self.__pic_url = pic_url
        self.__saucenao_apikey = saucenao_apikey
        self.__generalHeader = header
        self.__google_cookies = ""
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
            img = Image.new(mode="RGB", size=(width, total_height), color=(255, 255, 255))

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

                    thumbnail = thumbnail.resize((int((height - 2 * margin) * thumbnail.width / thumbnail.height), height - 2 * margin))
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
                    draw.text(xy=(text_x, vernier + text_ver), text="Title: ", fill=(160, 160, 160), font=font, anchor="la")
                    draw.text(xy=(text_x + 60, vernier + text_ver), text=f"{text[:20]}{'...' if len(text)>=20 else ''}", fill=(0, 0, 0), font=font, anchor="la")
                    text_ver = text_ver + font_size + margin / 2

                if ("similarity" in single) and single["similarity"]:  # saucenao
                    text = single["similarity"]
                    draw.text(xy=(text_x, vernier + text_ver), text="similarity: ", fill=(160, 160, 160), font=font, anchor="la")
                    draw.text(xy=(text_x + 115, vernier + text_ver), text=f"{text}", fill=(0, 0, 0), font=font, anchor="la")
                    text_ver = text_ver + font_size + margin / 2

                if ("description" in single) and single["description"]:
                    text = single["description"]
                    draw.text(xy=(text_x, vernier + text_ver), text=f"{text[:30]}{'...' if len(text)>=30 else ''}", fill=(0, 0, 0), font=font, anchor="la")
                    text_ver = text_ver + font_size + margin / 2

                if ("domain" in single) and single["domain"]:  # Yandex
                    text = single["domain"]
                    draw.text(xy=(text_x, vernier + text_ver), text="Source: ", fill=(160, 160, 160), font=font, anchor="la")
                    draw.text(xy=(text_x + 86, vernier + text_ver), text=f"{text}", fill=(0, 0, 0), font=font, anchor="la")
                    text_ver = text_ver + font_size + margin / 2

                if single["url"]:
                    url = single["url"]
                    draw.text(xy=(text_x, vernier + text_ver), text=f"{url[:80]}{'......' if len(url)>=80 else ''}", fill=(100, 100, 100), font=font3, anchor="la")
                vernier += height

            save = BytesIO()
            img.save("picsearch.jpg", format="JPEG", quality=95)
            return save.getvalue()
        except Exception as e:
            raise e

    async def __saucenao_build_result(self, result_num=8, minSim=68) -> list:
        resList = []
        try:
            async with Network(proxies=self.__proxy, timeout=100) as client:
                saucenao = SauceNAO(client=client, api_key=self.__saucenao_apikey, numres=result_num)
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
            print(e)
            return []
        finally:
            print(f"saucenao result:{len(resList)}")
            return resList

    async def __google_build_result(self, result_num=4) -> list:
        google_header = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36",
            "Cookie": self.__google_cookies,
        }
        resList = []
        try:
            params = {
                "url": self.__pic_url,
            }
            google_lens_text = (await self.client.get(f"https://lens.google.com/uploadbyurl", params=params, headers=google_header, follow_redirects=True, timeout=50)).text

            req_tex = re.findall(r"var AF_dataServiceRequests = (.+?); var AF_initDataChunkQueue", google_lens_text)
            if req_tex:
                ds1 = re.findall(r"'ds:1' : (.*)}", req_tex[0])
                if ds1:
                    ds = ds1[0]
                    # print(ds)
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
                        print(e)
                    dic["request"][-3].append(dic["request"][1])

            qest = [
                [
                    [
                        dic["id"],
                        json.dumps(dic["request"]),
                        None,
                        "generic",
                    ],
                ],
            ]
            postDate = {"f.req": json.dumps(qest)}
            post_headers = {
                "Accept": "*/*",
                "Accept-Encoding": "gzip, deflate, br",
                "Accept-Language": "zh-CN,zh;q=0.9",
                "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
                "Sec-Ch-Ua": '"Google Chrome";v="113", "Chromium";v="113", "Not-A.Brand";v="24"',
                "Referer": "https://lens.google.com/",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36",
            }
            te = await self.client.post(url="https://lens.google.com/_/LensWebStandaloneUi/data/batchexecute?hl=zh-CN", data=postDate, headers=post_headers)

            res_j = json.loads(te.text.replace(r")]}'", "", 1))
            search_result = json.loads(res_j[0][2])[1][0][1][8][20][0][0]

            for singleDiv in search_result[:result_num]:
                try:
                    sin_di = {
                        "title": singleDiv[4],
                        "thumbnail_url": singleDiv[0][0],
                        "url": singleDiv[2][2][2],
                        "source": "Google",
                        "domain": singleDiv[1][2],
                    }
                except IndexError:
                    continue
                resList.append(sin_di)

            thumbnail_urls = [single["thumbnail_url"] for single in resList]
            thumbnail_bytes = await self.ImageBatchDownload(thumbnail_urls, self.client)
            i = 0
            for single in resList:
                single["thumbnail_bytes"] = thumbnail_bytes[i]
                i += 1
            return resList
        except Exception as e:
            print(e)
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
                i = 0
                for single in result_li:
                    single["thumbnail_bytes"] = thumbnail_bytes[i]
                    i += 1
        except Exception as e:
            print(e)
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
                yandexPage = await self.client.get(url=redirectUrl, params=data, headers=self.__generalHeader, timeout=50)
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
            print(f"yandex result:{len(result_li)}")
            return result_li
        except Exception as e:
            print(e)
        finally:
            return result_li

    async def doSearch(self):
        task_saucenao = asyncio.create_task(self.__saucenao_build_result())
        task_google = asyncio.create_task(self.__google_build_result())
        task_yandex = asyncio.create_task(self.__yandex_build_result())

        self.__result_info = (await task_saucenao) + (await task_google) + (await task_yandex)
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
