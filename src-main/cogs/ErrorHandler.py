import discord

from discord import Embed
from discord.ext import commands
from discord.app_commands import AppCommandError

from Botty import Botty


class ErrorHandler(commands.Cog):
    def __init__(self, bot: Botty) -> None:
        self.bot = bot
        super().__init__()

    async def on_app_command_error(
        self, interaction: discord.Interaction, error: AppCommandError
    ):
        if isinstance(error, discord.app_commands.errors.MissingPermissions):
            await interaction.response.send_message(
                "You are missing the necessary perms to use this command.",
                ephemeral=True,
            )
        elif isinstance(error, discord.app_commands.errors.CommandNotFound):
            pass
        else:
            if channel := self.bot.get_channel(870011461194354738):
                e = Embed(
                    title="Error!",
                    description=f"{error.__class__.__name__}: {error}",
                    timestamp=discord.utils.utcnow(),
                    colour=0xAD3998,
                )
                if isinstance(interaction.channel, discord.abc.GuildChannel):
                    e.add_field(name="Channel", value=interaction.channel.mention)
                if interaction.user.avatar:
                    e.set_footer(
                        text=f"Error by {interaction.user}",
                        icon_url=interaction.user.avatar.url,
                    )
                else:
                    e.set_footer(text=f"Error by {interaction.user}")
                await channel.send(f"<@&996004219792400405>", embed=e)
            raise error

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, exc: commands.CommandError):

        if hasattr(ctx, "error_handled"):
            return

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
                e = Embed(
                    title="Error!",
                    description=f"{exc.__class__.__name__}: {exc}",
                    timestamp=discord.utils.utcnow(),
                    colour=0xAD3998,
                )
                e.add_field(name="Channel", value=ctx.channel.mention)
                e.set_footer(
                    text=f"Error by {ctx.author}", icon_url=ctx.author.avatar.url
                )
                await channel.send(f"<@&996004219792400405>", embed=e)
            raise exc


async def setup(bot: Botty):
    await bot.add_cog(ErrorHandler(bot))
