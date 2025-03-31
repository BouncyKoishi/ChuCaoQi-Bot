import re
import random
import asyncio
from nonebot import on_command, CommandSession
from dbConnection.draw_item import getItemsWithStorage, isPoolNameExist
from plugins.chatGPT_api import getChatReply

battle = {}
itemRareDescribe = ['Easy', 'Normal', 'Hard', 'Lunatic']


@on_command(name='对战', only_to_me=False)
async def _(session: CommandSession):
    global battle
    userId = session.ctx['user_id']
    if len(battle) >= 2:
        await session.send('有一场对战正在运行中！')
        return
    if userId in battle:
        await session.send('您已经在等待对战中！')
        return

    poolName = session.current_arg_text.strip()
    nameExist = await isPoolNameExist(poolName) if poolName else False
    itemList = await getItemsWithStorage(qqNum=userId, poolName=poolName) \
        if nameExist else await getItemsWithStorage(qqNum=userId)
    ownItems = [item for item in itemList if item.storage]
    if len(ownItems) == 0:
        await session.send('您没有可选物品，不能进行对战哦。')
        return

    output = '您创建了一场对战。' if len(battle) == 0 else '您加入了一场对战。'
    output += '请选择您想用于对战的物品:\n\n'
    itemOptions = random.sample(ownItems, min(3, len(ownItems)))
    descriptions = [
        f"{i + 1}. [{itemRareDescribe[item.rareRank]}]{item.name}\n" +
        (f'物品说明：{item.detail}' if item.detail else '暂无物品说明。')
        for i, item in enumerate(itemOptions)]
    userResponse = await session.aget(prompt=output + "\n\n".join(descriptions))
    if not re.match(r'^\d+$', userResponse):
        await session.send('非序号：物品选择失败，请重新创建/加入对战。')
        return
    selectedIndex = int(userResponse) - 1
    if selectedIndex < 0 or selectedIndex >= len(itemOptions):
        await session.send('无效的序号：物品选择失败，请重新创建/加入对战。')
        return
    selectedItem = itemOptions[selectedIndex]
    battle[userId] = selectedItem

    if len(battle) == 1:
        await session.send('你的物品已确认，等待你的对手……')
    elif len(battle) == 2:
        await session.send('创建对战中……')
        await battleMain(session)
        battle = {}
    elif len(battle) > 2:
        await session.send('似乎发生了异步问题呢，请等待下一次对战')


async def battleMain(session: CommandSession):
    battler1, battler2 = await asyncio.gather(
        getBattlerFromModel(battle[list(battle.keys())[0]]),
        getBattlerFromModel(battle[list(battle.keys())[1]])
    )
    battlerInfo = '已生成双方物品的对战数据。\n\n'
    battlerInfo += f'主玩家的物品：\n{battler1}\n\n'
    battlerInfo += f'副玩家的物品：\n{battler2}\n\n'
    battlerInfo += '正在启动对战……'
    await session.send(battlerInfo)
    battleResult = await getBattleInfoFromModel(battler1, battler2)
    await session.send(battleResult)


async def getBattlerFromModel(item):
    systemPrompt = '''
    接下来你模拟一个对战系统。该系统是一个回合制游戏，每个人选择一个物品进行对战，该物品每回合对敌方进行攻击，交替进行，当某方物品血量被耗尽时，对战结束并视为该方失败，对方胜利。
    每个物品具有血量，攻击力，命中值和回避值四个核心数值，除血量外，每个数值在一定范围内浮动，每回合中实际的数值为浮动范围内的任意数字。根据物品名称和简介，其在战斗中会有三种特效。
    物品存在Easy/Normal/Hard/Lunatic四档稀有度，高稀有度的符卡应有稍高的强度，但不宜与普通符卡差距过大。无论稀有度如何，特效数量都是三个。
    接下来我将输入一个物品的名字和简介，你输出该卡牌的数值和可能的特殊效果。物品特效应发挥创造性，不要被示例束缚，与物品名称和简介挂钩即可。
    我的输入可能仅有物品名，没有简介。在这种情况下你也要正常输出。
    
    示例如下：
    我的输入：
    [Easy]海洋女王
    物品说明：FFH最经常使用的符卡之一。FFH变身为海洋女王，并召唤海洋生物进行攻击。最佳时机是当对手处于弱点时。
    
    你的输出：
    海洋女王
    HP：280
    攻击力：45-52
    命中：80%-85%
    回避：5%-12%
    
    【特殊效果】
    「海潮共鸣」
    开场召唤三层海潮护盾（每层护盾可抵挡1次攻击），护盾被击破时引发小型潮旋造成[ATK×15%]持续伤害
    
    「珊瑚王座宣言」
    敌方血量首次低于50%时，召唤座头鲸进行一次终结攻击（ATK×200%+己方已损失HP10%）
    
    「怒涛之王」
    己方每损失10%HP，获得1层"怒涛"印记，每有一层提升5%暴击率与2%吸血效果
    '''
    inputStr = f'[{itemRareDescribe[item.rareRank]}]{item.name}\n' + f'物品说明：{item.detail}' if item.detail else '暂无物品说明。'
    prompt = [{"role": "system", "content": systemPrompt}, {"role": "user", "content": inputStr}]
    reply, tokenUsage = await getChatReply("deepseek-chat", prompt)
    print('tokenUsage:{}', tokenUsage)
    return reply


async def getBattleInfoFromModel(battler1, battler2):
    systemPrompt = '''
    接下来你模拟一个对战系统。该系统是一个回合制游戏，每个人选择一个物品进行对战，该物品每回合对敌方进行攻击，交替进行，当某方物品血量被耗尽时，对战结束并视为该方失败，对方胜利。
    每个物品具有血量，攻击力，命中值和回避值四个核心数值，除血量外，每个数值在一定范围内浮动，每回合中实际的数值为浮动范围内的任意数字。根据物品名称和简介，其在战斗中会有两种特殊效果。
    接下来我将输入两个物品的核心数值和特殊效果，你需要输出这两种物品的对战战报。战报需一定程度上文学化描述，无需体现具体数值，但需要体现特殊效果。
    '''
    inputStr = f'物品1的对战信息：\n{battler1}\n\n物品2的对战信息：\n{battler2}' if random.random() > 0.5 \
        else f'物品1的对战信息：\n{battler2}\n\n物品2的对战信息：\n{battler1}'
    prompt = [{"role": "system", "content": systemPrompt}, {"role": "user", "content": inputStr}]
    reply, tokenUsage = await getChatReply("deepseek-chat", prompt)
    print('tokenUsage:', tokenUsage)
    return reply
