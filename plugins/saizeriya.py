from __future__ import annotations

import random
import typing
from nonebot import on_command, CommandSession


class SaizeriyaMenuItem(typing.NamedTuple):
    id: int
    name: str
    price: int


saizeriyaGDMenu = (
    SaizeriyaMenuItem(id=1245, name='意式小吃拼盘', price=32),
    SaizeriyaMenuItem(id=1218, name='原味煮花蛤', price=13),
    SaizeriyaMenuItem(id=1607, name='鸡翅鸡排牛肉粒拼盘', price=49),
    SaizeriyaMenuItem(id=1509, name='番茄海鲜意面', price=22),
    SaizeriyaMenuItem(id=1011, name='金枪鱼沙拉', price=12),
    SaizeriyaMenuItem(id=1235, name='鱿鱼花蛤拼盘', price=26),
    SaizeriyaMenuItem(id=1116, name='蘑菇汤', price=9),
    SaizeriyaMenuItem(id=1208, name='意式茄红鸡翅', price=26),
    SaizeriyaMenuItem(id=1231, name='意式小吃拼盘配香芹酱', price=28),
    SaizeriyaMenuItem(id=1513, name='黑椒牛柳意面', price=18),
    SaizeriyaMenuItem(id=1387, name='榴莲小匹萨（6英寸）', price=21),
    SaizeriyaMenuItem(id=1613, name='烘烤羊排（2根）', price=49),
    SaizeriyaMenuItem(id=1888, name='畅饮', price=8),
    SaizeriyaMenuItem(id=1117, name='田园蔬菜汤', price=9),
    SaizeriyaMenuItem(id=1115, name='玉米汤', price=9),
    SaizeriyaMenuItem(id=1012, name='水果沙拉', price=9),
    SaizeriyaMenuItem(id=1013, name='海带丝沙拉', price=9),
    SaizeriyaMenuItem(id=1014, name='甜玉米沙拉', price=9),
    SaizeriyaMenuItem(id=1114, name='花蛤裙菜海鲜汤', price=9),
    SaizeriyaMenuItem(id=1290, name='蒜香花椰菜', price=9),
    SaizeriyaMenuItem(id=1289, name='什锦鲜蔬', price=12),
    SaizeriyaMenuItem(id=1288, name='白糖烤饼', price=5),
    SaizeriyaMenuItem(id=1287, name='蒜香烤饼', price=7),
    SaizeriyaMenuItem(id=1286, name='原味烤饼', price=5),
    SaizeriyaMenuItem(id=1246, name='椒盐鸡腿排', price=16),
    SaizeriyaMenuItem(id=1242, name='蒜香烤面包片', price=7),
    SaizeriyaMenuItem(id=1241, name='原味烤面包片', price=5),
    SaizeriyaMenuItem(id=1233, name='黑椒烤肠', price=16),
    SaizeriyaMenuItem(id=1226, name='烤甜玉米', price=7),
    SaizeriyaMenuItem(id=1204, name='QQ薯角', price=7),
    SaizeriyaMenuItem(id=1224, name='烤菠菜', price=7),
    SaizeriyaMenuItem(id=1229, name='芝士烤玉米', price=9),
    SaizeriyaMenuItem(id=1240, name='海带丝', price=9),
    SaizeriyaMenuItem(id=1232, name='盐酥鸡肉粒', price=13),
    SaizeriyaMenuItem(id=1275, name='芝士奶汁土豆泥', price=13),
    SaizeriyaMenuItem(id=1234, name='五目烤肠', price=16),
    SaizeriyaMenuItem(id=1209, name='本色烤全鱿', price=22),
    SaizeriyaMenuItem(id=1393, name='肉酱培根小匹萨（6英寸含酸菜）', price=14),
    SaizeriyaMenuItem(id=1389, name='香肠小匹萨（6英寸）', price=14),
    SaizeriyaMenuItem(id=1382, name='水果小匹萨（6英寸）', price=15),
    SaizeriyaMenuItem(id=1380, name='培根菠萝小匹萨（6英寸）', price=14),
    SaizeriyaMenuItem(id=1307, name='榴莲大匹萨（8英寸）', price=39),
    SaizeriyaMenuItem(id=1305, name='培根菠萝匹萨（8英寸）', price=22),
    SaizeriyaMenuItem(id=1420, name='金枪鱼焗意面', price=18),
    SaizeriyaMenuItem(id=1419, name='肉酱香肠芝士烤饭（含酸菜）', price=18),
    SaizeriyaMenuItem(id=1416, name='香烤鸡肉焗饭', price=18),
    SaizeriyaMenuItem(id=1410, name='海鲜焗意面', price=18),
    SaizeriyaMenuItem(id=1409, name='米饭', price=2),
    SaizeriyaMenuItem(id=1408, name='肉酱焗意面', price=18),
    SaizeriyaMenuItem(id=1404, name='鸡排烤饭', price=20),
    SaizeriyaMenuItem(id=1403, name='肉酱焗饭', price=19),
    SaizeriyaMenuItem(id=1402, name='芝士肉酱焗饭', price=23),
    SaizeriyaMenuItem(id=1415, name='芝士香烤鸡肉焗饭', price=23),
    SaizeriyaMenuItem(id=1405, name='蒜香鸡肉培根芝士烤饭', price=19),
    SaizeriyaMenuItem(id=1401, name='番茄海鲜烩饭', price=19),
    SaizeriyaMenuItem(id=1535, name='酸菜培根意面', price=12),
    SaizeriyaMenuItem(id=1512, name='墨鱼汁意面', price=15),
    SaizeriyaMenuItem(id=1523, name='蒜香茄汁鲜菇金枪鱼意面', price=18),
    SaizeriyaMenuItem(id=1505, name='青酱汁意面', price=14),
    SaizeriyaMenuItem(id=1617, name='烤肠鸡排牛肉粒拼盘', price=49),
    SaizeriyaMenuItem(id=1612, name='烤肠鸡排羊排拼盘', price=49),
    SaizeriyaMenuItem(id=1608, name='黑椒烤肠配黑椒鸡排', price=23),
    SaizeriyaMenuItem(id=1605, name='香烤鸡排（蒜香酱）', price=19),
    SaizeriyaMenuItem(id=1606, name='香烤鸡排（黑椒酱）', price=19),
    SaizeriyaMenuItem(id=1615, name='五目肠配香烤鸡排（蒜香酱）', price=24),
    SaizeriyaMenuItem(id=1603, name='牛排（黑椒风味）', price=49),
    SaizeriyaMenuItem(id=1602, name='牛排（蒜香风味）', price=49),
    SaizeriyaMenuItem(id=1601, name='鱿鱼配香烤鸡排', price=37),
    SaizeriyaMenuItem(id=1977, name='蓝布鲁斯科气泡', price=36),
    SaizeriyaMenuItem(id=1812, name='柠檬红茶', price=5),
    SaizeriyaMenuItem(id=1811, name='芬达', price=5),
    SaizeriyaMenuItem(id=1810, name='雪碧', price=5),
    SaizeriyaMenuItem(id=1809, name='可口可乐', price=5),
    SaizeriyaMenuItem(id=1733, name='草莓千层蛋糕配薄脆巧克力酱冰激凌', price=22),
    SaizeriyaMenuItem(id=1732, name='薄脆巧克力酱冰激凌', price=9),
    SaizeriyaMenuItem(id=1731, name='薄脆树莓果酱冰激凌', price=9),
    SaizeriyaMenuItem(id=1726, name='草莓千层蛋糕', price=16),
    SaizeriyaMenuItem(id=1717, name='激情果粒', price=8),
    SaizeriyaMenuItem(id=1713, name='芒果布丁', price=8),
    SaizeriyaMenuItem(id=1719, name='焦糖布丁', price=16),
    SaizeriyaMenuItem(id=1907, name='麒麟啤酒', price=10),
    SaizeriyaMenuItem(id=1921, name='赤霞珠干红葡萄酒', price=36),
    SaizeriyaMenuItem(id=1924, name='霞多丽干白葡萄酒', price=36),
    SaizeriyaMenuItem(id=1969, name='蒂安诺干红葡萄酒', price=58),
    SaizeriyaMenuItem(id=1022, name='海带丝沙拉（橄榄香草醋汁）', price=9),
    SaizeriyaMenuItem(id=1372, name='罗勒酱鸡肉小匹萨（6英寸）', price=18),
    SaizeriyaMenuItem(id=3372, name='罗勒酱鸡肉小匹萨加芝士（6英寸）', price=22),
    SaizeriyaMenuItem(id=1373, name='魔鬼小匹萨（6英寸）', price=18),
    SaizeriyaMenuItem(id=3373, name='魔鬼小匹萨加芝士（6英寸）', price=22),
    SaizeriyaMenuItem(id=1311, name='水果培根大匹萨（8英寸）', price=23),
    SaizeriyaMenuItem(id=3311, name='水果培根大匹萨加芝士（8英寸）', price=27),
    SaizeriyaMenuItem(id=1425, name='虾仁甜豌豆奶汁烩饭', price=17),
    SaizeriyaMenuItem(id=1560, name='博洛尼亚肉酱意面原味（含葡萄酒）', price=18),
    SaizeriyaMenuItem(id=1561, name='博洛尼亚肉酱意面辣味（含葡萄酒）', price=18),
    SaizeriyaMenuItem(id=1641, name='芝芝多多微辣辣鸡排', price=24),
    SaizeriyaMenuItem(id=1918, name='朝日啤酒', price=10),
    SaizeriyaMenuItem(id=1020, name='金枪鱼沙拉（橄榄香草醋汁）', price=12),
    SaizeriyaMenuItem(id=1270, name='蒜香黄油蜗牛配焦香小面包', price=19),
    SaizeriyaMenuItem(id=1244, name='人气小吃拼盘', price=28),
    SaizeriyaMenuItem(id=1547, name='肉酱意面', price=18),
    SaizeriyaMenuItem(id=1631, name='黄花鱼慕尼尔（裹粉蒜香黄油烤）', price=32),
    SaizeriyaMenuItem(id=1632, name='黄花鱼慕尼尔配意式肉丸', price=37),
    SaizeriyaMenuItem(id=1623, name='原切安格斯眼肉牛排（8分熟）', price=59),
    SaizeriyaMenuItem(id=1021, name='水果沙拉（橄榄香草醋汁）', price=9),
    SaizeriyaMenuItem(id=1023, name='甜玉米沙拉（橄榄香草醋汁）', price=9),
    SaizeriyaMenuItem(id=1019, name='布拉塔芝士沙拉（萨莉亚沙拉酱）', price=16),
    SaizeriyaMenuItem(id=1025, name='布拉塔沙拉（橄榄香草醋汁）', price=16),
    SaizeriyaMenuItem(id=1112, name='玉米汤', price=9),
    SaizeriyaMenuItem(id=1118, name='蘑菇汤', price=9),
    SaizeriyaMenuItem(id=1119, name='奶油海鲜汤', price=9),
    SaizeriyaMenuItem(id=1299, name='柠檬瓣', price=1),
    SaizeriyaMenuItem(id=1210, name='橄榄香草醋汁', price=1),
    SaizeriyaMenuItem(id=1264, name='特级初榨橄榄油', price=1),
    SaizeriyaMenuItem(id=1283, name='蜂蜜（8g/包）', price=1),
    SaizeriyaMenuItem(id=1296, name='意式辣椒酱', price=1),
    SaizeriyaMenuItem(id=1211, name='芝士粉', price=2),
    SaizeriyaMenuItem(id=1278, name='意式香芹酱', price=2),
    SaizeriyaMenuItem(id=1239, name='温泉蛋', price=4),
    SaizeriyaMenuItem(id=1257, name='佛卡夏', price=5),
    SaizeriyaMenuItem(id=1268, name='焦香小面包', price=5),
    SaizeriyaMenuItem(id=1258, name='蒜香佛卡夏', price=7),
    SaizeriyaMenuItem(id=1269, name='蒜香小面包', price=7),
    SaizeriyaMenuItem(id=1253, name='芝士烤菠菜', price=9),
    SaizeriyaMenuItem(id=1250, name='蒜香黄油炒菜心', price=9),
    SaizeriyaMenuItem(id=1255, name='橄榄油炒西葫芦', price=9),
    SaizeriyaMenuItem(id=1292, name='白葡萄酒炒什锦菌菇', price=9),
    SaizeriyaMenuItem(id=1277, name='布拉塔芝士（50g/个）', price=9),
    SaizeriyaMenuItem(id=1294, name='甜豌豆配温泉蛋', price=11),
    SaizeriyaMenuItem(id=1295, name='奶汁局甜豌豆', price=11),
    SaizeriyaMenuItem(id=1205, name='弗利塔塔（意式杂蔬烘蛋）', price=13),
    SaizeriyaMenuItem(id=1261, name='意式茄汁烤肉丸', price=13),
    SaizeriyaMenuItem(id=1262, name='香烤鱿鱼嘴', price=13),
    SaizeriyaMenuItem(id=1265, name='原味煮花蛤', price=13),
    SaizeriyaMenuItem(id=1282, name='香烤鸡肉丁配意式香芹酱', price=13),
    SaizeriyaMenuItem(id=1291, name='芝士肉酱烤茄子', price=13),
    SaizeriyaMenuItem(id=1279, name='橄榄油香草烤鲍鱼', price=21),
    SaizeriyaMenuItem(id=1502, name='热那亚风味罗勒酱意面', price=15),
    SaizeriyaMenuItem(id=1546, name='芝士番茄培根意面', price=15),
    SaizeriyaMenuItem(id=1552, name='戈贡佐拉“臭”芝士意面', price=15),
    SaizeriyaMenuItem(id=1558, name='蒜香花蛤菜心辣味意面', price=15),
    SaizeriyaMenuItem(id=1559, name='金枪鱼茄子阿拉比阿塔辣味意面', price=18),
    SaizeriyaMenuItem(id=1544, name='牛肝菌酱鸡肉奶汁意面', price=22),
    SaizeriyaMenuItem(id=1549, name='番茄海鲜意面', price=22),
    SaizeriyaMenuItem(id=1499, name='米饭（五常大米）', price=3),
    SaizeriyaMenuItem(id=1424, name='牛肝菌酱鸡肉芝士烤饭', price=21),
    SaizeriyaMenuItem(id=1423, name='海鲜烩饭', price=17),
    SaizeriyaMenuItem(id=1430, name='曙光女神酱烩饭', price=17),
    SaizeriyaMenuItem(id=1377, name='四喜芝士小匹萨（6英寸）', price=15),
    SaizeriyaMenuItem(id=3377, name='四喜芝士小匹萨加芝士（6英寸）', price=19),
    SaizeriyaMenuItem(id=3382, name='水果小匹萨加芝士（6英寸）', price=19),
    SaizeriyaMenuItem(id=1396, name='鸡肉培根小匹萨（6英寸）', price=15),
    SaizeriyaMenuItem(id=3396, name='鸡肉培根小匹萨加芝士（6英寸）', price=19),
    SaizeriyaMenuItem(id=1379, name='布拉塔芝士小匹萨（6英寸）', price=18),
    SaizeriyaMenuItem(id=1398, name='马苏里拉芝士小匹萨（6英寸）', price=18),
    SaizeriyaMenuItem(id=3398, name='马苏里拉芝士小匹萨加芝士（6英寸）', price=22),
    SaizeriyaMenuItem(id=3387, name='榴莲小匹萨加芝士（6英寸）', price=25),
    SaizeriyaMenuItem(id=1399, name='塞拉诺火腿配佛卡夏', price=21),
    SaizeriyaMenuItem(id=1374, name='塞拉诺火腿布拉塔佛卡夏（6英寸）', price=29),
    SaizeriyaMenuItem(id=3307, name='榴莲大匹萨加芝士（8英寸）', price=43),
    SaizeriyaMenuItem(id=1639, name='意式煮牛肚', price=21),
    SaizeriyaMenuItem(id=1627, name='意式肉丸配香烤鸡排', price=24),
    SaizeriyaMenuItem(id=1630, name='五目肠配香烤鸡排（黑椒酱）', price=24),
    SaizeriyaMenuItem(id=1744, name='意式酸奶树莓果酱', price=9),
    SaizeriyaMenuItem(id=1752, name='坚果树莓果酱冰淇淋', price=9),
    SaizeriyaMenuItem(id=1753, name='肉桂糖佛卡夏配香草冰淇淋', price=11),
    SaizeriyaMenuItem(id=1747, name='意大利香柠雪芭', price=12),
    SaizeriyaMenuItem(id=1741, name='红酒啤梨配香草冰淇淋', price=13),
    SaizeriyaMenuItem(id=1748, name='浓郁巧克力配清爽薄荷冰淇淋', price=13),
    SaizeriyaMenuItem(id=1750, name='提拉米苏冰蛋糕', price=16),
    SaizeriyaMenuItem(id=1914, name='阿佩罗柠檬斯普里茨（含酒精）', price=15),
    SaizeriyaMenuItem(id=1917, name='莫斯卡托干白葡萄酒', price=16),
    SaizeriyaMenuItem(id=1978, name='蓝布鲁斯科半甜型气泡葡萄酒', price=36),
    SaizeriyaMenuItem(id=1643, name='安格斯焦香牛肉汉堡', price=24),
    SaizeriyaMenuItem(id=1749, name='柠檬芝士蛋糕', price=12),
    SaizeriyaMenuItem(id=1640, name='波凯塔（意式香草脆皮猪肉卷）', price=24),
    SaizeriyaMenuItem(id=1754, name='蓝莓芝士蛋糕', price=12),
    SaizeriyaMenuItem(id=130, name='肉酱茄子香肠烤饭套餐（炖蔬菜）', price=27),
    SaizeriyaMenuItem(id=131, name='鸡排烤饭套（炖蔬菜）', price=27),
    SaizeriyaMenuItem(id=132, name='肉酱意面套餐（炖蔬菜）', price=27),
    SaizeriyaMenuItem(id=133, name='黑椒牛柳意面套餐（炖蔬菜）', price=27),
    SaizeriyaMenuItem(id=134, name='四喜芝士小匹萨套餐（炖蔬菜）', price=27),
    SaizeriyaMenuItem(id=140, name='肉酱茄子香肠烤饭套餐（烤菠菜）', price=27),
    SaizeriyaMenuItem(id=141, name='鸡排烤饭套餐（烤菠菜）', price=27),
    SaizeriyaMenuItem(id=142, name='肉酱意面套餐（烤菠菜）', price=27),
    SaizeriyaMenuItem(id=143, name='黑椒牛柳意面套餐（烤菠菜）', price=27),
    SaizeriyaMenuItem(id=144, name='四喜芝士小匹萨套餐（烤菠菜）', price=27),
    SaizeriyaMenuItem(id=146, name='鸡排烤饭套餐（烤菠菜）', price=25),
)

saizeriyaGDMenuPriceTotal = sum(x.price for x in saizeriyaGDMenu)


# 基本上是 https://github.com/TransparentLC/saizeriya/blob/master/src/main.js 的移植
def rollMenu(budgetMin: int, budgetMax: int | None = None) -> str:
    if budgetMax is None:
        budgetMax = budgetMin
    if budgetMin < 1:
        budgetMin = 1
    if budgetMax < 1:
        budgetMax = 1
    if budgetMin > budgetMax:
        budgetMin, budgetMax = budgetMax, budgetMin
    if budgetMax > 500:
        budgetMax = 500
    if budgetMin > 500:
        return '吃这么多，你是幽幽子吗 ( ｡╹ω╹｡ )'
    if budgetMax < min(x.price for x in saizeriyaGDMenu):
        return '这么点钱能吃啥啊 …_φ(･ω･` )'

    # 为了使每次运行的结果不一样，将菜单随机打乱
    randomizedMenu = list(saizeriyaGDMenu)
    random.shuffle(randomizedMenu)

    # 已经尝试过的预算值
    budgetTried: set[int] = set()
    result: list[SaizeriyaMenuItem] = []

    for _ in range(64):
        if len(budgetTried) >= (budgetMax - budgetMin + 1) or len(result):
            break
        result = []

        while True:
            budget = random.randint(budgetMin, budgetMax)
            if budget not in budgetTried:
                break
        budgetTried.add(budget)

        if budget == saizeriyaGDMenuPriceTotal:
            result = randomizedMenu
        else:
            subset = [
                [False for _ in range(budget + 1)]
                for _ in range(len(randomizedMenu) + 1)
            ]

            for i in range(budget + 1):
                subset[0][i] = False
            for i in range(len(randomizedMenu) + 1):
                subset[i][0] = True
            for i in range(1, len(randomizedMenu) + 1):
                for j in range(1, budget + 1):
                    subset[i][j] = (
                        subset[i - 1][j]
                        if j < randomizedMenu[i - 1].price else
                        (subset[i - 1][j] or subset[i - 1][j - randomizedMenu[i - 1].price])
                    )
            if subset[len(randomizedMenu)][budget]:
                for i in range(len(randomizedMenu), -1, -1):
                    if subset[i][budget] and not subset[i - 1][budget]:
                        result.append(randomizedMenu[i - 1])
                        budget -= randomizedMenu[i - 1].price
                    if not budget:
                        break

    if not result:
        return '居然找不到符合要求的点餐方案……( >﹏<。)'
    result.sort(key=lambda x: x.id)
    return '\n'.join((
        f'你点了{len(result)}份菜',
        *(f'{x.id} {x.name} {x.price}元' for x in result),
        f'总消费：{sum(x.price for x in result)}元',
    ))


@on_command(name='点餐', aliases={'saizeriya'}, only_to_me=False)
async def _(session: CommandSession):
    strippedText = session.current_arg_text.strip()
    if not strippedText:
        await session.send('没有输入预算或预算范围^ ^')
        return
    try:
        if '-' in strippedText:
            budgetMin, budgetMax = map(int, strippedText.split('-'))
        else:
            budgetMin = budgetMax = int(strippedText)
    except ValueError:
        await session.send('输入的预算格式不正确^ ^')
        return
    result = rollMenu(budgetMin, budgetMax)
    await session.send(result)
