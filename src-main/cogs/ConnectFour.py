from typing import (
    Optional,
    Any
)

import discord
import discord.ui as ui
from discord.ext import commands

from Botty import Botty
from framework import (
    BaseGame,
    GameCog,
    Game
)


class RowFull(Exception):
    pass


class ConnectFourGame(BaseGame):
    EMOJI_DICT: dict[int, str] = {0: "⚪", 1: "🟡", 2: "🔴"}
    COLOUR_DICT = {"yellow": "1", "red": "2"}

    def __init__(self, game: Game, bot: Botty, channel_id, guild_id,  current_player: int, players: Optional[list[int]]):
        super().__init__(game, bot, channel_id, guild_id, current_player, players)

        self.board: list[list[int]] = [[0 for _ in range(7)] for _ in range(6)]
        self.moves: int = 0

        self.msg: discord.Message = ...

    def debug_string(self, **extra) -> str:
        return super().debug_string(board=self.board_string, moves=self.moves)

    async def start(self, ctx: commands.Context):
        e = self.game_embed
        e.set_footer(text="Ask someone to join you!"),
        self.msg = await ctx.send(embed=e, view=ConnectFourPreGameView(self.bot, self))
        await self.check_inactive(120)

    async def graceful_shutdown(self, *args, **kwargs):
        if self.msg:
            await self.msg.edit(
                embed=discord.Embed(title="Failed game", description="Ended game due to inactivity (2min).",
                                    color=0xAD3998), view=ui.View())

    def other(self, player: int) -> int:
        return [i for i in self.players if i != player][0]

    def add_player(self, player: int):
        self.players = [self.current_player, player]

    async def remove_player(self, player: int, interaction: discord.Interaction) -> Any:
        other = self.other(player)

        if other == self.bot.user.id:
            await interaction.message.delete()

        e: discord.Embed = self.game_embed
        if self.moves > 21:
            e.set_footer(
                text=f"{self.bot.get_user(other).name} won the game since {self.bot.get_user(interaction.user.id)}!")
            await self.grand_some(1, other)
        else:
            e.set_footer(text=f"Game ended because {self.bot.get_user(interaction.user.id)} left!")

        await interaction.response.edit_message(embed=e, view=ui.View())

    @property
    def game_embed(self) -> discord.Embed:
        e = discord.Embed(
            title="🟡 Connect four 🔴",
            colour=0xAD3998,
        )
        e.add_field(
            name=f"Game of {self.bot.get_user(self.players[0]).name} and {self.bot.get_user(self.players[1]).name} ",
            value=self.board_string
        )
        return e

    @property
    def board_string(self) -> str:
        board = ""
        for line in self.board:

            line_string = "🟦"
            for dot in line:
                line_string += self.EMOJI_DICT[dot]
            line_string += "🟦"

            board = line_string + "\n" + board
        return board

    def get_player_colour(self, player: int) -> int:
        return self.players.index(player) + 1

    async def register_move(self, interaction: discord.Interaction, row: int, view: discord.ui.View, button: ui.Button) -> None:
        player = interaction.user.id
        if not (
                (self.moves % 2 == 0 and player == self.players[0])
                or
                (self.moves % 2 == 1 and player == self.players[1])
        ):
            if self.is_playing(player):
                await interaction.response.send_message("Please await your turn.", ephemeral=True)
            else:
                await interaction.response.send_message("You're not part of this game.", ephemeral=True)
            return

        colour: int = self.get_player_colour(player)

        if self.apple_move_and_return_full_row_bool(colour, row):
            button.disabled = True

        e: discord.Embed = self.game_embed

        if self.check_win_state(colour):
            e.set_footer(text=f"{self.bot.get_user(player).name} won the game!")
            await interaction.response.edit_message(embed=e, view=ui.View())
            await self.grand_current_player(1)
            return

        if self.moves == 42:
            e.set_footer(text="Games ends in a draw, all spaces are used!")
            await interaction.response.edit_message(embed=e, view=ui.View())

        next_player = self.next_player()
        e.set_footer(text=f"{self.bot.get_user(next_player).name}'s turn!")
        await interaction.response.edit_message(embed=e, view=view)
        await self.check_inactive(120, interaction.message)

    def apple_move_and_return_full_row_bool(self, player: int, row: int) -> bool:
        placed = False
        last_opening = False

        for index, line in enumerate(self.board):
            if line[row] == 0:
                line[row] = player
                placed = True
                if index == 5:
                    last_opening = True
                break

        if not placed:
            raise RowFull

        self.moves += 1
        return last_opening

    def check_win_state(self, player: int) -> bool:
        for line_index, line in enumerate(self.board):
            for dot_index, dot in enumerate(line):

                # Straight lines horizontal
                if dot_index < 4:
                    if dot == line[dot_index + 1] == line[dot_index + 2] == line[dot_index + 3] == player:
                        return True

                # Diagonal lines up
                if line_index < 3 and dot_index < 4:
                    if dot == self.board[line_index + 1][dot_index + 1] == self.board[line_index + 2][dot_index + 2] == \
                            self.board[line_index + 3][dot_index + 3] == player:
                        return True

                # Diagonal lines down
                if line_index > 2 and dot_index < 4:
                    if dot == self.board[line_index - 1][dot_index + 1] == self.board[line_index - 2][dot_index + 2] == \
                            self.board[line_index - 3][dot_index + 3] == player:
                        return True

                # Straight lines vertical
                if line_index < 3:
                    if dot == self.board[line_index + 1][dot_index] == self.board[line_index + 2][dot_index] == \
                            self.board[line_index + 3][dot_index] == player:
                        return True

        return False


class ConnectFourGameView(ui.View):

    def __init__(self, bot: Botty, game: ConnectFourGame):
        super().__init__(timeout=None)

        self.bot = bot
        self.game = game

    async def interaction_check(self, interaction: discord.Interaction, /) -> bool:
        return self.game.is_playing(interaction.user.id)

    @ui.button(emoji="1️⃣", style=discord.ButtonStyle.blurple)
    async def _one(self, interaction: discord.Interaction, button: ui.Button):
        await self.game.register_move(interaction, 0, self, button)

    @ui.button(emoji="2️⃣", style=discord.ButtonStyle.blurple)
    async def _two(self, interaction: discord.Interaction, button: ui.Button):
        await self.game.register_move(interaction, 1, self, button)

    @ui.button(emoji="3️⃣", style=discord.ButtonStyle.blurple)
    async def _three(self, interaction: discord.Interaction, button: ui.Button):
        await self.game.register_move(interaction, 2, self, button)

    @ui.button(emoji="4️⃣", style=discord.ButtonStyle.blurple)
    async def _four(self, interaction: discord.Interaction, button: ui.Button):
        await self.game.register_move(interaction, 3, self, button)

    @ui.button(emoji="5️⃣", style=discord.ButtonStyle.blurple)
    async def _five(self, interaction: discord.Interaction, button: ui.Button):
        await self.game.register_move(interaction, 4, self, button)

    @ui.button(emoji="6️⃣", style=discord.ButtonStyle.blurple)
    async def _six(self, interaction: discord.Interaction, button: ui.Button):
        await self.game.register_move(interaction, 5, self, button)

    @ui.button(emoji="7️⃣", style=discord.ButtonStyle.blurple)
    async def _seven(self, interaction: discord.Interaction, button: ui.Button):
        await self.game.register_move(interaction, 6, self, button)

    @ui.button(label="Join", style=discord.ButtonStyle.green, disabled=True)
    async def _join(self, interaction: discord.Interaction, button: ui.Button):
        ...

    @ui.button(label="Leave", style=discord.ButtonStyle.red)
    async def _leave(self, interaction: discord.Interaction, _):
        if self.game.is_playing(interaction.user.id):
            await self.game.remove_player(interaction.user.id, interaction)
        else:
            await interaction.response.send_message("You cannot leave a game you're not playing.", ephemeral=True)


class ConnectFourPreGameView(ui.View):

    def __init__(self, bot: Botty, game: ConnectFourGame):
        super().__init__(timeout=None)

        self.bot = bot
        self.game = game

    @ui.button(label="Join", style=discord.ButtonStyle.green)
    async def _join(self, interaction: discord.Interaction, _):
        if self.game.is_playing(interaction.user.id):
            await interaction.response.send_message("Cannot join your own game.", ephemeral=True)
        else:
            self.game.add_player(interaction.user.id)

            e = self.game.game_embed
            e.set_footer(text=f"{self.bot.get_user(self.game.current_player).name}'s turn!")
            await interaction.response.edit_message(embed=e, view=ConnectFourGameView(self.bot, self.game))

    @ui.button(label="Leave", style=discord.ButtonStyle.red)
    async def _leave(self, interaction: discord.Interaction, _):
        if self.game.is_playing(interaction.user.id):
            await self.game.remove_player(interaction.user.id, interaction)
        else:
            await interaction.response.send_message("You cannot leave a game you're not playing.", ephemeral=True)


class ConnectFour(GameCog):
    """
    A children classic since 1974!
    The board consists of a 6x7 grid. The starting player will be playing yellow, the other red.
    You'll be choosing a column to drop a coin in one after the other by clicking on the buttons!
    With the soul objective to have 4 coins in a row! These rows can be made; horizontally, vertically or diagonally.

    """

    def __init__(self, bot: Botty) -> None:
        self.bot = bot
        super().__init__(bot, Game.CONNECTFOUR)

    @property
    def display_emoji(self) -> discord.PartialEmoji:
        return discord.PartialEmoji(name='\U0001f7e1')

    @commands.command(aliases=["c4"])
    async def _connectfour(self, ctx: commands.Context[Botty]):
        """
        Start a game of ConnectFour, shorter: c4
        """
        game = ConnectFourGame(Game.CONNECTFOUR, self.bot, ctx.channel.id, ctx.guild.id,  ctx.author.id, [ctx.author.id, self.bot.user.id])
        await game.start(ctx)


async def setup(bot: Botty):
    await bot.add_cog(ConnectFour(bot))
