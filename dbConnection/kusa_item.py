import pytz
import datetime
from .models import KusaItemList, KusaItemStorage
from utils import romanNumToInt


async def getItem(itemName) -> KusaItemList:
    return await KusaItemList.filter(name=itemName).first()


async def getItemsByType(itemType):
    return await KusaItemList.filter(type=itemType).all()


async def getItemAmount(qqNum, itemName) -> int:
    item = await getItem(itemName)
    if item:
        itemStorage = await KusaItemStorage.filter(qq=qqNum, item=item).first()
        if itemStorage:
            return itemStorage.amount
    return 0


async def getItemStorageInfo(qqNum, itemName) -> KusaItemStorage:
    item = await getItem(itemName)
    if item:
        return await KusaItemStorage.filter(qq=qqNum, item=item).first()
    else:
        raise ValueError("Item not found")


async def getItemStorageListByItem(itemName):
    item = await getItem(itemName)
    if not item:
        return []
    return await KusaItemStorage.filter(item=item, allowUse=True, amount__gt=0).all()


async def getUserIdListByItem(itemName):
    item = await getItem(itemName)
    if not item:
        return []
    storageList = await KusaItemStorage.filter(item=item, allowUse=True, amount__gt=0).all()
    return [storage.qq for storage in storageList]


async def getTechLevel(qqNum, techNamePrefix) -> int:
    techList = await KusaItemStorage.filter(qq=qqNum, item__name__contains=techNamePrefix).all()
    if not techList:
        return 0
    techItemList = [await tech.item.all() for tech in techList]
    techLevelList = [romanNumToInt(techItem.name[len(techNamePrefix):]) for techItem in techItemList]
    return max(techLevelList) if techLevelList else 0


async def changeItemAmount(qqNum, itemName, increaseAmount):
    if increaseAmount == 0:
        return True

    item = await getItem(itemName)
    if not item:
        return False

    itemStorage = await KusaItemStorage.filter(qq=qqNum, item=item).first()
    if itemStorage:
        if itemStorage.amount + increaseAmount < 0:
            raise ValueError("Item amount cannot be negative")
        itemStorage.amount += increaseAmount
        await itemStorage.save()
        if itemStorage.amount == 0:
            await itemStorage.delete()
    else:
        if increaseAmount < 0:
            raise ValueError("Item amount cannot be negative")
        await KusaItemStorage.create(qq=qqNum, item=item, amount=increaseAmount)

    return True


async def changeItemAllowUse(qqNum, itemName, allowUse):
    item = await getItem(itemName)
    if not item:
        return False

    itemStorage = await KusaItemStorage.filter(qq=qqNum, item=item).first()
    if itemStorage:
        itemStorage.allowUse = allowUse
        await itemStorage.save()
        return True


async def updateTimeLimitedItem(qqNum, itemName, duration):
    item = await getItem(itemName)
    if not item:
        return False

    itemStorage = await KusaItemStorage.filter(qq=qqNum, item=item).first()
    if itemStorage:
        itemStorage.amount = 1
        itemStorage.timeLimitTs += duration
        await itemStorage.save()
    else:
        now = datetime.datetime.now().timestamp()
        timeLimitTs = now + duration
        await KusaItemStorage.create(qq=qqNum, item=item, amount=1, timeLimitTs=timeLimitTs)

    return True


async def removeTimeLimitedItem(qqNum, itemName):
    item = await getItem(itemName)
    if not item:
        return False

    itemStorage = await KusaItemStorage.filter(qq=qqNum, item=item).first()
    if itemStorage:
        await itemStorage.delete()
        return True
    return False


async def cleanTimeLimitedItems():
    now = datetime.datetime.now().timestamp()
    return await KusaItemStorage.filter(timeLimitTs__lt=now).delete()


async def getShopItemList(priceType):
    return await KusaItemList.filter(shopPrice__not_isnull=True, priceType=priceType).order_by('shopPrice').all()


async def getStoragesOrderByAmountDesc(itemName):
    item = await getItem(itemName)
    if item:
        return await KusaItemStorage.filter(item=item).order_by('-amount').all()
    return []


async def cleanAllG(qqNum):
    items = await getItemsByType('G')
    for item in items:
        gStorage = await KusaItemStorage.filter(qq=qqNum, item=item).first()
        if gStorage:
            await gStorage.delete()


