class AbstractCard:
    id = -1
    cost = 0

    def __init__(self):
        self.name = "DefaultCard"
        self.type = "main"
        self.cardHp = None
        self.atkPoint = None
        self.defPoint = None
        self.dodPoint = None
        self.describe = None
        self.user = None
        self.enemy = None

    def setPlayerInfo(self, user, enemy):
        self.user = user
        self.enemy = enemy

    def getCardDescribe(self, cardOrder):
        output = f"符卡 {cardOrder}: {self.name}\n"
        output += f"初始血量: {self.cardHp}\n"
        output += f"攻击骰: {self.atkPoint}\n"
        output += f"防御骰: {self.defPoint}\n"
        output += f"回避骰: {self.dodPoint}\n"
        output += f"特殊效果: {self.describe}\n"
        return output

    def onCardSet(self):
        return ""

    def onCardBreak(self):
        return ""

    def onTurnStart(self):
        return ""

    def onTurnEnd(self):
        return ""
