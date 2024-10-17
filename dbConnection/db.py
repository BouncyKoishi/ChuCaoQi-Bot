from nonebot import on_startup
from tortoise import Tortoise
from .models import User, KusaField, Flag, DonateRecord, TradeRecord
from .kusa_item import changeItemAmount
import datetime


async def createUser(qqNum):
    existUser = await getUser(qqNum)
    if not existUser:
        await User.create(qq=qqNum, lastUseTime=datetime.datetime.now())
        await KusaField.create(qq=qqNum)
        await changeItemAmount(qqNum, "草地", 1)
    else:
        existUser.lastUseTime = datetime.datetime.now()
        await existUser.save()


async def getNameListByQQ(qqList):
    users = await User.filter(qq__in=qqList).values('qq', 'name')
    return {user['qq']: user['name'] for user in users}


async def getUser(qqNum) -> User:
    return await User.filter(qq=qqNum).first()


async def getAllUser():
    return await User.all()


async def changeName(qqNum, newName):
    user = await getUser(qqNum)
    if user:
        user.name = newName
        await user.save()
        return True
    else:
        return False


async def changeTitle(qqNum, newTitle):
    user = await getUser(qqNum)
    if user:
        user.title = newTitle
        await user.save()
        return True
    else:
        return False


async def changeKusa(qqNum, changeAmount):
    user = await getUser(qqNum)
    if user:
        user.kusa += changeAmount
        await user.save()
        return True
    else:
        return False


async def changeAdvKusa(qqNum, changeAmount):
    user = await getUser(qqNum)
    if user:
        user.advKusa += changeAmount
        await user.save()
        return True
    else:
        return False


async def getFlagValue(userId, flagName):
    flag = await Flag.filter(name=flagName, ownerId=userId).first()
    if not flag:
        flag = await Flag.filter(name=flagName, forAll=True).first()
    if not flag:
        raise Exception("Config Error: 读取时错误，无该参数信息")
    return flag.value


async def setFlag(userId, flagName, value):
    existFlag = await Flag.filter(name=flagName, ownerId=userId).first()
    if existFlag:
        existFlag.value = value
        await existFlag.save()
    else:
        publicFlag = await Flag.filter(name=flagName, forAll=True).first()
        if not publicFlag:
            raise Exception("Config Error: 新增时错误，无此公共参数")
        await Flag.create(name=flagName, ownerId=userId, value=value, forAll=False)


async def getFlagList():
    return await Flag.filter(forAll=True).all()


async def getDonateRecords(qqNum=None, year=None):
    if qqNum:
        if year:
            return await DonateRecord.filter(qq=qqNum).filter(donateDate__contains=year).order_by('donateDate')
        return await DonateRecord.filter(qq=qqNum).order_by('donateDate')
    if year:
        return await DonateRecord.filter(donateDate__contains=year).order_by('donateDate')
    return await DonateRecord.all()


async def getDonateAmount(qqNum=None, year=None):
    records = await getDonateRecords(qqNum, year)
    return sum([record.amount for record in records])


async def getDonateRank(qqNum=None, year=None):
    records = await getDonateRecords(qqNum, year)
    groupedRecords = {}
    for record in records:
        groupedRecords.setdefault(record.qq, []).append(record.amount)
    donates = {qq: sum(amounts) for qq, amounts in groupedRecords.items()}
    donateRank = dict(sorted(donates.items(), key=lambda item: item[1], reverse=True))
    return donateRank


async def setDonateRecord(qqNum, amount, source):
    now = datetime.datetime.now()
    donateDate = now.strftime('%Y-%m-%d')
    await DonateRecord.create(qq=qqNum, amount=amount, donateDate=donateDate, source=source)


async def setTradeRecord(operator, tradeType, gainItemAmount, gainItemName, costItemAmount, costItemName, detail=None):
    timestamp = datetime.datetime.now().timestamp()
    await TradeRecord.create(operator=operator, tradeType=tradeType, detail=detail, timestamp=timestamp,
                             gainItemAmount=gainItemAmount, gainItemName=gainItemName,
                             costItemAmount=costItemAmount, costItemName=costItemName)


class DB:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

    @classmethod
    async def init(cls):
        from . import models
        await Tortoise.init({
            "connections": {
                "default": {
                    "engine": "tortoise.backends.sqlite",
                    "credentials": {
                        "file_path": "database/chuchu.sqlite",
                        "isolation_level": 'IMMEDIATE'
                    }
                }
            },
            "apps": {
                "models": {
                    "models": [locals()['models']],
                    "default_connection": "default",
                }
            }
        })
        await Tortoise.generate_schemas()


@on_startup
async def init():
    async with DB() as db:
        await db.init()
        print("--- DB Init ---")
