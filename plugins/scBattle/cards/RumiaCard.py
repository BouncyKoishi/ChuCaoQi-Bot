from plugins.scBattle.AbstractCard import AbstractCard


class DemarcationCard(AbstractCard):
    id = 13
    cost = 2

    def __init__(self):
        super().__init__()
        self.name = "暗符「境界线」"
        self.cardHp = 6
        self.atkPoint = "1d4"
        self.defPoint = "1d2"
        self.dodPoint = "1d3+1"
        self.describe = "无"
