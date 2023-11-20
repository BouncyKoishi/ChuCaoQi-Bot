import datetime
from tortoise import Tortoise
from tortoise.functions import Count, Sum, Avg
from .models import KusaField, KusaHistory


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


async def kusaHistoryAdd(qqNum):
    kusaField = await getKusaField(qqNum)
    if kusaField:
        kusa = kusaField.kusaResult * 2 if kusaField.kusaType == '灵草' else kusaField.kusaResult
        advKusa = kusaField.advKusaResult * 2 if kusaField.kusaType == '灵草' else kusaField.advKusaResult
        await KusaHistory.create(qq=kusaField.qq, kusaType=kusaField.kusaType, kusaResult=kusa, advKusaResult=advKusa)


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