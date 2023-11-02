class AbstractEffect:
    id = "DefaultEffect"

    def __init__(self, effectAmount: int = 1):
        self.displayName = ""
        self.effectType = "BUFF"
        self.effectAmount = effectAmount
        self.canGoNegative = False
        self.effectInfoMsg = ""
        self.user = None
        self.enemy = None

    def setPlayerInfo(self, user, enemy):
        self.user = user
        self.enemy = enemy

    def stackEffect(self, stackAmount: int):
        if self.effectAmount == -1:
            return
        self.effectAmount += stackAmount
    
    def reduceEffect(self, reduceAmount: int):
        if self.effectAmount <= reduceAmount and not self.canGoNegative:
            self.effectAmount = 0
        else:
            self.effectAmount -= reduceAmount

    def cleanEffect(self):
        self.effectAmount = 0

    def onRoundStart(self):
        return

    def onTurnStart(self):
        return

    def onRoundEnd(self):
        return
    
    def onTurnEnd(self):
        return

    def onAttackCalc(self, atkPoint: int):
        return atkPoint

    def onDefenceCalc(self, defPoint: int):
        return defPoint

    def onDodgeCalc(self, dodPoint: int):
        return dodPoint

    def onHealValueCalc(self, healPoint: int):
        return healPoint

    def onHurtValueCalc(self, hurtValue: int):
        return hurtValue

    def onEnemyHurtValueCalc(self, hurtValue: int):
        return hurtValue

    def onDefenceSuccessJudge(self, isSuccess):
        return isSuccess

    def onEnemyDefenceSuccessJudge(self, isSuccess):
        return isSuccess

    def onDodgeSuccessJudge(self, isSuccess):
        return isSuccess

    def onEnemyDodgeSuccessJudge(self, isSuccess):
        return isSuccess

    def beforeHurt(self, hurtValue: int):
        return hurtValue

    def onHurt(self, hurtValue: int):
        return hurtValue

    def onBattleHurt(self, hurtValue: int):
        return hurtValue

    def onEffectHurt(self, hurtValue: int):
        return hurtValue

    def onHeal(self):
        return

    def onCardSet(self):
        return

    def onEnemyCardSet(self):
        return

    def onCardBreak(self):
        return

    def onEnemyCardBreak(self):
        return
