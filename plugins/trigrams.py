import time
import random
from nonebot import scheduler
from nonebot import on_command, CommandSession
from plugins.chatGPT_api import getChatReply

gptUseRecord = {}


@on_command(name='起卦', only_to_me=False)
async def _(session: CommandSession):
    global gptUseRecord
    userId = session.ctx['user_id']
    strippedArg = session.current_arg_text.strip()
    if len(strippedArg) > 100:
        await session.send('暂不支持过长的起卦内容^ ^')
        return
    hashingStr = strippedArg + str(userId) + str(time.strftime("%Y-%m-%d %H", time.localtime())) + 'Trigram'
    random.seed(hash(hashingStr))

    symbols = []
    changeableIndex = []
    for i in range(6):
        coins = [random.randint(0, 1) for _ in range(3)]
        symbol, isChangeAble = getLinearSymbol(coins)
        symbols.append(symbol)
        if isChangeAble:
            changeableIndex.append(i)

    innerTrigram8 = getTrigram8(symbols[:3].copy())
    outerTrigram8 = getTrigram8(symbols[3:].copy())
    trigram64 = getTrigram64(symbols.copy())
    changedInnerTrigram8, changedOuterTrigram8, changedTrigram64 = innerTrigram8, outerTrigram8, trigram64

    if len(changeableIndex) != 0:
        changedSymbols = symbols.copy()
        for i in changeableIndex:
            changedSymbols[i] = b'1' if changedSymbols[i] == b'0' else b'0'
        changedInnerTrigram8 = getTrigram8(changedSymbols[:3].copy())
        changedOuterTrigram8 = getTrigram8(changedSymbols[3:].copy())
        changedTrigram64 = getTrigram64(changedSymbols.copy())

    outputStr = f'对【{strippedArg}】的占卜结果为：\n' if strippedArg != '' else '占卜结果为：\n'
    outputStr += f'爻：{getSymbolsName(symbols, changeableIndex)} '
    outputStr += f'({getSymbolsSign(outerTrigram8, innerTrigram8, changedOuterTrigram8, changedInnerTrigram8)})\n'
    outputStr += f'本卦：{getTrigramName(outerTrigram8, innerTrigram8, trigram64)}   '
    outputStr += f'之卦：{getTrigramName(changedOuterTrigram8, changedInnerTrigram8, changedTrigram64)}\n' if len(changeableIndex) != 0 else ''
    outputStr += f'卦辞：{getFinalWords(trigram64, changedTrigram64, changeableIndex)}'
    outputStr += '\n如果需要进一步解析，请输入“解卦”'

    confirm = await session.aget(prompt=outputStr)
    if '解卦' in confirm:
        if gptUseRecord.get(userId, 0) > 10:
            await session.send('今日解卦次数已达上限，请明日再来。')
            return
        gptUseRecord[userId] = gptUseRecord[userId] + 1 if userId in gptUseRecord else 1
        await session.send('请稍等，正在为你解卦...')
        chatGPTPrompt = getChatGPTPrompt(strippedArg, getFinalWords(trigram64, changedTrigram64, changeableIndex))
        reply, _ = await getChatReply("gpt-4o-mini", chatGPTPrompt)
        await session.send(f'{reply}\n\n注：以上解卦内容由AI生成，仅供参考。')

    random.seed()


@scheduler.scheduled_job('cron', day='*', hour='0', minute='5')
async def _():
    global gptUseRecord
    gptUseRecord = {}


# 根据铜钱正反面的结果，获取爻
def getLinearSymbol(coins):
    obverseCount = coins.count(1)
    if obverseCount == 0:
        return b'1', True
    elif obverseCount == 1:
        return b'0', False
    elif obverseCount == 2:
        return b'1', False
    elif obverseCount == 3:
        return b'0', True


def getSymbolsName(symbols, changeableIndex):
    nameList = []
    for i in range(6):
        if i == 0:
            symbolName = '初九' if symbols[i] == b'1' else '初六'
        elif i == 5:
            symbolName = '上九' if symbols[i] == b'1' else '上六'
        else:
            indexDict = {1: '二', 2: '三', 3: '四', 4: '五'}
            symbolName = '九' if symbols[i] == b'1' else '六'
            symbolName += indexDict[i] if i in indexDict else ''
        symbolName += '(动)' if i in changeableIndex else ''
        nameList.append(symbolName)
    return '，'.join(nameList)


def getSymbolsSign(outerTrigram8, innerTrigram8, changedOuterTrigram8, changedInnerTrigram8):
    outputStr = outerTrigram8['display'] + innerTrigram8['display']
    if outerTrigram8['name'] == changedOuterTrigram8['name'] and innerTrigram8['name'] == changedInnerTrigram8['name']:
        return outputStr
    outputStr += f" -> {changedOuterTrigram8['display'] + changedInnerTrigram8['display']}"
    return outputStr


def getTrigramName(outerTrigram8, innerTrigram8, trigram64):
    trigram64Name = trigram64['base'].split('：')[0]
    if outerTrigram8['name'] == innerTrigram8['name']:
        return f'{trigram64Name}为{outerTrigram8["alias"]}'
    return f'{outerTrigram8["alias"]}{innerTrigram8["alias"]}{trigram64Name}'


def getFinalWords(trigram64, changedTrigram64, changeableIndex):
    if len(changeableIndex) == 0:
        return trigram64['base']
    elif len(changeableIndex) == 1:
        index = changeableIndex[0]
        lineKey = f'line{index + 1}'
        return trigram64[lineKey]
    elif len(changeableIndex) == 2:
        index1, index2 = changeableIndex
        lineKey1 = f'line{index1 + 1}'
        lineKey2 = f'line{index2 + 1}'
        return trigram64[lineKey1] + '\n' + trigram64[lineKey2]
    elif len(changeableIndex) == 3:
        return trigram64['base'] + '\n' + changedTrigram64['base']
    elif len(changeableIndex) == 4:
        index1, index2 = set(range(6)) - set(changeableIndex)
        lineKey1 = f'line{index1 + 1}'
        lineKey2 = f'line{index2 + 1}'
        return trigram64[lineKey1] + '\n' + trigram64[lineKey2]
    elif len(changeableIndex) == 5:
        index = list(set(range(6)) - set(changeableIndex))[0]
        lineKey = f'line{index + 1}'
        return trigram64[lineKey]
    elif len(changeableIndex) == 6:
        if trigram64['base'].split('：')[0] == '乾':
            return '用九：见群龙无首，吉。'
        elif trigram64['base'].split('：')[0] == '坤':
            return '用六：利永贞。'
        else:
            return changedTrigram64['base']
    return '未知'


def getChatGPTPrompt(argStr, baseResultStr):
    content = f'来访者的问题或关键词：{argStr}' if argStr != '' else '来访者未给出问题或关键词。'
    content += f'\n你的初始占卜结果：{baseResultStr}'
    return [{"role": "system", "content": "你是一位精通周易的占卜师，正为一位来访者解卦。你应结合来访者的问题/关键词和你的初始占卜结果，为来访者提供简明扼要的解卦信息。"},
            {"role": "user", "content": content}]


def getTrigram8(linearSymbols):
    trigramsMap = {
        b'111': {'name': '乾', 'alias': '天', 'display': '☰'},
        b'011': {'name': '兑', 'alias': '泽', 'display': '☱'},
        b'101': {'name': '离', 'alias': '火', 'display': '☲'},
        b'001': {'name': '震', 'alias': '雷', 'display': '☳'},
        b'110': {'name': '巽', 'alias': '风', 'display': '☴'},
        b'010': {'name': '坎', 'alias': '水', 'display': '☵'},
        b'100': {'name': '艮', 'alias': '山', 'display': '☶'},
        b'000': {'name': '坤', 'alias': '地', 'display': '☷'}
    }
    linearSymbols.reverse()
    symbolsStr = b"".join(linearSymbols)
    return trigramsMap[symbolsStr]


def getTrigram64(linearSymbols):
    trigramsMap = {
        b'111111': {'order': 1, 'base': '乾：元，亨，利，贞。', 'line1': '初九：潜龙勿用。', 'line2': '九二：见龙在田，利见大人。', 'line3': '九三：君子终日乾乾，夕惕若厉，无咎。', 'line4': '九四：或跃在渊，无咎。', 'line5': '九五：飞龙在天，利见大人。', 'line6': '上九，亢龙有悔。'},
        b'000000': {'order': 2, 'base': '坤：元，亨，利牝马之贞。君子有攸往，先迷后得主，利。西南得朋，东北丧朋。安贞吉。', 'line1': '初六：履霜，坚冰至。', 'line2': '六二：直方大，不习无不利。', 'line3': '六三：含章可贞。或从王事，无成有终。', 'line4': '六四：括囊，无咎无誉。', 'line5': '六五：黄裳，元吉。', 'line6': '上六：龙战于野，其血玄黄。'},
        b'010001': {'order': 3, 'base': '屯：元亨利贞。勿用有攸往，利建侯。', 'line1': '初九：磐桓，利居贞，利建侯。', 'line2': '六二：屯如邅如，乘马班如。匪寇婚媾，女子贞不字，十年乃字。', 'line3': '六三：既鹿无虞，惟入于林中，君子几，不如舍，往吝。', 'line4': '六四：乘马班如，求婚媾，往吉，无不利。', 'line5': '九五：屯其膏，小贞吉，大贞凶。', 'line6': '上六：乘马班如，泣血涟如。'},
        b'100010': {'order': 4, 'base': '蒙：亨。匪我求童蒙，童蒙求我。初噬告，再三渎，渎则不告。利贞。', 'line1': '初六：发蒙，利用刑人，用说桎梏，以往吝。', 'line2': '九二：包蒙，吉。纳妇吉，子克家。', 'line3': '六三：勿用取女，见金夫，不有躬，无攸利。', 'line4': '六四：困蒙，吝。', 'line5': '六五：童蒙，吉。', 'line6': '上九：击蒙，不利为寇，利御寇。'},
        b'010111': {'order': 5, 'base': '需：有孚，光亨，贞吉。利涉大川。', 'line1': '初九：需于郊。利用恒，无咎。', 'line2': '九二：需于沙。小有言，终吉。', 'line3': '九三：需于泥，致寇至。', 'line4': '六四：需于血，出自穴。', 'line5': '九五：需于酒食，贞吉。', 'line6': '上六：入于穴，有不速之客三人来，敬之终吉。'},
        b'111010': {'order': 6, 'base': '讼：有孚，窒惕，中吉，终凶。利见大人，不利涉大川。', 'line1': '初六：不永所事，小有言，终吉。', 'line2': '九二：不克讼，归而逋，其邑人三百户，无眚。', 'line3': '六三：食旧德，贞厉，终吉，或从王事，无成。', 'line4': '九四：不克讼，复即命，渝安贞，吉。', 'line5': '九五：讼，元吉。', 'line6': '上九：或锡之鞶带，终朝三褫之。'},
        b'000010': {'order': 7, 'base': '师：贞，丈人吉，无咎。', 'line1': '初六：师出以律，否臧凶。', 'line2': '九二：在师，中吉，无咎，王三锡命。', 'line3': '六三：师或舆尸，凶。', 'line4': '六四：师左次，无咎。', 'line5': '六五：田有禽，利执言，无咎。长子帅师，弟子舆尸，贞凶。', 'line6': '上六：大君有命，开国承家，小人勿用。'},
        b'010000': {'order': 8, 'base': '比：吉。原筮，元永贞，无咎。不宁方来，后夫凶。', 'line1': '初六：有孚比之，无咎。有孚盈缶，终来有它，吉。', 'line2': '六二：比之自内，贞吉。', 'line3': '六三：比之匪人。', 'line4': '六四：外比之，贞吉。', 'line5': '九五：显比，王用三驱，失前禽。邑人不诫，吉。', 'line6': '上六：比之无首，凶。'},
        b'110111': {'order': 9, 'base': '小畜：亨。密云不雨，自我西郊。', 'line1': '初九：复自道，何其咎？吉。', 'line2': '九二：牵复，吉。', 'line3': '九三：舆说辐，夫妻反目。', 'line4': '六四：有孚，血去惕出，无咎。', 'line5': '九五：有孚挛如，富以其邻。', 'line6': '上九：既雨既处，尚德载，妇贞厉。月几望，君子征凶。'},
        b'111011': {'order': 10, 'base': '履：履虎尾，不咥人，亨。', 'line1': '初九：素履往，无咎。', 'line2': '九二：履道坦坦，幽人贞吉。', 'line3': '六三：眇能视，跛能履，履虎尾，咥人，凶。武人为于大君。', 'line4': '九四：履虎尾，愬愬，终吉。', 'line5': '九五：夬履，贞厉。', 'line6': '上九：视履考祥，其旋元吉。'},
        b'000111': {'order': 11, 'base': '泰：小往大来，吉，亨。', 'line1': '初九：拔茅茹，以其汇，征吉。', 'line2': '九二：包荒，用冯河，不遐遗，朋亡，得尚于中行。', 'line3': '九三：无平不陂，无往不复。艰贞无咎。勿恤其孚，于食有福。', 'line4': '六四：翩翩，不富以其邻，不戒以孚。', 'line5': '六五：帝乙归妹，以祉元吉。', 'line6': '上六：城复于隍，勿用师。自邑告命，贞吝。'},
        b'111000': {'order': 12, 'base': '否：否之匪人，不利君子贞，大往小来。', 'line1': '初六：拔茅茹，以其汇，贞吉，亨。', 'line2': '六二：包承，小人吉，大人否，亨。', 'line3': '六三：包羞。', 'line4': '九四：有命无咎，畴离祉。', 'line5': '九五：休否，大人吉。其亡其亡，系于苞桑。', 'line6': '上九：倾否，先否后喜。'},
        b'111101': {'order': 13, 'base': '同人：同人于野，亨。利涉大川，利君子贞。', 'line1': '初九：同人于门，无咎。', 'line2': '六二：同人于宗，吝。', 'line3': '九三：伏戎于莽，升其高陵，三岁不兴。', 'line4': '九四：乘其墉，弗克攻，吉。', 'line5': '九五：同人，先号咷而后笑。大师克相遇。', 'line6': '上九：同人于郊，无悔。'},
        b'101111': {'order': 14, 'base': '大有：元亨。', 'line1': '初九：无交害，匪咎，艰则无咎。', 'line2': '九二：大车以载，有攸往，无咎。', 'line3': '九三：公用亨于天子，小人弗克。', 'line4': '九四：匪其彭，无咎。', 'line5': '六五：厥孚交如，威如，吉。', 'line6': '上九：自天佑之，吉无不利。'},
        b'000100': {'order': 15, 'base': '谦：亨，君子有终。', 'line1': '初六：谦谦君子，用涉大川，吉。', 'line2': '六二：鸣谦，贞吉。', 'line3': '九三：劳谦君子，有终，吉。', 'line4': '六四：无不利，㧑谦。', 'line5': '六五：不富以其邻，利用侵伐，无不利。', 'line6': '上六：鸣谦，利用行师，征邑国。'},
        b'001000': {'order': 16, 'base': '豫：利建侯行师。', 'line1': '初六：鸣豫，凶。', 'line2': '六二：介于石，不终日，贞吉。', 'line3': '六三：盱豫，悔。迟有悔。', 'line4': '九四：由豫，大有得。勿疑。朋盍簪。', 'line5': '六五：贞疾，恒不死。', 'line6': '上六：冥豫，成有渝，无咎。'},
        b'011001': {'order': 17, 'base': '随：元亨利贞，无咎。', 'line1': '初九：官有渝，贞吉。出门交有功。', 'line2': '六二：系小子，失丈夫。', 'line3': '六三：系丈夫，失小子。随有求得，利居贞。', 'line4': '九四：随有获，贞凶。有孚，在道以明，何咎。', 'line5': '九五：孚于嘉，吉。', 'line6': '上六：拘系之，乃从维之。王用亨于西山。'},
        b'100110': {'order': 18, 'base': '蛊：元亨，利涉大川。先甲三日，后甲三日。', 'line1': '初六：干父之蛊，有子，考无咎，厉终吉。', 'line2': '九二：干母之蛊，不可贞。', 'line3': '九三：干父之蛊，小有悔，无大咎。', 'line4': '六四：裕父之蛊，往见吝。', 'line5': '六五：干父之蛊，用誉。', 'line6': '上九：不事王侯，高尚其事。'},
        b'000011': {'order': 19, 'base': '临：元亨利贞。至于八月有凶。', 'line1': '初九：咸临，贞吉。', 'line2': '九二：咸临，吉，无不利。', 'line3': '六三：甘临，无攸利。既忧之，无咎。', 'line4': '六四：至临，无咎。', 'line5': '六五：知临，大君之宜，吉。', 'line6': '上六：敦临，吉，无咎。'},
        b'110000': {'order': 20, 'base': '观：盥而不荐，有孚颙若。', 'line1': '初六：童观，小人无咎，君子吝。', 'line2': '六二：窥观，利女贞。', 'line3': '六三：观我生，进退。', 'line4': '六四：观国之光，利用宾于王。', 'line5': '九五：观我生，君子无咎。', 'line6': '上九：观其生，君子无咎。'},
        b'101001': {'order': 21, 'base': '噬嗑：亨。利用狱。', 'line1': '初九：屦校灭趾，无咎。', 'line2': '六二：噬肤灭鼻，无咎。', 'line3': '六三：噬腊肉，遇毒。小吝，无咎。', 'line4': '九四：噬干胏，得金矢。利艰贞，吉。', 'line5': '六五：噬干肉，得黄金。贞厉，无咎。', 'line6': '上九：何校灭耳，凶。'},
        b'100101': {'order': 22, 'base': '贲：亨。小利有所往。', 'line1': '初九：贲其趾，舍车而徒。', 'line2': '六二：贲其须。', 'line3': '九三：贲如，濡如，永贞吉。', 'line4': '六四：贲如，皤如，白马翰如，匪寇婚媾。', 'line5': '六五：贲于丘园，束帛戋戋，吝，终吉。', 'line6': '上九：白贲，无咎。'},
        b'100000': {'order': 23, 'base': '剥：不利有攸往。', 'line1': '初六：剥床以足，蔑贞，凶。', 'line2': '六二：剥床以辨，蔑贞，凶。', 'line3': '六三：剥之，无咎。', 'line4': '六四：剥床以肤，凶。', 'line5': '六五：贯鱼，以宫人宠，无不利。', 'line6': '上九：硕果不食，君子得舆，小人剥庐。'},
        b'000001': {'order': 24, 'base': '复：亨。出入无疾，朋来无咎。反复其道，七日来复，利有攸往。', 'line1': '初九：不远复，无祗悔，元吉。', 'line2': '六二：休复，吉。', 'line3': '六三：频复，厉，无咎。', 'line4': '六四：中行独复。', 'line5': '六五：敦复，无悔。', 'line6': '上六：迷复，凶，有灾眚。用行师，终有大败，以其国君凶。至于十年，不克征。'},
        b'111001': {'order': 25, 'base': '无妄：元亨利贞。其匪正有眚，不利有攸往。', 'line1': '初九：无妄，往吉。', 'line2': '六二：不耕获，不菑畲，则利有攸往。', 'line3': '六三：无妄之灾，或系之牛，行人之得，邑人之灾。', 'line4': '九四：可贞，无咎。', 'line5': '九五：无妄之疾，勿药有喜。', 'line6': '上九：无妄，行有眚，无攸利。'},
        b'100111': {'order': 26, 'base': '大畜：利贞。不家食吉，利涉大川。', 'line1': '初九：有厉，利已。', 'line2': '九二：舆说辐。', 'line3': '九三：良马逐，利艰贞。曰闲舆卫，利有攸往。', 'line4': '六四：童牛之牿，元吉。', 'line5': '六五：豮豕之牙，吉。', 'line6': '上九：何天之衢，亨。'},
        b'100001': {'order': 27, 'base': '颐：贞吉。观颐，自求口实。', 'line1': '初九：舍尔灵龟，观我朵颐，凶。', 'line2': '六二：颠颐，拂经，于丘颐，征凶。', 'line3': '六三：拂颐，贞凶，十年勿用，无攸利。', 'line4': '六四：颠颐，吉。虎视眈眈，其欲逐逐，无咎。', 'line5': '六五：拂经，居贞吉，不可涉大川。', 'line6': '上九：由颐，厉吉，利涉大川。'},
        b'011110': {'order': 28, 'base': '大过：栋桡，利有攸往，亨。', 'line1': '初六：藉用白茅，无咎。', 'line2': '九二：枯杨生稊，老夫得其女妻，无不利。', 'line3': '九三：栋桡，凶。', 'line4': '九四：栋隆，吉。它吝。', 'line5': '九五：枯杨生华，老妇得士夫，无咎无誉。', 'line6': '上六：过涉灭顶，凶，无咎。'},
        b'010010': {'order': 29, 'base': '坎：习坎，有孚，维心亨，行有尚。', 'line1': '初六：习坎，入于坎窞，凶。', 'line2': '九二：坎有险，求小得。', 'line3': '六三：来之坎坎，险且枕，入于坎窞，勿用。', 'line4': '六四：樽酒簋贰，用缶，纳约自牖，终无咎。', 'line5': '九五：坎不盈，祗既平，无咎。', 'line6': '上六：系用徽纆，窴于丛棘，三岁不得，凶。'},
        b'101101': {'order': 30, 'base': '离：利贞，亨。畜牝牛，吉。', 'line1': '初九：履错然，敬之无咎。', 'line2': '六二：黄离，元吉。', 'line3': '九三：日昃之离，不鼓缶而歌，则大耋之嗟，凶。', 'line4': '九四：突如其来如，焚如，死如，弃如。', 'line5': '六五：出涕沱若，戚嗟若，吉。', 'line6': '上九：王用出征，有嘉。折首，获其匪丑，无咎。'},
        b'011100': {'order': 31, 'base': '咸：亨，利贞，取女吉。', 'line1': '初六：咸其拇。', 'line2': '六二：咸其腓，凶，居吉。', 'line3': '九三：咸其股，执其随，往吝。', 'line4': '九四：贞吉悔亡，憧憧往来，朋从尔思。', 'line5': '九五：咸其脢，无悔。', 'line6': '上六：咸其辅，颊，舌。'},
        b'001110': {'order': 32, 'base': '恒：亨，无咎，利贞，利有攸往。', 'line1': '初六：浚恒，贞凶，无攸利。', 'line2': '九二：悔亡。', 'line3': '九三：不恒其德，或承之羞，贞吝。', 'line4': '九四：田无禽。', 'line5': '六五：恒其德，贞，妇人吉，夫子凶。', 'line6': '上六：振恒，凶。'},
        b'111100': {'order': 33, 'base': '遁：亨，小利贞。', 'line1': '初六：遁尾，厉，勿用有攸往。', 'line2': '六二：执之用黄牛之革，莫之胜说。', 'line3': '九三：系遁，有疾厉，畜臣妾，吉。', 'line4': '九四：好遁，君子吉，小人否。', 'line5': '九五：嘉遁，贞吉。', 'line6': '上九：肥遁，无不利。'},
        b'001111': {'order': 34, 'base': '大壮：利贞。', 'line1': '初九：壮于趾，征凶，有孚。', 'line2': '九二：贞吉。', 'line3': '九三：小人用壮，君子用罔，贞厉。羝羊触藩，羸其角。', 'line4': '九四：贞吉悔亡，藩决不羸，壮于大舆之輹。', 'line5': '六五：丧羊于易，无悔。', 'line6': '上六：羝羊触藩，不能退，不能遂，无攸利，艰则吉。'},
        b'101000': {'order': 35, 'base': '晋：康侯用锡马蕃庶，昼日三接。', 'line1': '初六：晋如，摧如，贞吉。罔孚，裕无咎。', 'line2': '六二：晋如，愁如，贞吉。受兹介福，于其王母。', 'line3': '六三：众允，悔亡。', 'line4': '九四：晋如鼫鼠，贞厉。', 'line5': '六五：悔亡，失得勿恤，往吉，无不利。', 'line6': '上九：晋其角，维用伐邑，厉吉无咎，贞吝。'},
        b'000101': {'order': 36, 'base': '明夷：利艰贞。', 'line1': '初九：明夷于飞，垂其翼。君子于行，三日不食，有攸往，主人有言。', 'line2': '六二：明夷，夷于左股，用拯马壮，吉。', 'line3': '九三：明夷于南狩，得其大首，不可疾，贞。', 'line4': '六四：入于左腹，获明夷之心，于出门庭。', 'line5': '六五：箕子之明夷，利贞。', 'line6': '上六：不明，晦，初登于天，后入于地。'},
        b'110101': {'order': 37, 'base': '家人：利女贞。', 'line1': '初九：闲有家，悔亡。', 'line2': '六二：无攸遂，在中馈，贞吉。', 'line3': '九三：家人嗃嗃，悔厉吉，妇子嘻嘻，终吝。', 'line4': '六四：富家，大吉。', 'line5': '九五：王假有家，勿恤，吉。', 'line6': '上九：有孚威如，终吉。'},
        b'101011': {'order': 38, 'base': '睽：小事吉。', 'line1': '初九：悔亡，丧马勿逐，自复，见恶人，无咎。', 'line2': '六二：遇主于巷，无咎。', 'line3': '六三：见舆曳，其牛掣，其人天且劓，无初有终。', 'line4': '九四：睽孤，遇元夫，交孚，厉无咎。', 'line5': '六五：悔亡，厥宗噬肤，往何咎。', 'line6': '上九：睽孤，见豕负涂，载鬼一车，先张之弧，后说之弧，匪寇婚媾，往遇雨则吉。'},
        b'010100': {'order': 39, 'base': '蹇：利西南，不利东北。利见大人，贞吉。', 'line1': '初六：往蹇来誉。', 'line2': '六二：王臣蹇蹇，匪躬之故。', 'line3': '九三：往蹇来反。', 'line4': '六四：往蹇来连。', 'line5': '九五：大蹇，朋来。', 'line6': '上六：往蹇来硕，吉，利见大人。'},
        b'001010': {'order': 40, 'base': '解：利西南，无所往，其来复吉。有攸往，夙吉。', 'line1': '初六：无咎。', 'line2': '九二：田获三狐，得黄矢，贞吉。', 'line3': '六三：负且乘，致寇至，贞吝。', 'line4': '九四：解而拇，朋至斯孚。', 'line5': '六五：君子维有解，吉，有孚于小人。', 'line6': '上六：公用射隼于高墉之上，获之，无不利。'},
        b'100011': {'order': 41, 'base': '损：有孚，元吉，无咎，可贞。利有攸往，曷之用？二簋可用享。', 'line1': '初九：已事遄往，无咎。酌损之。', 'line2': '九二：利贞，征凶。弗损，益之。', 'line3': '六三：三人行，则损一人，一人行，则得其友。', 'line4': '六四：损其疾，使遄有喜，无咎。', 'line5': '六五：或益之十朋之龟，弗克违。元吉。', 'line6': '上九：弗损，益之，无咎，贞吉，利有攸往，得臣无家。'},
        b'110001': {'order': 42, 'base': '益：利有攸往，利涉大川。', 'line1': '初九：利用为大作，元吉，无咎。', 'line2': '六二：或益之十朋之龟，弗克违，永贞吉。王用享于帝，吉。', 'line3': '六三：益之用凶事，无咎。有孚中行，告公用圭。', 'line4': '六四：中行，告公从。利用为依迁国。', 'line5': '九五：有孚惠心，勿问，元吉。有孚惠我德。', 'line6': '上九：莫益之，或击之，立心勿恒，凶。'},
        b'011111': {'order': 43, 'base': '夬：扬于王庭，孚号有厉。告自邑，不利即戎，利有攸往。', 'line1': '初九：壮于前趾，往不胜，为吝。', 'line2': '九二：惕号，莫夜有戎，勿恤。', 'line3': '九三：壮于頄，有凶。君子夬夬独行，遇雨若濡，有愠，无咎。', 'line4': '九四：臀无肤，其行次且，牵羊悔亡，闻言不信。', 'line5': '九五：苋陆夬夬，中行无咎。', 'line6': '上六：无号，终有凶。'},
        b'111110': {'order': 44, 'base': '姤：女壮，勿用取女。', 'line1': '初六：系于金柅，贞吉，有攸往，见凶，羸豕为吝。', 'line2': '九二：包有鱼，无咎，不利宾。', 'line3': '九三：臀无肤，其行次且，厉，无大咎。', 'line4': '九四：包无鱼，起凶。', 'line5': '九五：以杞包瓜，含章，有陨自天。', 'line6': '上九：姤其角，吝，无咎。'},
        b'011000': {'order': 45, 'base': '萃：亨。王假有庙，利见大人，亨，利贞。用大牲吉，利有攸往。', 'line1': '初六：有孚不终，乃乱乃萃，若号，一握为笑，勿恤，往无咎。', 'line2': '六二：引吉，无咎，孚乃利用禴。', 'line3': '六三：萃如，嗟如，无攸利，往无咎，小吝。', 'line4': '九四：大吉，无咎。', 'line5': '九五：萃有位，无咎。匪孚，元永贞，悔亡。', 'line6': '上六：赍咨涕洟，无咎。'},
        b'000110': {'order': 46, 'base': '升：元亨，用见大人，勿恤，南征吉。', 'line1': '初六：允升，大吉。', 'line2': '九二：孚乃利用禴，无咎。', 'line3': '九三：升虚邑。', 'line4': '六四：王用亨于岐山，吉，无咎。', 'line5': '六五：贞吉，升阶。', 'line6': '上六：冥升，利于不息之贞。'},
        b'011010': {'order': 47, 'base': '困：亨，贞，大人吉，无咎，有言不信。', 'line1': '初六：臀困于株木，入于幽谷，三岁不觌。', 'line2': '九二：困于酒食，朱绂方来，利用享祀，征凶，无咎。', 'line3': '六三：困于石，据于蒺藜，入于其宫，不见其妻，凶。', 'line4': '九四：来徐徐，困于金车，吝，有终。', 'line5': '九五：劓刖，困于赤绂，乃徐有说，利用祭祀。', 'line6': '上六：困于葛藟，于臲卼，曰动悔。有悔，征吉。'},
        b'010110': {'order': 48, 'base': '井：改邑不改井，无丧无得，往来井井。汔至亦未繘井，羸其瓶，凶。', 'line1': '初六：井泥不食，旧井无禽。', 'line2': '九二：井谷射鲋，瓮敝漏。', 'line3': '九三：井渫不食，为我心恻，可用汲，王明，并受其福。', 'line4': '六四：井甃，无咎。', 'line5': '九五：井冽寒泉，食。', 'line6': '上六：井收勿幕，有孚元吉。'},
        b'011101': {'order': 49, 'base': '革：巳日乃孚，元亨利贞。悔亡。', 'line1': '初九：巩用黄牛之革。', 'line2': '六二：巳日乃革之，征吉，无咎。', 'line3': '九三：征凶贞厉。革言三就，有孚。', 'line4': '九四：悔亡，有孚，改命，吉。', 'line5': '九五：大人虎变，未占有孚。', 'line6': '上六：君子豹变，小人革面，征凶，居贞吉。'},
        b'101110': {'order': 50, 'base': '鼎：元吉，亨。', 'line1': '初六：鼎颠趾，利出否，得妾以其子，无咎。', 'line2': '九二：鼎有实，我仇有疾，不我能即，吉。', 'line3': '九三：鼎耳革，其行塞，雉膏不食，方雨，亏悔，终吉。', 'line4': '九四：鼎折足，覆公餗，其形渥，凶。', 'line5': '六五：鼎黄耳金铉，利贞。', 'line6': '上九：鼎玉铉，大吉，无不利。'},
        b'001001': {'order': 51, 'base': '震：亨。震来虩虩，笑言哑哑，震惊百里，不丧匕鬯。', 'line1': '初九：震来虩虩，后笑言哑哑，吉。', 'line2': '六二：震来厉，亿丧贝，跻于九陵，勿逐，七日得。', 'line3': '六三：震苏苏，震行无眚。', 'line4': '九四：震遂泥。', 'line5': '六五：震往来厉，亿无丧，有事。', 'line6': '上六：震索索，视矍矍，征凶，震不于其躬，于其邻，无咎，婚媾有言。'},
        b'100100': {'order': 52, 'base': '艮：艮其背，不获其身，行其庭，不见其人，无咎。', 'line1': '初六：艮其趾，无咎，利永贞。', 'line2': '六二：艮其腓，不拯其随，其心不快。', 'line3': '九三：艮其限，列其夤，厉熏心。', 'line4': '六四：艮其身，无咎。', 'line5': '六五：艮其辅，言有序，悔亡。', 'line6': '上九：敦艮，吉。'},
        b'110100': {'order': 53, 'base': '渐：女归吉，利贞。', 'line1': '初六：鸿渐于干，小子厉，有言，无咎。', 'line2': '六二：鸿渐于磐，饮食衎衎，吉。', 'line3': '九三：鸿渐于陆，夫征不复，妇孕不育，凶，利御寇。', 'line4': '六四：鸿渐于木，或得其桷，无咎。', 'line5': '九五：鸿渐于陵，妇三岁不孕，终莫之胜，吉。', 'line6': '上九：鸿渐于逵，其羽可用为仪，吉。'},
        b'001011': {'order': 54, 'base': '归妹：征凶，无攸利。', 'line1': '初九：归妹以娣，跛能履，征吉。', 'line2': '九二：眇能视，利幽人之贞。', 'line3': '六三：归妹以须，反归以娣。', 'line4': '九四：归妹愆期，迟归有时。', 'line5': '六五：帝乙归妹，其君之袂不如其娣之袂良，月几望，吉。', 'line6': '上六：女承筐无实，士刲羊无血，无攸利。'},
        b'001101': {'order': 55, 'base': '丰：亨，王假之，勿忧，宜日中。', 'line1': '初九：遇其配主，虽旬无咎，往有尚。', 'line2': '六二：丰其蔀，日中见斗，往得疑疾，有孚发若，吉。', 'line3': '九三：丰其沛，日中见沫，折其右肱，无咎。', 'line4': '九四：丰其蔀，日中见斗，遇其夷主，吉。', 'line5': '六五：来章，有庆誉，吉。', 'line6': '上六：丰其屋，蔀其家，窥其户，阒其无人，三岁不觌，凶。'},
        b'101100': {'order': 56, 'base': '旅：小亨，旅贞吉。', 'line1': '初六：旅琐琐，斯其所取灾。', 'line2': '六二：旅即次，怀其资，得童仆，贞。', 'line3': '九三：旅焚其次，丧其童仆，贞厉。', 'line4': '九四：旅于处，得其资斧，我心不快。', 'line5': '六五：射雉，一矢亡，终以誉命。', 'line6': '上九：鸟焚其巢，旅人先笑后号啕，丧牛于易，凶。'},
        b'110110': {'order': 57, 'base': '巽：小亨，利有攸往，利见大人。', 'line1': '初六：进退，利武人之贞。', 'line2': '九二：巽在床下，用史巫纷若，吉，无咎。', 'line3': '九三：频巽，吝。', 'line4': '六四：悔亡，田获三品。', 'line5': '九五：贞吉，悔亡，无不利，无初有终，先庚三日，后庚三日，吉。', 'line6': '上九：巽在床下，丧其资斧，贞凶。'},
        b'011011': {'order': 58, 'base': '兑：亨，利贞。', 'line1': '初九：和兑，吉。', 'line2': '九二：孚兑，吉，悔亡。', 'line3': '六三：来兑，凶。', 'line4': '九四：商未宁，介疾有喜。', 'line5': '九五：孚于剥，有厉。', 'line6': '上六：引兑。'},
        b'110010': {'order': 59, 'base': '涣：亨。王假有庙，利涉大川，利贞。', 'line1': '初六：用拯马壮，吉。', 'line2': '九二：涣奔其机，悔亡。', 'line3': '六三：涣其躬，无悔。', 'line4': '六四：涣其群，元吉。涣有丘，匪夷所思。', 'line5': '九五：涣汗，其大号涣，王居，无咎。', 'line6': '上九：涣其血，去逖出，无咎。'},
        b'010011': {'order': 60, 'base': '节：亨，苦节，不可贞。', 'line1': '初九：不出户庭，无咎。', 'line2': '九二：不出门庭，凶。', 'line3': '六三：不节若，则嗟若，无咎。', 'line4': '六四：安节，亨。', 'line5': '九五：甘节，吉，往有尚。', 'line6': '上六：苦节，贞凶，悔亡。'},
        b'110011': {'order': 61, 'base': '中孚：豚鱼，吉，利涉大川，利贞。', 'line1': '初九：虞吉，有它不燕。', 'line2': '九二：鸣鹤在阴，其子和之，我有好爵，吾与尔靡之。', 'line3': '六三：得敌，或鼓或罢，或泣或歌。', 'line4': '六四：月几望，马匹亡，无咎。', 'line5': '九五：有孚挛如，无咎。', 'line6': '上九：翰音登于天，贞凶。'},
        b'001100': {'order': 62, 'base': '小过：亨，利贞，可小事，不可大事。飞鸟遗之音，不宜上，宜下，大吉。', 'line1': '初六：飞鸟以凶。', 'line2': '六二：过其祖，遇其妣，不及其君，遇其臣，无咎。', 'line3': '九三：弗过防之，从或戕之，凶。', 'line4': '九四：无咎，弗过遇之，往厉必戒，勿用永贞。', 'line5': '六五：密云不雨，自我西郊，公弋取彼在穴。', 'line6': '上六：弗遇过之，飞鸟离之，凶，是谓灾眚。'},
        b'010101': {'order': 63, 'base': '既济：亨，小利贞，初吉终乱。', 'line1': '初九：曳其轮，濡其尾，无咎。', 'line2': '六二：妇丧其茀，勿逐，七日得。', 'line3': '九三：高宗伐鬼方，三年克之，小人勿用。', 'line4': '六四：繻有衣袽，终日戒。', 'line5': '九五：东邻杀牛，不如西邻之禴祭，实受其福。', 'line6': '上六：濡其首，厉。'},
        b'101010': {'order': 64, 'base': '未济：亨，小狐汔济，濡其尾，无攸利。', 'line1': '初六：濡其尾，吝。', 'line2': '九二：曳其轮，贞吉。', 'line3': '六三：未济，征凶，利涉大川。', 'line4': '九四：贞吉，悔亡，震用伐鬼方，三年有赏于大国。', 'line5': '六五：贞吉，无悔，君子之光，有孚，吉。', 'line6': '上九：有孚于饮酒，无咎，濡其首，有孚失是。'}
    }
    linearSymbols.reverse()
    symbolsStr = b"".join(linearSymbols)
    return trigramsMap[symbolsStr]
