import string
from random import choice

import asyncpg
import discord
from discord.ext import commands, tasks

from Botty import Botty
from framework import (
    Game,
    GameCog,
    BaseGame
)


class WordSnakeGame(BaseGame):

    def __init__(self, game: Game, bot: Botty, channel_id: int, guild_id: int, current_player: int, *, last_word: str, last_msg_id: int, count: int, mistakes: int, max_mistakes: int) -> None:
        super().__init__(game, bot, channel_id, guild_id, current_player, None)

        self.last_word = last_word
        self.last_msg_id = last_msg_id
        self.count = count
        self.mistakes = mistakes
        self.max_mistakes = max_mistakes

    def debug_string(self) -> str:
        return super().debug_string(last_word=self.last_word, last_msg_id=self.last_msg_id, count=self.count, mistakes=self.mistakes)

    def sql_values(self) -> str:
        return f'({self.guild_id}, {self.channel_id}, {self.last_msg_id}, {self.current_player}, {self.count}, {self.last_word}, {self.mistakes})'

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



class WordSnake(GameCog):

    class WordToAdd:
        def __init__(self, guild_id: int, word: str) -> None:
            self.guild_id = guild_id
            self.word = word

    def __init__(self, bot: Botty):
        super().__init__(bot, Game.WORDSNAKE)
        self.games: dict[int, WordSnakeGame] = {}
        self.max_mistakes_config: dict[int, int] = {}

        self.to_add_words: list[self.WordToAdd] = []

    @property
    def display_emoji(self) -> discord.PartialEmoji:
        return discord.PartialEmoji(name='\U0001f40d')

    @tasks.loop(minutes=1)
    async def update_database(self):
        query = "INSERT INTO wordsnake (guild_id, channel_id, msg_id, current_player, count, last_word, mistakes) VALUES\n"
        for game in self.games.values():
            query += " " + game.sql_values() + ",\n"
        query += "ON CONFLICT (channel_id) DO set msg_id = msg_id, current_player = current_player, count = count, last_word = last_word, mistakes = mistakes;"
        print(query)
        async with self.bot.pool.acquire() as con:
            con: asyncpg.connection.Connection  # type: ignore
            async with con.transaction():
                await con.execute(query)

    async def cog_load(self) -> None:
        await super().cog_load()

        async with self.bot.pool.acquire() as con:
            con: asyncpg.connection.Connection  # type: ignore

            config = await con.fetch("SELECT guild_id,ws_wrong_guesses FROM game_settings;")
            for c in config:
                self.max_mistakes_config[c['guild_id']] = c['ws_wrong_guesses']


            games = await con.fetch("SELECT * FROM wordsnake;")
            for game in games:
                word_snake_game = WordSnakeGame(Game.WORDSNAKE, self.bot, game['channel_id'], game['guild_id'], game['current_player'],
                                                last_word=game['last_word'], last_msg_id=game['msg_id'], count=game['count'], mistakes=game['mistakes'],
                                                max_mistakes=self.max_mistakes_config[game['guild_id']])
                self.games[game['channel_id']] = word_snake_game
        
        print("\n".join(game.debug_string() for game in self.games.values()))

    @commands.group(name="wordsnake", aliases=["ws"])
    @commands.guild_only()
    async def _wordsnake(self, _):
        ...

    @_wordsnake.command(name="start")
    async def _wordsnake_start(self, ctx: commands.Context[Botty], word: str = None):
        game = self.games.get(ctx.channel.id, None)

        if game:
            return await ctx.message.delete()

        if word is None:
            word = choice(string.ascii_letters).lower()

        if len(word) > 1 and not self.bot.enchant_dictionary.check(word):
            return await ctx.send("This is not a word in the English language, please only use a-z and A-Z!")

        game = WordSnakeGame(Game.WORDSNAKE, self.bot, ctx.channel.id, ctx.guild.id, ctx.author.id,
                            last_word=word, last_msg_id=ctx.message.id, count=0, mistakes=0,
                            max_mistakes=self.max_mistakes_config.get(ctx.author.id, 3))
        
        if len(word) > 1:
            self.to_add_words.append(self.WordToAdd(ctx.guild.id, word))

        return await ctx.send(f"The game has begun! \nFind a word that starts with **{word[-1].lower()}**.")
    
    @_wordsnake.command(name="count")
    async def _wordsnake_count(self, ctx: commands.Context[Botty]):
        if game := self.games.get(ctx.channel.id, None):
            await ctx.send(f"You have been playing for **{game.count}** words!")

    @_wordsnake.command(name="resetwords", aliases=["rw"])
    async def _wordsnake_reset_words(self, ctx: commands.Context[Botty]):
        """
        Clear all used words in the channel
        """
        async with self.bot.pool.acquire() as con:
            con: asyncpg.Connection
            await con.execute("DELETE FROM usedwords WHERE channel_id = $1 AND game = $2;", ctx.channel.id, self.game.value)
        await ctx.message.delete()
        await ctx.send("The used words have been reset.")

    @commands.Cog.listener()
    async def on_message_delete(self, msg: discord.Message):
        if game := self.games.get(msg.channel.id, None):
            if game.last_msg_id == msg.id:
                await msg.channel.send(
                embed=discord.Embed(
                    title=f"Warning! Deleted message by {msg.author.name}",
                    description=f"The last word is: **{game.last_word}**",
                    colour=0xAD3998,
                )
            )

    @commands.Cog.listener()
    async def on_message_edit(self, msg: discord.Message, _):
        if game := self.games.get(msg.channel.id, None):
            if game.last_msg_id == msg.id:
                await msg.channel.send(
                embed=discord.Embed(
                    title=f"Warning! Edited message by {msg.author.name}",
                    description=f"The last word is: **{game.last_word}**",
                    colour=0xAD3998,
                )
            )

    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message):
        if msg.author.bot:
            return

        if msg.channel.id not in self.channels:
            return

        if msg.content[0] in await self.bot.get_prefix(msg):
            return

        game = self.games.get(msg.channel.id, None)

        if not game:
            return
        
        if msg.author.id == game.current_player:
            return await msg.delete()

        if await game.check_used(msg.content):
            return await msg.delete()

        if not self.bot.enchant_dictionary.check(msg.content):
            return await msg.delete()

        if msg.content[0].lower() != game.last_word[-1].lower():

            if msg.content[0].lower() == game.last_word[0].lower() \
            and game.mistakes < game.max_mistakes:
                game.mistakes += 1
                return await msg.delete()

            prefix = (await self.bot.get_prefix(msg))[-1]
            await msg.channel.send(
                f"Your worded started with **{msg.content[0].lower()}**, whilst it should have started with ** {game.last_word[-1].lower()}**."
                f"\nYou managed to reach **{game.count}** words this game! \nThe game has stopped, you can start a new one with"
                f"`{prefix}wordsnake start <word>` and reset the words with `{prefix}wordsnake resetwords` if you'd like."
            )
            self.games.pop(msg.channel.id)
            return

        game.count += 1
        game.mistakes = 0
        self.to_add_words.append(msg.content)

        game.last_msg_id = msg.id
        game.current_player = msg.author.id
        game.last_word = msg.content
        await game.grand_current_player(1)
        await msg.add_reaction("✅")



async def setup(bot: Botty):
    await bot.add_cog(WordSnake(bot))



