import datetime
from .models import GValue


async def getLatestCycle():
    latestValues = await getLatestGValues()
    return latestValues.cycle


async def getLatestGValues():
    return await GValue.all().order_by("-createTime").first()


async def getSecondLatestGValues():
    return await GValue.all().order_by("-createTime").offset(1).first()


async def getThisCycleGValues():
    cycle = await getLatestCycle()
    return await GValue.filter(cycle=cycle)


async def getLastCycleGValues():
    cycle = await getLatestCycle()
    return await GValue.filter(cycle=cycle - 1)



async def addNewGValue(cycle, turn, eg, sg, ng, zg, szg):
    nowTime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    await GValue.create(cycle=cycle, turn=turn,
                        eastValue=eg, southValue=sg, northValue=ng, zhuhaiValue=zg, shenzhenValue=szg,
                        createTime=nowTime)
