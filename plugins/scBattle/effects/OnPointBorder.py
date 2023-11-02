from plugins.scBattle.AbstractBorder import AbstractBorder


class StrengthBorder(AbstractBorder):
    id = "StrengthBorder"

    def __init__(self, effectAmount):
        super().__init__(effectAmount)
        self.displayName = "强化结界"

    def onAttackCalc(self, atkPoint: int):
        self.effectInfoMsg = f"[{self.user.name}]攻击增加了{self.borderStrength}点！\n"
        self.reduceEffect(1)
        return atkPoint + self.borderStrength


class WeakenBorder(AbstractBorder):
    id = "WeakenBorder"

    def __init__(self, effectAmount):
        super().__init__(effectAmount)
        self.displayName = "弱化结界"

    def onAttackCalc(self, atkPoint: int):
        self.effectInfoMsg = f"[{self.user.name}]攻击减少了{self.borderStrength}点！\n"
        self.reduceEffect(1)
        return atkPoint - self.borderStrength


class StableBorder(AbstractBorder):
    id = "StableBorder"

    def __init__(self, effectAmount):
        super().__init__(effectAmount)
        self.displayName = "稳固结界"

    def onDefenceCalc(self, defPoint: int):
        self.effectInfoMsg = f"[{self.user.name}]防御增加了{self.borderStrength}点！\n"
        self.reduceEffect(1)
        return defPoint + self.borderStrength


class FragileBorder(AbstractBorder):
    id = "FragileBorder"

    def __init__(self, effectAmount):
        super().__init__(effectAmount)
        self.displayName = "脆弱结界"

    def onDefenceCalc(self, defPoint: int):
        self.effectInfoMsg = f"[{self.user.name}]防御减少了{self.borderStrength}点！\n"
        self.reduceEffect(1)
        return defPoint - self.borderStrength


class AgileBorder(AbstractBorder):
    id = "AgileBorder"

    def __init__(self, effectAmount):
        super().__init__(effectAmount)
        self.displayName = "灵动结界"

    def onDodgeCalc(self, dodPoint: int):
        self.effectInfoMsg = f"[{self.user.name}]回避增加了{self.borderStrength}点！\n"
        self.reduceEffect(1)
        return dodPoint + self.borderStrength


class SluggishBorder(AbstractBorder):
    id = "SluggishBorder"

    def __init__(self, effectAmount):
        super().__init__(effectAmount)
        self.displayName = "迟缓结界"

    def onDodgeCalc(self, dodPoint: int):
        self.effectInfoMsg = f"[{self.user.name}]回避减少了{self.borderStrength}点！\n"
        self.reduceEffect(1)
        return dodPoint - self.borderStrength
