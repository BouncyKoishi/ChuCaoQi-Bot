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


def nameDetailSplit(stripped_arg):
    if not stripped_arg:
        return "", ""
    # 英文冒号
    splitEn = stripped_arg.split(':', 1)
    if len(splitEn) > 1:
        return splitEn
    # 中文冒号
    splitCn = stripped_arg.split('：', 1)
    if len(splitCn) > 1:
        return splitCn
    # 没有冒号
    return stripped_arg, ""
