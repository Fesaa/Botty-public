import toml  #  type: ignore
import pathlib
import asyncpg
import discord

from discord.ext import commands
from typing import (
    Tuple
)

from BottyTypes import Config
from BottyCache import BottyCache
from utils.PostgreSQL import PostgreSQL
from utils.translator import BottyTranslator

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

        config: Config = toml.load("config.toml")
        self.config = config

        self.cache = BottyCache()

        owner_ids = self.config["BOTTY"]["OWNER_IDS"]

        allowed_mentions = discord.AllowedMentions(roles=True, users=True, everyone=False)
        intents = discord.Intents().none()
        intents.members = True
        intents.guilds = True
        intents.messages = True
        intents.message_content = True

        case_insensitive = True

        super().__init__(
            command_prefix=self.get_prefix,
            allowed_mentions=allowed_mentions,
            intents=intents,
            case_insensitive=case_insensitive,
            application_id=self.config["DISCORD"]["APPLICATION_ID"],
            owner_ids=owner_ids,
        )

    @property
    def default_values(self) -> Defaults:
        if not hasattr(self, "defaults"):
            self._defaults = Defaults(self.config)
        return self._defaults

    @property
    def Botty_colour(self) -> int:
        return self.config["BOTTY"].get("COLOUR", 0xAD3998)  # type: ignore
    
    @property
    def owner(self) -> discord.User:
        return self.bot_app_info.owner
    
    def run(self, *args, **kwargs) -> None:
        return super().run(self.config["DISCORD"]["TOKEN"], *args, **kwargs)

    async def setup_hook(self) -> None:

        self.pool: asyncpg.Pool = await asyncpg.create_pool(**self.config["SERVER"]["POSTGRESQL"])
        self.PostgreSQL: PostgreSQL = PostgreSQL(self.pool)

        self.bot_app_info: discord.AppInfo = await self.application_info()

        t = BottyTranslator()
        await self.tree.set_translator(t)
        t.close()

        async with self.pool.acquire() as con:
            await self.build_cache(con)

        for file in sorted(pathlib.Path("cogs").glob("**/[!_]*.py")):
            ext = ".".join(file.parts).removesuffix(".py")
            try:
                await self.load_extension(ext)
            except Exception as error:
                print("Failed to load extension: %s\n\n%s", ext, error)

    async def on_ready(self) -> None:
        if not hasattr(self, "uptime"):
            self.uptime = discord.utils.utcnow()
            print(f"Ready: {self.user} (ID: {self.user.id})")

    async def get_prefix(self, msg: discord.Message):
        if not msg.guild:
            return commands.when_mentioned_or(self.config["DISCORD"]["DEFAULT_PREFIX"])(self, msg)
        else:
            return commands.when_mentioned_or(
                self.cache.get_command_prefix(msg.guild.id)
            )(self, msg)
    
    async def build_cache(self, con: asyncpg.connection.Connection) -> None:
        # Prefixes
        all_prefixes = await con.fetch("SELECT * FROM command_prefix;")
        for row in all_prefixes:
            self.cache.update_command_prefix(row["guild_id"], row["command_prefix"])

        # Channel Ids
        all_channel_ids = await con.fetch("SELECT * FROM channel_ids;")
        for row in all_channel_ids:
            self.cache.update_channel_id(
                row["guild_id"],
                "wordsnake",
                row["wordsnake"].split(",") if row["wordsnake"] else [],
            )
            self.cache.update_channel_id(
                row["guild_id"],
                "ntbpl",
                row["ntbpl"].split(",") if row["ntbpl"] else [],
            )
            self.cache.update_channel_id(
                row["guild_id"],
                "higherlower",
                row["higherlower"].split(",") if row["higherlower"] else [],
            )
            self.cache.update_channel_id(
                row["guild_id"],
                "connectfour",
                row["connectfour"].split(",") if row["connectfour"] else [],
            )
            self.cache.update_channel_id(
                row["guild_id"],
                "hangman",
                row["hangman"].split(",") if row["hangman"] else [],
            )
            self.cache.update_channel_id(
                row["guild_id"],
                "cubelvl",
                row["cubelvl"].split(",") if row["cubelvl"] else [],
            )
            self.cache.update_channel_id(
                row["guild_id"], "log", row["log"].split(",") if row["log"] else []
            )

        # Game Settings
        all_game_settings = await con.fetch("SELECT * FROM game_settings;")
        for row in all_game_settings:
            self.cache.update_game_settings(
                row["guild_id"], "max_lb_size", row["max_lb_size"]
            )
            self.cache.update_game_settings(
                row["guild_id"], "hl_max_reply", row["hl_max_reply"]
            )
            self.cache.update_game_settings(
                row["guild_id"], "ws_wrong_guesses", row["ws_wrong_guesses"]
            )
            self.cache.update_game_settings(
                row["guild_id"], "hl_max_number", row["hl_max_number"]
            )

        # Tags
        all_tags = await con.fetch("SELECT * FROM tag;")
        for row in all_tags:
            self.cache.add_tag(row["guild_id"], row["tag"], row["owner_id"])