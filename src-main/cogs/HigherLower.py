from random import randint
from typing import (
    Union,
    Optional,
)

import asyncpg
import discord
from discord.ext import commands

from Botty import Botty
from framework.BaseGame import BaseGame
from framework.GameChannelUpdate import GameChannelUpdateEvent
from framework.enums import Game


class HLGame(BaseGame):

    def __init__(self, game: Game, bot: Botty, guild: Union[int, discord.Guild], channel: Union[int, Union[discord.TextChannel, discord.ForumChannel]], current_player: int, players: Optional[list[int]], max_number: int, max_reply: int) -> None:
        super().__init__(game, bot, guild, channel, current_player, players)

        self.count = 0
        self.max_number = max_number
        self.max_reply = max_reply
        self.number = randint(0, self.max_number)

    def debug_string(self) -> str:
        return super().debug_string(count=self.count, max_number=self.max_number, max_reply=self.max_number, number=self.number)

    def reset(self):
        self.count = 0
        self.number = randint(0, self.max_number)


class HigherLower(commands.Cog):
    """
    Classic higher lower game, guess until you find the hidden number! 
    """

    MAX_NUMBERS: dict[int, tuple[int]] = {}
    GAMES: dict[int, HLGame] = {}

    def __init__(self, bot: Botty) -> None:
        super().__init__()
        self.bot = bot

    async def populate(self):
        async with self.bot.pool.acquire() as con:
            con: asyncpg.Connection
            rows = await con.fetch("SELECT guild_id, hl_max_number, hl_max_reply FROM game_settings WHERE hl_max_number IS NOT NULL;")
            for row in rows:
                self.MAX_NUMBERS[row["guild_id"]] = (row["hl_max_number"], row["hl_max_reply"])
            
            rows = await con.fetch("SELECT guild_id,higherlower FROM channel_ids;")
            for row in rows:
                if row["higherlower"] == '' or row["higherlower"] is None:
                    continue
                
                for channel in map(int, row["higherlower"].split(",")):
                    self.GAMES[channel] = HLGame(
                        Game.HIGHERLOWER, self.bot,
                        int(row["guild_id"]),
                        channel,
                        -1,
                        [],
                        self.MAX_NUMBERS[row["guild_id"]][0],
                        self.MAX_NUMBERS[row["guild_id"]][1]
                        )

    @commands.command(aliases=["hld"])
    @commands.is_owner()
    async def higherlowerdebug(self, ctx: commands.Context, channel_id: int = None):
        if not channel_id:
            return await ctx.send(str(self.GAMES))

        if game := self.GAMES.get(channel_id, None):
            await ctx.send(f'```{game.debug_string()}```')
        else:
            await ctx.send(f"No game found in `{channel_id}`")

    @property
    def display_emoji(self) -> discord.PartialEmoji:
        return discord.PartialEmoji(name='\U00002195')

    @commands.Cog.listener()
    async def on_game_channel_update(self, e: GameChannelUpdateEvent):
        ...
        # TODO: Implement listener for channel management

    @commands.Cog.listener()
    async def on_populate_cache(self):
        await self.populate()

    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message):
        if msg.author.bot:
            return

        if not msg.guild:
            return

        if msg.content.startswith(self.bot.cache.get_command_prefix(msg.guild.id)):
            return

        game: HLGame = self.GAMES.get(msg.channel.id, None)

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
