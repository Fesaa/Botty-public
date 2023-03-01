import io
import csv
import string
import discord
import asyncpg

from discord import Embed
from random import choice
from discord.ext import commands

from Botty import Botty
from utils.functions import allowed_word, time


class WordSnake(commands.Cog):
    """
    Create the longest possible snake!
    This is done by finding a word that starts with the last letter of the previous word!
    """
    def __init__(self, bot: Botty) -> None:
        super().__init__()
        self.bot = bot

    @property
    def display_emoji(self) -> discord.PartialEmoji:
        return discord.PartialEmoji(name='\U0001f40d')

    async def cog_check(self, ctx: commands.Context) -> bool:
        if isinstance(ctx.channel, discord.DMChannel) or ctx.author.bot:
            return False
        return ctx.channel.id in self.bot.cache.get_channel_id(
            ctx.guild.id, "wordsnake"
        )

    def embed_logger(self, txt_log, channel_id, error_type=None):
        if error_type == "succ":
            colour = 0x00A86B
        elif error_type == "error":
            colour = 0xF05E23
        elif error_type == "fail":
            colour = 0xB80F0A
        elif error_type == "s":
            colour = 0x1034A6
        else:
            colour = 0xAD3998
        embed = Embed(title="📖 Info 📖", colour=colour)
        embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar.url)
        embed.add_field(name="word_snake ", value=txt_log)
        embed.set_footer(text=f"🆔 {channel_id} ⏳" + time())
        return embed

    def perms_check(ctx: commands.Context):
        return (
            ctx.author.id in ctx.bot.owner_ids
            or ctx.channel.permissions_for(ctx.author).manage_messages is True
        )

    async def _update_WordSnake_data(
        self,
        *,
        channel_id: int,
        last_user_id: int,
        last_word: str,
        msg_id: int,
        count: int,
    ) -> None:
        async with self.bot.pool.acquire() as con:
            con: asyncpg.connection.Connection  # type: ignore
            async with con.transaction():
                await con.execute(
                    "UPDATE wordsnake_game_data SET last_user_id = $1, last_word = $2, msg_id = $3, count = $4 WHERE channel_id = $5;",
                    last_user_id,
                    last_word,
                    msg_id,
                    count,
                    channel_id,
                )
    
    async def _allowed_mistakes(self, *, channel_id: int, allowed_mistakes: int) -> None:
        async with self.bot.pool.acquire() as con:
            con: asyncpg.connection.Connection  # type: ignore
            async with con.transaction():
                await con.execute(
                    "UPDATE wordsnake_game_data SET allowed_mistakes = $1 WHERE channel_id = $2;",
                    allowed_mistakes,
                    channel_id,
                )

    @commands.command(aliases=["s"], no_pm=True)
    async def start(self, ctx: commands.Context, first_word: str = None):
        """
        Start a game of WordSnake, if no word is given. I will choose a word.
        """
        data = await self.bot.PostgreSQL.get_game_data("wordsnake", ctx.channel.id)

        if data is not None:
            return await ctx.message.delete()

        if first_word is None:
            first_word = choice(string.ascii_letters).lower()

        if not allowed_word(first_word) and len(first_word) > 1:
            return await ctx.send("This is not a word in the English language, please only use a-z and A-Z!")

        await self.bot.PostgreSQL.game_switch("wordsnake", ctx.channel.id, True)
        await self._update_WordSnake_data(
            channel_id=ctx.channel.id,
            last_user_id=ctx.author.id,
            last_word=first_word,  # type: ignore
            msg_id=ctx.message.id,
            count=0,
        )
        await self._allowed_mistakes(
            channel_id=ctx.channel.id,
            allowed_mistakes=self.bot.cache.get_game_settings(
                ctx.guild.id, "ws_wrong_guesses"
            ),
        )
        await self.bot.PostgreSQL.add_word("wordsnake", ctx.channel.id, first_word)

        return await ctx.send(
            f"The game has begun! \nFind a word that starts with **{first_word[-1].lower()}**."  # type: ignore
        )

    @commands.command(aliases=["c"], no_pm=True)
    async def count(self, ctx: commands.Context):
        """
        Display your current count
        """
        data = await self.bot.PostgreSQL.get_game_data('wordsnake', ctx.channel.id)
        await ctx.message.delete()

        if data:
            return await ctx.send(f"You have been playing for **{data['count']}** words!")

        await ctx.send(f"No game was running, start one with `{self.bot.cache.get_command_prefix(ctx.guild.id)}start <word*>`!")

    @commands.command(aliases=["rw"], no_pm=True)
    @commands.check(perms_check)
    async def resetwords(self, ctx: commands.Context):
        """
        Reset all used words in the channel
        """

        await self.bot.PostgreSQL.clear_words("wordsnake", ctx.channel.id)

        await ctx.message.delete()
        await ctx.send("The used words have been reset")

        for channel_id in self.bot.cache.get_channel_id(ctx.guild.id, "log"):
            channel = self.bot.get_channel(channel_id)
            if channel:
                await channel.send(embed=self.embed_logger(f" {ctx.author.name} reset the used words.", ctx.channel.id, "s"))

    @commands.command(no_pm = True, name = "listwords")
    @commands.check(perms_check)
    async def _listwords(self, ctx: commands.Context):
        """
        List all words
        """

        async with self.bot.pool.acquire() as con:
            rows = await con.fetch("SELECT word FROM usedwords WHERE game = $1 AND channel_id = $2;", "wordsnake", ctx.channel.id)
            if not rows:
                return

            buffer = io.StringIO()
            writer = csv.writer(buffer)
            writer.writerows([[r["word"]] for r in rows])
            buffer.seek(0)

            await ctx.channel.send(file=discord.File(buffer, 'words_csv'))

    @commands.Cog.listener()
    async def on_message_delete(self, msg: discord.Message):
        data = await self.bot.PostgreSQL.get_game_data("wordsnake", msg.channel.id)

        if not data:
            return

        if data["msg_id"] == msg.id:
            await msg.channel.send(
                embed=Embed(
                    title=f"Warning! Deleted message by {msg.author.name}",
                    description=f"The last word is: **{data['last_word']}**",
                    colour=0xAD3998,
                )
            )

    @commands.Cog.listener()
    async def on_message_edit(self, msg1: discord.Message, msg2: discord.Message):
        data = await self.bot.PostgreSQL.get_game_data("wordsnake", msg1.channel.id)

        if not data:
            return

        if data["msg_id"] == msg1.id:
            await msg1.channel.send(
                embed=Embed(
                    title=f"Warning! Edited message by {msg1.author.name}",
                    description=f"The last word is: **{data['last_word']}**",
                    colour=0xAD3998,
                )
            )

    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message):
        if msg.author.bot:
            return

        if not msg.guild:
            return

        if msg.channel.id not in self.bot.cache.get_channel_id(msg.guild.id, "wordsnake"):
            return

        if msg.content.startswith(self.bot.cache.get_command_prefix(msg.guild.id)):
            return

        data = await self.bot.PostgreSQL.get_game_data("wordsnake", msg.channel.id)

        if not data:
            return

        if data["last_user_id"] == msg.author.id:
            return await msg.delete()

        if await self.bot.PostgreSQL.check_used_word("wordsnake", msg.channel.id, msg.content):
            return await msg.delete()

        if not allowed_word(msg.content):
            return await msg.delete()

        if msg.content[0].lower() == data["last_word"][-1].lower():

            await self._update_WordSnake_data(
                channel_id=msg.channel.id,
                last_user_id=msg.author.id,
                last_word=msg.content,
                msg_id=msg.id,
                count=data["count"] + 1,
            )
            await self._allowed_mistakes(
                channel_id=msg.channel.id,
                allowed_mistakes=self.bot.cache.get_game_settings(
                    msg.guild.id, "ws_wrong_guesses"
                ),
            )
            await self.bot.PostgreSQL.add_word("wordsnake", msg.channel.id, msg.content)
            await self.bot.PostgreSQL.update_lb(
                "wordsnake", msg.channel.id, msg.author.id, msg.guild.id
            )
            await msg.add_reaction("✅")

        elif (
            msg.content[0].lower() == data["last_word"][0].lower()
            and data["allowed_mistakes"] > 0
        ):
            await self._allowed_mistakes(
                channel_id=msg.channel.id, allowed_mistakes=data["allowed_mistakes"] - 1
            )
            await msg.delete()

            for channel_id in (await self.bot.PostgreSQL.get_channel(msg.guild.id, "log")):
                await self.bot.get_channel(channel_id).send(
                    embed=self.embed_logger(
                        f'{msg.author} used an allowed mistakes point, {data["allowed_mistakes"] - 1} remaining.',
                        msg.channel.id,
                        "error",
                    )
                )
        else:
            await self.bot.PostgreSQL.game_switch("wordsnake", msg.channel.id, False)

            await msg.channel.send(
                f"Your worded started with **{msg.content[0].lower()}**, whilst it should have started with ** {data['last_word'][-1].lower()}**."
                f"\nYou managed to reach **{data['count']}** words this game! \nThe game has stopped, you can start a new one with"
                f"`{(await self.bot.get_prefix(msg))[-1]}start <word*>` and reset the words with `{(await self.bot.get_prefix(msg))[-1]}resetwords` if you'd like."
            )

            for channel_id in (await self.bot.PostgreSQL.get_channel(msg.guild.id, "log")):
                await self.bot.get_channel(channel_id).send(
                    embed=self.embed_logger(
                        f"{msg.author} failed and ended the game.",
                        msg.channel.id,
                        "fail",
                    )
                )


async def setup(bot: Botty):
    await bot.add_cog(WordSnake(bot))
