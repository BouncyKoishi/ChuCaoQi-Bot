from os import path
import nonebot
from nonebot.log import logger
import config


if __name__ == '__main__':
    nonebot.init(config)
    nonebot.load_plugins(path.join(path.dirname(__file__), 'plugins'), 'plugins')
    logger.info('starting')
    nonebot.run()