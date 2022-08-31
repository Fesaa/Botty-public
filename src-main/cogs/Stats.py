import asyncpg
import discord
import pkg_resources  # type: ignore

from discord import Embed
from discord.ext import commands, tasks # type: ignore
from typing import (
    TypedDict,
    Optional
)

import utils.time as time

from Botty import Botty


class DataBatchEntry(TypedDict):
    guild_id: Optional[int]
    channel_id: int
    author_id: int
    command: str
    uses: int



class Stats(commands.Cog):
    def __init__(self, bot: Botty) -> None:
        self.bot = bot
        self._data_batch: list[DataBatchEntry] = []
        self.bulk_insert_loop.start()
        super().__init__()
    
    def cog_unload(self):
        self.bulk_insert_loop.stop()

    async def bulk_insert(self) -> None:
        query = """INSERT INTO commands (guild_id, channel_id, author_id, command, uses)
                    SELECT x.guild, x.channel, x.author, x.command, x.used
                    FROM jsonb_to_recordset($1::jsonb) AS
                    x(guild BIGINT, channel BIGINT, author BIGINT, command TEXT, uses INT)
                """
        
        async with self.bot.pool.acquire() as con:
            con: asyncpg.connection.Connection  # type: ignore
            async with con.transaction():
                await con.execute(query, self._data_batch)
    
    async def register_command(self, ctx: commands.Context):
        if ctx.command is None:
            return

        command = ctx.command.qualified_name
        message = ctx.message
        if ctx.guild is None:
            guild_id = 0
        else:
            guild_id = ctx.guild.id

        async with self._batch_lock:
            self._data_batch.append(
                {
                    'guild': guild_id,
                    'channel': ctx.channel.id,
                    'author': ctx.author.id,
                    'used': message.created_at.isoformat(),
                    'command': command,
                }
            )
    
    @tasks.loop(minutes=1)
    async def bulk_insert_loop(self):
        await self.bulk_insert()


    def get_bot_uptime(self, *, brief: bool = False) -> str:
        return time.human_timedelta(self.bot.uptime, accuracy=None, brief=brief, suffix=False)

    @commands.command()
    async def uptime(self, ctx: commands.Context):
        """Tells you how long the bot has been up for."""
        await ctx.send(f"Uptime: **{self.get_bot_uptime()}**")

    @commands.command()
    async def about(self, ctx: commands.Context):
        """Tells you information about the bot itself."""

        for guild_id in self.command_stats.keys():
            await self.update_guild_stats(guild_id)

        embed = Embed()
        embed.colour = self.bot.Botty_colour

        if self.bot.owner.display_avatar:
            embed.set_author(name=str(self.bot.owner), icon_url=self.bot.owner.display_avatar.url)
        else:
            embed.set_author(name=str(self.bot.owner), icon_url=self.bot.owner.default_avatar)


        # statistics
        total_members = 0
        total_unique = len(self.bot.users)

        text = 0
        voice = 0
        guilds = 0
        for guild in self.bot.guilds:
            guilds += 1
            if guild.unavailable:
                continue

            total_members += guild.member_count or 0
            for channel in guild.channels:
                if isinstance(channel, discord.TextChannel):
                    text += 1
                elif isinstance(channel, discord.VoiceChannel):
                    voice += 1

        embed.add_field(name="Members", value=f"{total_members} total\n{total_unique} unique")
        embed.add_field(name="Channels", value=f"{text + voice} total\n{text} text\n{voice} voice")

        version = pkg_resources.get_distribution("discord.py").version
        embed.add_field(name="Guilds", value=guilds)
        embed.add_field(name="Commands Run", value=(await self.total_command_executions(ctx)) + 1)
        embed.add_field(name="Uptime", value=self.get_bot_uptime(brief=True))
        embed.set_footer(text=f"Made with discord.py v{version}", icon_url="http://i.imgur.com/5BFecvA.png")
        embed.timestamp = discord.utils.utcnow()
        await ctx.send(embed=embed)


async def setup(bot: Botty):
    await bot.add_cog(Stats(bot))
