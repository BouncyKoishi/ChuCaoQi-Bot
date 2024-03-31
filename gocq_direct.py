import requests
from config import HTTP_PORT


def setGroupPortrait(group_id: int, file: str):
    dataDict = {
        "group_id": group_id,
        "file": file,
        "cache": False
    }
    return _link("set_group_portrait", dataDict)


def sendForwardMessage(messages: list, group_id=None, user_id=None):
    if group_id:
        return sendGroupForwardMessage(group_id, messages)
    elif user_id:
        return sendPrivateForwardMessage(user_id, messages)
    else:
        print("cqAPI 请求失败: 未指定发送目标")
        return None


def sendPrivateForwardMessage(user_id: int, messages: list):
    dataDict = {
        "user_id": user_id,
        "messages": messages
    }
    return _link("send_private_forward_msg", dataDict)


def sendGroupForwardMessage(group_id: int, messages: list):
    dataDict = {
        "group_id": group_id,
        "messages": messages
    }
    return _link("send_group_forward_msg", dataDict)


# 直接调用go-cqhttp的正向HTTP Api
def _link(api: str, data: dict):
    goCqLink = f"http://localhost:{HTTP_PORT}/"
    try:
        with requests.post(f"{goCqLink}{api}", data=data) as req:
            json = req.json()
            print("cqAPI 响应: %s" % json)
            return json
    except Exception as err:
        print(f"cqAPI 请求失败: {err}")

    return None
