-- ----------------------------
-- Records of kusaitemlist
-- ----------------------------
INSERT INTO "kusaitemlist" VALUES ('G(东校区)', '东校区的G。', 'G', 0, 1, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO "kusaitemlist" VALUES ('G(南校区)', '南校区的G。', 'G', 0, 1, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO "kusaitemlist" VALUES ('G(北校区)', '北校区的G。附近的医院使G的波动趋于平缓。', 'G', 0, 1, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO "kusaitemlist" VALUES ('G(珠海校区)', '珠海校区的G。', 'G', 0, 1, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO "kusaitemlist" VALUES ('G(深圳校区)', '深圳校区的G。附近的工地使得G的波动较为剧烈。', 'G', 0, 1, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO "kusaitemlist" VALUES ('草地', '用于生草的地块。你有多少块草地，手动生草就获得多少倍的草。', '财产', 0, 0, '120', NULL, 1.04, '草', NULL, NULL);
INSERT INTO "kusaitemlist" VALUES ('生草机器', '自动生产草的机器。每天0点制造4~12个草。', '财产', 0, 0, '10', NULL, 1.01, '草', NULL, NULL);
INSERT INTO "kusaitemlist" VALUES ('生草工厂', '生产草的自动化工厂。每天0点制造640个草。', '财产', 0, 0, NULL, NULL, NULL, '自动化核心', NULL, NULL);
INSERT INTO "kusaitemlist" VALUES ('金坷垃', '高效的肥料，将生草速度加倍的同时还能使草产量翻倍。每块草地每次生草消耗一个金坷垃施肥。', '道具', 1, 1, '4', '3', NULL, '草', NULL, NULL);
INSERT INTO "kusaitemlist" VALUES ('双生法术卷轴', '记录着一种能使草的生长量翻倍的法术。使生草产量永久加倍。', '图纸', 0, 0, '240', NULL, NULL, '草', '1', NULL);
INSERT INTO "kusaitemlist" VALUES ('自动化核心', '储存着一些能量的精密核心，用于建造一些大型建筑。', '道具', 0, 1, '1000', '500', NULL, '草', NULL, NULL);
INSERT INTO "kusaitemlist" VALUES ('量子护盾', '闪耀着蓝光的不稳定护盾。抽奖时使用，被口球的概率降低90%。', '道具', 1, 1, '800', '600', NULL, '草', NULL, NULL);
INSERT INTO "kusaitemlist" VALUES ('十连券', '印着“抽奖”字样的白色票据。允许你进行一次十连抽奖，十连抽奖不会获得口球，除此以外没有保底。使用"!十连抽"以消耗十连券。', '道具', 1, 1, '32000', '24000', NULL, '草', NULL, NULL);
INSERT INTO "kusaitemlist" VALUES ('核心装配工厂', '自行装配自动化核心的工厂。每天0点生产4~12个自动化核心。', '财产', 0, 0, '25', NULL, 1.1, '自动化核心', NULL, NULL);
INSERT INTO "kusaitemlist" VALUES ('扭秤装置图纸', '罗俊测G时使用的某种大型装置的图纸。解锁建造“扭秤装置”的能力，可以使用"!扭秤装置"指令。', '图纸', 0, 0, '1000000', NULL, NULL, '草', '1', NULL);
INSERT INTO "kusaitemlist" VALUES ('扭秤装置', '能为你自动测G的大型装置。每次G市重置时，生成50~500个随机校区的G。', '财产', 0, 0, '250', NULL, NULL, '自动化核心', '50', '扭秤装置图纸');
INSERT INTO "kusaitemlist" VALUES ('生草工业园区蓝图', '一张指导你如何建立生草产业链的蓝图。解锁建造“草精炼厂”的能力，可以使用"!购买 草精炼厂 [数量]"指令。', '图纸', 0, 0, '5000000', NULL, NULL, '草', '1', 'Lv4');
INSERT INTO "kusaitemlist" VALUES ('草精炼厂', '草科学发展的基础，每天0点消耗5000个草，生成一个草之精华。你每有10个生草工厂，可以建设一个草精炼厂。', '财产', 1, 0, '500', NULL, NULL, '自动化核心', NULL, '生草工业园区蓝图');
INSERT INTO "kusaitemlist" VALUES ('生草质量I', '手动生草也能产出草之精华！每次生草有12.5%的概率产出一个草之精华。', '能力', 0, 0, '25', NULL, NULL, '草之精华', '1', NULL);
INSERT INTO "kusaitemlist" VALUES ('生草质量II', '掌握了一些从草地里收获草之精华的诀窍。每次生草产出草之精华的概率提高37.5%。', '能力', 0, 0, '200', NULL, NULL, '草之精华', '1', '生草质量I');
INSERT INTO "kusaitemlist" VALUES ('产业链优化', '同样的生草工厂可以支持更多的精炼厂了。现在每有8个生草工厂就可以建设一个草精炼厂。', '能力', 0, 0, '50', NULL, NULL, '草之精华', '1', NULL);
INSERT INTO "kusaitemlist" VALUES ('生草工厂效率I', '初步提高生草工厂的工作效率。所有生草工厂的产量*2。', '能力', 0, 0, '25', NULL, NULL, '草之精华', '1', NULL);
INSERT INTO "kusaitemlist" VALUES ('生草工厂效率II', '进一步提高生草工厂的工作效率。所有生草工厂的产量*2。', '能力', 0, 0, '150', NULL, NULL, '草之精华', '1', '生草工厂效率I');
INSERT INTO "kusaitemlist" VALUES ('生草工厂自动工艺I', '改进了自动化核心的组装和利用方法。大幅降低生草工厂的核心消耗，效果相当于一个信息员等级。', '能力', 0, 0, '333', NULL, NULL, '草之精华', '1', NULL);
INSERT INTO "kusaitemlist" VALUES ('七曜精炼术', '不愿透露姓名的魔法使提供的秘法。你每有七个草精炼厂，每日的草之精华产量就+4。', '能力', 0, 0, '177', NULL, NULL, '草之精华', '1', NULL);
INSERT INTO "kusaitemlist" VALUES ('生草工厂自动工艺II', '基于自动化核心的第二次产业升级。大幅降低生草工厂的核心消耗，效果相当于一个信息员等级。', '能力', 0, 0, '3333', NULL, NULL, '草之精华', '1', '生草工厂自动工艺I');
INSERT INTO "kusaitemlist" VALUES ('生草数量I', '先进的育种手段跨越性地提升了手动生草的产量。手动生草的产量*2.5。', '能力', 0, 0, '100', NULL, NULL, '草之精华', '1', NULL);
INSERT INTO "kusaitemlist" VALUES ('沼气池', '在百草园开挖一个味道有点重的沼气池，对作物有未知的影响。使生草产量在*0.5到*2之间随机波动。', '财产', 1, 0, '114514', NULL, NULL, '草', '1', NULL);
INSERT INTO "kusaitemlist" VALUES ('红茶', '添加了不明物质的红茶，和沼气池有玄学上的联系。如果当前存在沼气池，优化沼气池的效果，每次生草消耗一个。', '道具', 1, 1, '1919', '810', NULL, '草', NULL, '沼气池');
INSERT INTO "kusaitemlist" VALUES ('核心工厂效率I', '产出核心的效率得到了提升！所有核心装配工厂的产量*2。', '能力', 0, 0, '100', NULL, NULL, '草之精华', '1', NULL);
INSERT INTO "kusaitemlist" VALUES ('除草机', '一种农业机械，可以帮助你割除当前正在生长的草。允许你使用"!除草"指令。', '财产', 0, 0, '80000', NULL, NULL, '草', '1', NULL);
INSERT INTO "kusaitemlist" VALUES ('侦察凭证', '使用该凭证可以租借一次小除除部署的侦察卫星，探查其他人的仓库或各种排行榜。使用"!仓库 qq=[被探查者qq]"的形式以使用凭证。', '道具', 0, 1, '10000', '5000', NULL, '草', NULL, NULL);
INSERT INTO "kusaitemlist" VALUES ('深G复制品', '负G从生草宇宙中消失后留下的纪念品。仅供观赏，不能操作。', '道具', 0, 0, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO "kusaitemlist" VALUES ('生草质量III', '有概率收获复数个草之精华了！每成功产出一个草之精华，额外进行一次草之精华产出判定。', '能力', 0, 0, '1000', NULL, NULL, '草之精华', '1', '生草质量II');
INSERT INTO "kusaitemlist" VALUES ('巨草基因图谱', '允许你生“巨草”。巨草比普通的草大一倍，草产量、草精产量、生长用时、消耗土地承载力都是普通草的两倍。', '图纸', 0, 0, '800000', NULL, NULL, '草', '1', NULL);
INSERT INTO "kusaitemlist" VALUES ('速草基因图谱', '允许你生“速草”。速草比普通的草小一些，草产量是普通草的3/4，但生长用时只需普通草的一半。', '图纸', 0, 0, '75', NULL, NULL, '草之精华', '1', NULL);
INSERT INTO "kusaitemlist" VALUES ('流动生草工厂', '为特殊贡献者定制的生草工厂，可以根据需要随意移动。在每日草结算与草精炼厂建设中视为一个生草工厂。', '财产', 0, 1, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO "kusaitemlist" VALUES ('红茶池', '散发红茶清香的小池子，每天会从异次元补充一些茶水。每天0点生产15个红茶。', '财产', 0, 0, '1919810', NULL, NULL, '草', '2', '沼气池');
INSERT INTO "kusaitemlist" VALUES ('生草工厂新型设备I', '从某个工学院引进的先进生产设备，能够有效提升生草工厂的产量。所有生草工厂的产量*2。', '能力', 0, 0, '2000000', NULL, NULL, '草', '1', NULL);
INSERT INTO "kusaitemlist" VALUES ('试做型机器I', '把老旧的生草机器改造成最激进的独立生草单元！所有生草机器的产量*10。', '能力', 0, 0, '25', NULL, NULL, '草之精华', '1', NULL);
INSERT INTO "kusaitemlist" VALUES ('草精炼厂效率I', '建立了足够的草精炼厂，就可以在生产过程中总结经验了。从你的第八个精炼厂开始，每个精炼厂的产量+1。', '能力', 0, 0, '200', NULL, NULL, '草之精华', '1', '草精炼厂');
INSERT INTO "kusaitemlist" VALUES ('草之精华构造图', '草之精华的基本结构图纸，或许可以指导草之精华的人工合成。允许建造草压缩基地。', '图纸', 0, 0, '5', NULL, NULL, '草之精华', '1', NULL);
INSERT INTO "kusaitemlist" VALUES ('草压缩基地', '规模宏大的草处理基地，用于一次性将巨量的草压缩为草精。允许你使用"!草压缩"指令。', '财产', 0, 0, '10000', NULL, NULL, '自动化核心', '1', '草之精华构造图');
INSERT INTO "kusaitemlist" VALUES ('扭秤稳定理论', '向深G看齐！如果你的扭秤装置制造的G并非深G，则大幅提高G的产量。', '能力', 0, 0, '400', NULL, NULL, '草之精华', '1', '扭秤装置图纸');
INSERT INTO "kusaitemlist" VALUES ('半灵草基因图谱', '允许你生“半灵草”。有一半的概率让草的灵气具现化，使你生一份草就能得到两份收获。', '图纸', 0, 0, '500', NULL, NULL, '草之精华', '1', NULL);
INSERT INTO "kusaitemlist" VALUES ('开发组', '除草器、生草系统、符卡对战系统开发者的专属称号。', '称号', 0, 0, NULL, NULL, NULL, NULL, '1', NULL);
INSERT INTO "kusaitemlist" VALUES ('符卡规则议定者', '深度参与符卡对战系统开发人员的专属称号。', '称号', 0, 0, NULL, NULL, NULL, NULL, '1', NULL);
INSERT INTO "kusaitemlist" VALUES ('猫粮供应商', '累计投喂除草器总额较多的人员可获得的专属称号。', '称号', 0, 0, NULL, NULL, NULL, NULL, '1', NULL);
INSERT INTO "kusaitemlist" VALUES ('疯狂信息员', '在爱发电上使用特定方案投喂除草器的人员可获得的专属称号。', '称号', 0, 0, NULL, NULL, NULL, NULL, '1', NULL);
INSERT INTO "kusaitemlist" VALUES ('银行家', '生草系统早期开设银行的人员的专属称号。', '称号', 0, 0, NULL, NULL, NULL, NULL, '1', NULL);
INSERT INTO "kusaitemlist" VALUES ('大草本家', '草精版本更新前，生草工厂数达到50及以上的人员的专属称号。', '称号', 0, 0, NULL, NULL, NULL, NULL, '1', NULL);
INSERT INTO "kusaitemlist" VALUES ('G神', '草精版本更新前，通过炒G让持有草数达到一亿以上的人员的专属称号。', '称号', 0, 0, NULL, NULL, NULL, NULL, '1', NULL);
INSERT INTO "kusaitemlist" VALUES ('最初的天琴', '为第一个达到天琴信息员等级的人员所定制的专属称号。', '称号', 0, 0, NULL, NULL, NULL, NULL, '1', NULL);
INSERT INTO "kusaitemlist" VALUES ('除草王', '为发现负草、负G等特性，并搞了个大新闻的人员所定制的专属称号。', '称号', 0, 0, NULL, NULL, NULL, NULL, '1', NULL);
INSERT INTO "kusaitemlist" VALUES ('无敌暴龙战神', '定制称号。', '称号', 0, 0, NULL, NULL, NULL, NULL, '1', NULL);
INSERT INTO "kusaitemlist" VALUES ('早期符卡对战者', '在符卡对战早期版本进行过对战的人员可获得的专属称号。', '称号', 0, 0, NULL, NULL, NULL, NULL, '1', NULL);
INSERT INTO "kusaitemlist" VALUES ('投喂者', '投喂除草器总额超过20的人员可获得的专属称号。', '称号', 0, 0, NULL, NULL, NULL, NULL, '1', NULL);
INSERT INTO "kusaitemlist" VALUES ('土壤保护装置', '对百草园土壤进行强制保护的装置，保护措施好像有点极端了。禁止你在土壤承载力小于等于10的情况下生草。', '财产', 1, 0, '80000', NULL, NULL, '草', '1', NULL);
INSERT INTO "kusaitemlist" VALUES ('生草预知', '生草控制论的高级应用，不需要改造土地，只要已知草的幼苗状态就能完全预测草长成时的样子。生草时展示本次草和草精的精确产量。', '能力', 1, 0, '1000', NULL, NULL, '草之精华', '1', '初级生草预知');
INSERT INTO "kusaitemlist" VALUES ('初级生草预知', '生草控制论的初级应用，通过控制土地环境，使得草长成时的样子能被完全预测，这种受控的脆弱土地环境在进行除草会受到破坏。生草时展示本次草和草精的精确产量，但除草时需要消耗2点承载力。', '能力', 1, 0, '100', NULL, NULL, '草之精华', '1', NULL);
INSERT INTO "kusaitemlist" VALUES ('高效草精炼指南', '早期高效草精炼探索者们留下的指南，给出了优化最初几个精炼厂精炼效率的方法。你的第X本指南会使你的第X个精炼厂获得草精产量+1。', '财产', 0, 0, '250000', NULL, 4.0, '草', '7', '草精炼厂');
INSERT INTO "kusaitemlist" VALUES ('高级十连券', '印着“抽奖”字样的蓝色票据。允许你进行一次十连抽奖，抽奖获得的物品最低为Normal等级。', '道具', 1, 1, '640000', '48000', NULL, '草', NULL, NULL);
INSERT INTO "kusaitemlist" VALUES ('特级十连券', '印着“抽奖”字样的金色票据。允许你进行一次十连抽奖，抽奖获得的物品最低为Hard等级。', '道具', 1, 1, NULL, NULL, NULL, '草', NULL, NULL);
INSERT INTO "kusaitemlist" VALUES ('天琴十连券', '印着“抽奖”字样，闪耀着七色圣光的票据。允许你进行一次十连抽奖，抽奖获得的物品必定为Lunatic等级。', '道具', 1, 1, NULL, NULL, NULL, '草', NULL, NULL);
INSERT INTO "kusaitemlist" VALUES ('骰子碎片', '重置你的命运。如果抽奖单抽获得的物品是已经拥有的，消耗一个骰子碎片，重新进行抽取。每次抽奖最多消耗50个骰子碎片。', '道具', 1, 1, '3200', '2500', NULL, '草', NULL, NULL);
INSERT INTO "kusaitemlist" VALUES ('草精魔法入门', '借助草之精华的奇术性质，对草魔法进行更加深入的研究。可解锁后续的草精魔法。', '能力', 0, 0, '5', NULL, NULL, '草之精华', '1', 'Lv5');
INSERT INTO "kusaitemlist" VALUES ('纯酱的生草魔法', '魔法少女纯酱在生草时召唤了额外的草之精华喵(*^▽^)/★*☆
单次生草如果触发n连号，可以获得额外的草之精华，获取量为([(x+1)/3]+1)*3^(n-2)，其中x为本次连号数值，n为连号数量，且n≥3。', '能力', 0, 0, '200', NULL, NULL, '草之精华', '1', '草精魔法入门');
INSERT INTO "kusaitemlist" VALUES ('草精炼厂效率II', '草精炼探索者们开发了一套进一步优化基础精炼厂精炼效率的方法。你的第X本指南额外使第X个精炼厂获得草精产量+2X-2。', '能力', 0, 0, '1000', NULL, NULL, '草之精华', '1', '草精炼厂效率I');
INSERT INTO "kusaitemlist" VALUES ('奖券印刷机', '每天自动印刷抽奖券的机器，有时候会印刷出传说中没有人见过的抽奖券。每天0点时有62.5％概率获得一张十连券，25％概率获得一张高级十连券，12.5％概率获得一张特级十连券。', '财产', 0, 0, '125', NULL, NULL, '草之精华', '4', NULL);
INSERT INTO "kusaitemlist" VALUES ('奖券合成机', '获取幻之奖券必须的机器，同时也可以合成其他奖券。解锁“!合成 [奖券名称] [数量]”指令，每10个高级十连券可以合成1个特级十连券，每10个特级十连券可以合成1个天琴十连券。', '财产', 0, 0, '5000', NULL, NULL, '自动化核心', '1', NULL);
INSERT INTO "kusaitemlist" VALUES ('生草数量II', '先进的育种手段进一步提升了手动生草的产量。手动生草的产量*1.6。', '能力', 0, 0, '750', NULL, NULL, '草之精华', '1', '生草数量I');
INSERT INTO "kusaitemlist" VALUES ('生草数量III', '先进的育种手段进一步提升了手动生草的产量。手动生草的产量*1.5。', '能力', 0, 0, '2500', NULL, NULL, '草之精华', '1', '生草数量II');
INSERT INTO "kusaitemlist" VALUES ('生草数量IV', '先进的育种手段进一步提升了手动生草的产量。手动生草的产量*1.4。', '能力', 0, 0, '5000', NULL, NULL, '草之精华', '1', '生草数量III');
INSERT INTO "kusaitemlist" VALUES ('生草质量IV', '进一步提升获取草之精华的概率。生草产出草之精华的概率提高12.5%。', '能力', 0, 0, '5000', NULL, NULL, '草之精华', '1', '生草质量III');
INSERT INTO "kusaitemlist" VALUES ('试做型机器II', '对独立生草单元的设计进行了大幅度优化！所有生草机器的产量*5。', '能力', 0, 0, '250', NULL, NULL, '草之精华', '1', '试做型机器I');
INSERT INTO "kusaitemlist" VALUES ('生草工厂效率III', '进一步提高生草工厂的工作效率。所有生草工厂的产量*2。', '能力', 0, 0, '750', NULL, NULL, '草之精华', '1', '生草工厂效率II');
INSERT INTO "kusaitemlist" VALUES ('生草工厂效率IV', '进一步提高生草工厂的工作效率。所有生草工厂的产量*2。', '能力', 0, 0, '2500', NULL, NULL, '草之精华', '1', '生草工厂效率III');
INSERT INTO "kusaitemlist" VALUES ('核心工厂效率II', '进一步提高核心的产出效率！所有核心装配工厂的产量*2。', '能力', 0, 0, '500', NULL, NULL, '草之精华', '1', '核心工厂效率I');
INSERT INTO "kusaitemlist" VALUES ('核心工厂效率III', '进一步提高核心的产出效率！所有核心装配工厂的产量*2。', '能力', 0, 0, '2500', NULL, NULL, '草之精华', '1', '核心工厂效率II');
INSERT INTO "kusaitemlist" VALUES ('核心工厂效率IV', '进一步提高核心的产出效率！所有核心装配工厂的产量*1.5。', '能力', 0, 0, '5000', NULL, NULL, '草之精华', '1', '核心工厂效率III');
INSERT INTO "kusaitemlist" VALUES ('生草控制论', '生草控制论的完全应用，可以通过控制幼苗生长获得额外的草之精华。如果本次生草没有获得草之精华，获得一个额外的草之精华', '能力', 0, 0, '1200', NULL, NULL, '草之精华', '1', '生草预知,生草质量III');
INSERT INTO "kusaitemlist" VALUES ('除草器的共享魔法', '你被围殴时，如果围殴你的玩家为天琴信息员或以上，其额外得到1草之精华。
其他玩家产生生草质量喜报时，你获得1草之精华；产生连号魔法类喜报时，你获得连号部分数量的草。', '能力', 0, 0, '5', NULL, NULL, '草之精华', '1', '草精魔法入门');
INSERT INTO "kusaitemlist" VALUES ('小礼炮', '目前没有作用，请勿购买！原作用：产生各类喜报时，消耗一个小礼炮，产生一条私聊提醒。', '道具', 1, 0, '23333', '2333', NULL, '草', NULL, NULL);
INSERT INTO "kusaitemlist" VALUES ('蕾米球的生产魔法', '每日0点时，消耗所有承载力，并过载12小时。获得0.04×(x-20)份每日产量，x为消耗的承载力点数。', '能力', 1, 0, '100', NULL, NULL, '草之精华', '1', '草精魔法入门');
INSERT INTO "kusaitemlist" VALUES ('奈奈的过载魔法', '奈奈拥有的一种魔法，在挚友恋刃即将被反派劫走时觉醒。使用这种魔法，能在短期内大幅提升自己的战斗力，代价是后续能力过载而无法使用。是相当危险的一种魔法。
解锁“!过载生草 [草种]”指令，本次生草结束时，额外获得2n个草之精华，并进入3n小时的过载状态，n为本次草产量中相异数字的数量。', '能力', 0, 0, '5', NULL, NULL, '草之精华', '1', '草精魔法入门,生草质量I');
INSERT INTO "kusaitemlist" VALUES ('奈奈的时光魔法', '奈奈从伙伴Rasis和Mion处获得了时光胶囊 (XHRONOXAPSULΞ)
，觉醒了操作局部时光流逝的能力！
生草时有7％的概率使当次生草时间缩短77.7％，7‰的概率使当次生草立即完成，且不消耗承载力。', '能力', 0, 0, '7', NULL, NULL, '草之精华', '1', '草精魔法入门');
INSERT INTO "kusaitemlist" VALUES ('过载标记', '过载状态：无法生草，且降低承载力回复速度。', '状态', 0, 0, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO "kusaitemlist" VALUES ('时光胶囊标记', '时光胶囊状态：无论当前生草的剩余时间是多少，在生草判定时必然能生出草。', '状态', 0, 0, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO "kusaitemlist" VALUES ('最初的六连', '为第一个达成生草六连号的人员所定制的专属称号。', '称号', 0, 0, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO "kusaitemlist" VALUES ('不灵草基因图谱', '不灵草不会获得草，如果下一次生草不是不灵草，则产量翻倍。', '图纸', 0, 0, '2000', NULL, NULL, '草之精华', '1', '草类基因研究所');
INSERT INTO "kusaitemlist" VALUES ('灵性标记', '灵性状态：上一次生草的灵性被保存下来，使下一次生草的产量翻倍！', '状态', 0, 0, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO "kusaitemlist" VALUES ('草类基因研究所', '开放更多的草类基因图谱，开始探索草种杂交的奥秘吧！', '能力', 0, 0, '100', NULL, NULL, '草之精华', '1', '巨草基因图谱,速草基因图谱,半灵草基因图谱');
INSERT INTO "kusaitemlist" VALUES ('速速草基因图谱', '生草速度的极致！生草速度为随机1-5min，草产量为是普通草的1/2。', '图纸', 0, 0, '500', NULL, NULL, '草之精华', '1', '草类基因研究所');
INSERT INTO "kusaitemlist" VALUES ('巨巨草基因图谱', '超级巨大的草，单株产量很高的同时消耗巨大。生长用时、消耗土地承载力都是普通草的四倍，产量是普通草的三倍。', '图纸', 0, 0, '500', NULL, NULL, '草之精华', '1', '草类基因研究所');
INSERT INTO "kusaitemlist" VALUES ('灵灵草基因图谱', '对灵性基因的开发使得一次叠加多层灵气成为可能。1/2^(n+1)概率使用n灵草草种，n最多为8。n灵草：产量为正常生草的n+1倍。', '图纸', 0, 0, '2000', NULL, NULL, '草之精华', '1', '草类基因研究所');
INSERT INTO "kusaitemlist" VALUES ('半灵巨草基因图谱', '半灵草和巨草的杂交品种。草产量、生长用时、消耗土地承载力都是普通草的两倍。有1/2的概率为巨灵草，巨灵草的产量变为普通草的四倍。', '图纸', 0, 0, '2000', NULL, NULL, '草之精华', '1', '草类基因研究所');
INSERT INTO "kusaitemlist" VALUES ('神灵草基因模块', '神灵草是草类育种界的奇迹，可惜其性状并不稳定，无法稳定育种，仅能偶发产生。生非不灵草时，有1/20概率将草种更改为神灵草，神灵草的产量为普通草的10倍。', '图纸', 1, 0, '2000', NULL, NULL, '草之精华', '1', '草类基因研究所');
INSERT INTO "kusaitemlist" VALUES ('策划组', '生草系统策划组成员的专属称号。', '称号', 0, 0, NULL, NULL, NULL, NULL, '1', NULL);
INSERT INTO "kusaitemlist" VALUES ('攻略组', '为生草系统创作攻略的人员的专属称号。', '称号', 0, 0, NULL, NULL, NULL, NULL, '1', NULL);
INSERT INTO "kusaitemlist" VALUES ('冰雪酱的休耕魔法', '冰雪酱将长时间没有生草的土地冷藏了起来，进一步保持了休耕土地的肥力，使之后的生草产出得到了提升！触发[蕾米球的生产魔法]并消耗25点承载力时，将过载时间改为9h，且本日首次生草的产量变为3倍，第二次生草的产量变为2倍（包括草之精华）。', '能力', 1, 0, '149', NULL, NULL, '草之精华', '1', '蕾米球的生产魔法');
INSERT INTO "kusaitemlist" VALUES ('休耕标记', '休耕状态：由冰雪酱的休耕魔法提供。休耕后肥沃的土地可为草和草精产量提供加成。', '状态', 0, 0, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO "kusaitemlist" VALUES ('不灵草速生模块', '为不灵草特制的实验性催生装置。生不灵草时，50％概率在一分钟内收获。', '能力', 0, 0, '500', NULL, NULL, '草之精华', '1', '不灵草基因图谱,速速草基因图谱');
INSERT INTO "kusaitemlist" VALUES ('不灵草灵生模块', '对保存下来的灵性进行激活的装置。生不灵草后，下一次生草为神灵草的概率翻倍。', '能力', 0, 0, '2000', NULL, NULL, '草之精华', '1', '不灵草基因图谱,神灵草基因模块');
INSERT INTO "kusaitemlist" VALUES ('生草工厂新型设备II', '从某个工学院引进的生草自动化流水线，能够进一步提升生草工厂的产量。所有生草工厂的产量*2。', '能力', 0, 0, '200000000', NULL, NULL, '草', '1', '生草工厂新型设备I');
INSERT INTO "kusaitemlist" VALUES ('灵性自动分配装置', '发送"!生草"时，如果当前没有不灵增幅效果，则将生草草种自动修改为不灵草。对除草时的自动生草同样生效。', '能力', 1, 0, '5000', NULL, NULL, '草之精华', '1', '不灵草基因图谱,生草控制论');
INSERT INTO "kusaitemlist" VALUES ('小除除的原型', '专属称号。', '称号', 0, 0, NULL, NULL, NULL, NULL, '1', NULL);
INSERT INTO "kusaitemlist" VALUES ('祝福之色赠予结缘之人', '与奈奈结缘之人的特殊称号。', '称号', 0, 0, NULL, NULL, NULL, NULL, '1', NULL);
INSERT INTO "kusaitemlist" VALUES ('肥力贮存技术I', '罗俊的“天文密藏法”研究获得了突破性进展，允许部分存储溢出的承载力！当你承载力满时，每6小时获得1点后备承载力。
解锁!补充承载力 [数字]指令，允许你使用后备承载力补充草地承载力。
解锁物品“肥力贮存仓”，你的后备承载力上限取决于“肥力贮存仓”的数量。
（注意：本科技并不提供基础后备承载力上限，请购买适量贮存仓以发挥作用）
', '能力', 0, 0, '50', NULL, NULL, '草之精华', '1', '生草质量II');
INSERT INTO "kusaitemlist" VALUES ('肥力贮存技术II', '获取后备承载力的速度更快了。当你的承载力为25时，每4.5小时获得1点后备承载力。你的后备承载力上限取决于“肥力贮存仓”的数量。', '能力', 0, 0, '250', NULL, NULL, '草之精华', '1', '肥力贮存技术I');
INSERT INTO "kusaitemlist" VALUES ('肥力贮存技术III', '获取后备承载力的速度达到上限。当你的承载力为25时，每3小时获得1点后备承载力。你的后备承载力上限取决于“肥力贮存仓”的数量。', '能力', 0, 0, '1250', NULL, NULL, '草之精华', '1', '肥力贮存技术II');
INSERT INTO "kusaitemlist" VALUES ('肥力贮存仓', '你每拥有一个肥力贮存仓，便能多存储1点后备承载力。', '财产', 0, 0, '300', NULL, 1.2, '自动化核心', '50', '肥力贮存技术I');
INSERT INTO "kusaitemlist" VALUES ('后备承载力', '可使用!补充承载力 [数字]指令，消耗后备承载力补充草地承载力，不能突破承载力上限。', '状态', 0, 0, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO "kusaitemlist" VALUES ('后备承载力单元', '内部物品，用于标记后备承载力的获取进度。', '状态', 0, 0, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO "kusaitemlist" VALUES ('镜中草基因模块', '镜中草是俊俊子在开发了“天文密藏法”后发现的草种，能独立于原本的草地在肥力贮存仓中生长，可惜如镜花水月般难以捉摸。
当你的后备承载力不为0时，生“不灵草”以外的草种时有50％概率消耗一点后备承载力，使你本次生草获得的草精和草数翻倍。', '能力', 1, 0, '404', NULL, NULL, '草之精华', '1', '草类基因研究所,肥力贮存技术I');

-- ----------------------------
-- Records of flag
-- ----------------------------
INSERT INTO "main"."flag" ("id", "name", "value", "forAll", "ownerId") VALUES (1, '生草预估详情展示', 1, 1, NULL);
INSERT INTO "main"."flag" ("id", "name", "value", "forAll", "ownerId") VALUES (2, '发送承载力回满信息', 0, 1, NULL);
INSERT INTO "main"."flag" ("id", "name", "value", "forAll", "ownerId") VALUES (3, '除草后自动生草', 0, 1, NULL);
INSERT INTO "main"."flag" ("id", "name", "value", "forAll", "ownerId") VALUES (12, '过载结束提示', 0, 1, NULL);
INSERT INTO "main"."flag" ("id", "name", "value", "forAll", "ownerId") VALUES (13, 'G市重置提示', 0, 1, NULL);
INSERT INTO "main"."flag" ("id", "name", "value", "forAll", "ownerId") VALUES (16, '物品转让提示', 0, 1, NULL);
INSERT INTO "main"."flag" ("id", "name", "value", "forAll", "ownerId") VALUES (19, '捐赠信息公开展示', 1, 1, NULL);
