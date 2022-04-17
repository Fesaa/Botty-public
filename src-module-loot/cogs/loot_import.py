from discord import Attachment
from discord.ext import commands
from discord import app_commands, Interaction
from discord.app_commands import Choice

from functions.config_handler import GUILD_IDS


def decode(s, encoding="utf-8", errors="ignore"):
    return s.decode(encoding=encoding, errors=errors)


class LootImport(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name='loot',
        description='Mass import .csv file from the Minecraft mod. '
    )
    @app_commands.describe(
        loot_type='Loot type of the items you are currently submitting.',
        f1='.csv file, you can add up to 4 extra files by using the optional arguments.',
        f5='Blame discord for having a 5 limit >:('
    )
    @app_commands.choices(
        loot_type=[
            Choice(name='Hats', value='hat'),
            Choice(name='Banners', value='banner'),
            Choice(name='Wardrobe items', value='wardrobe'),
            Choice(name='Win Effects', value='win_effect'),
            Choice(name='Egg Break Messages', value='egg_break'),
            Choice(name='Cages', value='cage'),
            Choice(name='Shields', value='shield'),
            Choice(name='Miniatures', value='miniature'),
            Choice(name='Balloons', value='balloon'),
            Choice(name='Arrow Trails', value='arrow_trail'),
            Choice(name='Trails', value='trail'),
            Choice(name='Gadgets', value='gadget'),
        ]
    )
    @app_commands.rename(
        f1='file-1',
        f2='file-2',
        f3='file-3',
        f4='file-4',
        f5='file-5',
    )
    @app_commands.guilds(GUILD_IDS[0])
    async def _loot(self, interaction: Interaction, loot_type: str, f1: Attachment, f2: Attachment = None,
                    f3: Attachment = None, f4: Attachment = None, f5: Attachment = None):

        csv_file = True
        if not f1.filename.endswith('.csv'):
            csv_file = False
        if f2:
            if not f2.filename.endswith('.csv'):
                csv_file = False
        if f3:
            if not f3.filename.endswith('.csv'):
                csv_file = False
        if f4:
            if not f4.filename.endswith('.csv'):
                csv_file = False
        if f5:
            if not f5.filename.endswith('.csv'):
                csv_file = False

        if csv_file:
            raw_data = ''
            raw_data += decode(await f1.read())
            if f2:
                raw_data += decode(await f2.read())
            if f3:
                raw_data += decode(await f3.read())
            if f4:
                raw_data += decode(await f4.read())
            if f5:
                raw_data += decode(await f5.read())

            raw_list = [i.split(',') for i in raw_data.split('\n')]

            import_list = []

            for loot_item in raw_list:
                if len(loot_item) != 1:
                    if not ((loot_item[1] in ['Randomise', 'Back', 'Remove Helmet', 'Remove Chestplate',
                                              'Remove Leggings', 'Remove Boots', 'Unequip wardrobe items',
                                              'Next page', 'Previous page']) or loot_item[1].__contains__(
                                                'Ordered by') or loot_item[1].__contains__(
                                                'Remove') or loot_item[1].__contains__(
                                                'Reset') or loot_item[2].__contains__(
                                                'This item is locked') or loot_item[1].__contains__(
                                                'Equip all') or loot_item[2].__contains__("Reset")):

                        if loot_item[2].__contains__('Rarity'):
                            rarity = loot_item[2].split('Rarity: ')[1].split(';')[0].lower()
                        else:
                            rarity = 'no_rarity'

                        if loot_item[2].__contains__('Found in a'):
                            raw_cubelet = loot_item[2].split('Found in ')[1].split(' ')[1].split(';')[0].lower()

                            cubelet = {
                                'uber': 'normal',
                                'super': 'normal',
                                'cubelet': 'normal',
                                'summer': 'summer',
                                'winter': 'winter',
                                'halloween': 'halloween',
                                'spring': 'spring'
                            }[raw_cubelet]

                        elif loot_item[2].__contains__('Unlocked with'):
                            cubelet = 'pack_bundle'
                        else:
                            cubelet = 'unobtainable'

                        a = {
                            'type': loot_type,
                            'name': loot_item[1],
                            'rarity': rarity,
                            'cubelet': cubelet
                        }

                        import_list.append(a)

            self.bot.db.import_global_loot(import_list)
            if uuid := self.bot.db.get_uuid(interaction.user.id):
                self.bot.db.import_player_loot(import_list, uuid)
            else:
                await interaction.response.send_message("Unable to add to your personal loot list since your dc account"
                                                        " is not connected. Please connect with `!connect_ign <ign>`")

            await interaction.response.send_message("Submission processed.")

        else:
            await interaction.response.send_messag('Please only attach .csv files found in the iexport folder.',
                                                   ephemeral=True)


async def setup(bot):
    await bot.add_cog(LootImport(bot))
