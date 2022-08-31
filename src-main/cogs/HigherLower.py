import discord

from discord import Embed
from random import randint
from discord.ext import commands


from Botty import Botty
from utils.functions import time


class HigherLower(commands.Cog):
    def __init__(self, bot: Botty) -> None:
        super().__init__()
        self.bot = bot

    def embed_logger(self, txt_log, channel_id, error_type=None):
        if error_type == "succ":
            colour = 0x00A86B
        elif error_type == "error":
            colour = 0xF05E23
        else:
            colour = 0xAD3998
        embed = Embed(title="📖 Info 📖", colour=colour)
        embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar.url)
        embed.add_field(name="higher_lower", value=txt_log)
        embed.set_footer(text=f"🆔 {channel_id} ⏳" + time())
        return embed

    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message):
        if msg.author.bot:
            return

        if not msg.guild:
            return

        if msg.channel.id not in self.bot.cache.get_channel_id(
            msg.guild.id, "higherlower"
        ):
            return

        if msg.content.startswith(self.bot.cache.get_command_prefix(msg.guild.id)):
            return

        data = self.bot.cache.get_higherlower(msg.channel.id)

        if not data:
            data = self.bot.cache.update_higherlower(
                0,
                randint(
                    1, self.bot.cache.get_game_settings(msg.guild.id, "hl_max_number")  # type: ignore
                ),
                self.bot.user.id,
                msg.channel.id,
            )

        if (
            data["count"]
            == self.bot.cache.get_game_settings(msg.guild.id, "hl_max_reply")
            and data["last_user_id"] == msg.author.id
        ):
            return await msg.delete()

        try:
            sub_count = int(msg.content.split(" ")[0])
        except ValueError:
            return await msg.delete()

        if data["last_user_id"] != msg.author.id:
            data = self.bot.cache.update_higherlower(
                0, data["number"], msg.author.id, msg.channel.id
            )

        if sub_count < data["number"]:
            self.bot.cache.update_higherlower(
                data["count"] + 1, data["number"], msg.author.id, msg.channel.id
            )
            await msg.add_reaction("⬆️")
        elif sub_count > data["number"]:
            self.bot.cache.update_higherlower(
                data["count"] + 1, data["number"], msg.author.id, msg.channel.id
            )
            await msg.add_reaction("⬇️")
        else:
            await msg.add_reaction("⭐")
            await msg.channel.send(
                f"{msg.author.mention} Correct my love! I have granted you a star ⭐"
            )

            self.bot.cache.update_higherlower(
                0,
                randint(
                    1, self.bot.cache.get_game_settings(msg.guild.id, "hl_max_number")  # type: ignore
                ),
                msg.author.id,
                msg.channel.id,
            )
            await self.bot.PostgreSQL.update_lb(
                "higherlower", msg.channel.id, msg.author.id, msg.guild.id
            )


async def setup(bot: Botty):
    await bot.add_cog(HigherLower(bot))
