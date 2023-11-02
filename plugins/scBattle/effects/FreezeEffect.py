from plugins.scBattle.AbstractEffect import AbstractEffect


class FreezeEffect(AbstractEffect):
    id = "Freeze"

    def __init__(self, effectAmount):
        super().__init__(effectAmount)
        self.effectAmount = effectAmount
        self.displayName = "冰冻"
        self.effectType = "DEBUFF"
        self.effectInfoMsg = ""

    def onTurnStart(self):
        self.effectInfoMsg = f"{self.user.name}正被冰冻中，本回合无法进行攻击/防御/回避，所有非结界效果不触发！\n"
        self.user.states.append("Froze")
        return

    def onAttackCalc(self, atkPoint: int):
        self.effectInfoMsg = ""
        return 0

    def onDefenceCalc(self, defPoint: int):
        self.effectInfoMsg = ""
        return 0

    def onDodgeCalc(self, dodPoint: int):
        self.effectInfoMsg = ""
        return 0

    def onTurnEnd(self):
        self.effectInfoMsg = ""
        self.reduceEffect(1)
        self.keepFrozenJudge()
        return

    def onCardBreak(self):
        self.effectInfoMsg = ""
        self.reduceEffect(1)
        self.keepFrozenJudge()
        return

    def keepFrozenJudge(self):
        if self.effectAmount <= 0:
            self.user.states.remove("Froze")
