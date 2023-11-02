from plugins.scBattle.AbstractEffect import AbstractEffect


class ChaseEffect(AbstractEffect):
    id = "Chase"

    def __init__(self, effectAmount):
        super().__init__(effectAmount)
        self.displayName = "追击"
        self.effectType = "BUFF"

    def onEnemyHurtValueCalc(self, hurtValue: int):
        if hurtValue > 0:
            self.effectInfoMsg = f"[{self.enemy.name}]被敌方符卡追击，额外受到{self.effectAmount}点伤害！\n"
            return hurtValue + self.effectAmount
        return hurtValue
