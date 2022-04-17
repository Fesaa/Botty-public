import asyncio

from functions.database import Database
from discord import Intents, Object
from discord.ext import commands
from discord.errors import LoginFailure
from os import listdir, path, chdir

chdir(path.dirname(path.abspath(__file__)))

from functions.config_handler import host, user, password, database, TOKEN, time, GUILD_IDS, BOT_ID

bot = commands.Bot(command_prefix="!", intents=Intents().all(), case_insensitive=True,
                   help_command=None, application_id=BOT_ID)
bot.db = Database(host=host, database=database, password=password, user=user)


@bot.event
async def on_ready():
    print(time() + f" Code running on account with name: {bot.user.name} and id {bot.user.id}")
    print(bot.tree.get_commands(guild=Object(GUILD_IDS[0])))


async def load_extensions():
    for filename in listdir("./cogs"):
        if filename.endswith(".py"):
            await bot.load_extension(f"cogs.{filename[:-3]}")


async def main():
    async with bot:
        await load_extensions()
        await bot.start(TOKEN)


@bot.command()
async def sync_slash(ctx: commands.Context):
    await bot.tree.sync(guild=Object(GUILD_IDS[0]))
    await ctx.send("Tree synced!")


asyncio.run(main())
