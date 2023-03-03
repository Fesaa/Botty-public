import random

import discord
import discord.ui as ui
from discord.ext import commands

from Botty import Botty
from framework import (
    BaseGame,
    GameCog,
    Game
)


class HangManGame(BaseGame):
    HANGMANPICS = [
        "https://media.discordapp.net/attachments/869315104271904768/874025738238562344/01.png",
        "https://media.discordapp.net/attachments/869315104271904768/874025739098419300/02.png",
        "https://media.discordapp.net/attachments/869315104271904768/874025741354934272/04.png",
        "https://media.discordapp.net/attachments/869315104271904768/874025742797783150/05.png",
        "https://media.discordapp.net/attachments/869315104271904768/874025743678586960/06.png",
        "https://media.discordapp.net/attachments/869315104271904768/874025745524088843/07.png",
        "https://media.discordapp.net/attachments/869315104271904768/874025746828509204/08.png",
        "https://media.discordapp.net/attachments/869315104271904768/874025747881275422/09.png",
    ]

    def __init__(self, game: Game, bot: Botty, channel_id, guild_id, current_player: int) -> None:
        super().__init__(game, bot, channel_id, guild_id, current_player, None)

        self.word = self.generate_word()
        self.used_letters: list[str] = []

        self.msg: discord.Message = ...

    def generate_word(self) -> str:
        word = "thisshouldfailtheenchantcheck"
        while not ((self.bot.enchant_dictionary.check(word) or self.bot.enchant_dictionary.check(word.lower())) and 5 < len(word) < 19):
            word = random.choice(self.bot.words)[0]
        return word

    async def start(self, ctx: commands.Context) -> None:
        self.msg: discord.Message = await ctx.send(embed=self.current_embed(), view=HangManGameView(self.bot, self))
        await self.check_inactive(120)

    def debug_string(self) -> str:
        return super().debug_string(word=self.word, used_letters=self.used_letters)

    async def remove_player(self, player: int, interaction: discord.Interaction) -> None:
        self.players.pop(player)

        if len(self.players) == 0:
            await interaction.response.edit_message(
                embed=discord.Embed(
                    title="Failed game",
                    description="Ended game due to no players.",
                    color=0xAD3998,
                ),
                view=ui.View(),
            )
        else:
            if interaction.user.id == self.current_player:
                await self.register_letter(interaction, "")
            await interaction.response.send_message("You're not playing anymore, sad to see you go :(!", ephemeral=True)

    @property
    def winner_embed(self) -> discord.Embed:
        """
        :return: Embed for after winning the game
        :rtype: discord.Embed
        """
        e = discord.Embed(
            title="Winner Winner Chicken Dinner",
            description=f"The word you were looking for is **{self.word}**, congratulations!\n{','.join(f'<@{player}>' for player in self.players)}",
            color=0xAD3998,
        )
        e.add_field(name="Statistics",
                    value=f"{len(self.used_letters) + 1} guesses where used before the word was found\n"
                          f"It took you {round(((discord.utils.utcnow() - self.msg.created_at).total_seconds() / 60))} minute(s) to find the word.")
        return e

    @property
    def loser_embed(self) -> discord.Embed:
        """
        :return: Embed for after losing the game
        :rtype: discord.Embed
        """
        e = discord.Embed(
            title="Failed game",
            description=f"The word you were looking for is **{self.word}**. You have been hang before finding it :c",
            color=0xAD3998,
        )
        e.add_field(name="Statistics", value=f"{len(self.used_letters)} guesses where used before you were hang\n"
                                             f"It took you {round(((discord.utils.utcnow() - self.msg.created_at).total_seconds() / 60))} minute(s) to die.")
        return e

    @property
    def display_string(self) -> str:
        """
        :return: The string that shows with letters are missing, and which not.
        :rtype: str
        """
        return " ".join(r"\_" if letter not in self.used_letters else letter for letter in self.word)

    def wrong_guesses(self) -> int:
        """
        :return: Amount of wrongly guessed numbers
        :rtype: int
        """
        return len([i for i in self.used_letters if i not in self.word])

    def current_embed(self, wrong_guesses: int = None) -> discord.Embed:
        """
        :param wrong_guesses: amount of wrong guesses. Calls `wrong_guesses` if none are provided, defaults to None
        :type wrong_guesses: int, optional
        :return: Game embed
        :rtype: discord.Embed
        """
        if not wrong_guesses:
            wrong_guesses = self.wrong_guesses()
        e = discord.Embed(
            title="Hangman!",
            description=f"#Letters: {len(self.word)}\n <@{self.next_player()}>\n{self.display_string}",
            color=0xAD3998
        )
        e.set_image(url=self.HANGMANPICS[wrong_guesses])
        return e

    async def graceful_shutdown(self):
        await self.msg.edit(embed=discord.Embed(title="Failed game", description="Ended game due to inactivity (2min).",
                                                color=0xAD3998), view=ui.View())

    async def guess_word(self, interaction: discord.Interaction, word: str):
        if self.word == word.lower():
            await self.grand_current_player(1)
            return await interaction.response.edit_message(embed=self.winner_embed, view=ui.View())

        await self.register_letter(interaction, "")
        await interaction.response.send_message("Wrong guess, you lost your turn!", ephemeral=True)

    async def letter_select(self, dropdown: ui.Select, interaction: discord.Interaction):
        """Function to register a dropdown select to

        :param dropdown: The dropdown the select is coming from
        :type dropdown: ui.Select
        :param interaction: associated interaction
        :type interaction: discord.Interaction
        """
        letter = dropdown.values[0]

        if interaction.user.id not in self.players:
            return await interaction.response.send_message(
                "You are not part of this game, click the **Join** button to join the game!", ephemeral=True)

        if interaction.user.id != self.current_player:
            if len(self.players) != 1:
                return await interaction.response.send_message("Please await for your turn!", ephemeral=True)
            else:
                await interaction.message.delete()
                return await interaction.response.send_message(
                    "A fatal error occurred and the game has been destroyed. Sorry for the inconvenience.",
                    ephemeral=True)

        await self.register_letter(interaction, letter)

    async def register_letter(self, interaction: discord.Interaction, letter: str = ""):
        """Register a move

        :param interaction: Associate interaction
        :type interaction: discord.Interaction
        :param letter: Letter passed through, pass nothing to skip a move
        :type letter: str
        """
        self.used_letters.append(letter)
        display_string = self.display_string
        wrong_guesses = self.wrong_guesses()

        # All letters have been found
        if "_" not in display_string:
            await self.grand_everyone(1)
            return await interaction.response.edit_message(embed=self.winner_embed, view=ui.View())

        if wrong_guesses < 8:
            await interaction.response.edit_message(embed=self.current_embed(wrong_guesses),
                                                    view=HangManGameView(self.bot, self))
            return await self.check_inactive(120)

        await interaction.response.edit_message(embed=self.loser_embed, view=ui.View())


class AlphabetDropDown(ui.Select):

    def __init__(self, game: HangManGame, letters: list[discord.SelectOption], row: int) -> None:
        super().__init__(
            custom_id=f"choose_letter_{letters[0].value}{letters[-1].value}",
            placeholder=f"Which letter will you guess? {letters[0].label} - {letters[-1].label}",
            options=[option for option in letters if option.value not in game.used_letters],
            row=row,
        )

        self.game = game

    async def callback(self, interaction: discord.Interaction[Botty]):
        await self.game.letter_select(self, interaction)


class HangManWordGuessModal(ui.Modal):
    guess = ui.TextInput(label="word_guess", style=discord.TextStyle.short)

    def __init__(self, bot: Botty, game: HangManGame) -> None:
        super().__init__(title="Guess the word!")
        self.bot = bot

        self.game = game

    async def on_submit(self, interaction: discord.Interaction[Botty], /) -> None:
        await self.game.guess_word(interaction, self.guess.value)


class HangManGameView(ui.View):

    def __init__(self, bot: Botty, game: HangManGame):
        super().__init__(timeout=None)

        self.bot = bot
        self.game = game

        self.add_item(AlphabetDropDown(game, [
            discord.SelectOption(emoji="🇦", label="A", value="a"),
            discord.SelectOption(emoji="🇧", label="B", value="b"),
            discord.SelectOption(emoji="🇨", label="C", value="c"),
            discord.SelectOption(emoji="🇩", label="D", value="d"),
            discord.SelectOption(emoji="🇪", label="E", value="e"),
            discord.SelectOption(emoji="🇫", label="F", value="f"),
            discord.SelectOption(emoji="🇬", label="G", value="g"),
            discord.SelectOption(emoji="🇭", label="H", value="h"),
            discord.SelectOption(emoji="🇮", label="I", value="i"),
            discord.SelectOption(emoji="🇯", label="J", value="j"),
            discord.SelectOption(emoji="🇰", label="K", value="k"),
            discord.SelectOption(emoji="🇱", label="L", value="l"),
            discord.SelectOption(emoji="🇲", label="M", value="m"),
        ], 0))
        self.add_item(AlphabetDropDown(game, [
            discord.SelectOption(emoji="🇳", label="N", value="n"),
            discord.SelectOption(emoji="🇴", label="O", value="o"),
            discord.SelectOption(emoji="🇵", label="P", value="p"),
            discord.SelectOption(emoji="🇶", label="Q", value="q"),
            discord.SelectOption(emoji="🇷", label="R", value="r"),
            discord.SelectOption(emoji="🇸", label="S", value="s"),
            discord.SelectOption(emoji="🇹", label="T", value="t"),
            discord.SelectOption(emoji="🇺", label="U", value="u"),
            discord.SelectOption(emoji="🇻", label="V", value="v"),
            discord.SelectOption(emoji="🇼", label="W", value="w"),
            discord.SelectOption(emoji="🇽", label="X", value="x"),
            discord.SelectOption(emoji="🇾", label="Y", value="y"),
            discord.SelectOption(emoji="🇿", label="Z", value="z"),
        ], 1))

    @ui.button(custom_id="hangman_join", label="Join", style=discord.ButtonStyle.green, row=2)
    async def _join(self, interaction: discord.Interaction, _):
        if interaction.user.id in self.game.players:
            return await interaction.response.send_message("You are already playing.", ephemeral=True)

        self.game.add_player(interaction.user.id)
        await interaction.response.send_message("You can play now, wait for your turn :)!", ephemeral=True)

    @ui.button(custom_id="hangman_leave", label="Leave", style=discord.ButtonStyle.red, row=2)
    async def _leave(self, interaction: discord.Interaction, _):
        if interaction.user.id not in self.game.players:
            return await interaction.response.send_message("You are not playing.", ephemeral=True)

        await self.game.remove_player(interaction.user.id, interaction)

    @ui.button(custom_id="hangman_guess",
               label="Guess your word!",
               emoji="🔍",
               style=discord.ButtonStyle.blurple,
               row=2)
    async def _guess(self, interaction: discord.Interaction, _):
        if interaction.user.id != self.game.current_player:
            return await interaction.response.send_message("Please await your turn!", ephemeral=True)

        await interaction.response.send_modal(HangManWordGuessModal(self.bot, self.game))


class HangMan(GameCog):
    """
    Try to find the hidden word before you get hang!
    You can play the game alone or with more players, feel free to join or leave at any time by using the appropriate buttons.
    In order of joining you will have to take action, you can either guess a letter by selecting one with the menus or submit
    a guess by pressing guess.
    """
    def __init__(self, bot: Botty) -> None:
        super().__init__(bot, Game.HANGMAN)
        self.bot = bot

    @property
    def display_emoji(self) -> discord.PartialEmoji:
        return discord.PartialEmoji(name='\U0001faa2')

    @commands.command(aliases=["hg", "hm"])
    async def hangman(self, ctx: commands.Context):
        """
        Start a game of HangMan, shorter: hm
        """
        game = HangManGame(Game.HANGMAN, self.bot, ctx.channel.id, ctx.guild.id, ctx.author.id)
        await game.start(ctx)


async def setup(bot: Botty):
    await bot.add_cog(HangMan(bot))
