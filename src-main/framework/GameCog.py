import asyncpg
import discord
from typing import TYPE_CHECKING

from discord.ext import commands

if TYPE_CHECKING:
    from framework.BaseGame import BaseGame
    from framework.GameEvents import GameChannelUpdateEvent, GameDebugEvent, GameUpdateEvent
    from framework.enums import Game


from Botty import Botty


from framework.enums import Update, DebugRequest


class GameCog(commands.Cog):

    def __init__(self, bot: Botty, game: 'Game', limit_to_channel: bool = True):
        self.bot = bot
        super().__init__()

        self.game = game
        self.channels: list[int] = []
        self.games: dict[int, 'BaseGame'] = {}
        self.limit_to_channel = limit_to_channel

    @commands.Cog.listener()
    async def on_game_update(self, e: 'GameUpdateEvent'):
        if e.game != self.game:
            return

        if e.update_type == Update.ADD:
            self.games[e.game_data.snowflake] = e.game_data
            return

        if e.update_type == Update.REMOVE:
            try:
                self.games.pop(e.game_data.snowflake)
            except KeyError:
                pass

    @commands.Cog.listener()
    async def on_game_debug(self, e: 'GameDebugEvent'):
        if e.game != self.game:
            return

        if e.debug_type == DebugRequest.CHANNELS:
            await e.ctx.send(f"{self.game} is listening in {','.join(map(str, self.channels))}")

        if e.debug_type == DebugRequest.GAMEINFO:
            if e.snowflake:
                if game := self.games.get(e.snowflake, None):
                    await e.ctx.send(f"```{game.debug_string()}```")
                else:
                    await e.ctx.send(f"No games found for snowflake {e.snowflake} for {self.game}.")
            else:
                send: str = ""
                for game in self.games.values():
                    debug: str = game.debug_string()
                    if len(debug + send) < 1950:
                        debug += send
                    else:
                        break
                await e.ctx.send(send)

    @commands.Cog.listener()
    async def on_game_channel_update(self, e: 'GameChannelUpdateEvent'):
        if e.game != self.game:
            return

        if e.update_type == Update.ADD:
            for channel in e.channels:
                self.channels.append(channel)

        elif e.update_type == Update.REMOVE:
            for channel in e.channels:
                if channel in self.channels:
                    self.channels.remove(channel)

    async def cog_check(self, ctx: commands.Context) -> bool:
        if self.limit_to_channel:
            if isinstance(ctx.channel, discord.DMChannel) or ctx.author.bot:
                return False
            return ctx.channel.id in self.channels
        return True

    async def cog_load(self) -> None:
        game_string = self.game.value
        async with self.bot.pool.acquire() as con:
            con: asyncpg.Connection
            rows = await con.fetch(f"SELECT guild_id,{game_string} FROM channel_ids WHERE {game_string}  IS NOT NULL;")

            for row in rows:
                if row[game_string] == '':
                    continue

                for channel in map(int, row[game_string].split(",")):
                    self.channels.append(channel)
