from plugins.scBattle.AbstractCard import AbstractCard


class PerfectFreezeCard(AbstractCard):
    id = 14
    cost = 3

    def __init__(self):
        super().__init__()
        self.name = "冻符「完美冻结」"
        self.cardHp = 9
        self.atkPoint = "1d9"
        self.defPoint = "0"
        self.dodPoint = "0"
        self.describe = "回合开始时：获得[弱化1]；宣言时：赋予[冻结]"
        self.nowEffectAmount = 0

    def onCardSet(self):
        self.enemy.appendEffect("Freeze", 1)
        return ''

    def onTurnStart(self):
        self.user.appendEffect("Weaken", 1)
        self.nowEffectAmount += 1
        return ''

    def onCardBreak(self):
        self.user.removeEffect("Weaken", self.nowEffectAmount)
        return ''
