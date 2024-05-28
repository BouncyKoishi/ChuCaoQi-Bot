import re
import urllib.request
from kusa_base import config
from nonebot import on_command, CommandSession
from bs4 import BeautifulSoup

USER_AGENT = config['web']['userAgent']
CMA_INDEX = "http://www.nmc.cn/publish/typhoon/typhoon_new.html"
CMA_BROADCAST = "http://www.nmc.cn/publish/typhoon/message.html"
CMA_DETAIL = "http://www.nmc.cn/f/rest/getContent?dataId="
CMA_DATA_PREFIX = "SEVP_NMC_TCFC_SFER_ETCT_ACHN_LNO_P9_"
CMA_BROADCAST_PREFIX = "SEVP_NMC_TCMO_SFER_ETCT_ACHN_L88_P9_"

JMA_BROADCAST = "https://www.jma.go.jp/bosai/weather_map/#lang=cn_zs"


@on_command(name='台风', only_to_me=False)
async def _(session: CommandSession):
    stripped_arg = session.current_arg_text.strip()
    timeData = getCmaTime(CMA_INDEX)
    prevAmount = getPrevAmount(stripped_arg)
    cmaReport = getCmaReport(timeData[prevAmount].get('data-id') if timeData else None)
    await session.send(cmaReport + "\n具体路径信息：http://typhoon.zjwater.gov.cn")


@on_command(name='台风报文', only_to_me=False)
async def _(session: CommandSession):
    stripped_arg = session.current_arg_text.strip()
    prevAmount = getPrevAmount(stripped_arg)
    if 'jtwc' in stripped_arg.lower():
        broadcast = 'TODO: jtwc报文'
    elif 'jma' in stripped_arg.lower():
        broadcast = 'TODO: jma报文'
    else:
        timeData = getCmaTime(CMA_BROADCAST)
        broadcast = get_cma_broadcast(timeData[prevAmount].get('data-id'))
    await session.send(broadcast)


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


def getCmaReport(dataId):
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


def get_cma_broadcast(data_id):
    broadcastData = getWebPageData(CMA_DETAIL + data_id)
    broadcastBs = BeautifulSoup(broadcastData, "html.parser")
    return broadcastBs.get_text()
    

def getCmaTime(url):
    bsData = BeautifulSoup(getWebPageData(url), "html.parser")
    return bsData("p", "time")


def getWebPageData(url):
    req = urllib.request.Request(url)
    req.add_header("User-Agent", USER_AGENT)
    return urllib.request.urlopen(req).read().decode('utf-8')
