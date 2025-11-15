import re
import httpx
import base64
import nonebot
import traceback
from nonebot import Message, CQHttpError
from nonebot import MessageSegment as ms

groupMemberInfoCache = {}

def rd3(floatNumber: float):
    return round(floatNumber, 3)


# 仅转为base64
async def imgUrlTobase64(url):
    url = url.replace('amp;', '')
    print(f'imgUrlTobase64: {url}')
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
    return base64.b64encode(response.content).decode()


# 输出MessageSegment类型的图片
def imgBytesToBase64(data: bytes):
    pic_src = 'base64://' + base64.b64encode(data).decode()
    pic = ms.image(pic_src)
    return pic


def imgLocalPathToBase64(path: str):
    with open(path, 'rb') as f:
        p = f.read()
    return imgBytesToBase64(p)


def extractImgUrls(picInfo):
    picInfoMsg = Message(picInfo)
    urls = [
        s.data['url']
        for s in picInfoMsg
        if s.type in ['image', 'mface'] and 'url' in s.data
    ]
    urls = [url.replace('amp;', '') for url in urls]
    return urls


async def getUserAndGroupMsg(userId, groupId):
    userMsg = userId
    groupMsg = groupId
    bot = nonebot.get_bot()
    try:
        qqInfo = await bot.get_stranger_info(user_id=userId)
        if qqInfo:
            userMsg = f"{qqInfo['nickname']}({userId})"

        if groupId:
            groupInfo = await bot.get_group_info(group_id=groupId)
            if groupInfo:
                groupMsg = f"{groupInfo['group_name']}({groupId})"
        else:
            groupMsg = "私聊"
    except:
        print(f'Error: cqHttpApi not available')

    return userMsg, groupMsg


# 综合bot权限和被禁言者权限判断禁言能否被执行
async def checkBanAvailable(targetId, groupId):
    bot = nonebot.get_bot()
    botBaseInfo = await bot.get_login_info()
    if botBaseInfo['userId'] == targetId:
        return False
    try:
        botInfo = await getGroupMemberInfoFromCache(bot, groupId, botBaseInfo['userId'])
        targetInfo = await getGroupMemberInfoFromCache(bot, groupId, targetId)
        if not botInfo or not targetInfo:
            return False
        if botInfo['role'] == 'member':
            return False
        if targetInfo['role'] == 'owner':
            return False
        if botInfo['role'] == 'admin' and targetInfo['role'] == 'admin':
            return False
        return True
    except CQHttpError as e:
        traceback.print_exc()
        print(f'Error: cqHttpApi(GetGroupMemberInfo) not available')
        return False


async def getGroupMemberInfoFromCache(bot, groupId, userId):
    global groupMemberInfoCache
    cacheKey = f'{groupId}_{userId}'
    if cacheKey in groupMemberInfoCache:
        return groupMemberInfoCache[cacheKey]
    try:
        memberInfo = await bot.get_group_member_info(group_id=groupId, user_id=userId)
        groupMemberInfoCache[cacheKey] = memberInfo
        return memberInfo
    except CQHttpError as e:
        traceback.print_exc()
        print(f'Error: cqHttpApi(GetGroupMemberInfo) not available')
        return None


def nameDetailSplit(strippedText):
    if not strippedText:
        return "", ""
    colonEnIndex = strippedText.find(":")
    colonCnIndex = strippedText.find("：")
    colonEnIndex = len(strippedText) if colonEnIndex == -1 else colonEnIndex
    colonCnIndex = len(strippedText) if colonCnIndex == -1 else colonCnIndex
    # 英文冒号
    if colonEnIndex < colonCnIndex:
        return strippedText.split(':', 1)
    # 中文冒号
    if colonCnIndex < colonEnIndex:
        return strippedText.split('：', 1)
    # 没有冒号
    return strippedText, ""


# 当前仅支持10以内的罗马数字和Int互转
def romanNumToInt(romanNum):
    romanNum = romanNum.upper()
    romanNumList = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X']
    return romanNumList.index(romanNum) + 1 if romanNum in romanNumList else 0


def intToRomanNum(intNum):
    romanNumList = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X']
    return romanNumList[intNum - 1] if 0 < intNum <= 10 else ""


# 为数字添加千分号，代码来自扫地机
def intToFormattedStr(n: int) -> str:
    ans = ""
    k = 1000
    while abs(n) >= k:
        m = n % k
        mStr = str(m)
        while len(mStr) < 3:
            mStr = '0' + mStr
        ans = ',' + mStr + ans
        n //= k
    return str(n) + ans


# 支持k,m,b单位的数字字符串转换为int
def convertNumStrToInt(numStr):
    match = re.search(r'([\d,]+)([kmbKMB]?)', numStr)
    if match:
        numberPart = int(match.group(1).replace(',', ''))
        unit = match.group(2)
        if unit == 'k' or unit == 'K':
            return numberPart * 1_000
        elif unit == 'm' or unit == 'M':
            return numberPart * 1_000_000
        elif unit == 'b' or unit == 'B':
            return numberPart * 1_000_000_000
        else:
            return numberPart
    else:
        return None



