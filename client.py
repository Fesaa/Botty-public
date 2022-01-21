from discord import Intents
from discord.errors import LoginFailure
from discord.ext import commands
from discord_slash import SlashCommand
from os import listdir, chdir, path

chdir(path.dirname(path.abspath(__file__)))

from cogs.config_handler import token, get_prefix
from imports.database import database
from imports.functions import time

client = commands.Bot(command_prefix=get_prefix, intents=Intents().all(), case_insensitive=True)
slash = SlashCommand(client, sync_commands=True)
client.db = database()


@client.event
async def on_ready():
    print(time() + f" Code running on account with name: {client.user.name} and id {client.user.id}")

for filename in listdir("./cogs"):
    if filename.endswith(".py"):
        client.load_extension(f"cogs.{filename[:-3]}")

try:
    client.run(token)
except LoginFailure:
    print('Invalid token')
