from .models import WorkOrder


async def getWorkOrderById(orderId):
    return await WorkOrder.filter(id=orderId).first()


async def getUnreadWorkOrders():
    return await WorkOrder.filter(reply="")


async def addWorkOrder(author, title, detail):
    await WorkOrder.create(author=author, title=title, detail=detail, reply="")


async def replyWorkOrder(workOrder: WorkOrder, reply):
    workOrder.reply = reply
    await workOrder.save()
