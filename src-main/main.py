import os
import sys
import discord
import logging
import logging.handlers

os.chdir(os.path.dirname(os.path.abspath(__file__)))

from cogs.ConfigHandler import host, Database, user, password, token
from imports.db import DataBase
from Botty import Botty

logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
logging.getLogger('discord.http').setLevel(logging.INFO)

handler = logging.handlers.RotatingFileHandler(
    filename='discord.log',
    encoding='utf-8',
    maxBytes=32 * 1024 * 1024,  # 32 MiB
    backupCount=5,  # Rotate through 5 files
)
dt_fmt = '%Y-%m-%d %H:%M:%S'
formatter = logging.Formatter('[{asctime}] [{levelname:<8}] {name}: {message}', dt_fmt, style='{')
handler.setFormatter(formatter)
logger.addHandler(handler)

def main():
    bot = Botty()
    bot.db: DataBase = DataBase(host=host, database=Database, password=password, user=user)
    try:
        bot.run(token, log_handler=None)
    except discord.LoginFailure:
        print('Invalid token', file=sys.stderr)

if __name__ == '__main__':
    main()