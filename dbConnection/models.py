from tortoise.models import Model
from tortoise.fields import CharField, IntField, BooleanField, FloatField, DatetimeField, ForeignKeyField, CASCADE


class User(Model):
    qq = CharField(max_length=12, pk=True)
    name = CharField(max_length=32, null=True)
    title = CharField(max_length=32, null=True)
    kusa = IntField(default=0)
    advKusa = IntField(default=0)
    vipLevel = IntField(default=0)
    isSuperAdmin = BooleanField(default=False)
    isRobot = BooleanField(default=False)
    relatedQQ = CharField(max_length=12, null=True)
    lastUseTime = DatetimeField(null=True)


class KusaField(Model):
    qq = CharField(max_length=12, pk=True)
    kusaFinishTs = IntField(default=None, null=True)
    isUsingKela = BooleanField(default=False)
    isPrescient = BooleanField(default=False)
    overloadOnHarvest = BooleanField(default=False)
    biogasEffect = FloatField(default=1)
    soilCapacity = IntField(default=25)
    weedCosting = IntField(default=0)
    kusaResult = IntField(default=0)
    advKusaResult = IntField(default=0)
    kusaType = CharField(max_length=8, default=None, null=True)
    defaultKusaType = CharField(max_length=8, default="草")
    lastUseTime = DatetimeField(null=True)


class KusaHistory(Model):
    qq = CharField(max_length=12)
    kusaType = CharField(max_length=8, default="")
    kusaResult = IntField(default=0)
    advKusaResult = IntField(default=0)
    createTimeTs = IntField()


class DrawItemList(Model):
    id = IntField(pk=True)
    name = CharField(max_length=64)
    pool = CharField(max_length=32)
    rareRank = IntField()
    detail = CharField(max_length=1024)
    author = CharField(max_length=12)


class DrawItemStorage(Model):
    qq = CharField(max_length=12)
    item = ForeignKeyField("models.DrawItemList", on_delete=CASCADE, related_name="draw_item_storage")
    amount = IntField()


class KusaItemList(Model):
    name = CharField(max_length=64, pk=True)
    detail = CharField(max_length=1024, null=True)
    type = CharField(max_length=32, null=True)
    isControllable = BooleanField(default=True)
    isTransferable = BooleanField(default=True)
    shopPrice = IntField(null=True)
    sellingPrice = IntField(null=True)
    priceRate = FloatField(null=True)
    priceType = CharField(max_length=32, null=True)
    amountLimit = IntField(null=True)
    shopPreItems = CharField(max_length=128, null=True)


class KusaItemStorage(Model):
    qq = CharField(max_length=12)
    item = ForeignKeyField("models.KusaItemList", on_delete=CASCADE, related_name="kusa_item_storage")
    amount = IntField()
    allowUse = BooleanField(default=True)
    timeLimitTs = IntField(null=True)


class GValue(Model):
    cycle = IntField()
    turn = IntField()
    eastValue = FloatField()
    southValue = FloatField()
    northValue = FloatField()
    zhuhaiValue = FloatField()
    shenzhenValue = FloatField()
    createTime = DatetimeField()


class WorkOrder(Model):
    id = IntField(pk=True)
    title = CharField(max_length=128)
    author = CharField(max_length=12)
    detail = CharField(max_length=1024, null=True)
    reply = CharField(max_length=512, null=True)


class ChatUser(Model):
    qq = CharField(max_length=12, pk=True)
    allowPrivate = BooleanField(default=False)
    allowRole = BooleanField(default=False)
    allowAdvancedModel = BooleanField(default=False)
    chosenModel = CharField(max_length=32, default="deepseek-chat")
    tokenUse = IntField(default=0)
    todayTokenUse = IntField(default=0)
    dailyTokenLimit = IntField(default=10000)
    chosenRoleId = IntField(default=0)
    createTime = DatetimeField(auto_now_add=True)


class ChatRole(Model):
    id = IntField(pk=True)
    name = CharField(max_length=32)
    detail = CharField(max_length=10240)
    isPublic = BooleanField(default=False)
    creator = CharField(max_length=12)
    createTime = DatetimeField(auto_now_add=True)


class Flag(Model):
    name = CharField(max_length=32)
    value = BooleanField(default=False)
    forAll = BooleanField(default=True)
    ownerId = CharField(max_length=12, null=True)


class DonateRecord(Model):
    qq = CharField(max_length=12)
    amount = FloatField()
    donateDate = CharField(max_length=16)
    source = CharField(max_length=12)
    remark = CharField(max_length=128, null=True)


class TradeRecord(Model):
    id = IntField(pk=True)
    operator = CharField(max_length=12)
    tradeType = CharField(max_length=16)
    gainItemAmount = IntField(null=True)
    gainItemName = CharField(max_length=64, null=True)
    costItemAmount = IntField(null=True)
    costItemName = CharField(max_length=64, null=True)
    detail = CharField(max_length=128, null=True)
    timestamp = IntField()


