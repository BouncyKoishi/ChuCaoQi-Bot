from plugins.scBattle.AbstractEffect import AbstractEffect


class ShieldEffect(AbstractEffect):
    id = "Shield"

    def __init__(self, effectAmount):
        super().__init__(effectAmount)
        self.displayName = "护盾"
        self.effectType = "BUFF"

    def beforeHurt(self, hurtValue: int):
        if hurtValue > 0:
            reduceDamage = min(self.effectAmount, hurtValue)
            self.effectInfoMsg = f"[{self.user.name}]消耗了{reduceDamage}点护盾，吸收了{reduceDamage}点伤害！\n"
            self.reduceEffect(reduceDamage)
            return hurtValue - reduceDamage
        return hurtValue
