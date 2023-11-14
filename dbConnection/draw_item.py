from random import randint
from .models import DrawItemList, DrawItemStorage
from tortoise import Tortoise
from tortoise.query_utils import Prefetch
from tortoise.functions import Sum


async def getItem(itemId):
    return await DrawItemList.filter(id=itemId).first()


async def getItemByName(itemName):
    return await DrawItemList.filter(name=itemName).first()


async def getItemListByAuthor(qqNum):
    return await DrawItemList.filter(author=qqNum).order_by("-rareRank")


async def getRandomItem(rareRank):
    rareItemList = await DrawItemList.filter(rareRank=rareRank)
    return rareItemList[randint(0, len(rareItemList) - 1)]


async def searchItem(keyword, limit):
    conn = Tortoise.get_connection('default')
    rows = await conn.execute_query_dict(f'''
        SELECT
            name,
            rareRank
        FROM
            DrawItemList
        WHERE
            name LIKE ('%' || ? || '%')
            LIMIT ?
    ''', [keyword, limit])
    return rows


async def addItem(itemName, itemRare, itemDetail, author):
    await DrawItemList.create(name=itemName, rareRank=itemRare, detail=itemDetail, author=author)


async def deleteItem(item: DrawItemList):
    await item.delete()


async def setItemDetail(item: DrawItemList, newItemDetail):
    item.detail = newItemDetail
    await item.save()


async def getItemsWithStorage(qqNum, rareRank):
    if rareRank is not None:
        querySet = await DrawItemList.filter(rareRank=rareRank).prefetch_related(
            Prefetch("draw_item_storage", queryset=DrawItemStorage.filter(qq=qqNum), to_attr="storage")
        )
    else:
        querySet = await DrawItemList.all().order_by("-rareRank").prefetch_related(
            Prefetch("draw_item_storage", queryset=DrawItemStorage.filter(qq=qqNum), to_attr="storage")
        )
    return querySet


async def getSingleItemStorage(qqNum, itemId):
    return await DrawItemStorage.filter(qq=qqNum, item=itemId).first()


async def getItemStorageCount(itemId):
    personCount = await DrawItemStorage.filter(item=itemId).count()
    numberCount = await DrawItemStorage.filter(item=itemId).annotate(sum=Sum("amount")).first()
    return personCount, numberCount.sum


async def setItemStorage(qqNum, itemId):
    itemStorageData = await getSingleItemStorage(qqNum, itemId)
    if itemStorageData:
        itemStorageData.amount += 1
        await itemStorageData.save()
    else:
        item = await getItem(itemId)
        await DrawItemStorage.create(qq=qqNum, item=item, amount=1)