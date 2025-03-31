import re
import pytz
import requests
from nonebot import MessageSegment as ms
from kusa_base import config, sendGroupMsg
from nonebot import on_command, CommandSession, on_startup, scheduler
from utils import imgUrlTobase64
from datetime import datetime
from bs4 import BeautifulSoup

USER_AGENT = config['web']['userAgent']
CMA_INDEX_URL = "http://www.nmc.cn/publish/typhoon/typhoon_new.html"
CMA_DETAIL_URL = "http://www.nmc.cn/f/rest/getContent?dataId="
NMC_RADAR_BASE_URL = "http://www.nmc.cn/publish/radar/"
REPORT_BASE_URL = "https://www.wis-jma.go.jp/d/o/"
GET_REPORT_FLAG = (config['env'] == 'dev')
reportsStorage = {}
newReportsStorage = {}


@on_command(name='台风', only_to_me=False)
async def _(session: CommandSession):
    strippedArg = session.current_arg_text.strip()
    prevAmount = getPrevAmount(strippedArg)
    timeData = getCmaTime(CMA_INDEX_URL)
    cmaReport = getCmaSimpleReport(timeData[prevAmount].get('data-id') if timeData else None)
    await session.send(cmaReport + "\n具体路径信息：http://typhoon.zjwater.gov.cn")


def getPrevAmount(stripped_arg):
    if "prev" not in stripped_arg:
        prevAmount = 0
    else:
        prevStr = re.findall(r'(?<=prev)\d+', stripped_arg)
        if not prevStr:
            prevAmount = 1
        else:
            prevAmount = int(prevStr[0])
    return prevAmount


def getCmaTime(url):
    bsData = BeautifulSoup(getWebPageData(url), "html.parser")
    return bsData("p", "time")


def getCmaSimpleReport(dataId):
    if dataId:
        reportData = getWebPageData(CMA_DETAIL_URL + dataId)
    else:
        reportData = getWebPageData(CMA_INDEX_URL)
    reportBs = BeautifulSoup(reportData, "html.parser")

    if "提示：当前无台风，下列产品为上一个台风产品" in reportData:
        return "当前无台风或热带低压。"
    if reportBs("div", "nodata"):
        return "cma报文编码异常。"

    reportDetail = reportBs("div", "writing")[0]
    for tr in reportDetail("tr"):
        for td in tr("td"):
            td.string = td.get_text().replace("\xa0", "")
        tr.append("\n")

    return reportDetail.get_text()


@on_command(name='雷达回波', only_to_me=False)
async def _(session: CommandSession):
    nameDict = {'全国': 'chinaall.html', '华北': 'huabei.html', '东北': 'dongbei.html', '华东': 'huadong.html',
                '华中': 'huazhong.html', '华南': 'huanan.html', '西南': 'xinan.html', '西北': 'xibei.html',
                '广州': 'guang-dong/guang-zhou.htm', '韶关': 'guang-dong/shao-guan.htm', '梅州': 'guang-dong/mei-zhou.htm',
                '阳江': 'guang-dong/yang-jiang.htm', '汕头': 'guang-dong/shan-tou.htm', '深圳': 'guang-dong/shen-zhen.htm',
                '湛江': 'guang-dong/zhan-jiang.htm', '河源': 'guang-dong/he-yuan.htm', '汕尾': 'guang-dong/shan-wei.htm',
                '肇庆': 'guang-dong/zhao-qing.htm', '连州': 'guang-dong/lian-zhou.htm', '福州': 'fu-jian/fu-zhou.htm',
                '厦门': 'fu-jian/xia-men.htm', '杭州': 'zhe-jiang/hang-zhou.htm', '宁波': 'zhe-jiang/ning-bo.htm',
                '温州': 'zhe-jiang/wen-zhou.htm', '嵊泗': 'zhe-jiang/cheng-si.htm', '金华': 'zhe-jiang/jin-hua.htm',
                '上海': 'shang-hai/qing-pu.htm', '南京': 'jiang-su/nan-jing.htm'}
    strippedArg = session.current_arg_text.strip()
    if not strippedArg:
        await session.send(f"地区未指定^ ^\n目前支持的地区有：{'、'.join(nameDict.keys())}")
        return
    if strippedArg not in nameDict:
        await session.send(f"未找到对应地区的雷达回波图^ ^\n目前支持的地区有：{'、'.join(nameDict.keys())}")
        return
    radarUrl = NMC_RADAR_BASE_URL + nameDict[strippedArg]
    radarPicUrl = getRadarPicUrl(radarUrl)
    if not radarPicUrl:
        await session.send("获取雷达回波图失败^ ^")
        return
    radarPicBase64 = 'base64://' + await imgUrlTobase64(radarPicUrl)
    await session.send(ms.image(radarPicBase64))


def getRadarPicUrl(url):
    pageData = getWebPageData(url)
    if not pageData:
        return None
    bsData = BeautifulSoup(pageData, "html.parser")
    imgBlockDiv = bsData("div", "imgblock")[0]
    imgTag = imgBlockDiv("img")[0]
    return imgTag.get("src")


@on_command(name='台风报文', only_to_me=False)
async def _(session: CommandSession):
    if not GET_REPORT_FLAG:
        await session.send("台风报文自动获取功能已关闭。")
        return
    if newReportsStorage:
        for report in newReportsStorage.values():
            await session.send(report)
    else:
        await session.send("暂无新报文！")


@scheduler.scheduled_job('interval', minutes=30)
async def _():
    if not GET_REPORT_FLAG:
        return
    global reportsStorage
    global newReportsStorage
    latestReports = await getNewCmaReports()
    newReports = {k: v for k, v in latestReports.items() if k not in reportsStorage}
    if newReports:
        for report in newReports.values():
            await sendGroupMsg(config['group']['log'], report)
        newReportsStorage = newReports
    reportsStorage = latestReports


@on_startup
async def _():
    if not GET_REPORT_FLAG:
        print(f'--- 台风报文自动获取功能已关闭 ---')
        return
    global reportsStorage
    reportsStorage = await getNewCmaReports()


async def getNewCmaReports():
    reports = {}
    dateStr = datetime.now(pytz.timezone('UTC')).strftime("%Y%m%d")
    url = f"{REPORT_BASE_URL}/BABJ/Alphanumeric/Warning/Tropical_cyclone/{dateStr}/"

    nowTime = datetime.now(pytz.timezone('Asia/Shanghai')).strftime("%H:%M")
    print(f"--- 开始获取台风报文，当前时间：{nowTime} ---")
    response = getWebPageData(url)
    if not response:
        print("--- 当日无台风信息，或获取台风报文失败 ---")
        return reports

    soup = BeautifulSoup(response, 'html.parser')
    for link in soup.find_all('a'):
        timeStr = link.get('href')
        if timeStr is None or timeStr.startswith('?C=') or timeStr.startswith('/d/o/'):
            continue
        timeResponse = getWebPageData(f'{url}{timeStr}')
        timeSoup = BeautifulSoup(timeResponse, 'html.parser')
        for timeLink in timeSoup.find_all('a'):
            fileStr = timeLink.get('href')
            if fileStr is None or fileStr.startswith('?C=') or fileStr.startswith('/d/o/'):
                continue
            fileResponse = getWebPageData(f'{url}{timeStr}{fileStr}')
            reports[fileStr] = fileResponse
    print(f'--- 已获取当日的台风报文共{len(reports)}条 ---')
    return reports


def getWebPageData(url):
    response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=5)
    if response.status_code == 200:
        return response.text
    else:
        print(f"--- 天气模块HTTP请求出错: {response.status_code} ---")
        return None

