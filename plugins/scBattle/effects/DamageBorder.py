from plugins.scBattle.AbstractBorder import AbstractBorder


class DamageBorder(AbstractBorder):
    id = "DamageBorder"

    def __init__(self, effectAmount):
        super().__init__(effectAmount)
        self.displayName = "伤害结界"

    def onTurnStart(self):
        self.effectInfoMsg = f'伤害结界：[{self.enemy.name}]受到{self.borderStrength}点直接伤害\n'
        self.effectInfoMsg += self.enemy.effectHurt(self.borderStrength)
        self.reduceEffect(1)
        return
