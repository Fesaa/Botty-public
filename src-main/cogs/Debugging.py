from enum import Enum
from difflib import SequenceMatcher
from typing import (
    Union,
    Optional
)

import asyncpg
import discord
from discord.ext import commands

from Botty import Botty
from framework import GameDebugEvent, Game, DebugRequest

class EnumConverter(commands.Converter):

    def __init__(self, e: Enum) -> None:
        super().__init__()
        self.enum = e

    async def convert(self, _: commands.Context[Botty], argument: str):
        for e in self.enum:
            if SequenceMatcher(None, e.name.lower(), argument.lower()).ratio() > 0.75:
                return e


class Debugging(commands.Cog):
    """
    Debugging commands, to help aid permission problems.
    """

    def __init__(self, bot: Botty) -> None:
        self.bot = bot
        super().__init__()

    @property
    def display_emoji(self) -> discord.PartialEmoji:
        return discord.PartialEmoji(name='\U0001f914')

    async def say_permissions(self, ctx: commands.Context, member: discord.Member,
                              channel: Union[discord.abc.GuildChannel, discord.Thread]):
        permissions = channel.permissions_for(member)
        e = discord.Embed(colour=member.colour)
        avatar = member.display_avatar.url
        e.set_author(name=str(member), icon_url=avatar)
        allowed, denied = [], []
        for name, value in permissions:
            name = name.replace('_', ' ').replace('guild', 'server').title()
            if value:
                allowed.append(name)
            else:
                denied.append(name)

        e.add_field(name='Allowed', value='\n'.join(allowed))
        e.add_field(name='Denied', value='\n'.join(denied))
        await ctx.send(embed=e)

    @commands.group(name="debug", hidden=True)
    async def _debug(self, ctx: commands.Context):
        """
        Botty's internal debug commands.
        """
        ...

    @_debug.command()
    @commands.guild_only()
    async def userpermissions(
            self,
            ctx: commands.Context,
            member: discord.Member = None,
            channel: Union[discord.abc.GuildChannel, discord.Thread] = None,
    ):
        """Shows a member's permissions in a specific channel.
        If no channel is given then it uses the current one.
        You cannot use this in private messages. If no member is given then
        the info returned will be yours.
        """
        channel = channel or ctx.channel
        if member is None:
            member = ctx.author

        await self.say_permissions(ctx, member, channel)

    @_debug.command()
    @commands.guild_only()
    async def botpermissions(self, ctx: commands.Context, *,
                             channel: Union[discord.abc.GuildChannel, discord.Thread] = None):
        """Shows the bot's permissions in a specific channel.
        If no channel is given then it uses the current one.
        This is a good way of checking if the bot has the permissions needed
        to execute the commands it wants to execute.
        """
        channel = channel or ctx.channel
        member = ctx.guild.me
        await self.say_permissions(ctx, member, channel)

    @_debug.command(hidden=True)
    @commands.is_owner()
    async def permissions(self, ctx: commands.Context, guild_id: int, channel_id: int, author_id: int = None):
        """Shows permission resolution for a channel and an optional author."""

        guild = self.bot.get_guild(guild_id)
        if guild is None:
            return await ctx.send('Guild not found?')

        channel = guild.get_channel(channel_id)
        if channel is None:
            return await ctx.send('Channel not found?')

        if author_id is None:
            member = guild.me
        else:
            member = ctx.guild.get_member(author_id)
            if not member:
                try:
                    member = ctx.guild.fetch_member(author_id)
                except (discord.errors.HTTPException, discord.errors.Forbidden, discord.errors.NotFound):
                    pass

        if member is None:
            return await ctx.send('Member not found?')

        await self.say_permissions(ctx, member, channel)

    @_debug.command(name="config")
    @commands.is_owner()
    async def _server_config(self, ctx: commands.Context, guild: Optional[discord.Guild]):
        """
        Fetch a servers config
        """
        if not guild:
            guild = ctx.guild

        async with self.bot.pool.acquire() as con:
            con: asyncpg.connection.Connection  # type: ignore
            channel_ids = await con.fetchrow("SELECT * FROM channel_ids WHERE guild_id = $1;", guild.id)
            game_settings = await con.fetchrow("SELECT * FROM game_settings WHERE guild_id = $1", guild.id)

            await ctx.send("Channel IDs```" + str(channel_ids) + "```\nGame Settings```" + str(game_settings) + "```")

    @_debug.command(name="game")
    @commands.is_owner()
    async def _game_debug(self, ctx: commands.Context[Botty], game: EnumConverter(Game), debug_type: EnumConverter(DebugRequest), snowflake: Optional[int]):
        self.bot.dispatch('game_debug', GameDebugEvent(ctx, game, debug_type, snowflake=snowflake))


async def setup(bot: Botty):
    await bot.add_cog(Debugging(bot))
