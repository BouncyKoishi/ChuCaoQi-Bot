from plugins.scBattle.AbstractCard import AbstractCard


class RainbowChimesCard(AbstractCard):
    id = 15
    cost = 2

    def __init__(self):
        super().__init__()
        self.name = "虹符「彩虹的风铃」"
        self.cardHp = 6
        self.atkPoint = "1d6"
        self.defPoint = "2"
        self.dodPoint = "1d2"
        self.describe = "宣言时，破弃时：造成2点伤害"
        self.nowEffectAmount = 0

    def onCardSet(self):
        hurtInfo = self.enemy.effectHurt(2)
        return f"[{self.user.name}]符卡宣言效果：造成2点直接伤害\n" + hurtInfo

    def onCardBreak(self):
        hurtInfo = self.enemy.effectHurt(2)
        return f"[{self.user.name}]符卡终止效果：造成2点直接伤害\n" + hurtInfo


class RocDropFistCard(AbstractCard):
    id = 16
    cost = 3

    def __init__(self):
        super().__init__()
        self.name = "三华「崩山彩极炮」"
        self.cardHp = 8
        self.atkPoint = "2d3+1d4"
        self.defPoint = "1d4"
        self.dodPoint = "1d2"
        self.describe = "无"
