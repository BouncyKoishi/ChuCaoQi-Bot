class AbstractCard:
    id = -1
    cost = 0

    def __init__(self):
        self.name = "DefaultCard"
        self.type = "main"
        self.cardHp = None
        self.atkPoint = None
        self.hitPoint = None
        self.dodPoint = None
        self.describe = None
        self.user = None
        self.enemy = None

    def setPlayerInfo(self, user, enemy):
        self.user = user
        self.enemy = enemy

    def getCardDescribe(self):
        output = f"{self.name}\n"
        output += f"初始血量: {self.cardHp}\n"
        output += f"基础攻击: {self.atkPoint}\n"
        output += f"基础命中: {self.hitPoint}\n"
        output += f"基础回避: {self.dodPoint}\n"
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
