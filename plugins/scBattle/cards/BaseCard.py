from plugins.scBattle.AbstractCard import AbstractCard


class NonCardAttack1(AbstractCard):
    id = 0
    cost = 0

    def __init__(self):
        super().__init__()
        self.name = "非符1"
        self.cardHp = 20
        self.atkPoint = "1d10"
        self.hitPoint = "1d5"
        self.dodPoint = "1d4"
        self.describe = "无"


class NonCardAttack2(AbstractCard):
    id = 1
    cost = 0

    def __init__(self):
        super().__init__()
        self.name = "非符2"
        self.cardHp = 15
        self.atkPoint = "1d15"
        self.hitPoint = "1d3"
        self.dodPoint = "1d3"
        self.describe = "无"


class NonCardAttack3(AbstractCard):
    id = 2
    cost = 0

    def __init__(self):
        super().__init__()
        self.name = "非符3"
        self.cardHp = 20
        self.atkPoint = "1d7"
        self.hitPoint = "1d7"
        self.dodPoint = "1d4"
        self.describe = "无"
