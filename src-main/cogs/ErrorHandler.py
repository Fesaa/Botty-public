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
            if channel := self.bot.get_channel(870011461194354738):
                await channel.send(f'<@&996004219792400405> Error occurred!', embed=discord.Embed(title="Error!", description=error))
            raise error
    
    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, exc: commands.CommandError):

        if isinstance(exc, commands.CommandInvokeError):
            exc = exc.original

        if isinstance(exc, commands.errors.CommandNotFound):
            pass
        elif isinstance(exc, commands.errors.MissingRequiredArgument):
            pass
        elif isinstance(exc, commands.errors.CheckFailure):
            pass
        else:
            if channel := self.bot.get_channel(870011461194354738):
                e = discord.Embed(title="Error!", description=f'{type(exc)}\n{exc}', timestamp=discord.utils.utcnow(), colour=0xad3998)
                e.add_field(name="Channel", value=ctx.channel.mention)
                e.set_footer(text=f"Error by {ctx.author}", icon_url=ctx.author.avatar.url)
                await channel.send(f'<@&996004219792400405>', embed=e)
            raise exc

async def setup(bot: commands.Bot):
    await bot.add_cog(ErrorHandler(bot))