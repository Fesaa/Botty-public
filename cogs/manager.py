import os
import discord
from discord.errors import Forbidden, HTTPException
from discord.ext.commands.errors import ChannelNotFound, CommandNotFound, CommandOnCooldown, ExtensionNotLoaded, \
    MemberNotFound, MissingRequiredArgument
from discord.ext import commands
from imports.functions import time
from cogs.config_handler import master_logger_id, admin_id
from cogs.config_handler import get_configdata


class cogsManager(commands.Cog):

    def __init__(self, client):
        self.client = client

    def embed_logger(self, txt_log, channel_id):
        embed = discord.Embed(title='📖 Info 📖', colour=0xad3998)
        embed.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
        embed.add_field(name="Cogs manager ", value=txt_log)
        embed.set_footer(text=f'🆔 {channel_id} ⏳' + time())
        return embed

    @commands.command(aliases=["rl"], brief="Admin command to reload cogs")
    async def reload(self, ctx, name=None):
        if ctx.author.id in admin_id:
            if name is None:
                reloads = []
                for filename in os.listdir("./cogs"):
                    if filename.endswith(".py") and filename != 'manager.py':
                        self.client.unload_extension(f"cogs.{filename[:-3]}")
                        self.client.load_extension(f"cogs.{filename[:-3]}")
                        reloads.append(filename)
                for channel_id in master_logger_id:
                    await self.client.get_channel(channel_id).send(
                        embed=self.embed_logger(f'{ctx.author} reloaded {", ".join(reloads)}', ctx.channel.id))
            else:
                try:
                    self.client.unload_extension(f"cogs.{name}")
                    self.client.load_extension(f"cogs.{name}")
                    for channel_id in master_logger_id:
                        await self.client.get_channel(channel_id).send(
                            embed=self.embed_logger(f'{ctx.author} reloaded {name}.py', ctx.channel.id))
                except ExtensionNotLoaded:
                    await (await ctx.author.create_dm()).send(f"{str({name})} is not one of the cog files.")
        else:
            await (await ctx.author.create_dm()).send(
                f"You do not have acces to this command, ask the administrator to use this command."
                f" Or change the id the in the `config.json` file")

    @commands.Cog.listener()
    async def on_command_error(self, ctx, exc):
        game_channels = ((await get_configdata(self.client, ctx.guild.id, 'polly_channel_id'))
                         + (await get_configdata(self.client, ctx.guild.id, 'ntbpl_channel_id'))
                         + (await get_configdata(self.client, ctx.guild.id, 'word_snake__channel_id'))
                         + (await get_configdata(self.client, ctx.guild.id, 'HL_channel_id')))
        if isinstance(exc, MissingRequiredArgument):
            await ctx.send(f"One or more required arguments are missing.")
        elif isinstance(exc, HTTPException):
            for channel_id in master_logger_id:
                await self.client.get_channel(channel_id).send(
                    embed=self.embed_logger(f'Could not send message in {self.client.get_channel(channel_id).name}.',
                                            ctx.channel.id))
        elif isinstance(exc, Forbidden):
            for channel_id in master_logger_id:
                await self.client.get_channel(channel_id).send(embed=self.embed_logger(
                    f'I do not have permission to speak here.'
                    f' {self.client.get_channel(channel_id).name}', ctx.channel.id))
        elif isinstance(exc, MemberNotFound):
            await ctx.send(f"This member is not the in Guild. And Fesa doesn't know how to fix this ;-)")
        elif isinstance(exc, CommandNotFound):
            pass
        elif isinstance(exc, discord.errors.NotFound):
            for channel_id in master_logger_id:
                await self.client.get_channel(channel_id).send(embed=self.embed_logger(
                    f'An error happened while trying to find an element in channel:'
                    f' {self.client.get_channel(channel_id).name}\n{exc}',
                    ctx.channel.id))
        elif isinstance(exc, CommandOnCooldown):
            if self.client.db.get_dm_preff(ctx.author.id) == 1:
                if ctx.channel.id not in game_channels:
                    try:
                        await (await ctx.author.create_dm()).send(
                            f"Calm down lad, retry after {round(exc.retry_after)}s!")
                    except AttributeError:
                        pass
        elif isinstance(exc, ChannelNotFound):
            await ctx.send(f"This is not a valid channel, or you using the command right?")
        elif isinstance(exc, RuntimeWarning):
            pass
        else:
            raise exc


def setup(client):
    client.add_cog(cogsManager(client))
