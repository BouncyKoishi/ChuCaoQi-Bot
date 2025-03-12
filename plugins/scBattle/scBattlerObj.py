from typing import Optional
from plugins.scBattle.AbstractBorder import AbstractBorder
from plugins.scBattle.AbstractCard import AbstractCard
import plugins.scBattle.scBattleUtils as utils


class Battler:
    def __init__(self, userId, userName) -> None:
        self.id = userId
        self.name = userName
        self.chosenCard: list[AbstractCard] = []
        self.usedCardIndex: list[int] = []
        self.states = []
        self.effects = []
        self.nowHp: int = 0
        self.nowCard: Optional[AbstractCard] = None
        self.enemy = None
        self.attack, self.defence, self.dodge = 0, 0, 0
        self.dodSuccess, self.defSuccess = None, None

    def setEnemy(self, enemy):
        self.enemy = enemy

    def battleHurt(self, value):
        value, beforeHurtInfo = self.runEffect("beforeHurt", value)
        self.nowHp -= value
        _, commonHurtInfo = self.runEffect("onHurt", value)
        _, battleHurtInfo = self.runEffect("onBattleHurt", value)
        return beforeHurtInfo + commonHurtInfo + battleHurtInfo

    def effectHurt(self, value):
        value, beforeHurtInfo = self.runEffect("beforeHurt", value)
        self.nowHp -= value
        _, commonHurtInfo = self.runEffect("onHurt", value)
        _, effectHurtInfo = self.runEffect("onEffectHurt", value)
        return beforeHurtInfo + commonHurtInfo + effectHurtInfo

    def heal(self, value):
        value, healInfo = self.runEffect("onHealValueCalc", value)
        self.nowHp += value
        self.nowHp = min(self.nowHp, self.nowCard.cardHp)
        healInfo += self.runEffect("onHeal")
        return healInfo

    def appendEffect(self, effectId, effectAmount):
        if not effectId:
            return
        effectIdList = [effect.id for effect in self.effects] if self.effects else []
        if effectId in effectIdList:
            self.effects[effectIdList.index(effectId)].stackEffect(effectAmount)
        else:
            effect = utils.getEffectObjById(effectId, effectAmount)
            effect.setPlayerInfo(self, self.enemy)
            self.effects.append(effect)

    def appendBorder(self, effectId, borderTurn, borderStrength):
        if not effectId:
            return
        effectIdList = [effect.id for effect in self.effects] if self.effects else []
        if effectId in effectIdList:
            self.effects[effectIdList.index(effectId)].stackEffect(borderTurn)
        else:
            border = utils.getEffectObjById(effectId, borderTurn)
            border.setPlayerInfo(self, self.enemy)
            border.setBorderStrength(borderStrength)
            self.effects.append(border)

    def removeEffect(self, effectId, effectAmount=0):
        if not effectId:
            return
        effectIdList = [effect.id for effect in self.effects] if self.effects else []
        if effectId in effectIdList:
            if effectAmount == 0:
                self.effects.pop(effectIdList.index(effectId))
            else:
                self.effects[effectIdList.index(effectId)].reduceEffect(effectAmount)
        self.removeEmptyEffect()

    def removeEmptyEffect(self):
        for effect in self.effects:
            if effect.effectAmount == 0:
                self.effects.remove(effect)

    def runEffect(self, funcName, *args):
        effectInfoMsgs = []
        for effect in self.effects:
            if "Froze" in self.states:
                if effect.id != "Freeze" and not isinstance(effect, AbstractBorder):
                    continue
            func = getattr(effect, funcName)
            args = func(*args)
            args = () if args is None else args
            args = (args, ) if not isinstance(args, tuple) else args
            if effect.effectInfoMsg:
                effectInfoMsgs.append(effect.effectInfoMsg)
                effect.effectInfoMsg = ""
        effectInfoMsgs = "\n".join(effectInfoMsgs)
        self.removeEmptyEffect()
        if len(args) == 0:
            return effectInfoMsgs
        if len(args) == 1:
            return args[0], effectInfoMsgs
        # 多于一个参数的情况，需要用tuple接收返回参数
        return args, effectInfoMsgs

    def getPoints(self):
        self.attack = utils.runDiceByString(self.nowCard.atkPoint)
        self.attack, atkInfo = self.runEffect("onAttackCalc", self.attack)
        self.defence = utils.runDiceByString(self.nowCard.defPoint)
        self.defence, defInfo = self.runEffect("onDefenceCalc", self.defence)
        self.dodge = utils.runDiceByString(self.nowCard.dodPoint)
        self.dodge, dodInfo = self.runEffect("onDodgeCalc", self.dodge)
        self.attack, self.defence, self.dodge = max(self.attack, 0), max(self.defence, 0), max(self.dodge, 0)
        pointInfo = atkInfo + defInfo + dodInfo + f'{self.name} Hp:{self.nowHp} Atk:{self.attack} Def:{self.defence} Dod:{self.dodge}\n'
        return self.attack, pointInfo

    def calcHurt(self, enemyAtk):
        dodSuccess = True if self.dodge >= enemyAtk else False
        dodSuccess, dodInfo = self.runEffect('onDodgeSuccessJudge', dodSuccess)
        dodSuccess, enemyDodInfo = self.enemy.runEffect('onEnemyDodgeSuccessJudge', dodSuccess)
        defSuccess = True
        defSuccess, defInfo = self.runEffect('onDefenceSuccessJudge', defSuccess)
        defSuccess, enemyDefInfo = self.enemy.runEffect('onEnemyDefenceSuccessJudge', defSuccess)
        self.dodSuccess, self.defSuccess = dodSuccess, defSuccess
        hurtValue = 0 if dodSuccess else max(enemyAtk - self.defence, 1) if defSuccess else enemyAtk
        hurtValue, hurtInfo = self.runEffect('onHurtValueCalc', hurtValue)
        hurtValue, enemyHurtInfo = self.enemy.runEffect('onEnemyHurtValueCalc', hurtValue)
        hurtValue = 0 if hurtValue < 0 else hurtValue
        calcInfo = dodInfo + enemyDodInfo + defInfo + enemyDefInfo + hurtInfo + enemyHurtInfo + f'{self.name} 预计受伤:{hurtValue} \n'
        return hurtValue, calcInfo

    def getCardDescribe(self):
        return self.nowCard.getCardDescribe()

    def cleanTurnTempData(self):
        self.attack, self.defence, self.dodge = 0, 0, 0
        self.dodSuccess, self.defSuccess = None, None

    def shouldChangeCard(self):
        return self.nowHp <= 0

    def shouldEnd(self):
        return len(self.usedCardIndex) == 5

    def setNewMainCard(self, cardIndex) -> (bool, str):
        if cardIndex < 0 or cardIndex >= 5:
            return False, "无效的序号，请输入1-5之间的序号！"
        if cardIndex in self.usedCardIndex:
            return False, "该符卡已经使用过了！"

        self.nowCard = self.chosenCard[cardIndex]
        self.nowCard.setPlayerInfo(self, self.enemy)
        self.nowHp = self.nowCard.cardHp
        self.usedCardIndex.append(cardIndex)
        print(self.nowCard)
        return True
