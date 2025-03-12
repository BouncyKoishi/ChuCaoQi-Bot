from plugins.scBattle.AbstractCard import AbstractCard
from plugins.scBattle.scBattleUtils import runDiceByString


class KagomeCard(AbstractCard):
    id = 23
    cost = 2

    def __init__(self):
        super().__init__()
        self.name = "禁忌「笼中鸟」"
        self.cardHp = 6
        self.atkPoint = "1d3"
        self.defPoint = "1d4"
        self.dodPoint = "1d3"
        self.describe = "宣言时：获得[回避不可]"

    def onCardSet(self):
        self.user.appendEffect("CantDodge", 1)
        return ""

    def onCardBreak(self):
        self.user.removeEffect("CantDodge", 1)
        return ""


class FourOfAKindCard(AbstractCard):
    id = 24
    cost = 3

    def __init__(self):
        super().__init__()
        self.name = "禁忌「四重存在」"
        self.cardHp = 4
        self.atkPoint = "1d4"
        self.defPoint = "1d4"
        self.dodPoint = "0"
        self.describe = "破弃时：展开4回合的[强化结界1d4]"

    def onCardBreak(self):
        borderStrength = runDiceByString("1d4")
        self.user.appendBorder("StrengthBorder", 4, borderStrength)
        return f"{self.user.name}符卡破弃效果：展开4回合的[强化结界{borderStrength}]！"


class StarbowBreakCard(AbstractCard):
    id = 25
    cost = 3

    def __init__(self):
        super().__init__()
        self.name = "禁弹「星弧破碎」"
        self.cardHp = 10
        self.atkPoint = "1d6"
        self.defPoint = "1d4"
        self.dodPoint = "1d2"
        self.describe = "宣言时：造成x点伤害，x为你的剩余符卡数"

    def onCardSet(self):
        hurtValue = 6 - self.user.nowCardOrder
        hurtInfo = self.enemy.effectHurt(hurtValue)
        return f"[{self.user.name}]符卡效果：造成{hurtValue}点直接伤害\n" + hurtInfo
