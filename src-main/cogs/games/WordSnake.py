import string
import logging
from random import choice

import asyncpg
import discord
from discord.ext import commands, tasks

from Botty import Botty
from framework import (
    Game,
    GameCog,
    BaseGame,
    GameConfigUpdateEvent,
    GameSetting
)

_log = logging.getLogger("botty")


class WordSnakeGame(BaseGame):

    def __init__(self, game: Game, bot: Botty, channel_id: int, guild_id: int, current_player: int, *, last_word: str, last_msg_id: int, count: int, mistakes: int) -> None:
        super().__init__(game, bot, channel_id, guild_id, current_player, None)

        self.last_word = last_word
        self.last_msg_id = last_msg_id
        self.count = count
        self.mistakes = mistakes

    def debug_string(self) -> str:
        return super().debug_string(last_word=self.last_word, last_msg_id=self.last_msg_id, count=self.count)

    def sql_values(self) -> str:
        return f"({self.guild_id}, {self.channel_id}, {self.last_msg_id}, {self.current_player}, {self.count}, '{self.last_word}', {self.mistakes})"

    async def check_used(self, word: str) -> bool:
        async with self.bot.pool.acquire() as con:
            con: asyncpg.connection.Connection
            query = \
                """
            SELECT
                word
            FROM
                used_words
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
        def __init__(self, channel_id: int, word: str) -> None:
            self.channel_id = channel_id
            self.word = word

    def __init__(self, bot: Botty):
        super().__init__(bot, Game.WORDSNAKE)
        self.games: dict[int, WordSnakeGame] = {}
        self.prev_games: dict[int, string] = {}
        self.max_mistakes_config: dict[int, int] = {}

        self.to_add_words: list[WordSnake.WordToAdd] = []

        self.update_database.start()

    @property
    def display_emoji(self) -> discord.PartialEmoji:
        return discord.PartialEmoji(name='\U0001f40d')

    @commands.Cog.listener()
    async def on_config_update(self, e: GameConfigUpdateEvent):
        if e.setting != GameSetting.WS_WRONG_GUESSES:
            return

        if e.channels:
            for channel in e.channels:
                self.max_mistakes_config[channel] = e.new_value
            return await e.ctx.send(f'Changed {e.setting.pretty()} for {len(e.channels)} to {e.new_value}.', ephemeral=True)
        else:
            self.max_mistakes_config[e.ctx.guild.id] = e.new_value
            return await e.ctx.send(f'Changed {e.setting.pretty()} to {e.new_value}.', ephemeral=True)

    def update_prev_games(self):
        self.prev_games = {}
        for game_id, game in self.games.items():
            self.prev_games[game_id] = game.sql_values()


    def has_changes(self) -> bool:
        if len(self.prev_games) == 0:
            self.update_prev_games()
            return True

        for game_id, game in self.games.items():
            if self.prev_games.get(game_id, "") != game.sql_values():
                self.update_prev_games()
                return True

        self.update_prev_games()
        return False


    @tasks.loop(seconds=5)
    async def update_database(self):
        if len(self.games.values()) != 0 and self.has_changes():
            query = f"""
            INSERT INTO
                word_snake
                (guild_id, channel_id, msg_id, current_player, count, last_word, mistakes)
            VALUES
                {','.join(game.sql_values() for game in self.games.values())}
            ON CONFLICT
                (channel_id)
            DO UPDATE SET
                msg_id = EXCLUDED.msg_id,
                current_player = EXCLUDED.current_player,
                count = EXCLUDED.count,
                last_word = EXCLUDED.last_word,
                mistakes = EXCLUDED.mistakes;
            """
            try:
                await self.exec_sql(query)
            except Exception as e:
                _log.error(f"An error occured while updating games: %s", e)

        if len(self.to_add_words) != 0:
            query = f"""
            INSERT INTO
                used_words
                (channel_id, game, word)
            VALUES
                {','.join(f"('{word.channel_id}', $1, '{word.word}')" for word in self.to_add_words)};
            """
            try:
                await self.exec_sql(query, self.game.value)
            except Exception as e:
                _log.error(f"An error occured while updating games: %s", e)
            self.to_add_words = []

    def in_wait_list(self, word: str, channel_id: int):
        for entry in self.to_add_words:
            if entry.word == word and entry.channel_id == channel_id:
                return True
        return False

    async def cog_load(self) -> None:
        await super().cog_load()

        async with self.bot.pool.acquire() as con:
            con: asyncpg.connection.Connection  # type: ignore

            config = await con.fetch("SELECT guild_id,ws_wrong_guesses FROM guild_settings;")
            for c in config:
                self.max_mistakes_config[c['guild_id']] = c['ws_wrong_guesses']
                #TODO channel settings override


            games = await con.fetch("SELECT * FROM word_snake;")
            for game in games:
                word_snake_game = WordSnakeGame(Game.WORDSNAKE, self.bot, game['channel_id'], game['guild_id'], game['current_player'],
                                                last_word=game['last_word'], last_msg_id=game['msg_id'], count=game['count'], mistakes=game['mistakes'])
                self.games[game['channel_id']] = word_snake_game

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
                            last_word=word, last_msg_id=ctx.message.id, count=0, mistakes=0)

        game.game_start()

        if len(word) > 1:
            self.to_add_words.append(WordSnake.WordToAdd(ctx.channel.id, word))

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
            await con.execute("DELETE FROM used_words WHERE channel_id = $1 AND game = $2;", ctx.channel.id, self.game.value)
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

        if not msg.content:
            return

        if msg.content[0] in await self.bot.get_prefix(msg):
            return

        game = self.games.get(msg.channel.id, None)

        if not game:
            return
        
        if msg.author.id == game.current_player:
            _log.debug("Remove message of %s, because is current player", msg.author.name)
            return await msg.delete()

        if self.in_wait_list(msg.content, msg.channel.id):
            _log.debug("Removing message of %s, because it is already used", msg.author.name)
            return await msg.delete()

        if await game.check_used(msg.content):
            _log.debug("Removing message of %s, because it is already used", msg.author.name)
            return await msg.delete()

        if not self.bot.enchant_dictionary.check(msg.content):
            _log.debug("Removing message of %s, because it (%s) is not a word", msg.author.name, msg.content)
            return await msg.delete()

        if msg.content[0].lower() != game.last_word[-1].lower():
            max_mistakes = self.max_mistakes_config.get(msg.channel.id, None) or self.max_mistakes_config.get(msg.guild.id, 3)

            if msg.content[0].lower() == game.last_word[0].lower() \
            and game.mistakes < max_mistakes:
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
        self.to_add_words.append(WordSnake.WordToAdd(msg.channel.id, msg.content))

        game.last_msg_id = msg.id
        game.current_player = msg.author.id
        game.last_word = msg.content
        await game.grand_current_player(1)
        await msg.add_reaction("✅")



async def setup(bot: Botty):
    await bot.add_cog(WordSnake(bot))



