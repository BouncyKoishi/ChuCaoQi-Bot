from plugins.scBattle.AbstractCard import AbstractCard


class ScarletShootCard(AbstractCard):
    id = 22
    cost = 3

    def __init__(self):
        super().__init__()
        self.name = "红符「深红射击」"
        self.cardHp = 2
        self.atkPoint = "2d10"
        self.defPoint = "1"
        self.dodPoint = "1"
        self.describe = "无"

