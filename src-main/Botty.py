import os
import sys
import discord
import traceback

from discord.ext import commands

from cogs.ConfigHandler import get_prefix, bot_id

class Botty(commands.Bot):

    bot_app_info: discord.AppInfo

    def __init__(self) -> None:

        owner_ids = [474319793042751491, 322007790208155650]

        allowed_mentions = discord.AllowedMentions(roles=True, users=True, everyone=False)
        intents= discord.Intents().all()

        case_insensitive=True

        super().__init__(command_prefix=get_prefix, allowed_mentions=allowed_mentions,
                         intents=intents, case_insensitive=case_insensitive, 
                         application_id=bot_id, owner_ids=owner_ids)

    async def setup_hook(self) -> None:

        self.bot_app_info = await self.application_info()

        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                try:
                    await self.load_extension(f'cogs.{filename[:-3]}')
                except Exception as e:
                    print(f'Failed to load extension {filename}.', file=sys.stderr)
                    traceback.print_exc()

    async def on_ready(self) -> None:
        print(f'Ready: {self.user} (ID: {self.user.id})')
    
        if not hasattr(self, 'uptime'):
            self.uptime = discord.utils.utcnow()
    
    @property
    def owner(self) -> discord.User:
        return self.bot_app_info.owner