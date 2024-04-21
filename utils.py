import base64
import nonebot
from nonebot import MessageSegment as ms


def rd3(floatNumber: float):
    return round(floatNumber, 3)


def getImgBase64(path):
    with open(path, 'rb') as f:
        p = f.read()
        pic_src = 'base64://' + str(base64.b64encode(p)).replace("b'", "").replace("'", "")
        pic = ms.image(pic_src)
        return pic


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
