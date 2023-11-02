import nonebot
import dbConnection.work_order as orderDB
from nonebot import on_command, CommandSession
from kusa_base import isSuperAdmin
from utils import nameDetailSplit, getUserAndGroupMsg


@on_command(name='提交工单', only_to_me=False)
async def _(session: CommandSession):
    stripped_arg = session.current_arg_text.strip()
    userId = session.ctx['user_id']
    title, detail = nameDetailSplit(stripped_arg)
    if not title:
        await session.send('至少需要一个工单标题！')
        return
    if len(title) > 128:
        await session.send('标题太长啦！最多128字')
        return
    if detail and len(detail) > 1024:
        await session.send('内容太长啦！最多1024字')
        return
    await orderDB.addWorkOrder(author=userId, title=title, detail=detail)
    await session.send('提交成功！等待开发者回复^ ^')


@on_command(name='查看工单', only_to_me=False)
async def _(session: CommandSession):
    userId = session.ctx['user_id']
    if not await isSuperAdmin(userId):
        await session.send('目前仅供开发者使用^ ^')
        return

    workOrders = await orderDB.getUnreadWorkOrders()
    outputStr = ""
    if workOrders:
        for order in workOrders:
            authorName, _ = await getUserAndGroupMsg(order.author)
            outputStr += f"[{order.id}]{order.title}"
            outputStr += f":{order.detail}\n" if order.detail else "\n"
            outputStr += f"提出者: {authorName}"
            outputStr += f"({order.author})\n\n" if authorName != order.author else "\n\n"
        outputStr = outputStr[:-2]
    else:
        outputStr = "没有，别追啦"
    await session.send(outputStr)


@on_command(name='回复工单', only_to_me=False)
async def _(session: CommandSession):
    userId = session.ctx['user_id']
    if not await isSuperAdmin(userId):
        await session.send('仅供开发者使用^ ^')
        return

    stripped_arg = session.current_arg_text.strip()
    args = stripped_arg.split(" ", 1)
    orderId, reply = args if len(args) == 2 else [None, None]
    if not orderId or not reply:
        await session.send('参数异常，请自检^ ^')
        return

    order = await orderDB.getWorkOrderById(orderId)
    notifyStr = f"开发者回复了你的工单[{order.title}]！\n"
    notifyStr += f"工单详情：{order.detail}\n" if order.detail else ""
    notifyStr += f"回复内容：{reply}"
    await nonebot.get_bot().send_private_msg(user_id=order.author, message=notifyStr)
    await orderDB.replyWorkOrder(order, reply)
    await session.send("回复成功^ ^")


@on_command(name='删除所有工单', only_to_me=False)
async def _(session: CommandSession):
    userId = session.ctx['user_id']
    if not await isSuperAdmin(userId):
        await session.send('仅供开发者使用^ ^')
        return

    workOrders = await orderDB.getUnreadWorkOrders()
    print(workOrders)
    if workOrders:
        for order in workOrders:
            await orderDB.replyWorkOrder(order, "---")
            try:
                notifyStr = f"开发者删除了你的工单[{order.title}]！"
                await nonebot.get_bot().send_private_msg(user_id=order.author, message=notifyStr)
            except:
                await session.send(f'错误：sendmsg api not available，qq={order.author}')
        await session.send("已经全部删除^ ^")
    else:
        await session.send("当前没有未回复的工单！")
