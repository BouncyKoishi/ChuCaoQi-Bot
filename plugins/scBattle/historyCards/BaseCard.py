from plugins.scBattle.AbstractCard import AbstractCard


class NonCardAttack(AbstractCard):
    id = 0
    cost = 0

    def __init__(self):
        super().__init__()
        self.name = "非符"
        self.cardHp = 4
        self.atkPoint = "1d4"
        self.defPoint = "1d2"
        self.dodPoint = "1d2"
        self.describe = "无"


class BaseAttackCard(AbstractCard):
    id = 1
    cost = 1

    def __init__(self):
        super().__init__()
        self.name = "「妖怪破坏者」"
        self.cardHp = 3
        self.atkPoint = "1d8"
        self.defPoint = "1d2"
        self.dodPoint = "1d2"
        self.describe = "无"


class BaseNormalCard(AbstractCard):
    id = 2
    cost = 1

    def __init__(self):
        super().__init__()
        self.name = "「扩散灵符」"
        self.cardHp = 4
        self.atkPoint = "1d6"
        self.defPoint = "1d3"
        self.dodPoint = "1d2"
        self.describe = "无"


class BaseDefenceCard(AbstractCard):
    id = 3
    cost = 1

    def __init__(self):
        super().__init__()
        self.name = "「警醒阵」"
        self.cardHp = 6
        self.atkPoint = "1d4"
        self.defPoint = "1d2+2"
        self.dodPoint = "1d2"
        self.describe = "无"


class BaseTraceCard(AbstractCard):
    id = 4
    cost = 1

    def __init__(self):
        super().__init__()
        self.name = "「博丽护符」"
        self.cardHp = 6
        self.atkPoint = "1d4"
        self.defPoint = "1d2"
        self.dodPoint = "1d2"
        self.describe = "宣言时：获得[追踪1]"

    def onCardSet(self):
        self.user.appendEffect("Trace", 1)
        return ""

    def onCardBreak(self):
        self.user.removeEffect("Trace", 1)
        return ""


class BaseBattleCryCard(AbstractCard):
    id = 5
    cost = 1

    def __init__(self):
        super().__init__()
        self.name = "「弦月斩」"
        self.cardHp = 6
        self.atkPoint = "1d4"
        self.defPoint = "1d2"
        self.dodPoint = "1d2"
        self.describe = "宣言时：造成2点伤害"

    def onCardSet(self):
        hurtInfo = self.enemy.effectHurt(2)
        return f"[{self.user.name}]符卡宣言效果：造成2点直接伤害\n" + hurtInfo


class BaseDeathRattleCard(AbstractCard):
    id = 6
    cost = 1

    def __init__(self):
        super().__init__()
        self.name = "「炯眼剑」"
        self.cardHp = 6
        self.atkPoint = "1d4"
        self.defPoint = "1d2"
        self.dodPoint = "1d2"
        self.describe = "破弃时：造成2点直接伤害"

    def onCardBreak(self):
        hurtInfo = self.enemy.effectHurt(2)
        return f"[{self.user.name}]符卡终止效果：造成2点直接伤害\n" + hurtInfo


class BaseStrengthCard(AbstractCard):
    id = 7
    cost = 1

    def __init__(self):
        super().__init__()
        self.name = "「人偶振起」"
        self.cardHp = 4
        self.atkPoint = "1"
        self.defPoint = "0"
        self.dodPoint = "1d2+1"
        self.describe = "回合开始时：获得[强化1]"
        self.nowEffectAmount = 0

    def onTurnStart(self):
        self.user.appendEffect("Strength", 1)
        self.nowEffectAmount += 1
        return ""

    def onCardBreak(self):
        self.user.removeEffect("Strength", self.nowEffectAmount)
        return ""


class BaseBufferCard(AbstractCard):
    id = 8
    cost = 1

    def __init__(self):
        super().__init__()
        self.name = "「人偶置操」 "
        self.cardHp = 4
        self.atkPoint = "1d4"
        self.defPoint = "1d3"
        self.dodPoint = "1d2"
        self.describe = "宣言时：获得[缓冲1]"

    def onCardSet(self):
        self.user.appendEffect("Buffer", 1)
        return ""

    def onCardBreak(self):
        self.user.removeEffect("Buffer", 1)
        return ""


class BaseChaseCard(AbstractCard):
    id = 9
    cost = 1

    def __init__(self):
        super().__init__()
        self.name = "「乾神招来 风」"
        self.cardHp = 7
        self.atkPoint = "1d4"
        self.defPoint = "1d2"
        self.dodPoint = "1d2"
        self.describe = "宣言时：获得[追击1]"

    def onCardSet(self):
        self.user.appendEffect("Chase", 1)
        return ""

    def onCardBreak(self):
        self.user.removeEffect("Chase", 1)
        return ""


class BaseShieldCard(AbstractCard):
    id = 10
    cost = 1

    def __init__(self):
        super().__init__()
        self.name = "「坤神招来 盾」"
        self.cardHp = 1
        self.atkPoint = "1d6"
        self.defPoint = "0"
        self.dodPoint = "0"
        self.describe = "破弃时：获得永续的[护盾3]"

    def onCardBreak(self):
        self.user.appendEffect("Shield", 3)
        return "下一张符卡获得3点护盾！\n"


class BaseCantDefenceCard(AbstractCard):
    id = 11
    cost = 1

    def __init__(self):
        super().__init__()
        self.name = "「红寸劲」"
        self.cardHp = 4
        self.atkPoint = "1d4"
        self.defPoint = "1"
        self.dodPoint = "1d2"
        self.describe = "宣言时：获得[防御不可]"

    def onCardSet(self):
        self.user.appendEffect("CantDefence", 1)
        return f"[{self.user.name}]本符卡对方无法防御！\n"

    def onCardBreak(self):
        self.user.removeEffect("CantDefence", 1)
        return ""


class BaseBorderCard(AbstractCard):
    id = 12
    cost = 2

    def __init__(self):
        super().__init__()
        self.name = "梦符「封魔阵」"
        self.cardHp = 6
        self.atkPoint = "1d5"
        self.defPoint = "1d3"
        self.dodPoint = "1d2"
        self.describe = "宣言时：展开5回合的[伤害结界1]"

    def onCardSet(self):
        self.user.appendBorder("DamageBorder", 5, 1)
        return f"[{self.user.name}]展开了持续5回合的[伤害结界1]！\n"