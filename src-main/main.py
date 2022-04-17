from typing import Union
from discord.ext import commands
from os import listdir, chdir, path
from asyncio import run as asynciorun
from discord.errors import LoginFailure
from discord.app_commands import errors as app_errors
from discord import Intents, Object, app_commands, Interaction

chdir(path.dirname(path.abspath(__file__)))

from cogs.config_handler import host, Database, user, password, token, get_prefix, bot_id
from imports.database import DataBase
from imports.functions import time

bot = commands.Bot(command_prefix=get_prefix, intents=Intents().all(), case_insensitive=True, help_command=None, application_id=bot_id)
bot.db = DataBase(host=host, database=Database, password=password, user=user)
tree = bot.tree


@bot.event
async def on_ready():
    print(time() + f" Code running on account with name: {bot.user.name} and id {bot.user.id}")

async def load_extensions():
    for filename in listdir("./cogs"):
        if filename.endswith(".py"):
            await bot.load_extension(f"cogs.{filename[:-3]}")


async def main():
    async with bot:
        await load_extensions()
        try:
            await bot.start(token)
        except LoginFailure:
            print("Can't log in, please check your token in config.json!")
        

@bot.command()
async def sync_slash(ctx: commands.Context):
    await bot.tree.sync()
    await ctx.send("Tree synced!")

@tree.error
async def app_command_error(interaction: Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_errors.MissingPermissions):
        await interaction.response.send_message('You are missing the nessairy perms to use this command.', ephemeral=True)
    else:
        raise error

@commands.Cog.listener()
async def on_command_error(self, ctx, exc):
    if isinstance(exc, commands.errors.CommandNotFound):
        pass
    else:
        raise exc


asynciorun(main())