from .models import ChatUser, ChatRole


async def getChatUser(qqNum) -> ChatUser:
    return await ChatUser.filter(qq=qqNum).first()


async def getChatRoleById(roleId: int) -> ChatRole:
    return await ChatRole.filter(id=roleId).first()


async def getChatUserListByNowRoleId(roleId: int):
    return await ChatUser.filter(chosenRoleId=roleId).all()


async def getChatRoleByUserAndRoleName(qqNum, roleName: str, allowPublic: bool) -> ChatRole:
    # 自建角色优先级高于公用角色
    role = await ChatRole.filter(creator=qqNum).filter(name=roleName).first()
    if role or not allowPublic:
        return role
    return await ChatRole.filter(isPublic=True).filter(name=roleName).first()


async def getChatRoleList(qqNum):
    return await ChatRole.filter(creator=qqNum).all()


async def getPublicRoleList():
    return await ChatRole.filter(isPublic=True).all()


async def updateChatUser(qqNum, userMode: str):
    allowContinue = True if 'c' in userMode else False
    allowPrivate = True if 'p' in userMode else False
    allowGroup = True if 'g' in userMode else False
    allowRole = True if 'r' in userMode else False
    allowModel = True if 'm' in userMode else False
    await ChatUser.update_or_create(qq=qqNum, defaults={
        'allowContinue': allowContinue, 'allowPrivate': allowPrivate, 'allowGroup': allowGroup,
        'allowRole': allowRole, 'allowModel': allowModel
    })


async def updateUsingModel(qqNum, newModel):
    chatUser = await getChatUser(qqNum)
    chatUser.chosenModel = newModel
    await chatUser.save()


async def changeUsingRole(qqNum, roleName):
    chatUser = await getChatUser(qqNum)
    if not roleName:
        chatUser.chosenRoleId = 0
        await chatUser.save()
        return True
    role = await getChatRoleByUserAndRoleName(qqNum, roleName, True)
    if role:
        chatUser.chosenRoleId = role.id
        await chatUser.save()
        return True
    return False


async def updateRoleDetail(qqNum, roleName, detail, isPublic: bool):
    role = await getChatRoleByUserAndRoleName(qqNum, roleName, False)
    if role:
        role.detail = detail
        role.isPublic = isPublic
        await role.save()
    else:
        await ChatRole.create(creator=qqNum, name=roleName, detail=detail, isPublic=isPublic)


async def deleteRole(role: ChatRole):
    await role.delete()


async def addTokenUsage(chatUser: ChatUser, model: str, tokenUse: int):
    # 以deepseek-chat定价为基准，其他模型按比例大概换算
    if model == "gpt-5":
        # gpt-5 input 1.25刀/1m output 10刀/1m
        chatUser.tokenUse += tokenUse * 2
    if model == "gpt-5-mini":
        # gpt-5-mini input 0.25刀/1m output 2刀/1m
        chatUser.tokenUse += tokenUse // 2
    if model == "gpt-5-nano":
        # gpt-5-nano input 0.05刀/1m output 0.4刀/1m
        chatUser.tokenUse += tokenUse // 10
    if "deepseek" in model:
        # deepseek统一定价 input 4元/1m output 12元/1m
        chatUser.tokenUse += tokenUse
    chatUser.tokenUse += tokenUse
    await chatUser.save()
