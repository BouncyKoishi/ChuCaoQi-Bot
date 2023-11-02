from .models import KusaItemList, KusaItemStorage


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


async def changeItemAmount(qqNum, itemName, increaseAmount):
    item = await getItem(itemName)
    if item:
        itemStorage = await KusaItemStorage.filter(qq=qqNum, item=item).first()
        if itemStorage:
            if itemStorage.amount + increaseAmount < 0:
                raise ValueError("Item amount cannot be negative")
            itemStorage.amount += increaseAmount
            await itemStorage.save()
            if itemStorage.amount == 0:
                await itemStorage.delete()
            return True
        else:
            if increaseAmount < 0:
                raise ValueError("Item amount cannot be negative")
            await KusaItemStorage.create(qq=qqNum, item=item, amount=increaseAmount)
            return True
    else:
        return False


async def changeItemAllowUse(qqNum, itemName, allowUse):
    item = await getItem(itemName)
    if item:
        itemStorage = await KusaItemStorage.filter(qq=qqNum, item=item).first()
        if itemStorage:
            itemStorage.allowUse = allowUse
            await itemStorage.save()
            return True
    return False


async def getShopItemList(isAdvItem: bool):
    return await KusaItemList.filter(isInShop=True, isUsingAdvKusa=isAdvItem).order_by('shopPrice').all()


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
