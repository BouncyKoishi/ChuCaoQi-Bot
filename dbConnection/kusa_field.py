import datetime
from tortoise import Tortoise
from .models import KusaField, KusaHistory


async def getKusaField(qqNum) -> KusaField:
    return await KusaField.filter(qq=qqNum).first()


async def getAllKusaField(onlyFinished=False, onlySoilNotBest=False):
    if onlyFinished:
        nowTimestamp = datetime.datetime.now().timestamp()
        return await KusaField.filter(kusaFinishTs__lt=nowTimestamp).all()
    if onlySoilNotBest:
        return await KusaField.filter(soilCapacity__lt=25).all()
    return await KusaField.all()


async def kusaStartGrowing(qqNum, kusaFinishTs, usingKela, biogasEffect, kusaType, plantCosting, weedCosting, isPrescient, overloadOnHarvest):
    kusaField = await getKusaField(qqNum)
    if kusaField:
        kusaField.kusaFinishTs = kusaFinishTs
        kusaField.isUsingKela = usingKela
        kusaField.isPrescient = isPrescient
        kusaField.biogasEffect = biogasEffect
        kusaField.kusaType = kusaType
        kusaField.weedCosting = weedCosting
        kusaField.soilCapacity -= plantCosting
        kusaField.overloadOnHarvest = overloadOnHarvest
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


async def kusaStopGrowing(field: KusaField, force=False):
    if force:
        field.soilCapacity -= field.weedCosting
    field.weedCosting = 0
    field.kusaFinishTs = None
    field.isUsingKela = False
    field.isPrescient = False
    field.overloadOnHarvest = False
    field.biogasEffect = 1.0
    field.kusaResult = 0
    field.advKusaResult = 0
    field.kusaType = None
    field.lastUseTime = datetime.datetime.now()
    await field.save()


async def kusaSoilRecover(qqNum):
    kusaField = await getKusaField(qqNum)
    if kusaField:
        kusaField.soilCapacity += 1
        await kusaField.save()
        if kusaField.soilCapacity == 25:
            return True
    return False


async def kusaSoilUseUp(qqNum):
    kusaField = await getKusaField(qqNum)
    if kusaField:
        usedCapacity = kusaField.soilCapacity
        kusaField.soilCapacity = 0
        await kusaField.save()
        return usedCapacity
    return 0


async def kusaHistoryAdd(field: KusaField):
    await KusaHistory.create(qq=field.qq, kusaType=field.kusaType, kusaResult=field.kusaResult, advKusaResult=field.advKusaResult)


async def kusaHistoryReport(qqNum, endTime: datetime.datetime, interval):
    startTime = endTime - datetime.timedelta(seconds=interval)
    conn = Tortoise.get_connection('default')
    rows = await conn.execute_query_dict(f'''
            SELECT
                count(*) AS count,
                sum(kusaResult) AS sumKusa,
                avg(kusaResult) AS avgKusa,
                sum(advKusaResult) AS sumAdvKusa,
                avg(advKusaResult) AS avgAdvKusa
            FROM
                KusaHistory
            WHERE
                qq = ? AND strftime('%s', createTime) - 0 < ? AND strftime('%s', createTime) - 0 > ?
        ''', [qqNum, endTime.timestamp(), startTime.timestamp()])
    return rows[0]


async def noKusaAdvHistory(qqNum, limit: int):
    rows = await KusaHistory.filter(qq=qqNum).order_by('-createTime').limit(limit)
    return rows


async def kusaHistoryTotalReport(interval):
    conn = Tortoise.get_connection('default')
    rows = await conn.execute_query_dict(f'''
        SELECT
            count(*) AS count,
            sum(kusaResult) AS sumKusa,
            sum(advKusaResult) AS sumAdvKusa
        FROM
            KusaHistory
        WHERE
            strftime('%s', CURRENT_TIMESTAMP) - strftime('%s', createTime) < ?
    ''', [interval])
    return rows[0]


async def kusaFarmChampion():
    async def executeChampionQuery(conn, select: str, orderBy: str):
        rows = await conn.execute_query_dict(f'''
                SELECT
                    qq,
                    {select}
                FROM
                    KusaHistory
                WHERE
                    strftime('%s', CURRENT_TIMESTAMP) - strftime('%s', createTime) < 86400
                GROUP BY
                    qq
                ORDER BY
                    {orderBy} DESC
            ''', [])
        return rows[0]
    conn = Tortoise.get_connection('default')
    maxTimes = await executeChampionQuery(conn, "count(*) AS count", "count")
    maxKusa = await executeChampionQuery(conn, "sum(kusaResult) AS sumKusa", "sumKusa")
    maxAdvKusa = await executeChampionQuery(conn, "sum(advKusaResult) AS sumAdvKusa", "sumAdvKusa")
    maxAvgAdvKusa = await executeChampionQuery(conn, "avg(advKusaResult) AS avgAdvKusa", "avgAdvKusa")
    maxOnceAdvKusa = await executeChampionQuery(conn, "max(advKusaResult) AS maxAdvKusa", "maxAdvKusa")
    return maxTimes, maxKusa, maxAdvKusa, maxAvgAdvKusa, maxOnceAdvKusa


async def kusaOnceRanking(userId=None, limit=25):
    if userId:
        return await KusaHistory.filter(qq=userId).order_by('-kusaResult').limit(limit)
    return await KusaHistory.all().order_by('-kusaResult').limit(limit)


async def kusaAdvOnceRanking(userId=None, limit=25):
    if userId:
        return await KusaHistory.filter(qq=userId).order_by('-advKusaResult').limit(limit)
    return await KusaHistory.all().order_by('-advKusaResult').limit(limit)
