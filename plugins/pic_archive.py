import re
import os
import glob
import nonebot
import pytz
import random
import utils
from kusa_base import config, isSuperAdmin
from datetime import datetime
from nonebot import on_command, CommandSession
from nonebot import MessageSegment as ms
from urllib.request import urlretrieve

BASE_PATH = config['basePath']
SAVE_PATH = BASE_PATH + r'\examinePicSave'
archiveInfo = {
    "jun": {
        "onlinePath": BASE_PATH + r'\jun\online',
        "examinePath": BASE_PATH + r'\jun\examine',
    },
    "junOrigin": {
        "onlinePath": BASE_PATH + r'\jun\origin',
        "examinePath": BASE_PATH + r'\jun\examine',
    },
    "xhb": {
        "onlinePath": BASE_PATH + r'\xhb\online',
        "examinePath": BASE_PATH + r'\xhb\examine',
    }
}
for value in archiveInfo.values():
    value['onlineFilePaths'] = glob.glob(os.path.join(value['onlinePath'], '*.*'))
    value['examineFilePaths'] = glob.glob(os.path.join(value['examinePath'], '*.*'))
    value['onlineFilePaths'].sort()


@nonebot.scheduler.scheduled_job('cron', day='*')
async def dailyJun():
    bot = nonebot.get_bot()
    now = datetime.now(pytz.timezone('Asia/Shanghai'))
    paths = archiveInfo['jun']['onlineFilePaths']
    picPath = paths[int(random.random() * len(paths))]
    st = f'新的一天！今天是{now.year}年{now.month}月{now.day}日！今天的精选罗俊是——'
    await bot.send_group_msg(group_id=config['group']['sysu'], message=st)
    await bot.send_group_msg(group_id=config['group']['sysu'], message=utils.getImgBase64(picPath))


@on_command(name='rolllj', only_to_me=False)
async def _(session: CommandSession):
    await rollPic(session, "jun")


@on_command(name='rollpurelj', only_to_me=False)
async def _(session: CommandSession):
    await rollPic(session, "junOrigin")


@on_command(name='rollxhb', only_to_me=False)
async def _(session: CommandSession):
    await rollPic(session, "xhb")


@on_command(name="commitlj", only_to_me=False)
async def _(session: CommandSession):
    await commitPic(session, "jun")


@on_command(name="commitxhb", only_to_me=False)
async def _(session: CommandSession):
    await commitPic(session, "xhb")


@on_command(name="examinelj", only_to_me=False)
async def _(session: CommandSession):
    await examinePic(session, "jun")


@on_command(name="examinepurelj", only_to_me=False)
async def _(session: CommandSession):
    await examinePic(session, "junOrigin")


@on_command(name="examinexhb", only_to_me=False)
async def _(session: CommandSession):
    await examinePic(session, "xhb")


async def rollPic(session, imageArchiveName):
    if "group_id" not in session.ctx:
        return
    imageArchive = archiveInfo[imageArchiveName]
    paths = imageArchive['onlineFilePaths']
    picPath = paths[int(random.random() * len(paths))]
    await session.send(utils.getImgBase64(picPath))
    print(f'本次发送的图片：{picPath}')


async def commitPic(session, imageArchiveName):
    await session.send(ms.at(session.ctx['user_id']) + ' 请上传图片')
    imageArchive = archiveInfo[imageArchiveName]

    replyMsg = await session.aget(arg_filters=[str.strip])
    if not str(replyMsg).startswith('[CQ:image'):
        await session.send("非图片，取消本次上传")
        return

    picNameList = re.findall(r'(?<=,file=)\S+?(?=,)', replyMsg)
    picUrlList = re.findall(r'(?<=,url=)\S+?(?=])', replyMsg)
    for i in range(0, len(picNameList)):
        uploaderQQ = session.ctx['user_id']
        examinePath = imageArchive['examinePath']
        urlretrieve(picUrlList[i], f'{examinePath}\{uploaderQQ}-{picNameList[i]}')

    await session.send('上传成功，等待加入图库')
    imageArchive['examineFilePaths'] = glob.glob(os.path.join(imageArchive['examinePath'], '*.*'))


async def examinePic(session, imageArchiveName):
    if not await isSuperAdmin(session.ctx['user_id']):
        await session.send('该账号没有对应权限')
        return

    await session.send('start examine')
    imageArchive = archiveInfo[imageArchiveName]
    while True:
        examine_paths = imageArchive['examineFilePaths']
        if not examine_paths:
            break
        await session.send(utils.getImgBase64(examine_paths[0]))
        file_name = examine_paths[0].split('\\')[-1]
        reply_msg = await session.aget(prompt=f'文件名:{file_name} (y/n/s)', arg_filters=[str.strip])
        if reply_msg == 'y':
            os.system(f"move \"{examine_paths[0]}\" \"{imageArchive['onlinePath']}\" ")
        elif reply_msg == 'n':
            os.system(f"del \"{examine_paths[0]}\" ")
        elif reply_msg == 's':
            os.system(f"move \"{examine_paths[0]}\" \"{SAVE_PATH}\" ")
        else:
            break
        imageArchive['examineFilePaths'].remove(examine_paths[0])

    await session.send('end examine')
    imageArchive['onlineFilePaths'] = glob.glob(os.path.join(imageArchive['onlinePath'], '*.*'))
    imageArchive['examineFilePaths'] = glob.glob(os.path.join(imageArchive['examinePath'], '*.*'))
    imageArchive['onlineFilePaths'].sort()
