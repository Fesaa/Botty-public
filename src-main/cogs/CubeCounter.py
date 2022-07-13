import os
import re
import json
import aiohttp
import typing
import discord

from cogs.ConfigHandler import config
from imports.functions import time
from imports.time import human_timedelta
from discord.ext import commands
from Botty import Botty


dir = config['Server']['dir']
date_regex = re.compile(r'^\d{4}[\-\/\s]?((((0[13578])|(1[02]))[\-\/\s]?(([0-2][0-9])|(3[01])))|(((0[469])|(11))[\-\/\s]?(([0-2][0-9])|(30)))|(02[\-\/\s]?[0-2][0-9]))$')

def get_newest_file(dir: str, file_type: str):
    files = [dir + '/' + x for x in os.listdir(dir) if x.endswith(file_type)]
    return max(files , key = os.path.getctime)
            
async def cc_sorter(bot: Botty, jsonn , channel_id, user_id) -> None:
    c: discord.TextChannel = bot.get_channel(channel_id)
    if not c:
        c = await bot.fetch_channel(channel_id)
    start_time = discord.utils.utcnow()
    async with c.typing():
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(600)) as cs:
            async with cs.post("http://192.168.0.141/api/", data=jsonn, ) as r:
                res = r.headers

        path = get_newest_file(dir, ".png")
        file = discord.File(path, filename='graph.png')

        embed = discord.Embed(colour=discord.Colour.blurple(), timestamp=discord.utils.utcnow(), title="Cube Counter Request!")
        embed.set_image(url="attachment://graph.png")
        embed.set_footer(text=human_timedelta(start_time, accuracy=None, brief=False, suffix=False))
        bot.db.remove_task(user_id)
        await c.send(f'<@{user_id}> your Cube Counter requests has finished!', file=file, embed=embed)

    if task := bot.db.get_next_task():
        await cc_sorter(bot, task['json'], task['channel_id'], task['user_id'])
    else:
        return

class apiPostFlagConverter(commands.FlagConverter):
    Daily: bool = False
    DailyMessages: bool = False
    ConsecutiveTime: bool = True
    TotalMessages: bool = True
    ReplyTimes: bool = False
    RoleDistribution: bool = True
    Percentages: bool = False
    HourlyActivity: bool = True
    StaffHelp: bool = False
    Accurate: bool = False
    StartDate: str = "First Date"
    EndDate: str = "End Date"
    IgnoreMessages: int = 2
    MinMsg: int = 10
    MinTime: float = 0.5
    User: typing.Union[discord.Member, discord.User] = "True"


class CubeCounter(commands.Cog):

    def __init__(self, bot: Botty) -> None:
        self.bot = bot
        super().__init__()

    @commands.command(name='CubeCounter', aliases=['cc'])
    async def _CubeCounter(self, ctx: commands.Context, *,  kwargs: apiPostFlagConverter):
        """
        Generates an image with graphs about activity in Cube Discord. Most Flags from <https://github.com/Fesaa/cube-msg-processor/blob/main/README.md#usage-terminal> are supported as kwarg.
        """

        StartDate = kwargs.StartDate if re.match(date_regex, kwargs.StartDate) else kwargs.get_flags()['StartDate'].default
        EndDate = kwargs.EndDate if re.match(date_regex, kwargs.EndDate) else kwargs.get_flags()['EndDate'].default

        Dates = [StartDate, EndDate]
        
        body_json = {
            'Daily': kwargs.Daily,
            'DailyMessages': kwargs.DailyMessages,
            'ConsecutiveTime': kwargs.ConsecutiveTime,
            'TotalMessages': kwargs.TotalMessages,
            'ReplyTimes': kwargs.ReplyTimes,
            'RoleDistribution': kwargs.RoleDistribution,
            'Percentages': kwargs.Percentages,
            'HourlyActivity': kwargs.HourlyActivity,
            'StaffHelp': kwargs.StaffHelp,
            'Accurate': kwargs.Accurate,
            'IgnoreMessages': kwargs.IgnoreMessages,
            'MinMsg': kwargs.MinMsg,
            'MinTime': kwargs.MinTime,
            'User': str(kwargs.User.id) if hasattr(kwargs.User, 'id') else kwargs.User,
            "UpdateJson": False,
            "FigName": "output",
            "ShowGraphs": False,
            "time_range": Dates
        }
        if kwargs.StaffHelp:
            body_json["FileName"] = ["data/input/legancy_staff_help.csv","data/input/174845164899139584.csv"]
        else:
            body_json["FileName"] = []
            body_json["Path"] = "data/input/"
            body_json["Exclude"] = ["data/input/legancy_staff_help.csv","data/input/174845164899139584.csv"]

        if self.bot.db.check_has_task(ctx.author.id):
            return await ctx.reply('You already made a requests, please wait for it to finish before requesting a new graph.')
        
        if self.bot.db.get_next_task():
            self.bot.db.add_task(ctx.channel.id, ctx.author.id, body_json, time())
            return await ctx.reply('Added your requests to be fulfilled. This may take a while, you\'ll be pinged once it is done.')
        
        self.bot.db.add_task(ctx.channel.id, ctx.author.id, body_json, time())
        await cc_sorter(self.bot, json.dumps(body_json), ctx.channel.id, ctx.author.id)

    @_CubeCounter.error
    async def _error_CubeCounter(self, ctx: commands.Context, error: commands.CommandError):

        if isinstance(error, commands.BadFlagArgument):
            ctx.error_handled = True
            flag = error.flag
            await ctx.send(f'Your argument ({error.argument}) for {flag.attribute} should follow the annotation:\n{flag.annotation}')
            pass
        else:
            raise error

async def setup(bot: Botty):
    await bot.add_cog(CubeCounter(bot))
