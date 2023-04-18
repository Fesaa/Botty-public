from random import randint, choice

import asyncpg
import discord
from discord.ext import commands

from Botty import Botty
from framework import (
    Game,
    GameCog,
    BaseGame
)


class NTBPLGame(BaseGame):

    def __init__(self, game: Game, bot: Botty, channel_id, guild_id, current_player: int, *, count: int):
        super().__init__(game, bot, channel_id, guild_id, current_player, None)

        self.count = count
        self.letters: str = ...
        self.channel_id: int = ...
        self.word: str = ...

    async def new_letters(self, channel: discord.TextChannel):
        self.channel_id = channel.id
        self.letters = await self.get_new_letters()
        await channel.send(f"Find a word that includes the follow letters! **{self.letters}**")

    async def check_used(self, word: str) -> bool:
        async with self.bot.pool.acquire() as con:
            con: asyncpg.connection.Connection
            query = \
                """
            SELECT
                word
            FROM
                usedwords
            WHERE
                game = $1
            AND
                channel_id = $2
            AND
                LOWER(word) = LOWER($3);
            """
            row = await con.fetchrow(query, self.game.value, self.channel_id, word)
            return row is not None

    async def get_new_letters(self) -> str:
        word = "thisshouldfailtheenchantcheck"
        while not (
                (self.bot.enchant_dictionary.check(word) or self.bot.enchant_dictionary.check(word.lower()))
                and not await self.check_used(word)
                and len(word) > self.count + 2
        ):
            word = choice(self.bot.words)[0]

        spil = randint(1, len(word) - self.count - 1)
        self.word = word
        return word[spil: spil + self.count]


class NTBPL(GameCog):
    """
    A Custom game!
    I give you an amount of letters. And you send a word that contains these letters in the same order!
    Sending a message in a NTBPL channel will send new letters if the bot is not tracking any.
    What does this emoji mean?
    ✅: Your word was accepted
    🔁: Somebody already used this word before you!
    "None": Word is not valid
    """

    def __init__(self, bot: Botty):
        super().__init__(bot, Game.NTBPL)
        self.games: dict[int, NTBPLGame] = {}

    @property
    def display_emoji(self) -> discord.PartialEmoji:
        return discord.PartialEmoji(name='\U0001f4db')

    @commands.group(name="ntbpl")
    @commands.guild_only()
    async def _ntbpl(self, _):
        ...

    @_ntbpl.command(name="start")
    async def _ntbpl_start(self, ctx: commands.Context[Botty], count: int = 3):
        """
        Change the running game of NTBPL (change count), or get new letters
        """
        game = NTBPLGame(Game.NTBPL, self.bot, ctx.channel.id, ctx.guild.id, self.bot.user.id, count=count)
        game.game_start()
        await game.new_letters(ctx.channel)

    @_ntbpl.command(name="resetwords", aliases=["rw"])
    @commands.has_permissions(manage_messages=True)
    async def _ntbpl_reset_words(self, ctx: commands.Context):
        """
        Clear all used words in the channel
        """
        async with self.bot.pool.acquire() as con:
            con: asyncpg.Connection
            await con.execute("DELETE FROM usedwords WHERE channel_id = $1 AND game = $2;", ctx.channel.id, self.game.value)
        await ctx.message.delete()
        await ctx.send("The used words have been reset.")

    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message):
        if msg.author.bot:
            return

        if not msg.guild:
            return

        if msg.channel.id not in self.channels:
            return

        if msg.content[0] in await self.bot.get_prefix(msg):
            return

        game = self.games.get(msg.channel.id, None)

        if not game:
            game = NTBPLGame(Game.NTBPL, self.bot, msg.channel.id, msg.guild.id, self.bot.user.id, count=3)
            self.games[msg.channel.id] = game
            return await game.new_letters(msg.channel)

        word = msg.content.split(" ")[0].lower()

        if game.current_player == msg.author.id:
            return await msg.delete()

        if await game.check_used(word):
            return await msg.add_reaction("🔁")

        if not self.bot.enchant_dictionary.check(word):
            return

        if game.letters.lower() not in word.lower():
            return

        game.current_player = msg.author.id
        await game.grand_current_player(1)
        await game.new_letters(msg.channel)


async def setup(bot: Botty):
    await bot.add_cog(NTBPL(bot))
