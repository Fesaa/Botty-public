import asyncio

import discord


class RowFull(Exception):
    pass

class ConnectFourGame:
    EMOJI_DICT: dict[int, str] = {0: "⚪", 1: "🟡", 2: "🔴"}
    COLOUR_DICT = {"yellow": "1", "red": "2"}


    def __init__(self, bot,  player_one: int, player_id: int) -> None:
        self.player_one = player_one
        self.player_two = player_id
        self.bot = bot
        self.board: list[list[int]] = [[0 for _ in range(7)] for _ in range(6)]
        self.moves: int = 0


    def set_player_two(self, player_id: int) -> None:
        self.player_two = player_id


    def is_playing(self, user_id: int) -> bool:
        return user_id == self.player_one or user_id == self.player_two


    @property
    def game_embed(self) -> discord.Embed:
        e = discord.Embed(
            title="🟡 Connect four 🔴",
            colour=0xAD3998,
        )
        e.add_field(
            name=f"Game of {self.bot.get_user(self.player_one).name} and {self.bot.get_user(self.player_two).name} ",
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


    def get_player_colour(self, player_id: int) -> int:
        return 1 if self.player_one == player_id else 2 if self.player_two == player_id else -1


    def get_opposite(self, player_id: int) -> int:
        return self.player_two if self.player_one == player_id else self.player_one


    async def register_move(self, interaction: discord.Interaction, row: int, view: discord.ui.View, button: discord.ui.Button) -> None:
        player_id = interaction.user.id
        if not (
            (self.moves % 2 == 0 and player_id == self.player_one)
            or
            (self.moves % 2 == 1 and player_id == self.player_two)
        ):
            if self.is_playing(player_id):
                await interaction.response.send_message("Please await your turn.", ephemeral=True)
            else:
                await interaction.response.send_message("You're not part of this game.", ephemeral=True)
            return

        colour: int = self.get_player_colour(player_id)

        if self.apple_move_and_return_full_row_bool(colour, row):
            button.disabled = True

        e: discord.Embed = self.game_embed

        if self.check_win_state(colour):
            e.set_footer(text=f"{self.bot.get_user(player_id).name} won the game!")
            await interaction.response.edit_message(embed=e, view = discord.ui.View())
            self.bot.cache.remove_connect_four(interaction.message.id)
            await self.bot.PostgreSQL.update_lb("connectfour", interaction.channel_id, player_id, interaction.guild_id)
            return

        if self.moves == 42:
            e.set_footer(text="Games ends in a draw, all spaces are used!")
            await interaction.response.edit_message(embed=e, view = discord.ui.View())

        next_player = self.get_opposite(player_id)
        e.set_footer(text=f"{self.bot.get_user(next_player).name}'s turn!")
        await interaction.response.edit_message(embed=e, view = view)
        await self.check_inactive(120, interaction.message)


    async def check_inactive(self, time_out: int, msg: discord.Message):
        temp = [[i for i in row] for row in self.board]
        await asyncio.sleep(time_out)
        if temp == self.board:
            self.bot.cache.remove_connect_four(msg.id)
            await msg.edit(embed=discord.Embed(title="Failed game", description="Ended game due to inactivity (2min).", color=0xAD3998), view=discord.ui.View())


    def apple_move_and_return_full_row_bool(self, player: int, row: int) -> bool:
        placed = False
        last_opening = False

        for index, line in enumerate(self.board):
            if line[row] == 0:
                line[row] = player
                placed = True
                if index == 5: last_opening = True
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
                    if dot == self.board[line_index + 1][dot_index + 1] == self.board[line_index + 2][dot_index + 2] == self.board[line_index + 3][dot_index + 3] == player:
                        return True

                # Diagonal lines down
                if line_index > 2 and dot_index < 4:
                    if dot == self.board[line_index - 1][dot_index + 1] == self.board[line_index - 2][dot_index + 2] == self.board[line_index - 3][dot_index + 3] == player:
                        return True
                
                # Straight lines vertical
                if line_index < 3:
                    if dot == self.board[line_index + 1][dot_index] == self.board[line_index + 2][dot_index] == self.board[line_index + 3][dot_index] == player:
                        return True
        
        return False

