import nonebot
import requests
import typing
from datetime import datetime
from kusa_base import config
from nonebot import on_command, CommandSession


class SysuNetworkReport(typing.NamedTuple):
    title: str
    time: datetime
    content: str

    def __str__(self) -> str:
        return '\n'.join((
            self.title,
            self.time.strftime('%Y-%m-%d %H:%M'),
            '=' * 24,
            self.content,
        ))


latestReport: SysuNetworkReport = None


@nonebot.scheduler.scheduled_job('cron', minute='0', hour='8-23')
async def _():
    global latestReport

    r = requests.get('https://i.akarin.dev/sysu-network-report.json')
    r.raise_for_status()
    d: tuple[SysuNetworkReport, ...] = tuple(
        SysuNetworkReport(
            title=x['title'],
            time=datetime.fromisoformat(x['time']),
            content=x['content'],
        )
        for x in r.json()
    )

    bot = nonebot.get_bot()
    if latestReport is not None:
        for x in filter(lambda x: x.time > latestReport.time, d):
            await bot.send_group_msg(group_id=config['group']['sysu'], message=str(x))
    latestReport = max(d, key=lambda x: x.time)


@on_command(name='校园网', only_to_me=False)
async def _(session: CommandSession):
    if latestReport is None:
        return
    await session.send(str(latestReport))


@nonebot.scheduler.scheduled_job('cron', minute='0', hour='23', day='7-15/4', month='1,7')
async def _():
    bot = nonebot.get_bot()
    await bot.send_group_msg(group_id=config['group']['sysu'],
                             message='给网费按个暂停键！\n寒暑假将至，可以前往 https://netpay.sysu.edu.cn/ 自助办理个人网络服务的暂停和恢复。')
