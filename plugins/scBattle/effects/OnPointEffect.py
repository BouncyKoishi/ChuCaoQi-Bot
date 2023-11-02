from plugins.scBattle.AbstractEffect import AbstractEffect


class StrengthEffect(AbstractEffect):
    id = "Strength"

    def __init__(self, effectAmount):
        super().__init__(effectAmount)
        self.displayName = "强化"
        self.effectType = "BUFF"

    def onAttackCalc(self, atkPoint: int):
        self.effectInfoMsg = f"[{self.user.name}]攻击增加了{self.effectAmount}点！\n"
        return atkPoint + self.effectAmount


class WeakenEffect(AbstractEffect):
    id = "Weaken"

    def __init__(self, effectAmount):
        super().__init__(effectAmount)
        self.displayName = "弱化"
        self.effectType = "DEBUFF"

    def onAttackCalc(self, atkPoint: int):
        self.effectInfoMsg = f"[{self.user.name}]攻击减少了{self.effectAmount}点！\n"
        return atkPoint - self.effectAmount


class StableEffect(AbstractEffect):
    id = "Stable"

    def __init__(self, effectAmount):
        super().__init__(effectAmount)
        self.displayName = "稳固"
        self.effectType = "BUFF"

    def onDefenceCalc(self, defPoint: int):
        self.effectInfoMsg = f"[{self.user.name}]防御增加了{self.effectAmount}点！\n"
        return defPoint + self.effectAmount


class FragileEffect(AbstractEffect):
    id = "Fragile"

    def __init__(self, effectAmount):
        super().__init__(effectAmount)
        self.displayName = "脆弱"
        self.effectType = "DEBUFF"

    def onDefenceCalc(self, defPoint: int):
        self.effectInfoMsg = f"[{self.user.name}]防御减少了{self.effectAmount}点！\n"
        return defPoint - self.effectAmount


class AgileEffect(AbstractEffect):
    id = "Agile"

    def __init__(self, effectAmount):
        super().__init__(effectAmount)
        self.displayName = "灵动"
        self.effectType = "BUFF"

    def onDodgeCalc(self, dodPoint: int):
        self.effectInfoMsg = f"[{self.user.name}]回避增加了{self.effectAmount}点！\n"
        return dodPoint + self.effectAmount


class SluggishEffect(AbstractEffect):
    id = "Sluggish"

    def __init__(self, effectAmount):
        super().__init__(effectAmount)
        self.displayName = "迟缓"
        self.effectType = "DEBUFF"

    def onDodgeCalc(self, dodPoint: int):
        self.effectInfoMsg = f"[{self.user.name}]回避减少了{self.effectAmount}点！\n"
        return dodPoint - self.effectAmount