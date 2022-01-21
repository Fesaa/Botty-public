import discord
import emoji
from discord.errors import Forbidden
from discord.ext import commands

from cogs.config_handler import get_configdata, master_logger_id
from imports.functions import time


class BreakIt(Exception):
    pass


class Polly(commands.Cog):
    def __init__(self, client):
        self.client = client

    def embed_logger(self, txt_log, channel_id, error_type=None):
        if error_type == 'succ':
            colour = 0x00a86b
        else:
            colour = 0xb80f0a
        embed = discord.Embed(title='📖 Info 📖', colour=colour)
        embed.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
        embed.add_field(name="Polly", value=txt_log)
        embed.set_footer(text=f'🆔 {channel_id} ⏳' + time())
        return embed

    @commands.command(
        brief=f"poll <question> | <emoji name 1> <answer 1> | <emoji name 2> <answer 2> | ...`"
              f" - Starts a poll, only works in a specified channel.")
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def poll(self, ctx, *, arg: str):
        for role_id in (await get_configdata(self.client, ctx.guild.id, 'poll_maker_id')):
            if ctx.guild.get_role(role_id) in ctx.author.roles:
                try:
                    pollinfo = arg.split('|')
                    question = pollinfo[0]
                    answer_list = []
                    emoji_list = []
                    await ctx.message.delete()
                    for entry in pollinfo[1:]:
                        entry_list = entry.removeprefix(" ").removesuffix(" ").replace("  ", " ").split(' ')
                        if emoji.emojize(":" + entry_list[0] + ":", use_aliases=True) != ":" + entry_list[0] + ":":
                            emoji_list.append(entry_list[0])
                            answer_list.append(" ".join(entry_list[1:]))
                        else:
                            emojii = discord.utils.get(ctx.guild.emojis, name=entry_list[0])
                            if emojii is not None:
                                emoji_list.append(emojii)
                                answer_list.append(entry_list[1])
                            else:
                                await (await ctx.author.create_dm()).send(
                                    f"{entry_list[0]} is not the name of an emoji. The poll will not be made.")
                                raise BreakIt
                    text = question + "\n"
                    for entry in emoji_list:
                        try:
                            text += emoji.emojize(":" + entry + ":", use_aliases=True) + " - " + answer_list[
                                emoji_list.index(entry)] + "\n"
                        except TypeError:
                            text += "<:" + entry.name + ":" + str(entry.id) + ">" + " - " + answer_list[
                                emoji_list.index(entry)] + "\n"
                    polmsg = await ctx.channel.send(text)
                    if ctx.channel.id in (await get_configdata(self.client, ctx.guild.id, 'polly_channel_id')):
                        for channel_id in\
                                (await get_configdata(self.client, ctx.guild.id, 'logger_ids')) + master_logger_id:
                            if self.client.get_channel(channel_id) in ctx.guild.channels or\
                                    channel_id in master_logger_id:
                                await self.client.get_channel(channel_id).send(
                                    embed=self.embed_logger(f'{ctx.author} has made a poll -- {question} \n'
                                                            + "https://discord.com/channels/" + str(ctx.guild.id)
                                                            + "/" + str(ctx.channel.id) + "/" + str(polmsg.id),
                                                            ctx.channel.id, 'succ'))
                    for entry in emoji_list:
                        try:
                            await polmsg.add_reaction(emoji.emojize(":" + entry + ":", use_aliases=True))
                        except TypeError:
                            await polmsg.add_reaction(entry)
                except BreakIt:
                    pass
                break
        else:
            if self.client.db.get_dm_preff(ctx.author.id) == 1:
                await ctx.message.delete()
                try:
                    await (await ctx.author.create_dm()).send(f"You do not have the role requirement to make a poll"
                                                              ", request the roll from one of the server moderators.\n"
                                                              "If you think you do have the role,"
                                                              " contact a Botty admin.")
                except Forbidden:
                    pass

    @commands.Cog.listener()
    async def on_reaction_add(self, rec, user):
        for role_id in (await get_configdata(self.client, rec.message.guild.id, 'poll_maker_id')):
            if rec.message.guild.get_role(role_id) in user.roles:
                if str(rec) == '❌' and rec.message.author == self.client.user:
                    if rec.message.channel.id in \
                            (await get_configdata(self.client, rec.message.guild.id, 'polly_channel_id')):
                        for channel_id in (await get_configdata(self.client, rec.message.guild.id,
                                                                'logger_ids')) + master_logger_id:
                            if self.client.get_channel(channel_id) in rec.message.guild.channels or\
                                    role_id in master_logger_id:
                                await self.client.get_channel(channel_id).send(
                                    embed=self.embed_logger(f'{user} has removed a poll', rec.message.channel.id,
                                                            'fail'))
                    await rec.message.delete()
                break


def setup(client):
    client.add_cog(Polly(client))
