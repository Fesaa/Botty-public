import discord

from discord import Embed
from random import randint
from discord.ext import commands

from Botty import Botty
from utils.functions import time, get_NTBPL_letters, allowed_word


class Ntbpl(commands.Cog):
    def __init__(self, bot: Botty) -> None:
        self.bot = bot

    async def cog_check(self, ctx: commands.Context) -> bool:
        if isinstance(ctx.channel, discord.DMChannel) or ctx.author.bot:
            return False
        return ctx.channel.id in self.bot.cache.get_channel_id(ctx.guild.id, "ntbpl")

    def embed_logger(
        self, txt_log: str, channel_id: int, error_type: str = None
    ) -> Embed:
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
        embed.add_field(name="Name to be picked later", value=txt_log)
        embed.set_footer(text=f"🆔 {channel_id} ⏳" + time())
        return embed

    def perms_check(ctx: commands.Context):
        return (
            ctx.author.id in ctx.bot.owner_ids
            or ctx.channel.permissions_for(ctx.author).manage_messages is True
        )

    @commands.command(aliases=["b"], no_pm=True)
    async def begin(self, ctx: commands.Context, count: int = randint(2, 5)):
        """
        Begin a game of NTBPL, will overwrite the current game.
        """

        new_letters = await get_NTBPL_letters(self.bot, count, ctx.channel.id)
        if await self.bot.PostgreSQL.get_game_data("ntbpl", ctx.channel.id) is None:
            await self.bot.PostgreSQL.game_switch("ntbpl", ctx.channel.id, True)
        await self.bot.PostgreSQL.update_NTBPL_data(
            channel_id=ctx.channel.id,
            count=count,
            letters=new_letters,
            last_user_id=self.bot.user.id,
        )

        await ctx.send(
            f"A game has started! I will present to you {count} letters in a specific order,"
            f" you will have to reply with a word that has those letters in the same order!\n"
            f"The letters now are: **{new_letters}**"
        )

    @commands.command(aliases=["cw"], no_pm=True)
    @commands.check(perms_check)
    async def clearwords(self, ctx: commands.Context):
        """
        Clear all used words
        """
        await self.bot.PostgreSQL.clear_words("ntbpl", ctx.channel.id)
        await ctx.message.delete()
        await ctx.send("The used words have been reset")

        for channel_id in self.bot.cache.get_channel_id(ctx.guild.id, "log"):
            await self.bot.get_channel(channel_id).send(
                embed=self.embed_logger(
                    f" {ctx.author.name} reset the used words.", ctx.channel.id, "s"
                )
            )

    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message):
        if msg.author.bot:
            return

        if not msg.guild:
            return

        if msg.channel.id not in self.bot.cache.get_channel_id(msg.guild.id, "ntbpl"):
            return

        if msg.content.startswith(self.bot.cache.get_command_prefix(msg.guild.id)):
            return

        data = await self.bot.PostgreSQL.get_game_data("ntbpl", msg.channel.id)
        sub_word = msg.content.split(" ")[0]

        if not data:
            return

        if data["last_user_id"] == msg.author.id:
            return await msg.delete()

        if await self.bot.PostgreSQL.check_used_word("ntbpl", msg.channel.id, sub_word):
            return await msg.add_reaction("🔁")

        if allowed_word(sub_word):
            new_letters = await get_NTBPL_letters(
                self.bot, data["count"], msg.channel.id
            )
            await self.bot.PostgreSQL.update_NTBPL_data(
                channel_id=msg.channel.id,
                count=data["count"],
                letters=new_letters,
                last_user_id=msg.author.id,
            )
            await self.bot.PostgreSQL.add_word("ntbpl", msg.channel.id, sub_word)
            await self.bot.PostgreSQL.update_lb("ntbpl", msg.channel.id, msg.author.id, msg.guild.id)
            await msg.add_reaction("✅")
            await msg.channel.send(f"The new letters are **{new_letters}**")

        else:
            return await msg.delete()


async def setup(bot: Botty):
    await bot.add_cog(Ntbpl(bot))
