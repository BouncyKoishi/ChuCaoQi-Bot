from random import randint
from .models import DrawItemList, DrawItemStorage
from tortoise import Tortoise
from tortoise.query_utils import Prefetch
from tortoise.functions import Sum


async def getItem(itemId):
    return await DrawItemList.filter(id=itemId).first()


async def getItemByName(itemName):
    return await DrawItemList.filter(name=itemName).first()


async def getItemListByAuthor(qqNum, rareRank=None, poolName=None):
    filterQuery = getRareRankAndPoolFilter(rareRank, poolName)
    return await filterQuery.filter(author=qqNum).order_by("-rareRank")


async def getRandomItem(rareRank, poolName=None):
    if poolName:
        rareItemList = await DrawItemList.filter(rareRank=rareRank, pool=poolName)
    else:
        rareItemList = await DrawItemList.filter(rareRank=rareRank)
    if not rareItemList:
        raise Exception(f"DrawItem Error: 抽奖物品列表为空！")
    return rareItemList[randint(0, len(rareItemList) - 1)]


async def searchItem(keyword, limit, offset=0):
    conn = Tortoise.get_connection('default')
    count = (await conn.execute_query_dict('''
        SELECT
            count(*) AS count
        FROM
            DrawItemList
        WHERE
            name LIKE ('%' || ? || '%')
    ''', [keyword,]))[0]['count']
    rows = await conn.execute_query_dict('''
        SELECT
            name,
            rareRank
        FROM
            DrawItemList
        WHERE
            name LIKE ('%' || ? || '%')
        ORDER BY
            rareRank DESC
            LIMIT ? OFFSET ?
    ''', [keyword, limit, offset])
    return count, rows


async def addItem(itemName, itemRare, poolName, itemDetail, author):
    await DrawItemList.create(name=itemName, rareRank=itemRare, pool=poolName, detail=itemDetail, author=author)


async def deleteItem(item: DrawItemList):
    await item.delete()


async def setItemDetail(item: DrawItemList, newItemDetail):
    item.detail = newItemDetail
    await item.save()


async def getItemsWithStorage(qqNum, rareRank=None, poolName=None):
    filterQuery = getRareRankAndPoolFilter(rareRank, poolName)
    return await filterQuery.order_by("-rareRank").prefetch_related(
            Prefetch("draw_item_storage", queryset=DrawItemStorage.filter(qq=qqNum), to_attr="storage")
        )


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


def getRareRankAndPoolFilter(rareRank, poolName):
    if rareRank is not None and poolName:
        return DrawItemList.filter(rareRank=rareRank, pool=poolName)
    elif rareRank is None and poolName:
        return DrawItemList.filter(pool=poolName)
    elif rareRank is not None and not poolName:
        return DrawItemList.filter(rareRank=rareRank)
    else:
        return DrawItemList.all()
