from discord.ext import commands
from discord import Interaction, app_commands, Object
from math import ceil, sqrt
from imports import clc


class CubeLvlHandler(commands.Cog):

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        super().__init__()
        CubeLvlHandler.bot = self.bot
        self.bot.tree.add_command(self.CubeLvl())
    

    class CubeLvl(app_commands.Group, name='cubelvl', description='Your personal Cubecraft calculator!'):

        def __init__(self, *args, **kwargs) -> None:
            super().__init__(*args, **kwargs)
            self.bot = CubeLvlHandler.bot
        
        @app_commands.command(name='level', description='Calculate difference between two levels (Default: Difference with level 1)')
        @app_commands.rename(
            level1='current_level',
            level2='level_to_be'
        )
        async def _level(self, interaction: Interaction, level2: int, level1: int = 1, current_xp: int = 0):
            lvl1 = clc.Cubelvl(level1)
            lvl2 = clc.Cubelvl(level2)
            xp = lvl2() - (lvl1() + current_xp)
            levelx = clc.Cubelvl(clc.lvlxp(xp))
            await interaction.response.send_message(
                f"You still need **{xp}** xp to reach level **{level2}** from level **{level1}**"
                f"\nThat's the same as winning **{levelx.win('ew')}** Eggwars games!"
                f"\nThat's the same as winning **{levelx.win('sw')}** Skywars games!"
                f"\nThat's the same as winning **{levelx.win('li')}** Lucky Island games!"
                f"\nThat's the same as **{levelx.win('mt')}** thanks from a multiplier!"
                f"\nAssume you get 400-700 thank a multiplier: \nYou'd need "
                f"**{ceil(clc.m(levelx(), 700))}** - **{ceil(clc.m(levelx(), 400))}**"
                f" multipliers to reach the level!"
            )
        @app_commands.command(name='multies', description='Calculate which level you will be after using multies, or how many multies you need.')
        @app_commands.choices(
            action= [
                app_commands.Choice(name='level',value='level'),
                app_commands.Choice(name='multies', value='multies')
            ]
        )
        @app_commands.rename(
            var='level_multies',
            tg='guessed_thanks'
        )
        @app_commands.describe(
            var='Amount of multiepliers, or level you want to be'
        )
        async def _multies(self, interaction: Interaction, action: str, current_lvl: int, current_xp: int, var: int, tg: int):
            if action == 'level':
                def lvl(x):  # x = level => total xp
                    return 900 * int((x - 1)) + 100 * int((x - 1)) ** 2

                xp = lvl(int(var)) - lvl(int(current_lvl)) - int(current_xp)

                def m(x):  # Amount of multipliers needed for a certain amount of xp with x /thanks
                    return ceil(xp / (100 * x))
                if tg < 400:
                    await interaction.response.send_message(f"You'll need **{m(int(tg))}** multipliers if you receive "
                                                            f"**{tg}** /thanks \nYou'll need **{m(400)}** multipliers if you receive **400** "
                                                            f"/thanks \nYou'll need **{m(700)}** multipliers if you receive **700** /thanks")
                elif tg < 700:
                    await interaction.response.send_message(f"You'll need **{m(400)}** multipliers if you receive "
                                                            f"**400** /thanks \nYou'll need **{m(int(tg))}** multipliers if you receive **{tg}"
                                                            f"** /thanks \nYou'll need **{m(700)}** multipliers if you receive **700** /thanks")
                elif 700 < tg:
                    await interaction.response.send_message(f"You'll need **{m(400)}** multipliers if you receive "
                                                            f"**400** /thanks \nYou'll need **{m(700)}** multipliers if you receive **700** /thanks \n"
                                                            f"You'll need **{m(int(tg))}** multipliers if you receive **{tg}** /thanks")
                elif tg == 400 or tg == 700:
                    await interaction.response.send_message(f"You'll need **{m(400)}** multipliers if you receive "
                                                            f"**400** /thanks \nYou'll need **{m(700)}** multipliers if you receive **700** /thanks")

        
            elif action == 'multies':

                level = clc.Cubelvl(current_lvl)
                levelx = clc.Cubelvl(clc.lvlxp(level() + current_xp))
                if clc.xpm(tg, var) < clc.xpm(400, var):
                    await interaction.response.send_message((f"Assuming **{tg}** /thank, you'll be level: **"
                                                            f"{levelx.levelafterxp(clc.xpm(tg, var))}*"
                                                            f"\nAssuming **400** /thank, you'll be level: **"
                                                            f"{levelx.levelafterxp(clc.xpm(400, var))}**"
                                                            f"\nAssuming **700** /thank, you'll be level: **"
                                                            f"{levelx.levelafterxp(clc.xpm(700, var))}**"))
                elif clc.xpm(tg, var) < clc.xpm(700, var):
                    await interaction.response.send_message((f"Assuming **400** /thank, you'll be level: **"
                                                            f"{levelx.levelafterxp(clc.xpm(400, var))}**"
                                                            f"\nAssuming **{tg}** /thank, you'll be level: **"
                                                            f"{levelx.levelafterxp(clc.xpm(tg, var))}**"
                                                            f"\nAssuming **700** /thank, you'll be level: **"
                                                            f"{levelx.levelafterxp(clc.xpm(700, var))}**"))
                elif clc.xpm(700, var) < clc.xpm(tg, var):
                    await interaction.response.send_message((f"Assuming **400** /thank, you'll be level: **"
                                                            f"{levelx.levelafterxp(clc.xpm(400, var))}**"
                                                            f"\nAssuming **700** /thank, you'll be level: **"
                                                            f"{levelx.levelafterxp(clc.xpm(700, var))}**"
                                                            f"\nAssuming **{tg}** /thank, you'll be level: **"
                                                            f"{levelx.levelafterxp(clc.xpm(tg, var))}**"))
                elif clc.xpm(700, var) == clc.xpm(tg, var) or clc.xpm(400, var) == clc.xpm(tg, var):
                    await interaction.response.send_message((f"Assuming **400** /thank, you'll be level: **"
                                                            f"{levelx.levelafterxp(clc.xpm(400, var))}**"
                                                            f"\nAssuming **700** /thank, you'll be level: **"
                                                            f"{levelx.levelafterxp(clc.xpm(700, var))}**"))

        @app_commands.command(name='stats', description='How much of my level comes from ...?')
        @app_commands.choices(
            game = [
                app_commands.Choice(name="EggWars", value="ew"),
                app_commands.Choice(name="SkyWars", value='sw'),
                app_commands.Choice(name="Lucky Islands", value="li"),
                app_commands.Choice(name="Tower Defense", value='td'),
                app_commands.Choice(name="BlockWars", value='bwb'),
                app_commands.Choice(name="Duels", value="duels"),
                app_commands.Choice(name="Free For All", value="ffa"),
                app_commands.Choice(name="Among Slimes", value="as")
            ]
        )    
        async def _stats(self, interaction: Interaction, game: str, wins: int, games_played: int = 0, tasks_completed: int = None):
            def lvlxp(x):  # xp = total xp => level
                return round(-9 / 2 + 1 / 10 * sqrt(2025 + x))

            if game == "ew":
                xp = 250 * int(wins) + 5 * (int(games_played) - int(wins)) + 1 / 2 * int(games_played)
                await interaction.response.send_message(f"You have gained **{str(xp)}** experience in Eggwars,"
                                                        f" this is equivalent with level **{str(lvlxp(xp) + 1)}**")
            elif game == "sw":
                xp = 125 * int(wins) + 5 * (int(games_played) - int(wins)) + 1 / 2 * int(games_played)
                await interaction.response.send_message(f"You have gained **{str(xp)}** experience in SkyWars,"
                                                         f" this is equivalent with level **{str(lvlxp(xp) + 1)}**")
            elif game == "li":
                xp = 120 * int(wins) + 5 * (int(games_played) - int(wins)) + 1 / 2 * int(games_played)
                await interaction.response.send_message(f"You have gained **{str(xp)}** experience in Lucky Islands,"
                                                        f" this is equivalent with level **{str(lvlxp(xp) + 1)}**")
            elif game == "td":
                xp = 150 * int(wins) + 5 * (int(games_played) - int(wins)) + 1 / 2 * int(games_played)
                await interaction.response.send_message(f"You have gained **{str(xp)}** experience in Tower Defense,"
                                                        f" this is equivalent with level **{str(lvlxp(xp) + 1)}**")
            elif game == "bwb":
                xp = 100 * int(wins) + 5 * (int(games_played) - int(wins)) + 1 / 2 * int(games_played)
                await interaction.response.send_message(f"You have gained **{str(xp)}** experience in BlockWars Bridges,"
                                                        f" this is equivalent with level **{str(lvlxp(xp) + 1)}**")
            elif game == "duels":
                xp = 10 * int(wins) + 1 / 2 * int(games_played)
                await interaction.response.send_message(f"You have gained **{str(xp)}** experience in Duels,"
                                                        f" this is equivalent with level **{str(lvlxp(xp) + 1)}**")
            elif game == "ffa":
                xp = 1 * int(wins)
                await interaction.response.send_message(f"You have gained **{str(xp)}** experience in Duels,"
                                                        f" this is equivalent with level **{str(lvlxp(xp) + 1)}**")
            elif game == "as":
                xp = 100 * int(wins) + 3 * int(tasks_completed) + 2 / 3 * int(games_played) * 30 + 5 * (
                        int(games_played) - int(wins)) + 1 / 2 * int(games_played)

                await interaction.response.send_message(f"You have gained **{str(xp)}** experience in Among Slimes,"
                                                        f" this is equivalent with level **{str(lvlxp(xp) + 1)}**")


    @commands.command(description="How good are my stats?", brief=f"ratio_ew <wins> <Kills> <Eliminations> <Deaths>"
                                                                  f" <Games played> <Eggs Broken> <Blocks placed>"
                                                                  f" <Blocks walked> <Days> <Hours> <Minutes> <Seconds>"
                                                                  f"` to calculate a bunch of interesting ratio's of"
                                                                  f" your Eggwars stats. ", no_pm=True)
    async def ratio_ew(self, ctx, wins: int, kills: int, elims: int, deaths: int, games: int, eggs: int, placed: int,
                       walked: int, day: int, hours: int, mins: int, sec: int):
        if ctx.channel.id in self.bot.db.get_channel('CubeLvl'):
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
        if ctx.channel.id in self.bot.db.get_channel('CubeLvl'):
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


async def setup(bot: commands.Bot):
    await bot.add_cog(CubeLvlHandler(bot))