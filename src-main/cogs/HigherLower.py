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
    Game
)


class HigherLowerGame(BaseGame):

    def __init__(self, game: Game, bot: Botty, channel_id, guild_id, current_player: int, players: Optional[list[int]], max_number: int,
                 max_reply: int) -> None:
        super().__init__(game, bot, channel_id, guild_id, current_player, players)

        self.count = 0
        self.max_number = max_number
        self.max_reply = max_reply
        self.number = randint(0, self.max_number)

    def debug_string(self) -> str:
        return super().debug_string(count=self.count, max_number=self.max_number, max_reply=self.max_number,
                                    number=self.number)

    def reset(self):
        self.count = 0
        self.number = randint(0, self.max_number)


class HigherLower(GameCog):
    """
    Classic higher lower game, guess until you find the hidden number! 
    """

    CONFIG: dict[int, tuple[int, int]] = {}

    def __init__(self, bot: Botty) -> None:
        super().__init__(bot, Game.HIGHERLOWER)

        self.games: dict[int, HigherLowerGame] = {}

    async def cog_load(self) -> None:
        await super().cog_load()
        async with self.bot.pool.acquire() as con:
            con: asyncpg.Connection
            rows = await con.fetch(
                "SELECT guild_id, hl_max_number, hl_max_reply FROM game_settings WHERE hl_max_number IS NOT NULL;")
            for row in rows:
                self.CONFIG[row["guild_id"]] = (int(row["hl_max_number"]), int(row["hl_max_reply"]))

    @property
    def display_emoji(self) -> discord.PartialEmoji:
        return discord.PartialEmoji(name='\U00002195')

    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message):
        if msg.author.bot:
            return

        if not msg.guild:
            return

        if msg.content.startswith(self.bot.cache.get_command_prefix(msg.guild.id)):
            return

        if msg.channel.id not in self.channels:
            return

        game: HigherLowerGame = self.games.get(msg.channel.id, None)

        if not game:
            config = self.CONFIG[msg.guild.id]
            game = HigherLowerGame(Game.HIGHERLOWER, self.bot, msg.channel.id, msg.guild.id, self.bot.user.id, [], config[0], config[1])
            self.games[msg.channel.id] = game

        if game.count == game.max_reply and game.current_player == msg.author.id:
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


async def setup(bot: Botty):
    await bot.add_cog(HigherLower(bot))
