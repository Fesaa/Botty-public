from typing import Optional
from discord.ext import commands
from discord.ui import View, button
from discord import ButtonStyle, Embed, app_commands, Interaction
from requests import get

from functions.config_handler import GUILD_IDS, Q_CHANNEL_ID, S_CHANNEL_ID

def get_uuid(ign: str) -> str:
    return get(f"https://minecraft-api.com/api/uuid/{ign}").content.decode()


def get_ign(uuid: str) -> str:
    return get(f"https://minecraft-api.com/api/pseudo/{uuid}").content.decode()

class ConflictOfInterest(View):

    def __init__(self,  bot: commands.Bot, timeout: Optional[float] = 180):
        super().__init__(timeout=timeout)
        self.bot = bot

    @button(label='Keep', style=ButtonStyle.green)
    async def keep(self, interaction, button):
        await interaction.message.delete()

    @button(label='Change', style=ButtonStyle.red)
    async def change(self, interaction, button):
        msg = interaction.message
        ign = msg.embeds[0].description.split("to ")[3].split('?')[0]
        uuid = get_uuid(ign)
        self.bot.db.connect_ign(interaction.user.id, uuid)
        await interaction.message.delete()
        await interaction.response.send_message(f"Connected you to **{ign}** with uuid: **{uuid}**", ephemeral=True)

class ignConnect(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.wrong_ign = 'Player not found !'
        super().__init__()

    @app_commands.command(
        name='connect_ign',
        description='Connect your Minecraft account'
    )
    @app_commands.guilds(GUILD_IDS[0])
    async def _connect(self, interaction: Interaction, ign: str):
        uuid = get_uuid(ign)

        if uuid == self.wrong_ign:
            await interaction.response.send_message("This ign does not exist, please use your current one. Capitals do **not** matter.", ephemeral=True)
        else:
            if stored_dc_id := self.bot.db.get_dc_id(uuid):
                if stored_dc_id == interaction.user.id:
                    await interaction.response.send_message("You are already connected to this ign!", ephemeral=True)
                else:
                    await interaction.response.send_message(embed=Embed(title="Conflict of intrest",
                                                                        description=f"<@{stored_dc_id}> is already connected to this Minecraft account ({ign}). Did you spell your ign wrong?"
                                                                                    f" If they have yours, ask them to change or ping Fesa"))
            elif stored_uuid := self.bot.db.get_uuid(interaction.user.id):

                await interaction.response.send_message(embed=Embed(title="Conflict of interest",
                                                                    description=f"Your discord account is connected to {get_ign(stored_uuid)}. Would you like to change to {ign}?"),
                                                                    view=ConflictOfInterest(self.bot))
            else:
                self.bot.db.connect_ign(interaction.user.id, uuid)
                await interaction.response.send_message(f"Connected you to **{ign}** with uuid: **{uuid}**")
    
    @app_commands.command(
        name="connected_ign",
        description="Display your currently connected ign"
    )
    @app_commands.guilds(GUILD_IDS[0])
    async def _connected_ign(self, interaction: Interaction):
        if uuid := self.bot.db.get_uuid(interaction.user.id):
            await interaction.response.send_message(f"You are remembered as: **{get_ign(uuid)}**.", ephemeral=True)
        else:
            await interaction.response.send_message("I do not know who you are, you can connect your ign with `!connect_ign <ign>`!", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(ignConnect(bot))