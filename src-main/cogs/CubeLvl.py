import logging
from math import sqrt

import aiohttp
import discord
from discord import app_commands, DMChannel
from discord.ext import commands


from io import BytesIO
from PIL import Image

from Botty import Botty
from utils import clc
from utils.time import human_timedelta

_log = logging.getLogger("botty")


class CubeLvl(commands.Cog):
    """
    Calculate all things Cube!
    """
    def __init__(self, bot: Botty) -> None:
        self.bot = bot

    @property
    def display_emoji(self) -> discord.PartialEmoji:
        return discord.PartialEmoji(name='\U0001f4c8')

    async def cog_check(self, ctx: commands.Context) -> bool:
        if isinstance(ctx.channel, DMChannel) or ctx.author.bot:
            return False
        return True

    @commands.hybrid_group(name="cubecraft")
    async def _cube(self, ctx: commands.Context) -> None:
        """
        Quickly calculate a bunch of stuff around the CubeCraft leveling system!
        """
        ...

    @_cube.command(
        name="level",
        description="Calculate difference between two levels (Default: Difference with level 1)",
    )
    @app_commands.rename(level1="current_level", level2="level_to_be")
    @app_commands.describe(level2="Level you aim to be", level1="Level you are", current_xp="The amount of experience you have")
    async def _level(
        self, ctx: commands.Context, level2: int, level1: int = 1, current_xp: int = 0
    ):
        """
        Information on levels, and their differences.
        """

        host: str = f"{self.bot.config.get("SERVER").get("IMAGE").get("host")}:{self.bot.config.get("SERVER").get("IMAGE").get("port")}"
        if level1 == 1 and current_xp == 0:
            url = f"http://{host}/image-renderer/cube-level/single?level={level2}"
        else:
            url = f"http://{host}/image-renderer/cube-level/multi?level1={level1}&level2={level2}&current_xp={current_xp}"


        async with ctx.typing():
            t = discord.utils.utcnow()
            async with aiohttp.ClientSession() as cs:
                async with cs.get(url, timeout=30) as r:
                    if r.status == 200:
                        with Image.open(BytesIO(await r.read())) as img:
                            buffer = BytesIO()
                            img.save(buffer, "png")
                            buffer.seek(0)

                        e = discord.Embed(colour=discord.Colour.blurple(), timestamp=discord.utils.utcnow(), title="Cube Level")
                        e.set_image(url="attachment://image.png")
                        now = discord.utils.utcnow()
                        e.set_footer(text=f'It took {round((now - t).microseconds/1000)} ms to generate this image! {human_timedelta(now, accuracy=None, brief=False, suffix=False)}')
                        if ctx.author and ctx.author.avatar:
                            e.set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url)
                        await ctx.send(embed=e, file=discord.File(fp=buffer, filename="image.png"))
                    else:
                        await ctx.send(f"An error occurred. Please try again. `{await r.read()}`")

    @_cube.command(
        name="multies",
        description="Calculate which level you will be after using multies",
    )
    @app_commands.describe(current_lvl="Level you are", current_xp="The amount of experience you have",
    amount_of_multies="The amount of multipliers you aim to use", thanks="Guessed amount of thanks you'll receive (Defaults: 700)"
    )
    async def multies(
        self,
        ctx: commands.Context,
        current_lvl: int,
        current_xp: int,
        amount_of_multies: int,
        thanks: int = 700,
    ):
        """
        Information for the rich.
        """
        level = clc.Cubelvl(current_lvl)
        levelx = clc.Cubelvl(clc.lvlxp(level() + current_xp))
        await ctx.send(
            f"Assuming **{thanks}** /thank, you'll be level: **{levelx.levelafterxp(clc.xpm(thanks, amount_of_multies))}**"
        )

    @_cube.command(name="stats", description="How much of my level comes from ...?")
    @app_commands.describe(game="The game you want to calculate your experience gain from", wins="Amount of wins",
    games_played="Amount of played games (Default: $wins)", tasks_completed="Amount of completed tasks (Among Slimes only)"
    )
    @app_commands.choices(
        game=[
            app_commands.Choice(name="EggWars", value="ew"),
            app_commands.Choice(name="SkyWars", value="sw"),
            app_commands.Choice(name="Lucky Islands", value="li"),
            app_commands.Choice(name="Tower Defense", value="td"),
            app_commands.Choice(name="BlockWars", value="bwb"),
            app_commands.Choice(name="Duels", value="duels"),
            app_commands.Choice(name="Free For All", value="ffa"),
            app_commands.Choice(name="Among Slimes", value="as"),
        ]
    )
    async def _stats(
        self,
        ctx: commands.Context,
        game: str,
        wins: int,
        games_played: int | None = None,
        tasks_completed: int | None = None,
    ):
        """
        Game specific experience gain.
        """

        game = game.lower().replace("_", "")

        if game not in [
            "ew",
            "sw",
            "li",
            "td",
            "bwb",
            "duels",
            "ffa",
            "as",
            "eggwars",
            "skywars",
            "luckyislands",
            "towerdefence",
            "blockwarsbridges",
            "amongslimes",
        ]:
            await ctx.send(
                "This game is not supported. Feel free to use the help command if needed!",
                ephemeral=True,
            )
            return

        def lvlxp(x):  # xp = total xp => level
            return round(-9 / 2 + 1 / 10 * sqrt(2025 + x))

        if not games_played:
            games_played = wins

        if not tasks_completed:
            tasks_completed = 0

        if game in ["ew", "eggwars"]:
            xp = 250 * wins + 5 * (games_played - wins) + 1 / 2 * games_played
            await ctx.send(
                f"You have gained **{xp}** experience in Eggwars, this is equivalent with level **{lvlxp(xp) + 1}**"
            )
        elif game in ["sw", "skywars"]:
            xp = 125 * wins + 5 * (games_played - wins) + 1 / 2 * games_played
            await ctx.send(
                f"You have gained **{xp}** experience in SkyWars, this is equivalent with level **{lvlxp(xp) + 1}**"
            )
        elif game in ["li", "luckyislands"]:
            xp = 120 * wins + 5 * (games_played - wins) + 1 / 2 * games_played
            await ctx.send(
                f"You have gained **{xp}** experience in Lucky Islands, this is equivalent with level **{lvlxp(xp) + 1}**"
            )
        elif game in ["td", "towerdefence"]:
            xp = 150 * wins + 5 * (games_played - wins) + 1 / 2 * games_played
            await ctx.send(
                f"You have gained **{xp}** experience in Tower Defense, this is equivalent with level **{lvlxp(xp) + 1}**"
            )
        elif game in ["bwb", "blockwarsbridges"]:
            xp = 100 * wins + 5 * (games_played - wins) + 1 / 2 * games_played
            await ctx.send(
                f"You have gained **{xp}** experience in BlockWars Bridges, this is equivalent with level **{lvlxp(xp) + 1}**"
            )
        elif game == "duels":
            xp = 10 * wins + 1 / 2 * games_played
            await ctx.send(
                f"You have gained **{xp}** experience in Duels, this is equivalent with level **{lvlxp(xp) + 1}**"
            )
        elif game == "ffa":
            xp = 1 * wins
            await ctx.send(
                f"You have gained **{xp}** experience in Duels, this is equivalent with level **{lvlxp(xp) + 1}**"
            )
        elif game in ["as", "amongslimes"]:
            xp = (
                100 * wins
                + 3 * int(tasks_completed)
                + 2 / 3 * games_played * 30
                + 5 * (games_played - wins)
                + 1 / 2 * games_played
            )
            await ctx.send(
                f"You have gained **{xp}** experience in Among Slimes, this is equivalent with level **{lvlxp(xp) + 1}**"
            )

    @commands.command(description="How good are my stats?", no_pm=True)
    async def ratio_ew(
        self,
        ctx,
        wins: int,
        kills: int,
        elims: int,
        deaths: int,
        games: int,
        eggs: int,
        placed: int,
        walked: int,
        day: int,
        hours: int,
        mins: int,
        sec: int,
    ):
        """
        A bunch of extra Eggwars statistics
        """
        w_l = round(wins / (games - wins), 3)
        w_lp = round(wins / games * 100, 3)
        if deaths == 0:
            deaths = 1
        k_d = round(kills / deaths, 3)
        e_d = round(elims / deaths, 3)
        k_gp = round(kills / games, 3)
        d_gp = round(deaths / games, 3)
        el_gp = round(elims / games, 3)
        eb_gp = round(eggs / games, 3)
        bw_gp = round(walked / games, 3)
        bp_gp = round(placed / games, 3)
        bp_bw = round(placed / walked, 3)
        sec_played = day * 86400 + hours * 3600 + mins * 60 + sec
        avl = sec_played / games
        avl_hour = int(avl / 3600)
        avl_min = int(avl / 60) % 3600
        avl_sec = int(avl) % 60
        winstime = sec_played / wins
        winstime_hour = int(winstime / 3600)
        winstime_min = int(winstime / 60) % 3600
        winstime_sec = int(winstime) % 60
        tpk = round(sec_played / kills, 3)
        tpk_hour = int(tpk / 3600)
        tpk_min = int(tpk / 60) % 3600
        tpk_sec = int(tpk) % 60
        if deaths == 0:
            tpd = round(sec_played / 1, 3)
        else:
            tpd = round(sec_played / deaths, 3)
        tpd_hour = int(tpd / 3600)
        tpd_min = int(tpd / 60) % 3600
        tpd_sec = int(tpd) % 60
        await ctx.send(
            (
                f"**{wins}** Wins - **{kills}** Kills - **{elims}** Eliminations - **{deaths}** Deaths -"
                f" **{games}** Games played - **{eggs}** Eggs destroyed - **{placed}** Blocks placed -"
                f" **{walked}** Distance walked - Playtime **{day}** days **{hours}** hours **{mins}**"
                f" minutes **{sec}** seconds"
                f"\n\nW/L = **{w_l}**\nW/L% = **{w_lp}**\nK/D = **{k_d}**\nE/D = **{e_d}** \nKills/Games Played = "
                f"**{k_gp}**\nDeaths/Games Played = **{d_gp}**\nEliminations/Games Played = **{el_gp}**"
                f"\nEggs Broken/Games Played = **{eb_gp}**\nBlocks Walked/Games Played = **{bw_gp}**"
                f"\nBlocks Placed/Games Played = **{bp_gp}**"
                f"\nBlocks Placed/Blocks Walked = **{bp_bw}**\nSeconds played - **{sec_played}**"
                f" seconds\nAverage game time - **{avl_hour}** hours **{avl_min}** minutes **{avl_sec}**"
                f" seconds\nWins time - **{winstime_hour}** hours **{winstime_min}** minutes"
                f" **{winstime_sec}** seconds"
                f"\nTime per kill - **{tpk_hour}** hours **{tpk_min}** minutes **{tpk_sec}** seconds"
                f"\nTime per death - **{tpd_hour}** hours **{tpd_min}** minutes **{tpd_sec}** seconds"
            )
        )

    @commands.command(description="How good are my stats?", no_pm=True)
    async def ratio_sw(
        self,
        ctx,
        wins: int,
        kills: int,
        deaths: int,
        games: int,
        shot: int,
        hit: int,
        broken: int,
        placed: int,
        walked: int,
        days: int,
        hours: int,
        mins: int,
        secs: int,
    ):
        """
        A bunch of extra Skywars statistics
        """
        w_l = round(wins / (games - wins), 3)
        w_lp = round(wins / games * 100, 3)
        k_d = round(kills / deaths, 3)
        k_gp = round(kills / games, 3)
        d_gp = round(deaths / games, 3)
        bw_gp = round(walked / games, 3)
        bp_gp = round(placed / games, 3)
        bb_gp = round(broken / games, 3)
        bp_bw = round(placed / walked, 3)
        sec_played = days * 86400 + hours * 3600 + mins * 60 + secs
        avl = sec_played / games
        avl_hour = int(avl / 3600)
        avl_min = int(avl / 60) % 3600
        avl_sec = int(avl) % 60
        winstime = sec_played / wins
        winstime_hour = int(winstime / 3600)
        winstime_min = int(winstime / 60) % 3600
        winstime_sec = int(winstime) % 60
        ah_as = round(hit / shot, 3)
        as_gp = round(shot / games, 3)
        ah_gp = round(hit / games, 3)
        tpk = round(sec_played / kills, 3)
        tpk_hour = int(tpk / 3600)
        tpk_min = int(tpk / 60) % 3600
        tpk_sec = int(tpk) % 60
        tpd = round(sec_played / deaths, 3)
        tpd_hour = int(tpd / 3600)
        tpd_min = int(tpd / 60) % 3600
        tpd_sec = int(tpd) % 60
        await ctx.send(
            f"**{wins}** Wins - **{kills}** Kills - **{deaths}** Deaths - **{games}**"
            f" Games played - **{shot}** Arrows shot - **{hit}** Arrows hit - **{broken}**"
            f" Blocks broken - **{placed}** Blocks placed - **{walked}** Distance walked - Playtime"
            f" **{days}** days **{hours}** hours **{mins}** minutes **{secs}** seconds\n\nW/L = **{w_l}"
            f"**\nW/L% = **{w_lp}**\nK/D = **{k_d}**\nKills/Games Played = **{k_gp}**\nDeaths/Games"
            f" Played = **{d_gp}**\nBlocks Walked/Games Played = **{bw_gp}**\nBlocks Placed/Games Played"
            f" = **{bp_gp}**\nBlocks broken/Games Played = **{bb_gp}**\nBlocks Placed/Blocks Walked ="
            f" **{bp_bw}**\nSeconds played - **{sec_played}** seconds\nAverage game time -"
            f" **{avl_hour}** hours **{avl_min}** minutes **{avl_sec}** seconds\nWins time -"
            f" **{winstime_hour}** hours **{winstime_min}** minutes **{winstime_sec}** seconds\n"
            f"Time per kill - **{tpk_hour}** hours **{tpk_min}** minutes **{tpk_sec}** seconds\n"
            f"Time per death - **{tpd_hour}** hours **{tpd_min}** minutes **{tpd_sec}** seconds\n"
            f"Arrows hit/Arrows Shot = **{ah_as}**\nArrows Shot/Games Played = **{as_gp}**\n"
            f"Arrows Hit/Games Played **{ah_gp}**"
        )


async def setup(bot: Botty) -> None:
    await bot.add_cog(CubeLvl(bot))
