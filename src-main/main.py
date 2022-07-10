import os
import sys
import traceback
import discord
import logging
import logging.handlers

from discord.ext import commands

os.chdir(os.path.dirname(os.path.abspath(__file__)))

from cogs.ConfigHandler import host, Database, user, password, token, get_prefix, bot_id
from imports.db import DataBase

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

class Botty(commands.Bot):

    def __init__(self) -> None:

        allowed_mentions = discord.AllowedMentions(roles=True, users=True, everyone=False)
        intents= discord.Intents(
            guilds=True,
            members=True,
            bans=True,
            emojis=True,
            voice_states=False,
            messages=True,
            reactions=True,
            message_content=True,
        )
        case_insensitive=True

        super().__init__(command_prefix=get_prefix, allowed_mentions=allowed_mentions, intents=intents, case_insensitive=case_insensitive,  application_id=bot_id)

    async def setup_hook(self) -> None:
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                try:
                    await self.load_extension(f'cogs.{filename[:-3]}')
                except Exception as e:
                    print(f'Failed to load extension {filename}.', file=sys.stderr)
                    traceback.print_exc()

    async def on_ready(self) -> None:
        print(f'Ready: {self.user} (ID: {self.user.id})')

def main():
    bot = Botty()
    bot.db: DataBase = DataBase(host=host, database=Database, password=password, user=user)
    try:
        bot.run(token, log_handler=None)
    except discord.LoginFailure:
        print('Invalid token', file=sys.stderr)

if __name__ == '__main__':
    main()