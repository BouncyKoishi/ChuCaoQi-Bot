import time
import nonebot
import aiocqhttp
from kusa_base import config
import dbConnection.db as db

lastSpellRecord = dict()
repeatWarning = dict()


@nonebot.message_preprocessor
async def func(bot: nonebot.NoneBot, event: aiocqhttp.Event, plugin_manager: nonebot.plugin.PluginManager):
    global lastSpellRecord
    global repeatWarning

    if event.type == "message" and event.raw_message.startswith('!'):
        await db.createUser(event.user_id)
        if event.user_id in config['qq']['ban']:
            raise nonebot.message.CanceledException("此人处于除草器指令黑名单，跳过指令响应")
        if event.detail_type == "group":
            if event.group_id not in config['group']['allow']:
                raise nonebot.message.CanceledException("非可用群，跳过指令响应")
        
        # 记录触发指令时间，屏蔽刷指令
        warningCount = repeatWarning.get(event.user_id)
        if warningCount and warningCount >= 8:
            raise nonebot.message.CanceledException("刷指令人员，暂时屏蔽所有服务")
        if event.user_id in lastSpellRecord:
            recordTimeStamp = lastSpellRecord[event.user_id]
            if time.time() - recordTimeStamp <= 0.5:
                if warningCount:
                    warningCount += 1
                else:
                    warningCount = 1
                repeatWarning[event.user_id] = warningCount
                if warningCount >= 8:
                    msg = '识别到恶意刷指令。除草器所有服务对你停止1小时。'
                    if event.detail_type == "group":
                        await bot.send_group_msg(group_id=event.group_id, message=msg)
                    else:
                        await bot.send_private_msg(user_id=event.user_id, message=msg)
        lastSpellRecord[event.user_id] = time.time()


@nonebot.scheduler.scheduled_job('interval', minutes=1)
async def cleanWarning():
    global repeatWarning
    for key in repeatWarning:
        if time.time() - lastSpellRecord[key] > 3600:
            repeatWarning[key] = 0

