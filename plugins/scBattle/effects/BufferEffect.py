from plugins.scBattle.AbstractEffect import AbstractEffect


class BufferEffect(AbstractEffect):
    id = "Buffer"

    def __init__(self, effectAmount):
        super().__init__(effectAmount)
        self.displayName = "缓冲"
        self.effectType = "BUFF"

    def onHurtValueCalc(self, hurtValue: int):
        if hurtValue > 0:
            self.effectInfoMsg = f"[{self.user.name}]受缓冲层保护，受到的伤害减少{self.effectAmount}点\n"
            return hurtValue - self.effectAmount
        return hurtValue
