import asyncpg
import discord
from typing import TYPE_CHECKING

from discord.ext import commands
from framework.enums import Update, DebugRequest

if TYPE_CHECKING:
    from Botty import Botty
    from framework.BaseGame import BaseGame
    from framework.GameEvents import GameChannelUpdateEvent, GameDebugEvent, GameUpdateEvent
    from framework.enums import Game

class GameCog(commands.Cog):

    def __init__(self, bot: 'Botty', game: 'Game', limit_to_channel: bool = True):
        self.bot = bot
        super().__init__()

        self.game = game
        self.channels: list[int] = []
        self.games: dict[int, 'BaseGame'] = {}
        self.limit_to_channel = limit_to_channel

    async def exec_sql(self, query: str, *val):
        async with self.bot.pool.acquire() as con:
            con: asyncpg.Connection
            await con.execute(query, *val)

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
        
        ctx = e.ctx

        if e.update_type == Update.ADD:
            counter = 0
            added_channels: list[int] = []
            for channel in e.channels:
                if channel not in self.channels:
                    added_channels.append(channel)
                    self.channels.append(channel)
                    counter += 1
            await self.exec_sql(f"INSERT INTO channel_ids (guild_id, channel_type, channel_id) VALUES {','.join(f'($1, $2, {channel}' for channel in added_channels)});", ctx.guild.id, e.game.value.lower())
            await ctx.send(f'Added {counter} channels to be used for {e.game.value}!', ephemeral=True)

        elif e.update_type == Update.REMOVE:
            counter = 0
            removed_channels: list[int] = []
            for channel in e.channels:
                if channel in self.channels:
                        removed_channels.append(channel)
                        self.channels.remove(channel)
                        counter += 1
            await self.exec_sql(f"DELETE FROM channel_ids WHERE guild_id = $1 AND channel_type = $2 AND channel_id IN ({','.join(map(str, removed_channels))});", ctx.guild.id, e.game.value.lower())
            await ctx.send(f'Removed {counter} channels to be used for {e.game.value}', ephemeral=True)

    async def cog_check(self, ctx: commands.Context) -> bool:
        if self.limit_to_channel:
            if isinstance(ctx.channel, discord.DMChannel) or ctx.author.bot:
                return False
            return ctx.channel.id in self.channels
        return True

    async def cog_load(self) -> None:
        async with self.bot.pool.acquire() as con:
            con: asyncpg.Connection
            rows = await con.fetch(f"SELECT guild_id,channel_id FROM channel_ids WHERE channel_type = $1;", self.game.value)
            for row in rows:
                self.channels.append(row['channel_id'])
