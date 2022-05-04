from datetime import datetime
from discord import Embed, File
from discord.ext import commands
from discord import app_commands, Interaction
from discord.app_commands import Choice
from requests import get

from functions.config_handler import GUILD_IDS


def get_uuid(ign: str):
    return get(f"https://minecraft-api.com/api/uuid/{ign}").content.decode()


def get_ign(uuid: str):
    return get(f"https://minecraft-api.com/api/pseudo/{uuid}").content.decode()


LOOT_TYPE_SWITCHER = {
    'hat': 'Hats',
    'cage': 'Cages',
    'trail': 'Trails',
    'banner': 'Banners',
    'gadget': 'Gadgets',
    'shield': 'Shields',
    'balloon': 'Balloons',
    'wardrobe': 'Wardrobe',
    'miniature': 'Miniatures',
    'win_effect': 'Win Effects',
    'arrow_trail': 'Arrow Trails',
    'egg_break': 'Egg Break Messages'
}

LOOT_RARITY_SWITCHER = {
    'mythical': 'Mythical',
    'legendary': 'Legendary',
    'rare': 'Rare',
    'uncommon': 'Uncommon',
    'common': 'Common',
    'no_rarity': 'No rarity'
}

LOOT_CUBELET_SWITCHER = {
    'normal': 'Normal, super or uber',
    'halloween': 'Halloween',
    'winter': 'Winter',
    'spring': 'Spring',
    'summer': 'Summer',
    'unobtainable': 'No longer obtainable',
    'pack_bundle': 'Unlocked with a pack, bundle or rank'
}


class StatsFetcher(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.wrong_ign = 'Player not found !'

    @app_commands.command(
        name="reconnect",
        description="Reconnect to the database, use this if other commands aren't working.",
    )
    @app_commands.guilds(GUILD_IDS[0])
    async def _reconnect(self, interaction: Interaction):
        self.bot.db.reconnect()
        await interaction.response.send_message("Reconnected, feel free to try the other commands again!",
                                                ephemeral=True)

    @app_commands.command(
        name="player_lookup",
        description="Fetches all loot items of a certain player. Returns a .txt file."
    )
    @app_commands.guilds(GUILD_IDS[0])
    @app_commands.describe(ign='In game name of the player, defaults to yourself')
    async def _player_lookup(self, interaction: Interaction, ign: str = None):

        if ign is None:
            uuid = self.bot.db.get_uuid(interaction.user.id)
            ign = get_ign(uuid)

        if (uuid := get_uuid(ign)) != self.wrong_ign:
            print(uuid)
            print(self.wrong_ign)
            if data := self.bot.db.get_player_loot(uuid):

                current_type = None
                c = 0

                with open(f'./cogs/player_loot_txt/{interaction.user.id}.txt', 'w+') as f:

                    f.write(f"==============================\n"
                            f"Loot items of {ign}. Creation date: {datetime.now().strftime('%d/%m/%y')}\n"
                            f"Total loot items: {len(data)}\n"
                            f"NAME, RARITY, CUBELET\n")

                    for loot_item in data:
                        if current_type == loot_item[1]:
                            c += 1
                            f.write(f"{loot_item[2]}, {loot_item[3]}, {loot_item[4]}\n")
                        else:
                            old_type = current_type
                            current_type = loot_item[1]

                            to_write = f"==============================\n" \
                                       f"New loot type: {current_type}\n" \
                                       f"==============================\n" \
                                       f"{loot_item[2]}, {loot_item[3]}, {loot_item[4]}\n"

                            if old_type:
                                to_write = f"Total {old_type} loot: {c}\n" + to_write

                            f.write(to_write)
                            c = 1

                    f.write(f"Total {old_type} loot: {c}")

                with open(f'./cogs/player_loot_txt/{interaction.user.id}.txt', 'rb') as f:
                    await interaction.response.send_message(f"Loot items of {ign} in txt format:",
                                                            file=File(f, f'loot_{ign}.txt'))
            else:
                await interaction.response.send_message(f"No known loot of this user ({ign})", ephemeral=True)
        else:
            await interaction.response.send_message(f"Invalid ign ({ign}),"
                                                    f" must be there current ign. Capitals do not matter.",
                                                    ephemeral=True)

    @app_commands.command(
        name="missing_item",
        description="Returns all missing items of a player."
    )
    @app_commands.describe(ign='In game name of the player, defaults to yourself',
                           unobtainable='Count no longer obtainable items, defaults to False.',
                           pack_bundle_rank='Count item received by purchasing a rank/bundle/pack, defaults to False')
    @app_commands.guilds(GUILD_IDS[0])
    async def _missing_item(self, interaction: Interaction, ign: str = None, unobtainable: bool = False,
                            pack_bundle_rank: bool = False):

        if not ign:
            uuid = self.bot.db.get_uuid(interaction.user.id)
            ign = get_ign(uuid)
        else:
            uuid = get_uuid(ign)

        if uuid == self.wrong_ign:
            await interaction.response.send_message(f"Invalid ign ({ign}), must be there current ign. Capitals do not matter.",
                                                    ephemeral=True)
        else:

            if self.bot.db.check_in_system(uuid):
                missing_loot = self.bot.db.missing_player_loot(uuid, unobtainable, pack_bundle_rank)

                if missing_loot:

                    current_type = None
                    c = 0

                    with open(f'./cogs/missing_player_loot_txt/{interaction.user.id}.txt', 'w+') as f:

                        f.write(f"==============================\n"
                                f"Missing loot items of {ign}. Creation date: {datetime.now().strftime('%d/%m/%y')}\n"
                                f"Total loot items: {len(missing_loot)}\n"
                                f"NAME, RARITY, CUBELET\n")

                        counter_rarity = {
                            'mythical': 0,
                            'legendary': 0,
                            'rare': 0,
                            'uncommon': 0,
                            'common': 0,
                            'no_rarity': 0
                        }

                        counter_cubelet = {
                            'normal': 0,
                            'halloween': 0,
                            'winter': 0,
                            'spring': 0,
                            'summer': 0,
                            'unobtainable': 0,
                            'pack_bundle': 0

                        }

                        counter_type = {
                            'hat': 0,
                            'cage': 0,
                            'trail': 0,
                            'banner': 0,
                            'gadget': 0,
                            'shield': 0,
                            'balloon': 0,
                            'wardrobe': 0,
                            'miniature': 0,
                            'win_effect': 0,
                            'arrow_trail': 0,
                            'egg_break': 0
                        }

                        for loot_item in missing_loot:

                            counter_type[loot_item[0]] += 1
                            counter_rarity[loot_item[2]] += 1
                            counter_cubelet[loot_item[3]] += 1

                            if current_type == loot_item[0]:
                                c += 1
                                f.write(f"{loot_item[1]}, {loot_item[2]}, {loot_item[3]}\n")
                            else:
                                old_type = current_type
                                current_type = loot_item[0]

                                to_write = f"==============================\n" \
                                           f"New loot type: {current_type}\n" \
                                           f"==============================\n" \
                                           f"{loot_item[1]}, {loot_item[2]}, {loot_item[3]}\n"

                                if old_type:
                                    to_write = f"Total {old_type} loot: {c}\n" + to_write

                                f.write(to_write)
                                c = 1

                    e = Embed(title="Quick overview of missing items", colour=0xad3998)

                    val1 = ""
                    for rarity, count in counter_rarity.items():
                        val1 += f"{LOOT_RARITY_SWITCHER[rarity]}: **{count}**\n"
                    e.add_field(name="Rarities", value=val1)

                    val2 = ""
                    for cubelet, count in counter_cubelet.items():
                        val2 += f"{LOOT_CUBELET_SWITCHER[cubelet]}: **{count}**\n"
                    e.add_field(name="Cubelets", value=val2)

                    val3 = ""
                    for loot_type, count in counter_type.items():
                        val3 += f"{LOOT_TYPE_SWITCHER[loot_type]}: **{count}**\n"
                    e.add_field(name="Type", value=val3)

                    with open(f'./cogs/missing_player_loot_txt/{interaction.user.id}.txt', 'rb') as f:
                        await interaction.response.send_message(f"Missing loot items of {ign} in txt format:",
                                                                file=File(f, f'missing_loot_{ign}.txt'), embed=e)

                else:
                    await interaction.response.send_message(f"🎉 **{ign}** has everything in the database! 🎉")

            else:
                await interaction.response.send_message("No known loot for this user.", ephemeral=True)

    @app_commands.command(
        name="report",
        description="Create a report (stats) for the global database or a player. Defaults to yourself"
    )
    @app_commands.guilds(GUILD_IDS[0])
    @app_commands.choices(
        order=[
            Choice(name='Rarity', value='rarity'),
            Choice(name='Cubelet', value='cubelet')
        ]
    )
    @app_commands.describe(order='Order on rarity or cubelet kind',
                           global_loot='Create a report for all known loot (Will overwrite player choices)',
                           ign='In game name of the player, defaults to yourself')
    async def _report(self, interaction: Interaction, order: str, global_loot: bool = False, ign: str = None):

        if ign is None:
            uuid = self.bot.db.get_uuid(interaction.user.id)
        else:
            uuid = get_uuid(ign)

        if global_loot:
            loot_dict = self.bot.db.report(order, 'global')
            title = "Global report"
        else:
            loot_dict = self.bot.db.report(order, 'player', uuid)
            title = f"Player report of {get_ign(uuid)}"

        e = Embed(title=title, colour=0xad3998)
        for loot_type, count_dict in loot_dict.items():
            desc = ""
            c = 0
            for order_type, count in count_dict.items():
                c += count
                desc += f"{order_type}: **{count}**\n"

            desc = f"**Total: {c}**\n" + desc
            e.add_field(name=LOOT_TYPE_SWITCHER[loot_type], value=desc)

        await interaction.response.send_message(embed=e)


async def setup(bot):
    await bot.add_cog(StatsFetcher(bot))
