from plugins.scBattle.AbstractEffect import AbstractEffect


class CantDefenceEffect(AbstractEffect):
    id = "CantDefence"

    def __init__(self, effectAmount):
        super().__init__(effectAmount)
        self.displayName = "防御不可"
        self.effectType = "BUFF"

    def onEnemyDefenceSuccessJudge(self, isSuccess):
        if not self.enemy.dodSuccess:
            self.effectInfoMsg = f"[{self.enemy.name}]受对方符卡效果影响，无法作出防御\n"
        return False


class CantDodgeEffect(AbstractEffect):
    id = "CantDodge"

    def __init__(self, effectAmount):
        super().__init__(effectAmount)
        self.displayName = "回避不可"
        self.effectType = "BUFF"

    def onEnemyDodgeSuccessJudge(self, isSuccess):
        if not self.enemy.dodSuccess:
            self.effectInfoMsg = f"[{self.enemy.name}]受对方符卡效果影响，无法进行回避\n"
        return False
