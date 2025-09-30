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

BASE_PIC_PATH = config['basePath'] + r'\picArchive'
SAVE_PATH = BASE_PIC_PATH + r'\私藏'
EXAMINE_PATH = BASE_PIC_PATH + r'\待分类'

archiveInfo = {
    "jun": {"onlinePath": BASE_PIC_PATH + r'\jun\online', "displayName": "罗俊"},
    "junOrigin": {"onlinePath": BASE_PIC_PATH + r'\jun\origin', "displayName": "纯净罗俊"},
    "xhb": {"onlinePath": BASE_PIC_PATH + r'\xhb', "displayName": "xhb"},
    "tudou": {"onlinePath": BASE_PIC_PATH + r'\土豆泥', "displayName": "土豆"},
    "zundamon": {"onlinePath": BASE_PIC_PATH + r'\豆包2.0', "displayName": "俊达萌"},
}
for value in archiveInfo.values():
    value['onlineFilePaths'] = glob.glob(os.path.join(value['onlinePath'], '*.*'))
    value['onlineFilePaths'].sort()


def getExamineFiles():
    return glob.glob(os.path.join(EXAMINE_PATH, '*.*'))


@nonebot.scheduler.scheduled_job('cron', day='*')
async def dailyJun():
    bot = nonebot.get_bot()
    now = datetime.now(pytz.timezone('Asia/Shanghai'))
    paths = archiveInfo['jun']['onlineFilePaths']
    picPath = paths[int(random.random() * len(paths))]
    st = f'新的一天！今天是{now.year}年{now.month}月{now.day}日！今天的精选罗俊是——'
    await bot.send_group_msg(group_id=config['group']['sysu'], message=st)
    await bot.send_group_msg(group_id=config['group']['sysu'], message=utils.imgLocalPathToBase64(picPath))


@on_command(name='rolllj', only_to_me=False)
async def _(session: CommandSession):
    await rollPic(session, "jun")


@on_command(name='rollpurelj', only_to_me=False)
async def _(session: CommandSession):
    await rollPic(session, "junOrigin")


@on_command(name='rollxhb', only_to_me=False)
async def _(session: CommandSession):
    await rollPic(session, "xhb")


@on_command(name='rolltd', only_to_me=False)
async def _(session: CommandSession):
    await rollPic(session, "tudou")


@on_command(name='rolljdm', aliases=('rollzdm', 'rollmd'), only_to_me=False)
async def _(session: CommandSession):
    await rollPic(session, "zundamon")


@on_command(name="commitpic", aliases=('commitlj', 'commitpurelj', 'commitxhb'), only_to_me=False)
async def _(session: CommandSession):
    await commitPic(session)


@on_command(name="examinepic", only_to_me=False)
async def _(session: CommandSession):
    await examinePic(session)


async def rollPic(session, imageArchiveName):
    if "group_id" not in session.ctx:
        return
    imageArchive = archiveInfo[imageArchiveName]
    paths = imageArchive['onlineFilePaths']
    if not paths:
        await session.send(f'{imageArchive["displayName"]} 图库为空')
        return
    picPath = paths[int(random.random() * len(paths))]
    await session.send(utils.imgLocalPathToBase64(picPath))
    print(f'本次发送的图片：{picPath}')


async def commitPic(session):
    await session.send(ms.at(session.ctx['user_id']) + ' 请上传图片')

    replyMsg = await session.aget(arg_filters=[str.strip])
    if not str(replyMsg).startswith('[CQ:image'):
        await session.send("非图片，取消本次上传")
        return

    picNameList = re.findall(r'(?<=,file=)\S+?(?=,)', replyMsg)
    picUrlList = utils.extractImgUrls(replyMsg)
    uploaderQQ = session.ctx['user_id']
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    for i in range(0, len(picNameList)):
        safeFilename = re.sub(r'[^\w\.-]', '_', picNameList[i])
        newFilename = f'{uploaderQQ}-{timestamp}-{safeFilename}'
        urlretrieve(picUrlList[i], rf'{EXAMINE_PATH}\{newFilename}')
    await session.send('上传成功，等待加入图库')


async def examinePic(session):
    if not await isSuperAdmin(session.ctx['user_id']):
        await session.send('该账号没有对应权限')
        return
    
    examineFiles = getExamineFiles()
    await session.send(f'开始审核，共有 {len(examineFiles)} 张待审核图片')

    # 生成图库选择菜单
    archiveMenu = "请进行图库分类：\n"
    archive_keys = list(archiveInfo.keys())
    for i, key in enumerate(archive_keys, 1):
        archiveMenu += f"{i}. {archiveInfo[key]['displayName']}\n"
    archiveMenu += "0. 跳过此图片\n"
    archiveMenu += "d. 删除此图片\n"
    archiveMenu += "s. 移动到保存目录\n"
    archiveMenu += "q. 退出审核"

    index = 0
    while index < len(examineFiles):
        currentFile = examineFiles[index]

        # 显示当前图片
        await session.send(utils.imgLocalPathToBase64(currentFile))

        try:
            # 显示文件名和选择菜单，获取输入
            fileName = os.path.basename(currentFile)
            prompt = f'文件名: {fileName}\n{archiveMenu}\n请输入选择'
            choice = await session.aget(prompt=prompt, arg_filters=[str.strip])
            choice = choice.lower()

            if choice == 'q':
                await session.send('已退出审核')
                break
            elif choice == '0':
                await session.send('已跳过此图片')
                index += 1
                continue
            elif choice == 'd':
                os.remove(currentFile)
                await session.send('图片已删除')
                examineFiles.pop(index)
                continue  # 不增加index，因为列表已更新
            elif choice == 's':
                os.makedirs(SAVE_PATH, exist_ok=True)
                new_path = os.path.join(SAVE_PATH, os.path.basename(currentFile))
                os.rename(currentFile, new_path)
                await session.send('图片已移动到保存目录')
                examineFiles.pop(index)
                continue
            elif choice.isdigit():
                choice_num = int(choice)
                if 1 <= choice_num <= len(archive_keys):
                    archive_key = archive_keys[choice_num - 1]
                    archive_path = archiveInfo[archive_key]['onlinePath']

                    # 确保目标目录存在
                    os.makedirs(archive_path, exist_ok=True)

                    # 移动文件到对应图库
                    filename_parts = fileName.split('-', 2)  # 分割成 [QQ号, 时间戳, 剩余部分]
                    if len(filename_parts) >= 3:
                        # 保留QQ号，移除时间戳，保留原始文件名
                        newFileName = f"{filename_parts[0]}-{filename_parts[2]}"
                    else:
                        # 如果文件名格式不符合预期，保持原文件名
                        newFileName = fileName
                    new_path = os.path.join(archive_path, newFileName)
                    os.rename(currentFile, new_path)

                    await session.send(f'图片已分类到 {archiveInfo[archive_key]["displayName"]} 图库')
                    examineFiles.pop(index)
                    continue
                else:
                    await session.send('无效的选择，请重新输入')
                    continue
            else:
                await session.send('无效的选择，请重新输入')
                continue

        except Exception as e:
            await session.send(f'处理时出现错误: {e}')
            index += 1
            continue

    # 更新各图库的图片列表
    for value in archiveInfo.values():
        value['onlineFilePaths'] = glob.glob(os.path.join(value['onlinePath'], '*.*'))
        value['onlineFilePaths'].sort()

    remainingCount = len(getExamineFiles())
    await session.send(f'审核结束，剩余 {remainingCount} 张待审核图片')
