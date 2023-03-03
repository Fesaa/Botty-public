import discord
from discord.ext import commands

from Botty import Botty
from framework.GameEvents import GameChannelUpdateEvent, GameDebugEvent
from framework.enums import Game, Update, DebugRequest


class GameCog(commands.Cog):

    def __init__(self, bot: Botty, game: Game, limit_to_channel: bool = True):
        self.bot = bot
        super().__init__()

        self.game = game
        self.channels: list[int] = []
        self.limit_to_channel = limit_to_channel

    @commands.Cog.listener()
    async def on_game_debug(self, e: GameDebugEvent):
        if e.game != self.game:
            return

        if e.debug_type == DebugRequest.CHANNELS:
            await e.ctx.send(f"{self.game} is listening in {','.join(map(str, self.channels))}")

    @commands.Cog.listener()
    async def on_game_channel_update(self, e: GameChannelUpdateEvent):
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
