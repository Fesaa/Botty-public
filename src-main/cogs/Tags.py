import typing
import discord

from discord.ext import commands

from cogs.ConfigHandler import get_prefix

class ConfirmationView(discord.ui.View):

    def __init__(self, bot: commands.Bot, tag: str, desc: str, *, timeout: typing.Optional[float] = 180):
        self.bot = bot
        self.tag = tag
        self.desc = desc
        super().__init__(timeout=timeout)

    @discord.ui.button(label='Confirm', style=discord.ButtonStyle.green)
    async def _confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.bot.db.update_tag(interaction.guild_id, self.tag, self.desc)
        await interaction.message.delete()
        await interaction.response.send_message(embed=discord.Embed(title=f'Added "{self.tag}"!', description=self.desc, colour=0xad3998), ephemeral=True)
    
    @discord.ui.button(label='Deny', style=discord.ButtonStyle.red)
    async def _deny(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.message.delete()
        await interaction.response.send_message(f"{self.tag} will not be added.", ephemeral=True)

class Tags(commands.Cog):

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        super().__init__()

    @commands.group(name="tag")
    @commands.has_permissions(manage_channels=True)
    async def _tag(self, ctx: commands.Context):
        ...

    @_tag.command(name="add")
    async def add(self, ctx: commands.Context, tag: str, *desc: str):
        desc = " ".join(desc)
        check = self.bot.db.get_tag(ctx.guild.id, tag)

        if check:
            await ctx.send(embed=discord.Embed(title=f'Confirmation: do you want to add tag "{tag}"', description=desc, colour=0xad3998), view=ConfirmationView(self.bot, tag, desc))
        else:
            self.bot.db.add_tag(ctx.guild.id, tag, desc)
            await ctx.send(embed=discord.Embed(title=f'Added "{tag}"!', description=desc, colour=0xad3998))
    
    @_tag.command(name="delete")
    async def _delete(self, ctx: commands.Context, tag: str):
        check = self.bot.db.get_tag(ctx.guild.id, tag)

        if check:
            self.bot.db.delete_tag(ctx.guild.id, tag)
            await ctx.send(embed=discord.Embed(title=f'Deleted "{tag}"!', description=check["desc"], colour=0xad3998))
        else:
            await ctx.send("This is not a valid tag.")
    
    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message):
        if msg.author.bot or isinstance(msg.channel, discord.DMChannel) or len(msg.content.split(' ')) > 1:
            return
        elif any(bool_list := [msg.content.__contains__(i) for i in (await get_prefix(self.bot, msg))]):
            prefixes = await get_prefix(self.bot, msg)
            tag = msg.content.split(prefixes[bool_list.index(True)])[1]

            data = self.bot.db.get_tag(msg.guild.id, tag)

            if data:
                await msg.channel.send(data['desc'])
            return

async def setup(bot: commands.Bot):
    await bot.add_cog(Tags(bot))