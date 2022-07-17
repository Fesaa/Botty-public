import re
import typing
import aiohttp
import discord

from discord.ext import commands

from Botty import Botty

date_regex = re.compile(r'^\d{4}[\-\/\s]?((((0[13578])|(1[02]))[\-\/\s]?(([0-2][0-9])|(3[01])))|(((0[469])|(11))[\-\/\s]?(([0-2][0-9])|(30)))|(02[\-\/\s]?[0-2][0-9]))$')


class apiCubeCounterUserFlagConverter(commands.FlagConverter):
    Total: bool = False
    Daily: bool = False
    UserID: discord.Member = None
    ChannelID: typing.List[discord.abc.GuildChannel] = None
    StaffHelp: bool = None
    StartDate: str = "0001-01-01"
    StartHour: int = None
    EndDate: str = "9999-12-31"
    EndHour: int = None


class Activity(commands.Cog):

    def __init__(self, bot: Botty):
        self.bot = bot
        super().__init__()
    
    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message):
        self.bot.db.insert_data(msg)

    @commands.command(name='Activity', aliases=['a'])
    async def _Activity(self, ctx: commands.Context, lookup: typing.Optional[typing.Union[discord.Member, discord.Guild]]):
        if not lookup:
            lookup = ctx.guild
        
        if isinstance(lookup, discord.Guild):
            async with aiohttp.ClientSession() as cs:
                async with cs.get(f'http://127.0.0.1:5000/Counter/Guild/{lookup.id}', allow_redirects=False) as r:
                    res = await r.json()

            e = discord.Embed(title=f'Activity for {lookup}', colour=discord.Colour.fuchsia(), timestamp=discord.utils.utcnow())
            e.set_footer(text=f'Requested by {ctx.author}', icon_url=ctx.author.avatar.url)
            if lookup.icon:
                e.set_thumbnail(url=lookup.icon.url)
            if channels := res['ChannelCount']:
                channels = dict(sorted(channels.items(), key=lambda item: item[1], reverse=True))
                e.add_field(name='Top 5 Channels',
                            value="\n".join(f'<#{ChannelID}>: {channels[ChannelID]}'\
                            for index, ChannelID in enumerate(channels) if index < 5))
            if roles := res["RoleCount"]:
                role_counter = {}
                for CountDict in roles.values():
                    for RoleID, count in CountDict.items():
                        if int(RoleID) == lookup.id:
                            continue
                        if RoleID in role_counter:
                            role_counter[RoleID] += count
                        else:
                            role_counter[RoleID] = count
                role_counter = dict(sorted(role_counter.items(), key=lambda item: item[1], reverse=True))

                e.add_field(name='Top 5 Roles',
                            value="\n".join(f'<@&{RoleID}>: {role_counter[RoleID]}' for index, RoleID in enumerate(role_counter) if index < 5))
            return await ctx.send(embed=e)
        
        elif isinstance(lookup, discord.Member):
            async with aiohttp.ClientSession() as cs:
                async with cs.get(f'http://127.0.0.1:5000/Counter/Guild/{ctx.guild.id}/User/{lookup.id}', allow_redirects=False) as r:
                    res = await r.json()
            
            e = discord.Embed(title=f'Activity for {lookup}', colour=discord.Colour.fuchsia(), timestamp=discord.utils.utcnow())
            e.set_footer(text=f'Requested by {ctx.author}', icon_url=ctx.author.avatar.url)
            if lookup.avatar:
                e.set_thumbnail(url=lookup.avatar.url)
            if channels := res['TotalChannelCount']:
                channels = dict(sorted(channels.items(), key=lambda item: item[1], reverse=True))
                e.add_field(name='Top 5 Channels',
                            value="\n".join(f'<#{ChannelID}>: {channels[ChannelID]}'\
                            for index, ChannelID in enumerate(channels) if index < 5))
            if channel_hours := res['DailyChannelCount']:
                hour_counter = {i: 0 for i in range(24)}
                for channel in channel_hours.values():
                    for entry in channel:
                        hour_counter[entry['Hour']] += entry['Count']
                hour_counter = dict(sorted(hour_counter.items(), key=lambda item: item[1], reverse=True))
                
                e.add_field(name='Top 5 Hours (UTC)',
                            value="\n".join(f'{Hour}h: {hour_counter[Hour]}' for index, Hour in enumerate(hour_counter) if index < 5))
            
            return await ctx.send(embed=e)

async def setup(bot: Botty):
    await bot.add_cog(Activity(bot))