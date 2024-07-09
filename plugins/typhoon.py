import re
import pytz
import requests
from kusa_base import config, sendGroupMsg
from nonebot import on_command, CommandSession, on_startup, scheduler
from datetime import datetime
from bs4 import BeautifulSoup

USER_AGENT = config['web']['userAgent']
CMA_INDEX = "http://www.nmc.cn/publish/typhoon/typhoon_new.html"
CMA_DETAIL = "http://www.nmc.cn/f/rest/getContent?dataId="
REPORT_BASE_URL = "https://www.wis-jma.go.jp/d/o/"
reportsStorage = {}
newReportsStorage = {}


@on_command(name='台风', only_to_me=False)
async def _(session: CommandSession):
    strippedArg = session.current_arg_text.strip()
    prevAmount = getPrevAmount(strippedArg)
    timeData = getCmaTime(CMA_INDEX)
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
        reportData = getWebPageData(CMA_DETAIL + dataId)
    else:
        reportData = getWebPageData(CMA_INDEX)
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


def getWebPageData(url):
    response = requests.get(url, headers={"User-Agent": USER_AGENT})
    if response.status_code == 200:
        return response.text
    else:
        print(f"--- 台风模块HTTP请求出错: {response.status_code} ---")
        return None


@on_command(name='台风报文', only_to_me=False)
async def _(session: CommandSession):
    if newReportsStorage:
        for report in newReportsStorage.values():
            await session.send(report)
    else:
        await session.send("暂无新报文！")


@scheduler.scheduled_job('interval', minutes=30)
async def _():
    global reportsStorage
    global newReportsStorage
    latestReports = await getNewCmaReports()
    newReports = {k: v for k, v in latestReports.items() if k not in reportsStorage}
    if newReports:
        for report in newReports.values():
            await sendGroupMsg(config['group']['main'], report)
        newReportsStorage = newReports
    reportsStorage = latestReports


@on_startup
async def _():
    global reportsStorage
    global newReportsStorage
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



