from plugins.scBattle.AbstractCard import AbstractCard


class ScarletShootCard(AbstractCard):
    id = 22
    cost = 3

    def __init__(self):
        super().__init__()
        self.name = "红符「深红射击」"
        self.cardHp = 2
        self.atkPoint = "2d10"
        self.defPoint = "1"
        self.dodPoint = "1"
        self.describe = "无"


# class StarOfDavidCard(AbstractCard):
#     id = 1001
#     cost = 2
#
#     def __init__(self):
#         super().__init__()
#         self.name = "神罚「幼小的恶魔领主」"
#         self.cardHp = 2
#         self.atkPoint = "1d4"
#         self.defPoint = "1d4"
#         self.dodPoint = "1d4"
#         self.describe = "展开五回合的[吸血]结界"
#
#
# class VampireFantasyCard(AbstractCard):
#     id = 1002
#     cost = 3
#
#     def __init__(self):
#         super().__init__()
#         self.name = "神术「吸血鬼幻想」"
#         self.cardHp = 8
#         self.atkPoint = "1d12"
#         self.defPoint = "1d3"
#         self.dodPoint = "1d3"
#         self.describe = "本符卡的ATK roll点结果不会为5-10。"
#         self.nowEffectAmount = 0
#
#
# class ScarletGensokyoCard(AbstractCard):
#     id = 1003
#     cost = 5
#
#     def __init__(self):
#         super().__init__()
#         self.name = "「红色的幻想乡」"
#         self.cardHp = 16
#         self.atkPoint = "1d15"
#         self.defPoint = "1d3"
#         self.dodPoint = "1d3"
#         self.describe = "本符卡的ATK roll点结果不会为5-12。本符卡的最终ATK会附加上回合ATK值的50%。"
#         self.nowEffectAmount = 0
#
