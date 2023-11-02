import json
from urllib import request
from urllib import parse
from nonebot import on_command, CommandSession
from kusa_base import config


@on_command(name='music', only_to_me=False)
async def _(session: CommandSession):
    stripped_arg = session.current_arg_text.strip()
    if stripped_arg == '':
        await session.send('未输入搜索内容。')
    else:
        musicInfo = getMusicInfoFromNetease(stripped_arg, 0)
        await musicSendFromNetease(musicInfo, session)


def getMusicInfoFromNetease(name, offset):
    name_quote = parse.quote_plus(name)
    api_url = f'http://music.163.com/api/search/pc?s={name_quote}&offset={offset}&limit=1&type=1'

    if api_url:
        http_req = request.Request(api_url)
        http_req.add_header('User-Agent', config['web']['userAgent'])
        http_req.add_header('Cookie', config['web']['neteaseMusic']['cookie'])

        with request.urlopen(http_req) as req:
            data = req.read().decode('utf-8')
            return json.loads(data)
    return 'Failed'


async def musicSendFromNetease(infor, session: CommandSession):
    if infor == 'Failed':
        await session.send('网络连接异常。')
    else:
        if infor['code'] != 200:
            await session.send('网易云查询服务异常。')
            print(infor)
        elif 'songs' not in infor['result']:
            await session.send('查无结果。')
        else:
            song = infor['result']['songs'][0]
            song_id = song['id']
            artist_name = song['artists'][0]['name']
            album_name = song['album']['name']

            url = f'https://music.163.com/#/song?id={song_id}'
            name = song['name']
            detail_infor = f'艺术家：{artist_name}\n专辑：{album_name}'
            message = f'{url}\n曲名：{name}\n{detail_infor}'
            await session.send(message)
