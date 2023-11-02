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


async def addTokenUsage(chatUser: ChatUser, tokenUse: int):
    modelName = chatUser.chosenModel
    if modelName == "gpt-3.5-turbo":
        chatUser.tokenUse += tokenUse
    elif modelName == "gpt-4":
        chatUser.tokenUseGPT4 += tokenUse
    chatUser.tokenUse += tokenUse
    await chatUser.save()
