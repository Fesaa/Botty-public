import os
import re
import json
import typing
import asyncio
import aiohttp
import discord
import datetime

from io import BytesIO
from PIL import Image

from discord import Embed
from discord.ext import commands
from utils.time import human_timedelta
from Botty import Botty


date_regex = re.compile(
    r"^\d{4}[\-\/\s]?((((0[13578])|(1[02]))[\-\/\s]?(([0-2][0-9])|(3[01])))|(((0[469])|(11))[\-\/\s]?(([0-2][0-9])|(30)))|(02[\-\/\s]?[0-2][0-9]))$"
)


def get_newest_file(dir: str, file_type: str):
    files = [dir + "/" + x for x in os.listdir(dir) if x.endswith(file_type)]
    return max(files, key=os.path.getctime)


async def cc_sorter(bot: Botty, jsonn, channel_id, user_id) -> None:
    c: discord.TextChannel = bot.get_channel(channel_id)
    if not c:
        c = await bot.fetch_channel(channel_id)
    start_time = discord.utils.utcnow()
    async with c.typing():
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(600)) as cs:
            async with cs.post(
                "http://127.0.0.1:8081/api/",
                data=jsonn,
            ) as r:
                res = await r.read()

        with Image.open(BytesIO(res)) as my_image:
            output_buffer = BytesIO()
            my_image.save(output_buffer, "png")
            output_buffer.seek(0)

            embed = Embed(
                colour=discord.Colour.blurple(),
                timestamp=discord.utils.utcnow(),
                title="Cube Counter Request!",
            )
            embed.set_image(url="attachment://image.png")
            embed.set_footer(
                text=human_timedelta(
                    start_time, accuracy=None, brief=False, suffix=False
                )
            )
            await bot.PostgreSQL.remove_task(user_id)
            await c.send(
                f"<@{user_id}> your Cube Counter requests has finished!",
                file=discord.File(fp=output_buffer, filename="image.png"),
                embed=embed,
            )

    if task := bot.db.get_next_task():
        await cc_sorter(
            bot,
            json.dumps(task["json"].decode("utf-8")),
            task["channel_id"],
            task["user_id"],
        )
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
    MinMsg: int | None = None
    MinTime: float | None = None
    User: typing.Union[discord.Member, discord.User] | typing.Literal["True"] = "True"


class CubeCounter(commands.Cog):
    def __init__(self, bot: Botty) -> None:
        self.bot = bot
        super().__init__()

    @commands.command(name="CubeCounter", aliases=["cc"])
    async def _CubeCounter(
        self,
        ctx: commands.Context,
        update: typing.Optional[typing.Literal["Update"]],
        PastDays: typing.Optional[int],
        PreSet: typing.Optional[typing.Literal["Staff", "StaffHelp", "General", "Gen"]],
        *,
        kwargs: apiPostFlagConverter,
    ):
        """
        Generates an image with graphs about activity in Cube Discord.
            Update: Updates the internal cache
            PastDays: Only use days from the last n days, must be an integer
            PreSet: Use a pre defined layout.
            Kwargs: Customize your graph completely. Does not overwrite PreSet. Usage: <flag>:<value>
                Most Flags from <https://github.com/Fesaa/cube-msg-processor/blob/main/README.md#usage-terminal> are supported as kwarg.
        """

        if update:
            cmd0, opt0 = "cp", (
                "-r",
                "/root/Python/CubeCounter/.",
                "/root/Python/counter/data/input/",
            )
            cmd1, opt1 = "rm", (
                "/root/Python/counter/data/input/client.py",
                "/root/Python/counter/data/input/config.json",
            )
            await asyncio.create_subprocess_exec(
                cmd0,
                *opt0,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await asyncio.create_subprocess_exec(
                cmd1,
                *opt1,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

        if PastDays:
            dt = str(datetime.datetime.now().date() - datetime.timedelta(days=PastDays))
        else:
            dt = None

        rt = False
        sh = None
        dm = False
        if PreSet in ["General", "Gen"]:
            sh = False
        elif PreSet in ["Staff", "StaffHelp"]:
            sh = True
            rt = True
            dm = True

        StartDate = dt or (
            kwargs.StartDate
            if re.match(date_regex, kwargs.StartDate)
            else kwargs.get_flags()["StartDate"].default
        )
        EndDate = (
            kwargs.EndDate
            if re.match(date_regex, kwargs.EndDate)
            else kwargs.get_flags()["EndDate"].default
        )

        Dates = [StartDate, EndDate]

        body_json = {
            "Daily": dm or kwargs.Daily,
            "DailyMessages": kwargs.DailyMessages,
            "ConsecutiveTime": kwargs.ConsecutiveTime,
            "TotalMessages": kwargs.TotalMessages,
            "ReplyTimes": rt or kwargs.ReplyTimes,
            "RoleDistribution": kwargs.RoleDistribution,
            "Percentages": kwargs.Percentages,
            "HourlyActivity": kwargs.HourlyActivity,
            "StaffHelp": sh or kwargs.StaffHelp,
            "Accurate": kwargs.Accurate,
            "IgnoreMessages": kwargs.IgnoreMessages,
            "MinMsg": kwargs.MinMsg,
            "MinTime": kwargs.MinTime,
            "User": str(kwargs.User.id) if hasattr(kwargs.User, "id") else kwargs.User,  # type: ignore
            "UpdateJson": False,
            "FigName": "output",
            "ShowGraphs": False,
            "time_range": Dates,
        }
        if kwargs.StaffHelp:
            body_json["FileName"] = [
                "data/input/legancy_staff_help.csv",
                "data/input/174845164899139584.csv",
            ]
        else:
            body_json["FileName"] = []
            body_json["Path"] = "data/input/"
            body_json["Exclude"] = [
                "data/input/legancy_staff_help.csv",
                "data/input/174845164899139584.csv",
            ]

        if await self.bot.PostgreSQL.check_has_task(ctx.author.id):
            return await ctx.reply(
                "You already made a requests, please wait for it to finish before requesting a new graph."
            )

        if await self.bot.PostgreSQL.get_next_task():
            await self.bot.PostgreSQL.add_task(
                ctx.channel.id, ctx.author.id, str(body_json), datetime.datetime.now()
            )
            return await ctx.reply(
                "Added your requests to be fulfilled. This may take a while, you'll be pinged once it is done."
            )

        await self.bot.PostgreSQL.add_task(
            ctx.channel.id, ctx.author.id, str(body_json), datetime.datetime.now()
        )
        await cc_sorter(self.bot, json.dumps(body_json), ctx.channel.id, ctx.author.id)

    @_CubeCounter.error
    async def _error_CubeCounter(
        self, ctx: commands.Context, error: commands.CommandError
    ):

        if isinstance(error, commands.BadFlagArgument):
            ctx.error_handled = True
            flag = error.flag
            await ctx.send(
                f"Your argument ({error.argument}) for {flag.attribute} should follow the annotation:\n{flag.annotation}"
            )
            pass
        else:
            raise error


async def setup(bot: Botty):
    await bot.add_cog(CubeCounter(bot))
