from itertools import chain
from pkgutil import iter_modules

import aiohttp
import asyncpg
import discord
import enchant
import toml  # type: ignore
import logging
from discord.ext import commands

from BottyTypes import Config

_log = logging.getLogger("botty")

class Defaults:

    def __init__(self, c: Config) -> None:
        self.default_lb_size = c["DISCORD"]["DEFAULTS"]["DEFAULT_LB_SIZE"]
        self.default_channel = c["DISCORD"]["DEFAULTS"]["DEFAULT_CHANNEL"]
        self.default_max_reply = c["DISCORD"]["DEFAULTS"]["DEFAULT_MAX_REPLY"]
        self.default_ws_guesses = c["DISCORD"]["DEFAULTS"]["DEFAULT_WS_GUESSES"]
        self.default_hl_max_number = c["DISCORD"]["DEFAULTS"]["DEFAULT_HL_MAX_NUMBER"]


class Botty(commands.Bot):

    bot_app_info: discord.AppInfo

    def __init__(self) -> None:

        self.pool: asyncpg.Pool = ... # type: ignore

        self.httpClientSession: aiohttp.ClientSession = ... # type: ignore

        config: Config = toml.load("config.toml") # type: ignore
        self.config: Config = config

        with open("utils/words.txt", 'rt', encoding='utf-8') as file:
            self.words = [line.strip().split() for line in file.readlines()]

        self.enchant_dictionary = enchant.Dict("en_GB")

        self.default_values = Defaults(self.config)

        owner_ids = self.config["BOTTY"]["OWNER_IDS"]

        allowed_mentions = discord.AllowedMentions(roles=True, users=True, everyone=False)
        intents = discord.Intents().none()
        intents.members = True
        intents.guilds = True
        intents.messages = True
        intents.message_content = True

        case_insensitive = True

        super().__init__(
            command_prefix=self.get_prefix, # type: ignore
            allowed_mentions=allowed_mentions,
            intents=intents,
            case_insensitive=case_insensitive,
            application_id=self.config["DISCORD"]["APPLICATION_ID"],
            owner_ids=owner_ids,
        )

    @property
    def Botty_colour(self) -> int:
        return self.config["BOTTY"].get("COLOUR", 0xAD3998)  # type: ignore

    @property
    def owner(self) -> discord.User:
        return self.bot_app_info.owner

    def run(self, *args, **kwargs) -> None:
        return super().run(self.config["DISCORD"]["TOKEN"], *args, **kwargs)

    async def setup_hook(self) -> None:
        self.httpClientSession = aiohttp.ClientSession()
        self.bot_app_info: discord.AppInfo = await self.application_info()

        pool: asyncpg.Pool | None = await asyncpg.create_pool(**self.config["SERVER"]["POSTGRESQL"])
        if pool is None:
            raise Exception("Could not make pool")

        self.pool: asyncpg.Pool = pool

        self.prefixes: dict[int, list[str]] = {}
        async with self.pool.acquire() as con:
            con: asyncpg.Connection
            prefixes_data = await con.fetch("SELECT guild_id,prefix FROM prefixes")
            for prefix_info in prefixes_data:
                if self.prefixes.get(prefix_info["guild_id"], None):
                    self.prefixes[prefix_info["guild_id"]].append(prefix_info["prefix"])
                else:
                    self.prefixes[prefix_info["guild_id"]] = [prefix_info["prefix"]]

        for ext in chain(iter_modules(["cogs"], prefix='cogs.'), iter_modules(["cogs/games"], prefix='cogs.games.')):
            try:
                await self.load_extension(ext.name)
                _log.info("Loaded extension: %s", ext.name)
            except Exception as error:
                _log.error("Failed to load extension: %s\n\n%s", ext.name, error)

    async def on_ready(self) -> None:
        if not hasattr(self, "uptime"):
            self.uptime = discord.utils.utcnow()
            if self.user is not None:
                _log.info(f"Ready: {self.user} (ID: {self.user.id})")

    async def get_prefix(self, msg: discord.Message):
        prefixes: list[str]

        if not msg.guild:
            prefixes = commands.when_mentioned_or(self.config["DISCORD"]["DEFAULT_PREFIX"])(self, msg)
        else:
            prefixes = commands.when_mentioned_or(*self.prefixes.get(msg.guild.id, [self.config["DISCORD"]["DEFAULT_PREFIX"]]))(self, msg)

        if self.owner_ids is not None and msg.author.id in self.owner_ids:
            prefixes.append("?")

        return prefixes

    async def exec_sql(self, query: str, *val):
        async with self.pool.acquire() as con:
            con: asyncpg.Connection
            await con.execute(query, *val)
