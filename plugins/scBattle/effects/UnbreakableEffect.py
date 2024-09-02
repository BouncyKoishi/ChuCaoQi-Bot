from plugins.scBattle.AbstractEffect import AbstractEffect


class UnbreakableEffect(AbstractEffect):
    id = "Unbreakable"

    def __init__(self, effectAmount):
        super().__init__(effectAmount)
        self.displayName = "击破保护"
        self.effectType = "BUFF"

    def beforeHurt(self, hurtValue: int):
        if hurtValue >= self.user.nowHp:
            self.effectInfoMsg = f"[{self.user.name}]的击破保护触发，免疫本次伤害！\n"
            self.effectAmount -= 1
            return 0
        return hurtValue

