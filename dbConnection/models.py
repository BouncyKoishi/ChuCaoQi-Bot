from tortoise.models import Model
from tortoise.fields import CharField, IntField, BooleanField, FloatField, DatetimeField, ForeignKeyField, CASCADE


class User(Model):
    qq = CharField(max_length=12, pk=True)
    name = CharField(max_length=32, null=True)
    title = CharField(max_length=32, null=True)
    kusa = IntField(default=0)
    advKusa = IntField(default=0)
    vipLevel = IntField(default=0)
    donateAmount = FloatField(default=0)
    isSuperAdmin = BooleanField(default=False)
    trigger = CharField(max_length=32, null=True)
    lastUseTime = DatetimeField(null=True)


class KusaField(Model):
    qq = CharField(max_length=12, pk=True)
    kusaRestTime = IntField(default=0)
    kusaIsGrowing = BooleanField(default=False)
    isUsingKela = BooleanField(default=False)
    isPrescient = BooleanField(default=False)
    biogasEffect = FloatField(default=1)
    soilCapacity = IntField(default=25)
    weedCosting = IntField(default=0)
    kusaResult = IntField(default=0)
    advKusaResult = IntField(default=0)
    kusaType = CharField(max_length=8, default="")
    defaultKusaType = CharField(max_length=8, default="草")
    lastUseTime = DatetimeField(null=True)


class KusaHistory(Model):
    qq = CharField(max_length=12)
    createTime = DatetimeField(auto_now_add=True)
    kusaType = CharField(max_length=8, default="")
    kusaResult = IntField(default=0)
    advKusaResult = IntField(default=0)


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
    timeLimitTs = DatetimeField(null=True)


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
    allowContinue = BooleanField(default=False)
    allowPrivate = BooleanField(default=False)
    allowGroup = BooleanField(default=False)
    allowRole = BooleanField(default=False)
    allowModel = BooleanField(default=False)
    chosenModel = CharField(max_length=32, default="gpt-3.5-turbo")
    tokenUse = IntField(default=0)
    tokenUseGPT4 = IntField(default=0)
    chosenRoleId = IntField(default=0)
    createTime = DatetimeField(auto_now_add=True)


class ChatRole(Model):
    id = IntField(pk=True)
    name = CharField(max_length=32)
    detail = CharField(max_length=1024)
    isPublic = BooleanField(default=False)
    creator = CharField(max_length=12)
    createTime = DatetimeField(auto_now_add=True)


class Flag(Model):
    name = CharField(max_length=32)
    value = BooleanField(default=False)
    forAll = BooleanField(default=True)
    ownerId = CharField(max_length=12, null=True)
