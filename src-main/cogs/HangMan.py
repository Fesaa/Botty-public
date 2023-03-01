import typing
import asyncio
import discord

from discord.ext import commands
from discord.ui import View, Select, button, TextInput, Modal

from Botty import Botty
from utils.functions import get_HangMan_word, time

class DropDownAM(Select):
    """
    DropDown for letters A to M
    """
    def __init__(self, used_letters: list[str]):
        options = [
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
        ]

        options = [i for i in options if i.value not in used_letters]

        super().__init__(
            custom_id="choose_letter_am",
            placeholder="Which letter will you guess? A - M",
            options=options,
            row=0,
        )

    async def callback(self, interaction: discord.Interaction):
        if game := ACTIVE_GAMES.get(interaction.message.id, None):
            await game.letter_select(self, interaction)


class DropDownNZ(Select):
    """
    DropDown for letters N to Z
    """
    def __init__(self, used_letters: list[str]):
        options = [
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
        ]

        options = [i for i in options if i.value not in used_letters]

        super().__init__(
            custom_id="choose_letter_nz",
            placeholder="Which letter will you guess? N - Z",
            options=options,
            row=1,
        )

    async def callback(self, interaction: discord.Interaction):
        if game := ACTIVE_GAMES.get(interaction.message.id, None):
            await game.letter_select(self, interaction)



class HangManGame:
    """
    HangManGame instance. Should be short lived. Does not survive bot restarts.
    """

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

    def __init__(self, bot: Botty, player: int, word: str, msg: discord.Message) -> None:
        self.bot = bot
        self.word = word.lower()
        self.msg = msg
        self.current_player = player
        self.players: list[int] = [player]

        self.used_letters: list[str] = []

    @property
    def next_player(self) -> int:
        """
        :return: the id of the next players, and updates the `current_player` var to that value
        :rtype: int
        """
        next_player: int = self.players[(self.players.index(self.current_player) + 1) % len(self.players)]
        self.current_player = next_player
        return next_player

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
                        f"It took you {round(((discord.utils.utcnow() - self.msg.created_at).total_seconds()/60))} minute(s) to find the word.")
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
                                    f"It took you {round(((discord.utils.utcnow() - self.msg.created_at).total_seconds()/60))} minute(s) to die.")
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
            wrong_guesses = self.wrong_guesses
        e = discord.Embed(
                title="Hangman!",
                description=f"#Letters: {len(self.word)}\n <@{self.next_player}>\n{self.display_string}",
                color=0xAD3998
            )
        e.set_image(url=self.HANGMANPICS[wrong_guesses])
        return e

    async def check_inactive(self, time_out: int):
        """Function to call after move to remove the game from memory after `time_out` seconds  .

        :param time_out: Seconds to wait
        :type time_out: int
        """
        snap_shot = [i for i in self.used_letters]
        await asyncio.sleep(time_out)
        if snap_shot == self.used_letters:
            await self.msg.edit(embed=discord.Embed(title="Failed game", description="Ended game due to inactivity (2min).", color=0xAD3998), view=View())

    async def letter_select(self, dropdown: typing.Union[DropDownAM, DropDownNZ], interaction: discord.Interaction):
        """Function to register a dropdown select to

        :param dropdown: The dropdown the select is coming from
        :type dropdown: typing.Union[DropDownAM, DropDownNZ]
        :param interaction: associated interaction
        :type interaction: discord.Interaction
        """
        letter = dropdown.values[0]

        if interaction.user.id not in self.players:
            return await interaction.response.send_message("You are not part of this game, click the **Join** button to join the game!", ephemeral=True)

        if interaction.user.id != self.current_player:
            return await interaction.response.send_message("Please await for your turn!", ephemeral=True)

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
            await self.register_points()
            return await interaction.response.edit_message(embed=self.winner_embed, view=View())

        if wrong_guesses < 8:
            await interaction.response.edit_message(embed=self.current_embed(wrong_guesses), view=DropDownView(self.used_letters, self.bot))
            return await self.check_inactive(120)

        ACTIVE_GAMES.pop(self.msg.id)
        await interaction.response.edit_message(embed=self.loser_embed, view=View())

    async def register_points(self):
        """Gives all players in the game a point for guessing correctly.
        """
        for player in self.players:
            await self.bot.PostgreSQL.update_lb("hangman", self.msg.channel.id, player, self.msg.guild.id)


ACTIVE_GAMES: dict[int, HangManGame] = {}

class WordGuess(Modal):
    """
    Modal to guess the entire word with
    """
    guess = TextInput(label="word_guess", style=discord.TextStyle.short)  # type: ignore

    def __init__(self, bot: Botty, title: str = "Guess the word!") -> None:
        super().__init__(title=title)
        self.bot = bot

    async def on_submit(self, interaction: discord.Interaction):
        game = ACTIVE_GAMES.get(interaction.message.id, None)
        word_guess = interaction.data["components"][0]["components"][0]["value"]  # type: ignore

        if not game:
            return

        if game.current_player != interaction.user.id:
            return await interaction.response.send_message("Please wait for your turn!", ephemeral=True)

        if game.word == word_guess.lower():
            ACTIVE_GAMES.pop(interaction.message.id)
            game.register_points()
            return await interaction.response.edit_message(embed=game.winner_embed, view=View())

        await game.register_letter(interaction, "")
        await interaction.response.send_message("Wrong guess, you lost your turn!", ephemeral=True)


class DropDownView(View):
    """
    The view containing all actions
    """

    def __init__(self, used_letters: list[str], bot: Botty):
        super().__init__(timeout=None)
        self.bot = bot

        self.add_item(DropDownAM(used_letters))
        self.add_item(DropDownNZ(used_letters))

    @button(custom_id="join", label="Join", style=discord.ButtonStyle.green, row=2)
    async def _join(self, interaction: discord.Interaction, _):
        game = ACTIVE_GAMES.get(interaction.message.id, None)

        if not game:
            return

        if interaction.user.id in game.players:
            return await interaction.response.send_message("You are already playing.", ephemeral=True)
        
        game.players.append(interaction.user.id)
        await interaction.response.send_message("You can play now, wait for your turn :)!", ephemeral=True)

    @button(custom_id="leave", label="Leave", style=discord.ButtonStyle.red, row=2)
    async def _leave(self, interaction: discord.Interaction, _):
        game = ACTIVE_GAMES.get(interaction.message.id, None)

        if not game:
            return

        if interaction.user.id not in game.players:
            return await interaction.response.send_message("You are not playing.", ephemeral=True)

        game.players.remove(interaction.user.id)


        if len(game.players) > 0:
            if interaction.user.id == game.current_player:
                await game.register_letter(interaction, "")
            return await interaction.response.send_message("You're not playing anymore, sad to see you go :(!", ephemeral=True)
        else:
            ACTIVE_GAMES.pop(interaction.message.id)
            await interaction.response.edit_message(
                embed=discord.Embed(
                    title="Failed game",
                    description="Ended game due to no players.",
                    color=0xAD3998,
                ),
                view=View(),
            )

    @button(
        custom_id="guess",
        label="Guess your word!",
        emoji="🔍",
        style=discord.ButtonStyle.blurple,
        row=2,
    )
    async def _guess(self, interaction: discord.Interaction, _):
        await interaction.response.send_modal(WordGuess(self.bot))


class HangMan(commands.Cog):
    """
    Try to find the hidden word before you get hang!
    You can play the game alone or with more players, feel free to join or leave at any time by using the appropriate buttons.
    In order of joining you will have to take action, you can either guess a letter by selecting one with the menus or submit
    a guess by pressing guess.
    """
    def __init__(self, bot: Botty) -> None:
        super().__init__()
        self.bot = bot
    
    @property
    def display_emoji(self) -> discord.PartialEmoji:
        return discord.PartialEmoji(name='\U0001faa2')

    def embed_logger(self, txt_log, channel_id, error_type=None):
        if error_type == "succ":
            colour = 0x00A86B
        elif error_type == "fail":
            colour = 0xB80F0A
        elif error_type == "s":
            colour = 0x1034A6
        else:
            colour = 0xAD3998
        e = discord.Embed(title="📖 Info 📖", colour=colour)
        e.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar.url)
        e.add_field(name="Hangman", value=txt_log)
        e.set_footer(text=f"🆔 {channel_id} ⏳" + time())
        return e

    async def cog_check(self, ctx: commands.Context) -> bool:
        if isinstance(ctx.channel, discord.DMChannel) or ctx.author.bot:
            return False
        return ctx.channel.id in self.bot.cache.get_channel_id(ctx.guild.id, "hangman")

    @commands.command(aliases=["hg", "hm"])
    async def hangman(self, ctx: commands.Context):
        """
        Start a game of HangMan, shorter: hm
        """
        word = get_HangMan_word()
        display_string = " _ " * len(word)

        e = discord.Embed(
                title="Hangman!",
                description=f"#Letters: {len(word)}\n <@{ctx.author.id}>\n{display_string}",
                color=0xAD3998
            )
        e.set_image(url=HangManGame.HANGMANPICS[0])
        msg: discord.Message = await ctx.send(embed=e, view=DropDownView([], self.bot))
        game = HangManGame(self.bot, ctx.author.id, word, msg)
        ACTIVE_GAMES[msg.id] = game

        for channel_id in self.bot.cache.get_channel_id(ctx.guild.id, "log"):
            await self.bot.get_channel(channel_id).send(
                embed=self.embed_logger(
                    f'{ctx.author} start a game of hangman, the word is {word}.',
                    ctx.channel.id,
                    "s",
                )
            )

        await game.check_inactive(120)


async def setup(bot: Botty):
    await bot.add_cog(HangMan(bot))
