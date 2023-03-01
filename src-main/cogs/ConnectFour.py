import discord
from discord.ext import commands
from discord.ui import View, button, Button
from discord import ButtonStyle, Interaction, DMChannel

from Botty import Botty
from utils.ConnectFourGame import ConnectFourGame

class ConnectFourGameView(View):
    def __init__(self, bot: Botty, timeout=None):
        self.bot = bot
        super().__init__(timeout=timeout)

    async def interaction_check(self, interaction: Interaction) -> bool:
        connect_four_game = self.bot.cache.get_connect_four(interaction.message.id)  # type: ignore

        if not connect_four_game:
            return False

        return connect_four_game.is_playing(interaction.user.id)

    @button(emoji="1️⃣", style=ButtonStyle.blurple)
    async def _one(self, interaction: Interaction, button: Button):
        await self.button_callback(interaction, button, 0)

    @button(emoji="2️⃣", style=ButtonStyle.blurple)
    async def _two(self, interaction: Interaction, button: Button):
        await self.button_callback(interaction, button, 1)

    @button(emoji="3️⃣", style=ButtonStyle.blurple)
    async def _three(self, interaction: Interaction, button: Button):
        await self.button_callback(interaction, button, 2)

    @button(emoji="4️⃣", style=ButtonStyle.blurple)
    async def _four(self, interaction: Interaction, button: Button):
        await self.button_callback(interaction, button, 3)

    @button(emoji="5️⃣", style=ButtonStyle.blurple)
    async def _five(self, interaction: Interaction, button: Button):
        await self.button_callback(interaction, button, 4)

    @button(emoji="6️⃣", style=ButtonStyle.blurple)
    async def _six(self, interaction: Interaction, button: Button):
        await self.button_callback(interaction, button, 5)

    @button(emoji="7️⃣", style=ButtonStyle.blurple)
    async def _seven(self, interaction: Interaction, button: Button):
        await self.button_callback(interaction, button, 6)

    @button(label="Join", style=ButtonStyle.green, disabled=True)
    async def _join(self, interaction: Interaction, button: Button):
        ...

    @button(label="Leave", style=ButtonStyle.red)
    async def _leave_in_game(self, interaction: Interaction, button):
        connect_four_game = self.bot.cache.get_connect_four(interaction.message.id)  # type: ignore
        if not connect_four_game:
            return

        e: discord.Embed = connect_four_game.game_embed
        if connect_four_game.moves > 21:
            e.set_footer(f"{self.bot.get_user(connect_four_game.get_opposite(interaction.user.id)).name} won the game since {self.bot.get_user(interaction.user.id)}!")
            await self.bot.PostgreSQL.update_lb("connectfour", interaction.channel_id, connect_four_game.get_opposite(interaction.user.id), interaction.guild_id)
        else:
            e.set_footer(f"Game ended because {self.bot.get_user(interaction.user.id)} left!")
        
        await interaction.response.edit_message(embed=e, view=View())


    async def button_callback(self, interaction: Interaction, button: Button, row: int):
        connect_four_game = self.bot.cache.get_connect_four(interaction.message.id)  # type: ignore
        if not connect_four_game:
            return
        await connect_four_game.register_move(interaction, row, self, button)


class ConnectFourPreGameView(View):
    def __init__(self, bot: Botty, timeout=None):
        self.bot = bot
        super().__init__(timeout=timeout)

    @button(label="Join", style=ButtonStyle.green)
    async def _join(self, interaction: Interaction, button: Button):
        connect_four_game = self.bot.cache.get_connect_four(interaction.message.id)  # type: ignore

        if not connect_four_game:
            return

        if connect_four_game.is_playing(interaction.user.id):
            await interaction.response.send_message("You cannot join your own game.", ephemeral=True)
        else:
            connect_four_game.set_player_two(interaction.user.id)
            button.disabled = True

            e: discord.Embed = connect_four_game.game_embed
            e.set_footer(text=f"{self.bot.get_user(connect_four_game.player_one).name}'s turn!")
            await interaction.response.edit_message(embed=e, view=ConnectFourGameView(self.bot),)

    @button(label="Leave", style=ButtonStyle.red)
    async def _leave(self, interaction: Interaction, button):
        connect_four_game = self.bot.cache.get_connect_four(interaction.message.id)  # type: ignore

        if not connect_four_game:
            return

        if not connect_four_game.is_playing(interaction.user.id):
            return

        await interaction.message.delete()


class ConnectFour(commands.Cog):
    """
    A children classic since 1974!
    The board consists of a 6x7 grid. The starting player will be playing yellow, the other red.
    You'll be choosing a column to drop a coin in one after the other by clicking on the buttons!
    With the soul objective to have 4 coins in a row! These rows can be made; horizontally, vertically or diagonally.

    """
    def __init__(self, bot: Botty) -> None:
        self.bot = bot
        super().__init__()

    @property
    def display_emoji(self) -> discord.PartialEmoji:
        return discord.PartialEmoji(name='\U0001f7e1')

    async def cog_check(self, ctx: commands.Context) -> bool:
        if isinstance(ctx.channel, DMChannel) or ctx.author.bot:
            return False
        return ctx.channel.id in self.bot.cache.get_channel_id(
            ctx.guild.id, "connectfour"
        )

    @commands.command(aliases=["connect-four", "cf", "c4", "ConnectFour"])
    async def connect_four(self, ctx: commands.Context):
        """
        Start a game of ConnectFour, shorter: c4
        """
        new_game = ConnectFourGame(self.bot, ctx.author.id, self.bot.user.id)
        e = new_game.game_embed
        e.set_footer(text="Ask someone to join you!"),
        msg = await ctx.send(embed=e,view=ConnectFourPreGameView(self.bot))
        self.bot.cache.add_connect_four(msg.id, new_game)
        await new_game.check_inactive(120, msg)


async def setup(bot: Botty):
    await bot.add_cog(ConnectFour(bot))
