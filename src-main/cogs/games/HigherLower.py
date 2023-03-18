from random import randint
from typing import (
    Optional,
)

import asyncpg
import discord
from discord.ext import commands

from Botty import Botty
from framework import (
    BaseGame,
    GameCog,
    Game,
    GameConfigUpdateEvent,
    GameSetting
)


class HigherLowerGame(BaseGame):

    def __init__(self, game: Game, bot: Botty, channel_id, guild_id, current_player: int, players: Optional[list[int]], max_number: int) -> None:
        super().__init__(game, bot, channel_id, guild_id, current_player, players)

        self.count = 0
        self.number = randint(0, max_number)
        self.game_start()

    def debug_string(self) -> str:
        return super().debug_string(count=self.count, number=self.number)

    def reset(self):
        self.count = 0

class HlSetting:

    @classmethod
    def default(cls, bot: 'Botty'):
        return HlSetting(
                        bot.default_values.default_hl_max_number,
                        bot.default_values.default_max_reply
                    )

    def __init__(self, max_number: int, max_reply: int):
        self.max_number = max_number
        self.max_reply = max_reply

    def update_setting(self, setting: GameSetting, value: int ):
        if setting == GameSetting.HL_MAX_NUMBER:
            self.max_number = value
        elif setting == GameSetting.HL_MAX_REPLY:
            self.max_reply = value

class HigherLower(GameCog):
    """
    Classic higher lower game, guess until you find the hidden number! 
    """

    CONFIG: dict[int, HlSetting] = {}

    def __init__(self, bot: Botty) -> None:
        super().__init__(bot, Game.HIGHERLOWER)

        self.games: dict[int, HigherLowerGame] = {}

    async def cog_load(self) -> None:
        await super().cog_load()
        async with self.bot.pool.acquire() as con:
            con: asyncpg.Connection
            rows = await con.fetch("SELECT guild_id, hl_max_number, hl_max_reply FROM guild_settings;")
            for row in rows:
                self.CONFIG[row["guild_id"]] = HlSetting(int(row["hl_max_number"]), int(row["hl_max_reply"]))
                # TODO channel settings override

    @property
    def display_emoji(self) -> discord.PartialEmoji:
        return discord.PartialEmoji(name='\U00002195')
    
    def update_config(self, key: int, setting: GameSetting, value: int):
        if config := self.CONFIG.get(key, None):
            config.update_setting(setting, value)
        else:
            config = HlSetting.default(self.bot)
            config.update_setting(setting, value)
            self.CONFIG[key] = config

    @commands.Cog.listener()
    async def on_config_update(self, e: GameConfigUpdateEvent):
        if e.channels:
            for channel in e.channels:
                self.update_config(channel, e.setting, e.new_value)
            await self.exec_sql(f"""
            INSERT INTO 
                channel_settings
                (channel_id, setting_type, setting_value)
            VALUES 
                {",".join(f'({channel}, $1, $2)' for channel in e.channels)}
            ON CONFLICT
                (channel_id, setting_type)
            DO 
                SET setting_value = $2;
            """, e.setting.value, e.new_value)
            return await e.ctx.send(f'Changed {e.setting.pretty()} for {len(e.channels)} to {e.new_value}.', ephemeral=True)
        else:
            self.update_config(e.ctx.guild.id, e.setting, e.new_value)
            await self.exec_sql(f"""
            UPDATE 
                guild_settings
            SET
                {e.setting.value} = $1
            WHERE
                guild_id = $2;    
            """, e.new_value, e.ctx.guild.id)
            return await e.ctx.send(f'Changed {e.setting.pretty()} to {e.new_value}.', ephemeral=True)

    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message):
        if msg.author.bot:
            return

        if not msg.guild:
            return

        if msg.content.startswith(tuple(self.bot.prefixes.get(msg.guild.id, ()))):
            return

        if msg.channel.id not in self.channels:
            return

        game: HigherLowerGame = self.games.get(msg.channel.id, None)
        max_reply: int = (self.CONFIG.get(msg.channel.id, None) or self.CONFIG.get(msg.guild.id)).max_reply
        max_number: int = (self.CONFIG.get(msg.channel.id, None) or self.CONFIG.get(msg.guild.id)).max_number

        if not game:
            game = HigherLowerGame(Game.HIGHERLOWER, self.bot, msg.channel.id, msg.guild.id, self.bot.user.id, [], max_number)
            self.games[msg.channel.id] = game

        if game.count == max_reply and game.current_player == msg.author.id:
            return await msg.delete()

        try:
            sub_count = int(msg.content.split(" ")[0])
        except ValueError:
            return await msg.delete()

        if game.current_player != msg.author.id:
            game.count = 0
            game.current_player = msg.author.id

        if sub_count < game.number:
            game.count = game.count + 1
            await msg.add_reaction("⬆️")
        elif sub_count > game.number:
            game.count = game.count + 1
            await msg.add_reaction("⬇️")
        else:
            await msg.add_reaction("⭐")
            await msg.channel.send(f"{msg.author.mention} Correct my love! I have granted you a star ⭐")
            await game.grand_current_player(1)
            game.reset()
            game.number = randint(0, max_number)


async def setup(bot: Botty):
    await bot.add_cog(HigherLower(bot))
