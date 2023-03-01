import typing
import random
import asyncpg
import discord

from discord.ext import commands

from Botty import Botty


class QuestionDict(typing.TypedDict):
    category: str
    category_key: str
    type: typing.Literal["multiple", "boolean"]
    difficulty: typing.Literal["easy", "medium", "hard"]
    question: str
    correct_answer: str
    incorrect_answers: typing.List[str]


class BottyInteraction(discord.Interaction):

    @property
    def client(self) -> Botty:
        return self.client


class MultipleChoiceButton(discord.ui.Button):

    def __init__(self, q: QuestionDict, correct: bool, label: str, row: int):
        super().__init__(label=label, style=discord.ButtonStyle.blurple, row=row)
        self.correct = correct
        self.q = q

    async def callback(self, interaction: BottyInteraction):  # type: ignore
        self.view.responded = True  # type: ignore
        if self.correct:
            await interaction.client.PostgreSQL.update_lb("trivia", interaction.channel_id, interaction.user.id, interaction.guild_id)
            e = question_embed(self.q, 0x00ff7f)
            e.add_field(name="Answered correctly \U0001f973!", value=f"{self.label}")

            return await interaction.response.edit_message(embed=e, view=discord.ui.View())
        
        e = question_embed(self.q, 0xff0800)
        e.add_field(name="Answered incorrectly \U0001f641!", value=f"You answered: {self.label}\nShould have been: {self.q['correct_answer']}")

        return await interaction.response.edit_message(embed=e, view=discord.ui.View())

class TriviaView(discord.ui.View):

    def __init__(self, owner: int, q: QuestionDict,  *, timeout: typing.Optional[float] = 180):
        super().__init__(timeout=timeout)
        self.response: typing.Optional[discord.Message] = None
        self.responded = False
        self.owner = owner

        all_answerers = q["incorrect_answers"] + [q["correct_answer"]]
        random.shuffle(all_answerers)
        for index, answer in enumerate(all_answerers):
            correct_answer = answer == q["correct_answer"]
            self.add_item(MultipleChoiceButton(q, correct_answer, label=answer, row=index % 2))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return self.owner == interaction.user.id

    async def on_timeout(self) -> None:
        for child in self.children:
            if isinstance(child, discord.ui.Button):
                child.disabled = True
                child.style = discord.ButtonStyle.green if child.correct else discord.ButtonStyle.red  # type: ignore

        if self.response and not self.responded:
            await self.response.edit(view=self)
        return await super().on_timeout()


def question_embed(q: QuestionDict, colour: int = None):
    colour_dict = {
            "easy": 0x00ff7f,
            "medium": 0xffa089,
            "hard": 0xff0800
        }
    e = discord.Embed(title="Trivia Question", description=q["question"], colour=colour or colour_dict[q["difficulty"]])
    e.add_field(name="Extra information", value=f"Category: {q['category']}\nDifficulty: {q['difficulty']}")
    return e


class TriviaCog(commands.Cog):
    """
    A small and easy to use trivia game!
    """

    def __init__(self, bot: Botty) -> None:
        self.bot = bot
        super().__init__()

    @property
    def display_emoji(self) -> discord.PartialEmoji:
        return discord.PartialEmoji(name='\U00002753')

    @discord.app_commands.command(name='trivia', description="Are you brave enough to try one of my questions?")
    @discord.app_commands.choices(category=[
        discord.app_commands.Choice(name='General Knowledge', value='general_knowledge'),
        discord.app_commands.Choice(name='Entertainment', value='entertainment'),
        discord.app_commands.Choice(name='Science', value='science'),
        discord.app_commands.Choice(name='Sports', value='sports'),
        discord.app_commands.Choice(name='Geography', value='geography'),
        discord.app_commands.Choice(name='History', value='history'),
        discord.app_commands.Choice(name='Art', value='art')
    ])
    async def _trivia(self, interaction: BottyInteraction, category: str = None):
        """
        You'll be presented with a question. You have 3 minutes to answer the question! 
        The correct answer is shown if you don't answer in time \U0001f642 
        """
        async with self.bot.pool.acquire() as con:
            con: asyncpg.connection.Connection  # type: ignore
            if category:
                query = "SELECT * FROM trivia_questions WHERE category_key = $1 ORDER BY random() LIMIT 1;"
                row = await con.fetchrow(query, category)
            else:
                query = "SELECT * FROM trivia_questions ORDER BY random() LIMIT 1;"
                row = await con.fetchrow(query)  # type: ignore

        if not row:
            return await interaction.response.send_message("No questions found, please try again.", ephemeral=True)

        q: QuestionDict = {}  # type: ignore
        q["category"] = row["category"]
        q["category_key"] = row["category_key"]
        q["correct_answer"] = row["correct_answer"]
        q["difficulty"] = row["difficulty"]
        q["incorrect_answers"] = row["incorrect_answers"].split('§§§')
        q["question"] = row["question"]

        trivia_view = TriviaView(interaction.user.id, q)
        await interaction.response.send_message(embed=question_embed(q), view=trivia_view)
        trivia_view.response = await interaction.original_response()

async def setup(bot: Botty):
    await bot.add_cog(TriviaCog(bot))