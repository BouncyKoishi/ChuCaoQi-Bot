from plugins.scBattle.AbstractEffect import AbstractEffect


class AbstractBorder(AbstractEffect):
    id = "AbstractBorder"

    def __init__(self, borderTurn: int):
        super().__init__(1)
        self.displayName = ""
        self.effectType = "BORDER"
        self.borderTurn = borderTurn
        self.borderStrength = 0

    def setBorderStrength(self, borderStrength: int):
        self.borderStrength = borderStrength

    def stackEffect(self, borderTurn: int):
        newBorderTurn = max(self.borderTurn, borderTurn)
        self.borderTurn = newBorderTurn

    def reduceEffect(self, _):
        self.borderTurn -= 1
        if self.borderTurn <= 0:
            self.effectAmount = 0

    def cleanEffect(self):
        self.borderTurn = 0
        self.effectAmount = 0

