"""
This cog has been forked from: https://github.com/Rapptz/RoboDanny/blob/rewrite/cogs/stats.py
"""

import asyncio
import datetime
import textwrap
import traceback
from collections import Counter
from difflib import SequenceMatcher
from typing import (
    TypedDict,
    Optional,
    Union
)

import aiohttp
import discord
import pkg_resources  # type: ignore
from discord import Embed
from discord.app_commands import AppCommandError
from discord.ext import commands, tasks  # type: ignore

import utils.time as time
from Botty import Botty


class DataBatchEntry(TypedDict):
    guild_id: Optional[int]
    channel_id: int
    author_id: int
    used: str
    prefix: str
    command: str
    failed: bool
    app_command: bool


class Stats(commands.Cog):
    """
    Keeps track of used commands! For some fun stats :)
    """
    def __init__(self, bot: Botty) -> None:
        self.bot = bot
        self._batch_lock = asyncio.Lock()
        self._data_batch: list[DataBatchEntry] = []
        self.bulk_insert_loop.start()
        super().__init__()

        self.command_stats: Counter[str]
        self.command_types_used: Counter[bool]
        bot.tree.on_error = self.on_app_command_error

    def get_bot_uptime(self, *, brief: bool = False) -> str:
        return time.human_timedelta(
            self.bot.uptime, accuracy=None, brief=brief, suffix=False
        )

    @discord.utils.cached_property
    def webhook(self) -> discord.Webhook:
        wh_id, wh_token = self.bot.config['DISCORD']['WEBHOOK']['ID'], self.bot.config['DISCORD']['WEBHOOK']['TOKEN']
        hook = discord.Webhook.partial(id=wh_id, token=wh_token, session=aiohttp.ClientSession())
        return hook

    @commands.command()
    async def uptime(self, ctx: commands.Context):
        """Tells you how long the bot has been up for"""
        await ctx.send(f"Uptime: **{self.get_bot_uptime()}**")

    @commands.command()
    async def about(self, ctx: commands.Context):
        """Get to know me better!"""

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
        embed.add_field(name="Commands Run", value=sum(self.bot.command_stats.values()))
        embed.add_field(name="Uptime", value=self.get_bot_uptime(brief=True))
        embed.set_footer(text=f"Made with discord.py v{version}", icon_url="http://i.imgur.com/5BFecvA.png")
        embed.timestamp = discord.utils.utcnow()
        await ctx.send(embed=embed)
    
    @property
    def display_emoji(self) -> discord.PartialEmoji:
        return discord.PartialEmoji(name='\N{BAR CHART}')

    async def bulk_insert(self) -> None:
        values_list = ",\n".join(f"""{tuple(i.values())}""" for i in self._data_batch)
        query = f"""INSERT INTO commands (guild_id, channel_id, author_id, used, prefix, command, failed, app_command)
                    VALUES {values_list};
                """

        if self._data_batch:
            await self.bot.pool.execute(query)
            self._data_batch.clear()

    @tasks.loop(seconds=10.0)
    async def bulk_insert_loop(self):
        async with self._batch_lock:
            await self.bulk_insert()
    
    async def register_command(self, ctx: commands.Context) -> None:
        if ctx.command is None:
            return

        command = ctx.command.qualified_name
        is_app_command = ctx.interaction is not None
        self.bot.command_stats[command] += 1
        self.bot.command_types_used[is_app_command] += 1
        message = ctx.message
        if ctx.guild is None:
            guild_id = None
        else:
            guild_id = ctx.guild.id

        async with self._batch_lock:
            self._data_batch.append(
                {
                    'guild_id': guild_id,
                    'channel_id': ctx.channel.id,
                    'author_id': ctx.author.id,
                    'used': message.created_at.isoformat(),
                    'prefix': ctx.prefix,
                    'command': command,
                    'failed': ctx.command_failed,
                    'app_command': is_app_command,
                }
            )
    
    @commands.Cog.listener()
    async def on_command_completion(self, ctx: commands.Context):
        await self.register_command(ctx)
    
    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        command = interaction.command
        if (
            command is not None
            and interaction.type is discord.InteractionType.application_command
            and not command.__class__.__name__.startswith('Hybrid')
        ):
            ctx = await self.bot.get_context(interaction)
            ctx.command_failed = interaction.command_failed or ctx.command_failed
            await self.register_command(ctx)
    
    def error_embed(self, ctx: Union[commands.Context, discord.Interaction], error: Union[Exception, AppCommandError]) -> Embed:
        e = discord.Embed(title='Command Error', colour=0xCC3366)
        if hasattr(ctx.command, 'qualified_name'):
            e.add_field(name='Name', value=ctx.command.qualified_name)  # type: ignore
        elif hasattr(ctx.command, 'name'):
            e.add_field(name='Name', value=ctx.command.name)  # type: ignore
        if hasattr(ctx, 'author'):
            e.add_field(name='Author', value=f'{ctx.author} (ID: {ctx.author.id})')  # type: ignore

        if ctx.channel:
            fmt = f'Channel: {ctx.channel} (ID: {ctx.channel.id})'
            if ctx.guild:
                fmt = f'{fmt}\nGuild: {ctx.guild} (ID: {ctx.guild.id})'

            e.add_field(name='Location', value=fmt, inline=False)
        if ctx.message:
            e.add_field(name='Content', value=textwrap.shorten(ctx.message.content, width=512))

        exc = ''.join(traceback.format_exception(type(error), error, error.__traceback__, chain=False))
        e.description = f'```py\n{exc}\n```'
        e.timestamp = discord.utils.utcnow()

        return e
    
    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: Exception) -> None:
        await self.register_command(ctx)
        if not isinstance(error, (commands.CommandInvokeError, commands.ConversionError)):
            return
        
        if hasattr(ctx, "error_handled"):
            return
        
        if isinstance(error, commands.CommandInvokeError):
            error = error.original
        if isinstance(error, commands.errors.CommandNotFound):
            if ctx.author.id in self.bot.owner_ids:
                possible_commands = [cmd.full_parent_name + cmd.name for cmd in self.bot.commands if SequenceMatcher(ctx.message, cmd.full_parent_name + cmd.name).ratio() > 0.5]
                if possible_commands:
                    await ctx.send("commands.errors.CommandNotFound!\n" + ", ".join(possible_commands))
            pass
        elif isinstance(error, commands.errors.MissingRequiredArgument):
            if ctx.author.id in self.bot.owner_ids:
                await ctx.send("commands.errors.MissingRequiredArgument!\n```" + error + "```")

            pass
        elif isinstance(error, commands.errors.CheckFailure):
            pass
        elif isinstance(error, (discord.Forbidden, discord.NotFound)):
            return
        else:
            await self.webhook.send("<@&996004219792400405>",embed=self.error_embed(ctx, error))
            raise error
    
    async def on_app_command_error(self, interaction: discord.Interaction, error: AppCommandError):
        if isinstance(error, discord.app_commands.errors.MissingPermissions):
            await interaction.response.send_message("You are missing the necessary perms to use this command.",ephemeral=True)
        elif isinstance(error, discord.app_commands.errors.CommandNotFound):
            pass
        else:
            await self.webhook.send("<@&996004219792400405>",embed=self.error_embed(interaction, error))
            raise error
    
    async def show_guild_stats(self, ctx: commands.Context) -> None:
        lookup = (
            '\N{FIRST PLACE MEDAL}',
            '\N{SECOND PLACE MEDAL}',
            '\N{THIRD PLACE MEDAL}',
            '\N{SPORTS MEDAL}',
            '\N{SPORTS MEDAL}',
        )

        embed = discord.Embed(title='Server Command Stats', colour=discord.Colour.blurple())

        # total command uses
        query = "SELECT COUNT(*), MIN(used) FROM commands WHERE guild_id=$1;"
        async with self.bot.pool.acquire() as con:
            count: tuple[int, datetime.datetime] = await con.fetchrow(query, ctx.guild.id)  # type: ignore

        embed.description = f'{count[0]} commands used.'
        if count[1]:
            timestamp = count[1].replace(tzinfo=datetime.timezone.utc)
        else:
            timestamp = discord.utils.utcnow()

        embed.set_footer(text='Tracking command usage since')
        embed.timestamp = timestamp

        query = """SELECT command,
                          COUNT(*) as "uses"
                   FROM commands
                   WHERE guild_id=$1
                   GROUP BY command
                   ORDER BY "uses" DESC
                   LIMIT 5;
                """
        async with self.bot.pool.acquire() as con:
            records = await con.fetch(query, ctx.guild.id)

        value = (
            '\n'.join(f'{lookup[index]}: {command} ({uses} uses)' for (index, (command, uses)) in enumerate(records))
            or 'No Commands'
        )

        embed.add_field(name='Top Commands', value=value, inline=True)

        query = """SELECT command,
                          COUNT(*) as "uses"
                   FROM commands
                   WHERE guild_id=$1
                   AND used > (CURRENT_TIMESTAMP - INTERVAL '1 day')
                   GROUP BY command
                   ORDER BY "uses" DESC
                   LIMIT 5;
                """

        async with self.bot.pool.acquire() as con:
            records = await con.fetch(query, ctx.guild.id)

        value = (
            '\n'.join(f'{lookup[index]}: {command} ({uses} uses)' for (index, (command, uses)) in enumerate(records))
            or 'No Commands.'
        )
        embed.add_field(name='Top Commands Today', value=value, inline=True)
        embed.add_field(name='\u200b', value='\u200b', inline=True)

        query = """SELECT author_id,
                          COUNT(*) AS "uses"
                   FROM commands
                   WHERE guild_id=$1
                   GROUP BY author_id
                   ORDER BY "uses" DESC
                   LIMIT 5;
                """

        async with self.bot.pool.acquire() as con:
            records = await con.fetch(query, ctx.guild.id)

        value = (
            '\n'.join(
                f'{lookup[index]}: <@!{author_id}> ({uses} bot uses)' for (index, (author_id, uses)) in enumerate(records)
            )
            or 'No bot users.'
        )

        embed.add_field(name='Top Command Users', value=value, inline=True)

        query = """SELECT author_id,
                          COUNT(*) AS "uses"
                   FROM commands
                   WHERE guild_id=$1
                   AND used > (CURRENT_TIMESTAMP - INTERVAL '1 day')
                   GROUP BY author_id
                   ORDER BY "uses" DESC
                   LIMIT 5;
                """

        async with self.bot.pool.acquire() as con:
            records = await con.fetch(query, ctx.guild.id)

        value = (
            '\n'.join(
                f'{lookup[index]}: <@!{author_id}> ({uses} bot uses)' for (index, (author_id, uses)) in enumerate(records)
            )
            or 'No command users.'
        )

        embed.add_field(name='Top Command Users Today', value=value, inline=True)
        await ctx.send(embed=embed)

    async def show_member_stats(self, ctx: commands.Context, member: discord.Member) -> None:
        lookup = (
            '\N{FIRST PLACE MEDAL}',
            '\N{SECOND PLACE MEDAL}',
            '\N{THIRD PLACE MEDAL}',
            '\N{SPORTS MEDAL}',
            '\N{SPORTS MEDAL}',
        )

        embed = discord.Embed(title='Command Stats', colour=member.colour)
        embed.set_author(name=str(member), icon_url=member.display_avatar.url)

        # total command uses
        query = "SELECT COUNT(*), MIN(used) FROM commands WHERE guild_id=$1 AND author_id=$2;"
        async with self.bot.pool.acquire() as con:
            count: tuple[int, datetime.datetime] = await con.fetchrow(query, ctx.guild.id, member.id)  # type: ignore

        embed.description = f'{count[0]} commands used.'
        if count[1]:
            timestamp = count[1].replace(tzinfo=datetime.timezone.utc)
        else:
            timestamp = discord.utils.utcnow()

        embed.set_footer(text='First command used')
        embed.timestamp = timestamp

        query = """SELECT command,
                          COUNT(*) as "uses"
                   FROM commands
                   WHERE guild_id=$1 AND author_id=$2
                   GROUP BY command
                   ORDER BY "uses" DESC
                   LIMIT 5;
                """

        async with self.bot.pool.acquire() as con:
            records = await con.fetch(query, ctx.guild.id, member.id)

        value = (
            '\n'.join(f'{lookup[index]}: {command} ({uses} uses)' for (index, (command, uses)) in enumerate(records))
            or 'No Commands'
        )

        embed.add_field(name='Most Used Commands', value=value, inline=False)

        query = """SELECT command,
                          COUNT(*) as "uses"
                   FROM commands
                   WHERE guild_id=$1
                   AND author_id=$2
                   AND used > (CURRENT_TIMESTAMP - INTERVAL '1 day')
                   GROUP BY command
                   ORDER BY "uses" DESC
                   LIMIT 5;
                """

        async with self.bot.pool.acquire() as con:
            records = await con.fetch(query, ctx.guild.id, member.id)

        value = (
            '\n'.join(f'{lookup[index]}: {command} ({uses} uses)' for (index, (command, uses)) in enumerate(records))
            or 'No Commands'
        )

        embed.add_field(name='Most Used Commands Today', value=value, inline=False)
        await ctx.send(embed=embed)

    @commands.group(invoke_without_command=True)
    @commands.guild_only()
    @commands.cooldown(1, 30.0, type=commands.BucketType.member)
    async def stats(self, ctx: commands.Context, *, member: discord.Member = None):
        """Tells you command usage stats for the server or a member."""
        async with ctx.typing():
            if member is None:
                await self.show_guild_stats(ctx)
            else:
                await self.show_member_stats(ctx, member)
    
    @stats.command(name='global')
    @commands.is_owner()
    async def stats_global(self, ctx: commands.Context):
        """Global all time command statistics."""

        query = "SELECT COUNT(*) FROM commands;"
        async with self.bot.pool.acquire() as con:
            total: tuple[int] = await con.fetchrow(query)  # type: ignore

        e = discord.Embed(title='Command Stats', colour=discord.Colour.blurple())
        e.description = f'{total[0]} commands used.'

        lookup = (
            '\N{FIRST PLACE MEDAL}',
            '\N{SECOND PLACE MEDAL}',
            '\N{THIRD PLACE MEDAL}',
            '\N{SPORTS MEDAL}',
            '\N{SPORTS MEDAL}',
        )

        query = """SELECT command, COUNT(*) AS "uses"
                   FROM commands
                   GROUP BY command
                   ORDER BY "uses" DESC
                   LIMIT 5;
                """

        async with self.bot.pool.acquire() as con:
            records = await con.fetch(query)
        value = '\n'.join(f'{lookup[index]}: {command} ({uses} uses)' for (index, (command, uses)) in enumerate(records))
        e.add_field(name='Top Commands', value=value, inline=False)

        query = """SELECT guild_id, COUNT(*) AS "uses"
                   FROM commands
                   GROUP BY guild_id
                   ORDER BY "uses" DESC
                   LIMIT 5;
                """

        async with self.bot.pool.acquire() as con:
            records = await con.fetch(query)
        value = []
        for (index, (guild_id, uses)) in enumerate(records):
            if guild_id is None:
                guild = 'Private Message'
            else:
                guild = self.bot.get_guild(guild_id) or f'<Unknown {guild_id}>'

            emoji = lookup[index]
            value.append(f'{emoji}: {guild} ({uses} uses)')

        e.add_field(name='Top Guilds', value='\n'.join(value), inline=False)

        query = """SELECT author_id, COUNT(*) AS "uses"
                   FROM commands
                   GROUP BY author_id
                   ORDER BY "uses" DESC
                   LIMIT 5;
                """

        async with self.bot.pool.acquire() as con:
            records = await con.fetch(query)
        value = []
        for (index, (author_id, uses)) in enumerate(records):
            user = self.bot.get_user(author_id) or f'<Unknown {author_id}>'
            emoji = lookup[index]
            value.append(f'{emoji}: {user} ({uses} uses)')

        e.add_field(name='Top Users', value='\n'.join(value), inline=False)
        await ctx.send(embed=e)

    @stats.command(name='today')
    @commands.is_owner()
    async def stats_today(self, ctx: commands.Context):
        """Global command statistics for the day."""

        query = "SELECT failed, COUNT(*) FROM commands WHERE used > (CURRENT_TIMESTAMP - INTERVAL '1 day') GROUP BY failed;"
        async with self.bot.pool.acquire() as con:
            total = await con.fetch(query)
        failed = 0
        success = 0
        question = 0
        for state, count in total:
            if state is False:
                success += count
            elif state is True:
                failed += count
            else:
                question += count

        e = discord.Embed(title='Last 24 Hour Command Stats', colour=discord.Colour.blurple())
        e.description = (
            f'{failed + success + question} commands used today. '
            f'({success} succeeded, {failed} failed, {question} unknown)'
        )

        lookup = (
            '\N{FIRST PLACE MEDAL}',
            '\N{SECOND PLACE MEDAL}',
            '\N{THIRD PLACE MEDAL}',
            '\N{SPORTS MEDAL}',
            '\N{SPORTS MEDAL}',
        )

        query = """SELECT command, COUNT(*) AS "uses"
                   FROM commands
                   WHERE used > (CURRENT_TIMESTAMP - INTERVAL '1 day')
                   GROUP BY command
                   ORDER BY "uses" DESC
                   LIMIT 5;
                """

        async with self.bot.pool.acquire() as con:
            records = await con.fetch(query)
        value = '\n'.join(f'{lookup[index]}: {command} ({uses} uses)' for (index, (command, uses)) in enumerate(records))
        e.add_field(name='Top Commands', value=value, inline=False)

        query = """SELECT guild_id, COUNT(*) AS "uses"
                   FROM commands
                   WHERE used > (CURRENT_TIMESTAMP - INTERVAL '1 day')
                   GROUP BY guild_id
                   ORDER BY "uses" DESC
                   LIMIT 5;
                """

        async with self.bot.pool.acquire() as con:
            records = await con.fetch(query)
        value = []
        for (index, (guild_id, uses)) in enumerate(records):
            if guild_id is None:
                guild = 'Private Message'
            else:
                guild = self.bot.get_guild(guild_id) or f'<Unknown {guild_id}>'
            emoji = lookup[index]
            value.append(f'{emoji}: {guild} ({uses} uses)')

        e.add_field(name='Top Guilds', value='\n'.join(value), inline=False)

        query = """SELECT author_id, COUNT(*) AS "uses"
                   FROM commands
                   WHERE used > (CURRENT_TIMESTAMP - INTERVAL '1 day')
                   GROUP BY author_id
                   ORDER BY "uses" DESC
                   LIMIT 5;
                """

        async with self.bot.pool.acquire() as con:
            records = await con.fetch(query)
        value = []
        for (index, (author_id, uses)) in enumerate(records):
            user = self.bot.get_user(author_id) or f'<Unknown {author_id}>'
            emoji = lookup[index]
            value.append(f'{emoji}: {user} ({uses} uses)')

        e.add_field(name='Top Users', value='\n'.join(value), inline=False)
        await ctx.send(embed=e)

    @stats_today.before_invoke
    @stats_global.before_invoke
    async def before_stats_invoke(self, ctx: commands.Context):
        await ctx.typing()
    
    @stats.error
    async def _error_stats(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.CommandOnCooldown):
            ctx.error_handled = True
            pass
        elif isinstance(error, commands.errors.MemberNotFound):
            ctx.error_handled = True
            pass
        else:
            raise error

async def setup(bot: Botty):
    if not hasattr(bot, 'command_stats'):
        bot.command_stats = Counter()

    if not hasattr(bot, 'command_types_used'):
        bot.command_types_used = Counter()
    await bot.add_cog(Stats(bot))
