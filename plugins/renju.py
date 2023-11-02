import re
from kusa_base import config
from nonebot import on_command, CommandSession
from nonebot import on_natural_language, NLPSession

game_state = 0
attendance = []
chessboard = []
in_turn = 0

allow_group = config['group']['allow']


@on_command(name='renju', only_to_me=False)
async def renju_start(session: CommandSession):
    global game_state
    if 'group_id' not in session.ctx:
        return
    groupnum = session.ctx['group_id']
    if groupnum in allow_group:
        if game_state == 0:
            game_state = 1
            await session.send('开了，请参加者举手')


@on_natural_language(keywords=None, only_to_me=False)
async def renju_main(session: NLPSession):
    global game_state
    global attendance
    global chessboard

    if 'group_id' not in session.ctx:
        return
    groupnum = session.ctx['group_id']
    if groupnum in allow_group:
        if game_state == 1:
            await renju_join(session, attendance, chessboard)
        if game_state == 2:
            if session.ctx['sender']['nickname'] in attendance:
                await renju_play(session, attendance, chessboard)


async def renju_join(session, attendence, chessboard):
    global game_state
    if session.msg == '举手':
        member = session.ctx['sender']['nickname']
        if member in attendence:
            msg = '你已经举手！'
        else:
            attendence.append(member)
            msg = member + '加入成功。目前准备人数:' + str(len(attendence))
        await session.send(msg)
    if len(attendence) >= 2:
        game_state = 2
        msg = '人数已满，可以开始游戏。黑方为' + attendence[0] + '，请落子。\n落子格式为"下（横坐标字母）（纵坐标数字）"，例如“下H7”。'
        await session.send(msg)

        await make_board(chessboard)
        await draw_board(session, chessboard)


async def renju_play(session, attendence, chessboard):
    global game_state
    global in_turn

    member = session.ctx['sender']['nickname']
    content = session.msg
    if re.match('下([A-N]|[a-n])\d{1,2}', content):
        if member == attendence[in_turn]:
            across = get_across_number(content[1])
            endlong = int(content[2:])
            if 1 <= across <= 14 and 1 <= endlong <= 14:
                if chessboard[endlong][across] == '＋':  # ╋
                    if in_turn == 0:
                        chessboard[endlong][across] = '黑'  # ●
                        await draw_board(session, chessboard)
                        await win_judge(session, chessboard, endlong, across, in_turn)
                        in_turn = 1
                    elif in_turn == 1:
                        chessboard[endlong][across] = '白'  # ○
                        await draw_board(session, chessboard)
                        await win_judge(session, chessboard, endlong, across, in_turn)
                        in_turn = 0
                    # 正常落子
                else:
                    await session.send('该位置已有其他棋子，请重下')
            else:
                await session.send('下出棋盘外了，请重下')
        else:
            await session.send('还没到你呢，别急')
    elif content == '投降' or content == '认输':
        if member == attendence[0]:
            msg = attendence[0] + '（黑方）认输，' + attendence[1] + '（白方）胜利'
        elif member == attendence[1]:
            msg = attendence[1] + '（白方）认输，' + attendence[0] + '（黑方）胜利'
        end_game()
        await session.send(msg)


async def make_board(chessboard):
    for i in range(0, 15):
        if i == 0:
            crossdata = ['  ', 'Ａ', 'Ｂ', 'Ｃ', 'Ｄ', 'Ｅ', 'Ｆ', 'Ｇ', 'Ｈ', 'Ｉ', 'Ｊ', 'Ｋ', 'Ｌ', 'Ｍ', 'Ｎ']
        else:
            crossdata = []
            for j in range(0, 15):
                if j == 0:
                    if i < 10:
                        crossdata.append(str(i))
                    else:
                        crossdata.append(str(i - 10))
                else:
                    crossdata.append('＋')
        crossdata.append('\n')
        chessboard.append(crossdata)


async def draw_board(session, chessboard):
    output_board = chessboard
    output_str = ''

    for crossdata in output_board:
        output_str += ''.join(crossdata)

    await session.send(output_str)


def get_across_number(letter_input):
    if re.match('[A-I]', letter_input):
        across = int(chr(ord(letter_input) - 16))
    elif re.match('[J-N]', letter_input):
        across = int(chr(ord(letter_input) - 25)) + 9
    if re.match('[a-i]', letter_input):
        across = int(chr(ord(letter_input) - 48))
    elif re.match('[j-n]', letter_input):
        across = int(chr(ord(letter_input) - 57)) + 9
    return across


async def win_judge(session, chessboard, endlong, across, in_turn):
    # 不优美 很暴力 待重构
    global game_state
    in_turn_chess = ['黑', '白', '黑']
    connect = 0

    for i in range(1, 15):
        for j in range(1, 15):
            if chessboard[i][j] == in_turn_chess[in_turn]:
                connect += 1
            else:
                connect = 0
            if connect >= 5:
                msg = in_turn_chess[in_turn] + '方获胜！'
                await session.send(msg)
                end_game()
                return

    connect = 0
    for j in range(1, 15):
        for i in range(1, 15):
            if chessboard[i][j] == in_turn_chess[in_turn]:
                connect += 1
            else:
                connect = 0
            if connect >= 5:
                msg = in_turn_chess[in_turn] + '方获胜！'
                await session.send(msg)
                end_game()
                return
    # 横竖

    connect = 0
    endl_limit = endlong
    acro_limit = across
    while endl_limit > 1 and acro_limit > 1:
        endl_limit -= 1
        acro_limit -= 1

    while endl_limit <= 14 and acro_limit <= 14:
        if chessboard[endl_limit][acro_limit] == in_turn_chess[in_turn]:
            connect += 1
        else:
            connect = 0
        if connect >= 5:
            msg = in_turn_chess[in_turn] + '方获胜！'
            await session.send(msg)
            end_game()
            return
        endl_limit += 1
        acro_limit += 1
    # 斜下

    connect = 0
    endl_limit = endlong
    acro_limit = across
    while endl_limit > 1 and acro_limit < 14:
        endl_limit -= 1
        acro_limit += 1

    while endl_limit <= 14 and acro_limit >= 1:
        if chessboard[endl_limit][acro_limit] == in_turn_chess[in_turn]:
            connect += 1
        else:
            connect = 0
        if connect >= 5:
            msg = in_turn_chess[in_turn] + '方获胜！'
            await session.send(msg)
            end_game()
            return
        endl_limit += 1
        acro_limit -= 1
    # 斜上


def end_game():
    global game_state
    global attendance
    global chessboard
    global in_turn

    game_state = 0
    attendance = []
    chessboard = []
    in_turn = 0
