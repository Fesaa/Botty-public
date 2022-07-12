import typing
import discord

from discord.ext import commands

from cogs.ConfigHandler import get_prefix
from Botty import Botty

class ConfirmationView(discord.ui.View):

    def __init__(self, bot: Botty, tag: str, desc: str, *, timeout: typing.Optional[float] = 180):
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

    def __init__(self, bot: Botty) -> None:
        self.bot = bot
        super().__init__()

    @commands.group(name="tag", invoke_without_command=True)
    @commands.has_permissions(manage_channels=True)
    async def _tag(self, ctx: commands.Context, *tag: str):
        """
        Remove or Delete the tags of this server, you need manage_channels permissions to do so.
        If a subcommand is not called, then this will search the tag database 
        for the tag requested.
        """
        tag = " ".join(tag).lower()
        data = self.bot.db.get_tag(ctx.guild.id, tag)

        if data:
            await ctx.send(data['desc'],  reference=ctx.message.reference)
        return

    @_tag.command(name="add")
    async def add(self, ctx: commands.Context, tag: str, *, desc: typing.Annotated[str, commands.clean_content]):
        """
        Add a tag to the server, if duplicate a confirmation button will appear.
        This tag is server-specific and cannot be used in other servers.
        """
        tag = tag.lower()
        if tag in [i.name for i in self.bot.commands]:
            return await ctx.send("Can't use command name as tag")
        check = self.bot.db.get_tag(ctx.guild.id, tag)

        if len(desc) > 2000:
            return await ctx.send('Tag content is a maximum of 2000 characters.')

        if check:
            e = discord.Embed(title=f'Confirmation!', colour=0xad3998)
            e.add_field(name='Old:', value=check['desc'][:1000] + '...')
            e.add_field(name='New:', value=desc[:1000] + '...')

            await ctx.send(embed=e, view=ConfirmationView(self.bot, tag, desc))
        else:
            self.bot.db.add_tag(ctx.guild.id, tag, desc)
            await ctx.send('\N{OK HAND SIGN}')
    
    @_tag.command(name="delete")
    async def _delete(self, ctx: commands.Context, *tag: str):
        """
        Delete a tag from the server.
        """
        tag = " ".join(tag).lower()
        check = self.bot.db.get_tag(ctx.guild.id, tag)

        if check:
            self.bot.db.delete_tag(ctx.guild.id, tag)
            await ctx.send('\N{OK HAND SIGN}')
        else:
            await ctx.send("This is not a valid tag.")
    
    @_tag.command(name='edit')
    async def _edit(self, ctx: commands.Context, tag: str, *, desc: typing.Annotated[str, commands.clean_content]):
        """
        Edit a tag from the server.
        """
        tag = tag.lower()
        check = self.bot.db.get_tag(ctx.guild.id, tag)

        if check:
            self.bot.db.update_tag(ctx.guild.id, tag, desc)
            await ctx.send('\N{OK HAND SIGN}')
        else:
            await ctx.send('Tag not found.')
    
    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message):
        if msg.author.bot or isinstance(msg.channel, discord.DMChannel):
            return
        elif any(bool_list := [msg.content.__contains__(i) for i in (await get_prefix(self.bot, msg))]):
            prefixes = await get_prefix(self.bot, msg)
            tag = msg.content.split(prefixes[bool_list.index(True)])[1].lower()

            data = self.bot.db.get_tag(msg.guild.id, tag)

            if data:
                await msg.channel.send(data['desc'], reference=msg.reference)
            return

async def setup(bot: Botty):
    await bot.add_cog(Tags(bot))