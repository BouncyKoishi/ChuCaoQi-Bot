import datetime
from .models import KusaField


async def getKusaField(qqNum) -> KusaField:
    return await KusaField.filter(qq=qqNum).first()


async def getAllKusaField(onlyGrowing=False, onlySoilNotBest=False):
    if onlyGrowing:
        return await KusaField.filter(kusaIsGrowing=True).all()
    if onlySoilNotBest:
        return await KusaField.filter(soilCapacity__lt=25).all()
    return await KusaField.all()


async def kusaStartGrowing(qqNum, kusaRestTime, usingKela, biogasEffect, kusaType, weedCosting, isPrescient):
    kusaField = await getKusaField(qqNum)
    if kusaField:
        kusaField.kusaIsGrowing = True
        kusaField.kusaRestTime = kusaRestTime
        kusaField.isUsingKela = usingKela
        kusaField.isPrescient = isPrescient
        kusaField.biogasEffect = biogasEffect
        kusaField.kusaType = kusaType
        kusaField.weedCosting = weedCosting
        kusaField.soilCapacity -= 2 if kusaType == "巨草" else 1
        kusaField.lastUseTime = datetime.datetime.now()
        await kusaField.save()


async def updateKusaResult(qqNum, kusaResult, advKusaResult):
    kusaField = await getKusaField(qqNum)
    if kusaField:
        kusaField.kusaResult = kusaResult
        kusaField.advKusaResult = advKusaResult
        await kusaField.save()


async def updateDefaultKusaType(qqNum, kusaType):
    kusaField = await getKusaField(qqNum)
    if kusaField:
        kusaField.defaultKusaType = kusaType
        await kusaField.save()


async def kusaStopGrowing(qqNum, force=False):
    kusaField = await getKusaField(qqNum)
    if kusaField:
        if force:
            kusaField.soilCapacity -= kusaField.weedCosting
        kusaField.weedCosting = 0
        kusaField.kusaIsGrowing = False
        kusaField.kusaRestTime = 0
        kusaField.isUsingKela = False
        kusaField.isPrescient = False
        kusaField.biogasEffect = 1.0
        kusaField.kusaResult = 0
        kusaField.advKusaResult = 0
        kusaField.kusaType = ""
        kusaField.lastUseTime = datetime.datetime.now()
        await kusaField.save()


async def kusaTimePass(qqNum):
    kusaField = await getKusaField(qqNum)
    if kusaField:
        kusaField.kusaRestTime -= 1
        await kusaField.save()


async def kusaSoilRecover(qqNum):
    kusaField = await getKusaField(qqNum)
    if kusaField:
        kusaField.soilCapacity += 1
        await kusaField.save()
        if kusaField.soilCapacity == 25:
            return True
    return False
