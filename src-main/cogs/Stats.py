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
        super().__init__()

        bot.tree.on_error = self.on_app_command_error

    def get_bot_uptime(self, *, brief: bool = False) -> str:
        return time.human_timedelta(
            self.bot.uptime, accuracy=None, brief=brief, suffix=False
        )

    @discord.utils.cached_property
    def webhook(self) -> discord.Webhook:
        wh_id, wh_token = self.bot.config['DISCORD']['WEBHOOK']['ID'], self.bot.config['DISCORD']['WEBHOOK']['TOKEN']
        hook = discord.Webhook.partial(id=wh_id, token=wh_token, session=self.bot.httpClientSession)
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
        embed.add_field(name="Uptime", value=self.get_bot_uptime(brief=True))
        embed.set_footer(text=f"Made with discord.py v{version}", icon_url="http://i.imgur.com/5BFecvA.png")
        embed.timestamp = discord.utils.utcnow()
        await ctx.send(embed=embed)
    
    @property
    def display_emoji(self) -> discord.PartialEmoji:
        return discord.PartialEmoji(name='\N{BAR CHART}')
    
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
    
async def setup(bot: Botty):
    await bot.add_cog(Stats(bot))
