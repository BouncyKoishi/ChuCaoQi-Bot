from plugins.scBattle.AbstractEffect import AbstractEffect


class TraceEffect(AbstractEffect):
    id = "Trace"

    def __init__(self, effectAmount):
        super().__init__(effectAmount)
        self.displayName = "追踪"
        self.effectType = "BUFF"

    def onEnemyHurtValueCalc(self, hurtValue: int):
        if self.enemy.dodSuccess:
            self.effectInfoMsg = f"[{self.enemy.name}]闪避成功，但被敌方符卡追踪，受到{self.effectAmount}点伤害！\n"
            return hurtValue + self.effectAmount
        return hurtValue
