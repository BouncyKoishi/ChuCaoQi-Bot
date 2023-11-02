from plugins.scBattle.scBattlerObj import Battler
from plugins.scBattle.scBattleUtils import getBattlerName
from PIL import Image, ImageDraw, ImageFont
from utils import getImgBase64
import time

class Battle:
    def __init__(self, creatorId, groupId) -> None:
        self.creatorId = creatorId
        self.joinerId = None
        self.creator: Battler or None = None
        self.joiner: Battler or None = None
        self.lastTurnInfoImg = None
        self.groupId = groupId
        self.gameRound = None
        self.stateCardId = 0
        self.spellCardSettled = []
        self.turnInfoMsg, self.creatorCardMsg, self.joinerCardMsg = "", "", ""
        self.cAtk, self.jAtk, self.cHurt, self.jHurt = 0, 0, 0, 0

    async def setCreator(self):
        creatorName = await getBattlerName(self.creatorId, self.groupId)
        self.creator = Battler(self.creatorId, creatorName)

    async def joinBattle(self, joinerId) -> None:
        self.joinerId = joinerId
        joinerName = await getBattlerName(self.joinerId, self.groupId)
        self.joiner = Battler(self.joinerId, joinerName)
        self.creator.setEnemy(self.joiner)
        self.joiner.setEnemy(self.creator)
        self.gameRound = 0

    async def setSingleBattleEnemy(self, enemyName, enemyCardList):
        self.joinerId = -1
        self.joiner = Battler(self.joinerId, enemyName)
        self.joiner.cardIdList = enemyCardList
        self.creator.setEnemy(self.joiner)
        self.joiner.setEnemy(self.creator)
        self.spellCardSettled.append(self.joinerId)
        self.gameRound = 0

    def gameStart(self) -> None:
        self.creator.setNewMainCard()
        self.joiner.setNewMainCard()
        self.roundStart()
        self.creatorCardMsg = self.creator.getCardDescribe()
        self.joinerCardMsg = self.joiner.getCardDescribe()
        self.turnInfoMsg += self.creator.nowCard.onCardSet()
        self.turnInfoMsg += self.joiner.nowCard.onCardSet()
        self.turnInfoMsg += self.creator.runEffect("onCardSet")
        self.turnInfoMsg += self.joiner.runEffect("onCardSet")
        self.turnInfoMsg += f'-------------------------------------------------------\n'

    def roundStart(self):
        self.gameRound += 1
        self.turnInfoMsg += f'-- 宣言回目 {self.gameRound} --\n'
        self.turnInfoMsg += f'{self.creator.name} 当前血量:{self.creator.nowHp}\n'
        self.turnInfoMsg += f'{self.joiner.name} 当前血量:{self.joiner.nowHp}\n'
        
    def turnStart(self):
        self.turnInfoMsg += self.creator.nowCard.onTurnStart()
        self.turnInfoMsg += self.joiner.nowCard.onTurnStart()
        self.turnInfoMsg += self.creator.runEffect('onTurnStart')
        self.turnInfoMsg += self.joiner.runEffect('onTurnStart')

    def turnGetBasePoint(self):
        self.cAtk, pointMsg1 = self.creator.getPoints()
        self.jAtk, pointMsg2 = self.joiner.getPoints()
        self.turnInfoMsg += (pointMsg1 + pointMsg2)

    def turnHurtValueCalc(self):
        self.cHurt, hurtMsg1 = self.creator.calcHurt(self.jAtk)
        self.jHurt, hurtMsg2 = self.joiner.calcHurt(self.cAtk)
        self.turnInfoMsg += (hurtMsg1 + hurtMsg2)

    def turnHpChange(self):
        self.turnInfoMsg += self.creator.battleHurt(self.cHurt)
        self.turnInfoMsg += self.joiner.battleHurt(self.jHurt)

    def turnEnd(self):
        self.turnInfoMsg += self.creator.runEffect('onTurnEnd')
        self.turnInfoMsg += self.joiner.runEffect('onTurnEnd')
        self.turnInfoMsg += self.creator.nowCard.onTurnEnd()
        self.turnInfoMsg += self.joiner.nowCard.onTurnEnd()
        self.turnInfoMsg += f'-------------------------------------------------------\n'
        self.cleanTurnTempData()

    def cleanTurnTempData(self):
        self.creator.cleanTurnTempData()
        self.joiner.cleanTurnTempData()
        self.cAtk, self.jAtk, self.cHurt, self.jHurt = 0, 0, 0, 0

    def cardBreakJudge(self):
        creatorBreak = self.creator.shouldChangeCard()
        joinerBreak = self.joiner.shouldChangeCard()
        if creatorBreak and joinerBreak:
            self.turnInfoMsg += f'-------------------------------------------------------\n'
            self.turnInfoMsg += f'{self.creator.name} 当前符卡被击破！\n'
            self.turnInfoMsg += self.creator.runEffect("onCardBreak")
            self.turnInfoMsg += self.joiner.runEffect("onEnemyCardBreak")
            self.turnInfoMsg += self.creator.nowCard.onCardBreak()
            self.turnInfoMsg += f'{self.joiner.name} 当前符卡被击破！\n'
            self.turnInfoMsg += self.joiner.runEffect("onCardBreak")
            self.turnInfoMsg += self.creator.runEffect("onEnemyCardBreak")
            self.turnInfoMsg += self.joiner.nowCard.onCardBreak()
            self.lastTurnInfoImg = self.getTurnInfoImg()
            self.cleanTurnTempData()
            time.sleep(4)
            gameContinueA = self.creator.setNewMainCard()
            gameContinueB = self.joiner.setNewMainCard()
            if not gameContinueA or not gameContinueB:
                return True, True
            self.roundStart()
            self.creatorCardMsg = self.creator.getCardDescribe()
            self.joinerCardMsg = self.joiner.getCardDescribe()
            self.turnInfoMsg += self.creator.nowCard.onCardSet()
            self.turnInfoMsg += self.joiner.nowCard.onCardSet()
            self.turnInfoMsg += self.creator.runEffect("onCardSet")
            self.turnInfoMsg += self.joiner.runEffect("onCardSet")
            self.turnInfoMsg += f'-------------------------------------------------------\n'
            return True, False
        elif creatorBreak:
            self.turnInfoMsg += f'-------------------------------------------------------\n'
            self.turnInfoMsg += f'{self.creator.name} 当前符卡被击破！\n'
            self.turnInfoMsg += self.creator.runEffect("onCardBreak")
            self.turnInfoMsg += self.joiner.runEffect("onEnemyCardBreak")
            self.turnInfoMsg += self.creator.nowCard.onCardBreak()
            self.lastTurnInfoImg = self.getTurnInfoImg()
            self.cleanTurnTempData()
            time.sleep(4)
            gameContinue = self.creator.setNewMainCard()
            if not gameContinue:
                return True, True
            self.roundStart()
            self.creatorCardMsg = self.creator.getCardDescribe()
            self.turnInfoMsg += self.creator.nowCard.onCardSet()
            self.turnInfoMsg += self.creator.runEffect("onCardSet")
            self.turnInfoMsg += f'-------------------------------------------------------\n'
            return True, False
        elif joinerBreak:
            self.turnInfoMsg += f'-------------------------------------------------------\n'
            self.turnInfoMsg += f'{self.joiner.name} 当前符卡被击破！\n'
            self.turnInfoMsg += self.joiner.runEffect("onCardBreak")
            self.turnInfoMsg += self.creator.runEffect("onEnemyCardBreak")
            self.turnInfoMsg += self.joiner.nowCard.onCardBreak()
            self.lastTurnInfoImg = self.getTurnInfoImg()
            self.cleanTurnTempData()
            time.sleep(4)
            gameContinue = self.joiner.setNewMainCard()
            if not gameContinue:
                return True, True
            self.roundStart()
            self.joinerCardMsg = self.joiner.getCardDescribe()
            self.turnInfoMsg += self.joiner.nowCard.onCardSet()
            self.turnInfoMsg += self.joiner.runEffect("onCardSet")
            self.turnInfoMsg += f'-------------------------------------------------------\n'
            return True, False
        return False, False

    def getTurnInfoImg(self):
        sizeBig = 25
        sizeMid = 20
        sizeSmall = 15
        rowSpacing = 3
        width = 900
        margin = 20
        font1 = ImageFont.truetype("HarmonyOS_Sans_SC_Bold", sizeBig)
        font2 = ImageFont.truetype("HarmonyOS_Sans_SC_Regular", sizeMid)
        font3 = ImageFont.truetype("HarmonyOS_Sans_SC_Light", sizeSmall)
        baseHeight = sizeBig + sizeMid * 6 + rowSpacing * 6 + margin * 2
        turnInfoMsgLineCount = self.turnInfoMsg.count('\n') + 1
        turnInfoMsgHeight = (sizeSmall + rowSpacing) * turnInfoMsgLineCount + margin * 2
        totalHeight = baseHeight + turnInfoMsgHeight

        img = Image.new(mode="RGB", size=(width, totalHeight), color=(255, 255, 255))
        draw = ImageDraw.Draw(img)
        draw.text((margin, margin), self.creator.name, font=font1, fill=(96, 16, 16))
        draw.text((margin, margin + sizeBig + rowSpacing), self.creatorCardMsg, font=font2, fill=(96, 16, 16))
        draw.text((width / 2, margin), self.joiner.name, font=font1, fill=(16, 16, 96))
        draw.text((width / 2, margin + sizeBig + rowSpacing), self.joinerCardMsg, font=font2, fill=(16, 16, 96))
        draw.line(xy=(margin, baseHeight, width - margin, baseHeight), fill=(100, 100, 100), width=2)
        draw.text((margin, baseHeight + margin), self.turnInfoMsg, font=font3, fill=(0, 0, 0))
        img.save("temp.jpg", format="JPEG", quality=95)
        self.turnInfoMsg = ""
        return getImgBase64(r"temp.jpg")

    def endGameCheck(self):
        isEndGame = False
        loserName = []
        if self.creator.shouldEnd():
            isEndGame = True
            loserName.append(self.creator.name)
        if self.joiner.shouldEnd():
            isEndGame = True
            loserName.append(self.joiner.name)
        time.sleep(4)
        return isEndGame, loserName



