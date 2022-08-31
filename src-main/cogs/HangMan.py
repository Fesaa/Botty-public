import typing
import asyncio
import discord

from discord import Embed
from discord.ext import commands
from discord.ui import View, Select, button, TextInput, Modal

from Botty import Botty
from BottyCache import HangManDict
from utils.functions import get_HangMan_word, time



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

def winner_embed(data: HangManDict) -> Embed:
    players = [int(i) for i in data["players"].split(",")]
    e = Embed(
            title="Winner Winner Chicken Dinner",
            description=f"The word you were looking for is **{data['word']}**, congratulations!\n{','.join(f'<@{user_id}>' for user_id in players)}",
            color=0xAD3998,
        )
    e.add_field(name="Statistics", value=f"{len(data['used_letters']) + 1} guesses where used before the word was found\n"
                                            f"It took you {round(((discord.utils.utcnow() - data['start_time']).total_seconds()/60))} minute(s) to find the word.")
    return e

def hangman_str(word: str, letters: typing.List[str]) -> typing.Tuple[str, int, bool]:
    hg_str = ""
    wrong_letters = 0
    for letter in word.lower():
        if letter in letters:
            hg_str += " " + letter + " "
        else:
            hg_str += r" \_ "
    for letter in letters:
        if letter not in word.lower():
            wrong_letters += 1
    if r" \_ " in hg_str:
        found = False
    else:
        found = True
    return (hg_str, wrong_letters, found)


def splitletters(used_letters: str) -> list:
    alphabet0 = "abcdefghijklm"
    alphabet1 = "nopqrstuvwxyz"

    used_letters = "".join(sorted(used_letters))

    s0, s1 = "", ""

    contains0 = False
    contains1 = False

    for letter in reversed(alphabet0):
        if letter in used_letters:
            s1 = used_letters.split(letter)[1]
            contains0 = True
            break

    for letter in alphabet1:
        if letter in used_letters:
            s0 = used_letters.split(letter)[0]
            contains1 = True
            break

    if contains0 and not contains1:
        return [used_letters, ""]
    elif contains1 and not contains0:
        return ["", used_letters]
    else:
        return [s0, s1]


async def check_inactive(
    bot: Botty, current_data: dict, msg: discord.Message, time_out: int
):
    await asyncio.sleep(time_out)
    if current_data == bot.cache.get_hangman(msg.id):
        bot.cache.remove_hangman(msg.id)

        await msg.edit(
            embed=Embed(
                title="Failed game",
                description=f"Ended game due to inactivity (2min).",
                color=0xAD3998,
            ),
            view=View(),
        )


class DropDownAM(Select):
    def __init__(self, used_letters: str, bot: Botty):

        self.bot = bot

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
        await letter_select(self, interaction)


class DropDownNZ(Select):
    def __init__(self, used_letters: str, bot: Botty):

        self.bot = bot

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
        await letter_select(self, interaction)


async def letter_select(
    self: typing.Union[DropDownAM, DropDownNZ], interaction: discord.Interaction
):
    sub_letter = self.values[0]

    data = self.bot.cache.get_hangman(interaction.message.id)  # type: ignore

    if not data:
        return

    players = [int(i) for i in data["players"].split(",")]
    used_letters = list(data["used_letters"])

    if interaction.user.id in players:

        turn = data["user_id"]

        if turn == players[-1]:
            next_turn = players[0]
        else:
            next_turn = players[players.index(turn) + 1]

        if interaction.user.id == turn:
            used_letters.append(sub_letter)

            HM_str_data = hangman_str(data["word"], used_letters)

            if HM_str_data[2]:
                self.bot.cache.remove_hangman(interaction.message.id)  # type: ignore

                for user_id in players:
                    await self.bot.PostgreSQL.update_lb(
                        "hangman", interaction.channel_id, user_id, interaction.guild_id
                    )
                await interaction.response.edit_message(
                    embed=winner_embed(data),
                    view=View(),
                )
            elif HM_str_data[1] < 8:
                e = Embed(
                    title="Hangman!",
                    description=f"#Letters: {len(data['word'])}\n <@{next_turn}>\n{HM_str_data[0]}",
                    color=0xAD3998,
                )
                e.set_image(url=HANGMANPICS[HM_str_data[1]])
                new_data = self.bot.cache.update_hangman(
                    data["word"],
                    "".join(used_letters),
                    next_turn,
                    data["players"],
                    interaction.message.id,  # type: ignore
                    data["start_time"]
                )

                await interaction.response.edit_message(
                    embed=e, view=DropDownView("".join(used_letters), self.bot)
                )

                await check_inactive(self.bot, new_data, interaction.message, 120)  # type: ignore

            else:
                self.bot.cache.remove_hangman(interaction.message.id)  # type: ignore
                e = Embed(
                        title="Failed game",
                        description=f"The word you were looking for is **{data['word']}**. You have been hang before finding it :c",
                        color=0xAD3998,
                    )
                e.add_field(name="Statistics", value=f"{len(data['used_letters']) + 1} guesses where used before you were hang\n"
                                            f"It took you {round(((discord.utils.utcnow() - data['start_time']).total_seconds()/60))} minute(s) to die.")
                await interaction.response.edit_message(
                    embed=e,
                    view=View(),
                )
        else:
            await interaction.response.send_message(
                "Please wait for your turn!", ephemeral=True
            )

    else:
        await interaction.response.send_message(
            "You are not part of this game, click the **Join** button to join the game!",
            ephemeral=True,
        )


class WordGuess(Modal):
    guess = TextInput(label="word_guess", style=discord.TextStyle.short)  # type: ignore

    def __init__(self, bot: Botty, title: str = "Guess the word!") -> None:
        super().__init__(title=title)
        self.bot = bot

    async def on_submit(self, interaction: discord.Interaction):
        data = self.bot.cache.get_hangman(interaction.message.id)  # type: ignore
        sub_word = interaction.data["components"][0]["components"][0]["value"]  # type: ignore

        if not data:
            return

        players = [int(i) for i in data["players"].split(",")]

        if data["user_id"] == interaction.user.id:

            if data["word"].lower() == sub_word.lower():
                self.bot.cache.remove_hangman(interaction.message.id)  # type: ignore
                await self.bot.PostgreSQL.update_lb(
                    "hangman", interaction.channel.id, interaction.user.id, interaction.guild_id  # type: ignore
                )
                await interaction.response.edit_message(
                    embed=winner_embed(data),
                    view=View(),
                )
            else:

                turn = data["user_id"]
                players = [int(i) for i in data["players"].split(",")]

                if turn == players[-1]:
                    next_turn = players[0]
                else:
                    next_turn = players[players.index(turn) + 1]

                self.bot.cache.update_hangman(
                    data["word"],
                    data["used_letters"],
                    next_turn,
                    data["players"],
                    interaction.message.id,  # type: ignore
                    data["start_time"]
                )

                HM_str_data = hangman_str(data["word"], list(data["used_letters"]))
                e = Embed(
                    title="Hangman!",
                    description=f"#Letters: {len(data['word'])}\n <@{next_turn}>\n{HM_str_data[0]}",
                    color=0xAD3998,
                )
                e.set_image(url=HANGMANPICS[HM_str_data[1]])
                await interaction.response.edit_message(
                    embed=e, view=DropDownView(data["used_letters"], self.bot)
                )
                await interaction.message.reply(  # type: ignore
                    "Wrong guess, you lost your turn!", ephemeral=True
                )

        else:
            await interaction.response.send_message(
                "Please wait for your turn!", ephemeral=True
            )


class DropDownView(View):
    def __init__(self, used_letters: str, bot: Botty):
        super().__init__(timeout=None)
        self.bot = bot

        letters = splitletters(used_letters)

        self.add_item(DropDownAM(letters[0], bot))
        self.add_item(DropDownNZ(letters[1], bot))

    @button(custom_id="join", label="Join", style=discord.ButtonStyle.green, row=2)
    async def _join(self, interaction: discord.Interaction, button):
        data = self.bot.cache.get_hangman(interaction.message.id)  # type: ignore

        if not data:
            return

        players = [int(i) for i in data["players"].split(",")]

        if interaction.user.id in players:
            await interaction.response.send_message(
                "You are already playing.", ephemeral=True
            )
        else:
            players.append(interaction.user.id)
            self.bot.cache.update_hangman(
                data["word"],
                data["used_letters"],
                data["user_id"],
                ",".join([str(i) for i in players]),
                data["msg_id"],
                data["start_time"]
            )
            await interaction.response.send_message(
                "You can play now, wait for your turn :)!", ephemeral=True
            )

    @button(custom_id="leave", label="Leave", style=discord.ButtonStyle.red, row=2)
    async def _leave(self, interaction: discord.Interaction, button):
        data = self.bot.cache.get_hangman(interaction.message.id)  # type: ignore

        if not data:
            return

        players = [int(i) for i in data["players"].split(",")]

        if interaction.user.id not in players:
            await interaction.response.send_message(
                "You are not playing.", ephemeral=True
            )
        else:

            if interaction.user.id == (turn := data["user_id"]):
                if turn == players[-1]:
                    next_turn = players[0]
                else:
                    next_turn = players[players.index(turn) + 1]

                HM_str_data = hangman_str(data["word"], list(data["used_letters"]))

                e = Embed(
                    title="Hangman!",
                    description=f"#Letters: {len(data['word'])}\n <@{next_turn}>\n{HM_str_data[0]}",
                    color=0xAD3998,
                )
                e.set_image(url=HANGMANPICS[HM_str_data[1]])

                if interaction.message:
                    await interaction.message.edit(
                        embed=e, view=DropDownView(data["used_letters"], self.bot)
                    )

            else:
                next_turn = data["user_id"]

            players.remove(interaction.user.id)

            if len(players) > 0:
                self.bot.cache.update_hangman(
                    data["word"],
                    data["used_letters"],
                    next_turn,
                    ",".join([str(i) for i in players]),
                    data["msg_id"],
                    data["start_time"]
                )
                await interaction.response.send_message(
                    "You're not playing anymore, sad to see you go :(!", ephemeral=True
                )
            else:
                self.bot.cache.remove_hangman(data["msg_id"])
                await interaction.response.edit_message(
                    embed=Embed(
                        title="Failed game",
                        description=f"Ended game due to no players.",
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
    async def _guess(self, interaction: discord.Interaction, button):
        await interaction.response.send_modal(WordGuess(self.bot))


class HangMan(commands.Cog):
    def __init__(self, bot: Botty) -> None:
        super().__init__()
        self.bot = bot

    def embed_logger(self, txt_log, channel_id, error_type=None):
        if error_type == "succ":
            colour = 0x00A86B
        elif error_type == "fail":
            colour = 0xB80F0A
        elif error_type == "s":
            colour = 0x1034A6
        else:
            colour = 0xAD3998
        e = Embed(title="📖 Info 📖", colour=colour)
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

        e = Embed(
            title="Hangman!",
            description=f"#Letters: {len(word)}\n <@{ctx.author.id}>"
            f" \n{hangman_str(word, [])[0]}",
            color=0xAD3998,
        )
        e.set_image(url=HANGMANPICS[hangman_str(word, [""])[1]])
        msg = await ctx.send(embed=e, view=DropDownView("", self.bot))
        self.bot.cache.update_hangman(
            word, "", ctx.author.id, str(ctx.author.id), msg.id, msg.created_at
        )

        for channel_id in self.bot.cache.get_channel_id(ctx.guild.id, "log"):
            await self.bot.get_channel(channel_id).send(
                embed=self.embed_logger(
                    f'{ctx.author} start a game of hangman, the word is {word}."',
                    ctx.channel.id,
                    "s",
                )
            )

        await check_inactive(self.bot, self.bot.cache.get_hangman(msg.id), msg, 120)  # type: ignore


async def setup(bot: Botty):
    await bot.add_cog(HangMan(bot))
