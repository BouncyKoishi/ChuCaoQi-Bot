from plugins.scBattle.AbstractCard import AbstractCard


class AgniShineCard(AbstractCard):
    id = 17
    cost = 2

    def __init__(self):
        super().__init__()
        self.name = "火符「火神之光」"
        self.cardHp = 7
        self.atkPoint = "0"
        self.defPoint = "1d3"
        self.dodPoint = "1d2"
        self.describe = "回合开始时：造成2点伤害"

    def onTurnStart(self):
        hurtInfo = self.enemy.effectHurt(2)
        return f"[{self.user.name}]符卡效果：造成2点直接伤害\n" + hurtInfo


class PrincessUndineCard(AbstractCard):
    id = 18
    cost = 2

    def __init__(self):
        super().__init__()
        self.name = "水符「水精公主」"
        self.cardHp = 7
        self.atkPoint = "1d5"
        self.defPoint = "1d3"
        self.dodPoint = "1d2"
        self.describe = "受到致命伤害时，免疫此次伤害（只能发动一次）"

    def onCardSet(self):
        self.user.appendEffect("Unbreakable", 1)
        return ""


class SylphyHornCard(AbstractCard):
    id = 19
    cost = 2

    def __init__(self):
        super().__init__()
        self.name = "木符「风灵的角笛」"
        self.cardHp = 7
        self.atkPoint = "1d5"
        self.defPoint = "1d3"
        self.dodPoint = "1d2"
        self.describe = "偶数回合开始时：获得仅本回合生效的[灵动2]"
        self.turnCount = 0
        self.effectOn = False

    def onTurnStart(self):
        self.turnCount += 1
        if self.turnCount % 2 == 0:
            self.user.appendEffect("Agile", 2)
            self.effectOn = True
        return ""

    def onTurnEnd(self):
        if self.effectOn:
            self.user.removeEffect("Agile", 2)
            self.effectOn = False
        return ""

    def onCardBreak(self):
        if self.effectOn:
            self.user.removeEffect("Agile", 2)
            self.effectOn = False
        return ""


class MetalFatigueCard(AbstractCard):
    id = 20
    cost = 2

    def __init__(self):
        super().__init__()
        self.name = "金符「金属疲劳」"
        self.cardHp = 7
        self.atkPoint = "1d5"
        self.defPoint = "1d3"
        self.dodPoint = "1d2"
        self.describe = "宣言时：展开5回合的[脆弱结界]"

    def onCardSet(self):
        self.user.appendBorder("FragileBorder", 5, 1)
        return ""


class LazyTrilithonCard(AbstractCard):
    id = 21
    cost = 2

    def __init__(self):
        super().__init__()
        self.name = "土符「慵懒三石塔」"
        self.cardHp = 7
        self.atkPoint = "1d5"
        self.defPoint = "1d3"
        self.dodPoint = "1d2"
        self.describe = "宣言时：获得[缓冲1]"

    def onCardSet(self):
        self.user.appendEffect("Buffer", 1)
        return ""

    def onCardBreak(self):
        self.user.removeEffect("Buffer", 1)
        return ""
