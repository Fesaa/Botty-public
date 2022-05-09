from typing import Optional
from discord import Attachment, ButtonStyle, Embed, SelectOption, TextStyle
from discord.ui import View, button, select, Modal, TextInput, Select
from discord.ext import commands
from discord import app_commands, Interaction
from discord.app_commands import Choice
from requests import get
from re import match

from functions.config_handler import GUILD_IDS, Q_CHANNEL_ID, S_CHANNEL_ID


def get_uuid(ign: str) -> str:
    return get(f"https://minecraft-api.com/api/uuid/{ign}").content.decode()


def get_ign(uuid: str) -> str:
    return get(f"https://minecraft-api.com/api/pseudo/{uuid}").content.decode()


async def sub_embed(uuid: str, loot_type: str, name: str, rarity: str, cubelet: str, discord_id: int, evidence_url: str, interaction: Interaction) -> Embed:
    embed = Embed(title=f"New loot item, please check if the given information is correct. If not, deny.",url=f"https://discord.com/channels/{interaction.guild_id}/{interaction.channel_id}/{(await interaction.original_message()).id}",
                  colour=0xad3998)

    embed.description = f"uuid={uuid}\n" \
                        f"loot_type={loot_type}\n" \
                        f"name={name}\n" \
                        f"rarity={rarity}\n" \
                        f"cubelet={cubelet}\n" \
                        f"id={discord_id}"
    
    embed.set_image(url=evidence_url)

    return embed

class EditRaritySelect(Select):

    def __init__(self, selected_rarity: str, bot: commands.Bot):

        self.bot = bot

        options=[
            SelectOption(label="Mythical", value="change_rarity_mythical", emoji="💎"),
            SelectOption(label="Legendary", value="change_rarity_legendary", emoji="✨"),
            SelectOption(label="Rare", value="change_rarity_rare", emoji="🎈"),
            SelectOption(label="Uncommon", value="change_rarity_uncommon", emoji="🧱"),
            SelectOption(label="Common", value="change_rarity_common", emoji="🪨"),
            SelectOption(label="Not applicable", value="change_rarity_no_rarity", emoji="⛔")
        ]

        options = [i for i in options if i.value[14:] != selected_rarity]

        super().__init__(custom_id='change_rarity', placeholder="Choose new rarity",options=options)
    
    async def callback(self, interaction: Interaction):
        new_rarity = interaction.data['values'][0][14:]
        msg = interaction.message

        em = msg.embeds[0]

        em.description = em.description.replace(match(r"uuid=\S{32}\nloot_type=\S*\nname=.*\nrarity=(\S*)\ncubelet=\S*\nid=\d*", em.description).group(1), new_rarity)

        await interaction.response.edit_message(embed=em, view=SubmissionButtons(self.bot))

class EditRarity(View):

    def __init__(self, bot: commands.Bot, selected_rarity: str, timeout: Optional[float] = None):
        super().__init__(timeout=timeout)
        self.bot = bot
        self.add_item(EditRaritySelect(selected_rarity, self.bot))

class EditCubeletSelect(Select):

    def __init__(self, selected_cubelet: str, bot: commands.Bot):

        self.bot = bot

        options=[
            SelectOption(label="Normal, Super or Uber Cubelet", value="change_cubelet_normal", emoji="🟪"),
            SelectOption(label="Winter Cubelet", value="change_cubelet_winter", emoji="🟥"),
            SelectOption(label="Summer Cubelet", value="change_cubelet_summer", emoji="🟨"),
            SelectOption(label="Halloween Cubelet", value="change_cubelet_halloween", emoji="🟫"),
            SelectOption(label="Spring Cubelet", value="change_cubelet_spring", emoji="🟦"),
            SelectOption(label="Pack or bundle", value="change_cubelet_pack_bundle", emoji="⬛"),
            SelectOption(label="Unobtainable", value="change_cubelet_unobtainable", emoji="⬛")
        ]

        options = [i for i in options if i.value[15:] != selected_cubelet]

        super().__init__(custom_id='change_cubelet', placeholder="Choose new cubelet", options=options)
    
    async def callback(self, interaction: Interaction):
        new_cubelet = interaction.data['values'][0][15:]
        msg = interaction.message

        em = msg.embeds[0]

        em.description = em.description.replace(match(r"uuid=\S{32}\nloot_type=\S*\nname=.*\nrarity=\S*\ncubelet=(\S*)\nid=\d*", em.description).group(1), new_cubelet)

        await interaction.response.edit_message(embed=em, view=SubmissionButtons(self.bot))


class EditCubelet(View):

    def __init__(self, bot: commands.Bot, selected_cubelet: str, timeout: Optional[float] = None):
        super().__init__(timeout=timeout)
        self.bot = bot

        self.add_item(EditCubeletSelect(selected_cubelet, self.bot))

class EditName(Modal):

    new_name = TextInput(label='New name', style=TextStyle.short)

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        super().__init__(title='Edit name of the submission')
    
    async def on_submit(self, interaction: Interaction) -> None:
        msg = interaction.message
        new_name = interaction.data['components'][0]['components'][0]['value']
        
        em = msg.embeds[0]
        em.description = em.description.replace(match(r"uuid=\S{32}\nloot_type=\S*\nname=(.*)\nrarity=\S*\ncubelet=\S*\nid=\d*", em.description).group(1), new_name)

        await interaction.response.edit_message(embed=em, view=SubmissionButtons(self.bot))
       

class SubmissionButtons(View):

    def __init__(self, bot: commands.Bot, timeout: Optional[float] = None):
        super().__init__(timeout=timeout)
        self.bot = bot

    @button(label='Accept', style=ButtonStyle.green)
    async def _accept(self, interaction: Interaction, button):
        msg = interaction.message
        info_list = [i.split("=") for i in msg.embeds[0].description.split("\n")]
        info = {}

        for entry in info_list:
            info[entry[0]] = entry[1]

        if data := self.bot.db.global_checker(loot_type=info['loot_type'], name=info['name']):
            if data[2] != info['rarity']:
                if data[2] == "no_rarity":
                    rarity = info['rarity']
                else:
                    rarity = data[2]
            else:
                rarity = info['rarity']
        else:
            rarity = info['rarity']

        self.bot.db.add_global_loot(loot_type=info['loot_type'], name=info['name'], rarity=rarity,
                                       cubelet=info['cubelet'])
        self.bot.db.add_player_loot(uuid=info['uuid'], loot_type=info['loot_type'], name=info['name'],
                                       rarity=info['rarity'], cubelet=info['cubelet'])

        await msg.delete()
        await self.bot.get_channel(S_CHANNEL_ID).send(f"<@{info['id']}>. Your submission for {info['name']} has been accepted!\n{msg.embeds[0].url}")
    
    @button(label='Edit Rarity', style=ButtonStyle.gray)
    async def edit_rarity(self, interaction: Interaction, button):
        msg = interaction.message
        await interaction.response.edit_message(embed=msg.embeds[0], view=EditRarity(self.bot, match(r"uuid=\S{32}\nloot_type=\S*\nname=.*\nrarity=(\S*)\ncubelet=\S*\nid=\d*", msg.embeds[0].description).group(1)))

    @button(label='Edit Cubelet', style=ButtonStyle.gray)
    async def edit_cubelet(self, interaction: Interaction, button):
        msg = interaction.message
        await interaction.response.edit_message(embed=msg.embeds[0], view=EditCubelet(self.bot, match(r"uuid=\S{32}\nloot_type=\S*\nname=.*\nrarity=\S*\ncubelet=(\S*)\nid=\d*", msg.embeds[0].description).group(1)))
    
    @button(label='Edit Name', style=ButtonStyle.gray)
    async def edit_name(self, interaction: Interaction, button):
        await interaction.response.send_modal(EditName(self.bot))

    @button(label='Deny', style=ButtonStyle.red)
    async def deny(self, interaction: Interaction, button):
        msg = interaction.message
        info_list = [i.split("=") for i in msg.embeds[0].description.split("\n")]
        info = {}
        for entry in info_list:
            info[entry[0]] = entry[1]

        await msg.delete()
        await self.bot.get_channel(S_CHANNEL_ID).send(f"<@{info['id']}>. Your submission for {info['name']} has been denied.\n{msg.embeds[0].url}")


class ManualSubmission(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.wrong_ign = 'Player not found !'

    @app_commands.command(
        name="submit",
        description="Submit a loot item, evidence can be send in an extra message underneath this command."
    )
    @app_commands.guilds(GUILD_IDS[0])
    @app_commands.choices(
        loot_type=[
            Choice(name="Cage", value="cage"),
            Choice(name="Hat", value="hat"),
            Choice(name="Win effect", value="win_effect"),
            Choice(name="Wardrobe", value="wardrobe"),
            Choice(name="Egg break message", value="egg_break"),
            Choice(name="Miniature", value="miniature"),
            Choice(name="Shield", value="shield"),
            Choice(name="Banner", value="banner"),
            Choice(name="Arrow trail", value="arrow_trail"),
            Choice(name="Gadget", value="gadget"),
            Choice(name="Balloon", value="balloon"),
            Choice(name="Trail", value="trail")
        ],
        rarity=[
            Choice(name="Mythical", value="mythical"),
            Choice(name="Legendary", value="legendary"),
            Choice(name="Rare", value="rare"),
            Choice(name="Uncommon", value="uncommon"),
            Choice(name="Common", value="common"),
            Choice(name="Not applicable", value="no_rarity")
        ],
        cubelet = [
            Choice(name="Normal, Super or Uber cubelet", value="normal"),
            Choice(name="Winter Cubelet", value="winter"),
            Choice(name="Summer Cubelet", value="summer"),
            Choice(name="Halloween Cubelet", value="halloween"),
            Choice(name="Spring Cubelet", value="spring"),
            Choice(name="Pack or bundle", value="pack_bundle"),
            Choice(name="Unobtainable", value="unobtainable")
        ]
    )
    async def _submit(self, interaction: Interaction, loot_type: str, name: str, rarity: str, cubelet: str, evidence: Attachment):

        if (uuid := self.bot.db.get_uuid(interaction.user.id)):
            await interaction.response.send_message("Your submission has been forwarded!")
            await self.bot.get_channel(Q_CHANNEL_ID).send(embed= await sub_embed(
                uuid=uuid, loot_type=loot_type, name=name, rarity=rarity, cubelet=cubelet, discord_id=interaction.user.id, evidence_url=evidence.url, interaction=interaction),
                view=SubmissionButtons(self.bot))

async def setup(bot: commands.Bot):
    await bot.add_cog(ManualSubmission(bot))