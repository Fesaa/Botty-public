import discord

from discord.ext import commands
from discord.app_commands import AppCommandError

class ErrorHandler(commands.Cog):

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        super().__init__()
    
    async def on_app_command_error(self, interaction: discord.Interaction, error: AppCommandError):
        if isinstance(error, discord.app_commands.errors.MissingPermissions):
            await interaction.response.send_message('You are missing the necessary perms to use this command.', ephemeral=True)
        elif isinstance(error, discord.app_commands.errors.CommandNotFound):
            pass
        else:
            raise error
    
    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, exc):
        if isinstance(exc, commands.errors.CommandNotFound):
            pass
        elif isinstance(exc, commands.errors.MissingRequiredArgument):
            pass
        elif isinstance(exc, commands.errors.CheckFailure):
            pass
        else:
            raise exc

async def setup(bot: commands.Bot):
    await bot.add_cog(ErrorHandler(bot))