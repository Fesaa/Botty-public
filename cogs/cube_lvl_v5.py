from discord.ext import commands
from imports import clc
from math import ceil, sqrt
from cogs.config_handler import get_configdata


class cube_lvl(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.command(description="Which level will I be?", brief="lvl <level1>` to calculate the total amount of wins"
                                                                  " and experience needed for that specific level. ",
                      no_pm=True)
    async def lvl(self, ctx, levell: int):
        if ctx.channel.id in (await get_configdata(self.client, ctx.guild.id, "clvl_channel_id")):
            level = clc.Cubelvl(levell)
            await ctx.send((f"The total xp you need to reach level **{str(levell)}** is **{str(level())}**!\n"
                            f"That's the same as winning **{str(level.win('ew'))}** Eggwars games!\n"
                            f"That's the same as winning **{str(level.win('sw'))}** Skywars games!\n"
                            f"That's the same as winning **{str(level.win('li'))}** Lucky Island games!\n"
                            f"That's the same as **{str(level.win('mt'))}** thanks from a multiplier!\n"
                            f"Assume you get 400-700 thank a multiplier:\n"
                            f"You'd need **{str(ceil(clc.m(level(), 700)))}** - **{str(ceil(clc.m(level(), 400)))}**"
                            f" multipliers to reach the level!"))

    @commands.command(description="Which level will I be?", brief=f"xp <level1> <experience> <level2>` to calculate"
                                                                  f" the total amount of wins and experience needed"
                                                                  f" to reach level2.", no_pm=True)
    async def xp(self, ctx, levell1: int, xpnow: int, levell2: int):
        if ctx.channel.id in (await get_configdata(self.client, ctx.guild.id, "clvl_channel_id")):
            level1 = clc.Cubelvl(levell1)
            level2 = clc.Cubelvl(levell2)
            xp = level2() - (level1() + xpnow)
            levelx = clc.Cubelvl(clc.lvlxp(xp))
            await ctx.send((f"You still need **{xp}** xp to reach level **{str(level2)}**"
                            f"\nThat's the same as winning **{str(levelx.win('ew'))}** Eggwars games!"
                            f"\nThat's the same as winning **{str(levelx.win('sw'))}** Skywars games!"
                            f"\nThat's the same as winning **{str(levelx.win('li'))}** Lucky Island games!"
                            f"\nThat's the same as **{str(levelx.win('mt'))}** thanks from a multiplier!"
                            f"\nAssume you get 400-700 thank a multiplier: \nYou'd need "
                            f"**{str(ceil(clc.m(levelx(), 700)))}** - **{str(ceil(clc.m(levelx(), 400)))}**"
                            f" multipliers to reach the level!"))

    @commands.command(description="Which level will I be?", brief=f"mplvl <level1> <experience>"
                                                                  f" <Amount of multipliers> <Guessed thanks>`"
                                                                  f" to calculate the level you are going to be"
                                                                  f" after using some multipliers. ", no_pm=True)
    async def mplvl(self, ctx, levell: int, xpnow: int, amountmulti: int, tg: int):
        if ctx.channel.id in (await get_configdata(self.client, ctx.guild.id, "clvl_channel_id")):
            level = clc.Cubelvl(levell)
            levelx = clc.Cubelvl(clc.lvlxp(level() + xpnow))
            if clc.xpm(tg, amountmulti) < clc.xpm(400, amountmulti):
                await ctx.send((f"Assuming **{str(tg)}** /thank, you'll be level: **"
                                f"{str(levelx.levelafterxp(clc.xpm(tg, amountmulti)))}**"
                                f"\nAssuming **400** /thank, you'll be level: **"
                                f"{str(levelx.levelafterxp(clc.xpm(400, amountmulti)))}**"
                                f"\nAssuming **700** /thank, you'll be level: **"
                                f"{str(levelx.levelafterxp(clc.xpm(700, amountmulti)))}**"))
            elif clc.xpm(tg, amountmulti) < clc.xpm(700, amountmulti):
                await ctx.send((f"Assuming **400** /thank, you'll be level: **"
                                f"{str(levelx.levelafterxp(clc.xpm(400, amountmulti)))}**"
                                f"\nAssuming **{str(tg)}** /thank, you'll be level: **"
                                f"{str(levelx.levelafterxp(clc.xpm(tg, amountmulti)))}**"
                                f"\nAssuming **700** /thank, you'll be level: **"
                                f"{str(levelx.levelafterxp(clc.xpm(700, amountmulti)))}**"))
            elif clc.xpm(700, amountmulti) < clc.xpm(tg, amountmulti):
                await ctx.send((f"Assuming **400** /thank, you'll be level: **"
                                f"{str(levelx.levelafterxp(clc.xpm(400, amountmulti)))}**"
                                f"\nAssuming **700** /thank, you'll be level: **"
                                f"{str(levelx.levelafterxp(clc.xpm(700, amountmulti)))}**"
                                f"\nAssuming **{str(tg)}** /thank, you'll be level: **"
                                f"{str(levelx.levelafterxp(clc.xpm(tg, amountmulti)))}**"))

    @commands.command(description="Which level will I be?", brief=f"lvlmp <level1> <experience> <level2>"
                                                                  f" <Guessed thanks>` to calculate the needed amount"
                                                                  f" of multipliers to reach level2.", no_pm=True)
    async def lvlmp(self, ctx, level, xpnow, level2, tg):
        if ctx.channel.id in (await get_configdata(self.client, ctx.guild.id, "clvl_channel_id")):
            def lvl(x):  # x = level => total xp
                return 900 * int((x - 1)) + 100 * int((x - 1)) ** 2

            xp = lvl(int(level2)) - lvl(int(level)) - int(xpnow)

            def m(x):  # Amount of multipliers needed for a certain amount of xp with x /thanks
                return xp / (100 * x)

            if int(tg) < 400:
                await ctx.send(f"You'll need **{str(m(int(tg)))}** multipliers if you recieve "
                               f"**{str(tg)}** /thanks \nYou'll need **{str(m(400))}** multipliers if you recieve 400 "
                               f"/thanks \nYou'll need **{str(m(700))}** multipliers if you recieve 700 /thanks")
            elif int(tg) < 700:
                await ctx.send(f"You'll need **{str(m(400))}** multipliers if you recieve "
                               f"400 /thanks \nYou'll need **{str(m(int(tg)))}** multipliers if you recieve **{str(tg)}"
                               f"** /thanks \nYou'll need **{str(m(700))}** multipliers if you recieve 700 /thanks")
            elif 700 < int(tg):
                await ctx.send(f"You'll need **{str(m(400))}** multipliers if you recieve "
                               f"400 /thanks \nYou'll need **{str(m(700))}** multipliers if you recieve 700 /thanks \n"
                               f"You'll need **{str(m(int(tg)))}** multipliers if you recieve **{str(tg)}** /thanks")

    @commands.command(description="How much of my level comes from ...?", brief=" ", no_pm=True)
    async def stats(self, ctx, game: str, wins, played=None):
        if ctx.channel.id in (await get_configdata(self.client, ctx.guild.id, "clvl_channel_id")):
            if played is None:
                played = 0

            def lvlxp(x):  # xp = total xp => level
                return -9 / 2 + 1 / 10 * sqrt(2025 + x)

            if game == "tew" or game == "sew":
                xp = 250 * int(wins) + 5 * (int(played) - int(wins)) + 1 / 2 * int(played)
                await ctx.send(f"You have gained **{str(xp)}** experience with Eggwars,"
                               f" this is equivalent with level **{str(lvlxp(xp) + 1)}**")
            elif game == "tsw" or game == "ssw":
                xp = 125 * int(wins) + 5 * (int(played) - int(wins)) + 1 / 2 * int(played)
                await ctx.send(f"You have gained **{str(xp)}** experience with SkyWars,"
                               f" this is equivalent with level **{str(lvlxp(xp) + 1)}**")
            elif game == "tli" or game == "sli":
                xp = 120 * int(wins) + 5 * (int(played) - int(wins)) + 1 / 2 * int(played)
                await ctx.send(f"You have gained **{str(xp)}** experience with Lucky Islands,"
                               f" this is equivalent with level **{str(lvlxp(xp) + 1)}**")
            elif game == "td":
                xp = 150 * int(wins) + 5 * (int(played) - int(wins)) + 1 / 2 * int(played)
                await ctx.send(f"You have gained **{str(xp)}** experience with Tower Defence,"
                               f" this is equivalent with level **{str(lvlxp(xp) + 1)}**")
            elif game == "bwb":
                xp = 100 * int(wins) + 5 * (int(played) - int(wins)) + 1 / 2 * int(played)
                await ctx.send(f"You have gained **{str(xp)}** experience with BlockWars Bridges,"
                               f" this is equivalent with level **{str(lvlxp(xp) + 1)}**")
            elif game == "duels":
                xp = 10 * int(wins) + 1 / 2 * int(played)
                await ctx.send(f"You have gained **{str(xp)}** experience with Duels,"
                               f" this is equivalent with level **{str(lvlxp(xp) + 1)}**")
            elif game == "ffa":
                xp = 1 * int(wins)
                await ctx.send(f"You have gained **{str(xp)}** experience with Duels,"
                               f" this is equivalent with level **{str(lvlxp(xp) + 1)}**")
            else:
                await ctx.send((f"The game you entered does not exist, I know the following games:"
                                f"\n `tew,sew,tsw,ssw,tli,sli,td,bwb,duels,ffa`"
                                f"\n For among slimes use `.stats_as <wins> <completed tasks> <total played games>`"))

    @commands.command(description="How much of my level comes from ...?", brief=" ", no_pm=True)
    async def stats_as(self, ctx, wins, played, task):
        if ctx.channel.id in (await get_configdata(self.client, ctx.guild.id, "clvl_channel_id")):
            xp = 100 * int(wins) + 3 * int(task) + 2 / 3 * int(played) * 30 + 5 * (
                        int(played) - int(wins)) + 1 / 2 * int(played)

            def lvlxp(x):  # xp = total xp => level
                return -9 / 2 + 1 / 10 * sqrt(2025 + x)

            await ctx.send(f"You have gained **{str(xp)}** experience with Among Slimes,"
                           f" this is equivalent with level **{str(lvlxp(xp) + 1)}**")

    @commands.command(description="Which level will I be?", brief=f"exlvl <level1> <experience gained>`"
                                                                  f" to calculate which level you will be"
                                                                  f" after gaining some experience.", no_pm=True)
    async def exlvl(self, ctx, level: int, xpgain: int):
        if ctx.channel.id in (await get_configdata(self.client, ctx.guild.id, "clvl_channel_id")):
            def lvlxp(x):  # xp = total xp => level
                return -9 / 2 + 1 / 10 * sqrt(2025 + x)

            def lvl(x):  # x = level => total xp
                return 900 * (x - 1) + 100 * (x - 1) ** 2

            xp = lvl(int(level)) + int(xpgain)
            await ctx.send(f"You will be level **{str(lvlxp(xp) + 1)}** if you gain **{str(xpgain)}** experience")

    @commands.command(description="How good are my stats?", brief=f"ratio_ew <wins> <Kills> <Eliminations> <Deaths>"
                                                                  f" <Games played> <Eggs Broken> <Blocks placed>"
                                                                  f" <Blocks walked> <Days> <Hours> <Minutes> <Seconds>"
                                                                  f"` to calculate a bunch of interesting ratio's of"
                                                                  f" your Eggwars stats. ", no_pm=True)
    async def ratio_ew(self, ctx, wins: int, kills: int, elims: int, deaths: int, games: int, eggs: int, placed: int,
                       walked: int, day: int, hours: int, mins: int, sec: int):
        if ctx.channel.id in (await get_configdata(self.client, ctx.guild.id, "clvl_channel_id")):
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
            await ctx.send((f"**{wins}** Wins - **{kills}** Kills - **{elims}** Eliminations - **{deaths}** Deaths -"
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
                            f"\nTime per death - **{tpd_hour}** hours **{tpd_min}** minutes **{tpd_sec}** seconds"))

    @commands.command(description="How good are my stats?", brief=f"ratio_sw <Wins> <Kills> <Deaths> <Games Played>"
                                                                  f" <Arrows shot> <Arrows hit> <Blocks broken>"
                                                                  f" <Blocks placed> <Distance walked> <Days> <Hours>"
                                                                  f" <Minutes> <Seconds>` to calculate a bunch of"
                                                                  f" interesting ratio's of your Skywars stats. ",
                      no_pm=True)
    async def ratio_sw(self, ctx, wins: int, kills: int, deaths: int, games: int, shot: int, hit: int, broken: int,
                       placed: int, walked: int, days: int, hours: int, mins: int, secs: int):
        if ctx.channel.id in (await get_configdata(self.client, ctx.guild.id, "clvl_channel_id")):
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
            await ctx.send(f"**{wins}** Wins - **{kills}** Kills - **{deaths}** Deaths - **{games}**"
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
                           f"Arrows Hit/Games Played **{ah_gp}**")

    @commands.command(description="How good are my stats?", brief=f"ratio_td <Wins> <Games played> <Monsters killed>"
                                                                  f" <Monsters send> <Towers built> <Days> <Hours>"
                                                                  f" <Minutes> <Seconds>` to calculate a bunch of"
                                                                  f" interesting ratio's of your Tower Defence stats",
                      no_pm=True)
    async def ratio_td(self, ctx, wins: int, games: int, killed: int, sent: int, placed: int, days: int, hours: int,
                       mins: int, secs: int):
        if ctx.channel.id in (await get_configdata(self.client, ctx.guild.id, "clvl_channel_id")):
            w_l = round(wins / (games - wins), 3)
            w_lp = round(wins / games * 100, 3)
            s_gp = round(sent / games, 3)
            p_gp = round(placed / games, 3)
            k_gp = round(killed / games, 3)
            s_p = round((sent / 12) / placed, 3)
            k_s = round(killed / sent, 3)
            sec_played = days * 86400 + hours * 3600 + mins * 60 + secs
            avl = sec_played / games
            avl_hour = int(avl / 3600)
            avl_min = int(avl / 60) % 3600
            avl_sec = int(avl) % 60
            winstime = sec_played / wins
            winstime_hour = int(winstime / 3600)
            winstime_min = int(winstime / 60) % 3600
            winstime_sec = int(winstime) % 60
            tpk = round(sec_played / killed, 3)
            tpk_hour = int(tpk / 3600)
            tpk_min = int(tpk / 60) % 3600
            tpk_sec = int(tpk) % 60
            tps = round(sec_played / sent, 3)
            tps_hour = int(tps / 3600)
            tps_min = int(tps / 60) % 3600
            tps_sec = int(tps) % 60
            tpb = round(sec_played / placed, 3)
            tpb_hour = int(tpb / 3600)
            tpb_min = int(tpb / 60) % 3600
            tpb_sec = int(tpb) % 60
            await ctx.send(f"**{wins}** Wins - **{games}** Games - **{killed}** Troops killed - **{sent}**"
                           f" Troops sent - **{placed}** Towers built - Playtime **{days}** days **{hours}**"
                           f" hours **{mins}** minutes **{secs}** seconds\n\nW/L = **{w_l}**\nW/L% = **{w_lp}**\n"
                           f"Troops sent/Games Played = **{s_gp}**\nTowers Placed/Games Played = **{p_gp}**\n"
                           f"Troops Killed/Games Played = **{k_gp}**\nTroops Sent/Towers Placed = **{s_p}**\n"
                           f"Troops Killed/Troops Sent = **{k_s}**\nSeconds played - **{sec_played}** seconds\n"
                           f"Average game time - **{avl_hour}** hours **{avl_min}** minutes **{avl_sec}** seconds\n"
                           f"Wins time - **{winstime_hour}** hours **{winstime_min}** minutes **{winstime_sec}"
                           f"** seconds\nTime per troops killed - **{tpk_hour}** hours **{tpk_min}** minutes"
                           f" **{tpk_sec}** seconds\nTime per troops sent - **{tps_hour}** hours **{tps_min}**"
                           f" minutes **{tps_sec}** seconds\nTime per towers built - **{tpb_hour}** hours **{tpb_min}**"
                           f" minutes **{tpb_sec}** seconds")


def setup(client):
    client.add_cog(cube_lvl(client))
