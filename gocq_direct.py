import requests
from config import HTTP_PORT


def setGroupPortrait(group_id: int, file: str):
    dataDict = {
        "group_id": group_id,
        "file": file,
        "cache": False
    }
    return _link("set_group_portrait", dataDict)


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
