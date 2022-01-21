import datetime
import discord
from discord.ext import commands

from cogs.config_handler import master_logger_id, get_configdata
from imports.functions import time


class tool_Commands(commands.Cog):

    def __init__(self, client):
        self.client = client

    def embed_logger(self, txt_log, channel_id):
        embed = discord.Embed(title='📖 Info 📖', colour=0xad3998)
        embed.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
        embed.add_field(name="General commands ", value=txt_log)
        embed.set_footer(text=f'🆔 {channel_id} ⏳' + time())
        return embed

    @commands.command(aliases=['avt'],
                      brief=f"avatar/avt <user>` - to send the embed with the avatar of the specified user.",
                      no_pm=True)
    async def Avatar(self, ctx, user: discord.Member = None):
        if user is None:
            user = ctx.author
        embed = discord.Embed(title=f"Avatar of {user}", color=0xad3998)
        embed.description = f"Links: \n [png]({str(user.avatar_url).replace('webp', 'png')}) | [jpg]" \
                            f"({str(user.avatar_url).replace('webp', 'jpg')}) | [webp]({user.avatar_url})"
        embed.set_image(url=user.avatar_url)
        await ctx.send(embed=embed)
        for channel_id in (await get_configdata(self.client, ctx.guild.id, 'logger_ids')) + master_logger_id:
            if self.client.get_channel(channel_id) in ctx.guild.channels or channel_id in master_logger_id:
                await self.client.get_channel(channel_id).send(
                    embed=self.embed_logger(f"{ctx.author} asked for {user}'s avatar.", ctx.channel.id))

    @commands.command(brief=f"info <user>` - to send the embed with info about the user.", no_pm=True)
    @commands.cooldown(1, 60, commands.BucketType.channel)
    async def Info(self, ctx, user: discord.Member = None):
        if user is None:
            user = ctx.author
        embed = discord.Embed(title=f"Some (ir)relevant info about {user}", color=0xad3998)
        # Alt checker
        if (datetime.datetime.now() - user.created_at).total_seconds() < 86400 * 3:
            alt = " ⚠️ new account ⚠️"
        else:
            alt = " "
        # Activity checker
        if user.activity is None:
            act = None
        else:
            act = str(user.activity.type).removeprefix('ActivityType.')
        embed.description = (f"Name: {user.name} | Nick: {user.nick}\n"
                             f"Bot: {user.bot}\n"
                             f"id: {user.id}\n"
                             f"Acc made at: {user.created_at.strftime('%d-%m-%y %H:%M')} {alt}\n"
                             f"Joined guild at: {user.joined_at.strftime('%d-%m-%y %H:%M')}\n"
                             f"On mobile: {user.is_on_mobile()}\n"
                             f"Status: {user.status}\n"
                             f"Activity: {act}")
        embed.set_author(name=user.name, url=f" https://discordapp.com/users/{user.id}/", icon_url=user.avatar_url)
        embed.set_thumbnail(
            url="https://media1.tenor.com/images/b25bb53205e7087790cd133ff960c222/tenor.gif?itemid=7914122")
        embed.set_footer(text=f"You can only use this command every minute, don't be too much off a stalker :)")
        await ctx.send(embed=embed)
        for channel_id in (await get_configdata(self.client, ctx.guild.id, 'logger_ids')) + master_logger_id:
            if self.client.get_channel(channel_id) in ctx.guild.channels or channel_id in master_logger_id:
                await self.client.get_channel(channel_id).send(
                    embed=self.embed_logger(f"{ctx.author} asked for info about {user}.", ctx.channel.id))

    @commands.command(aliases=[''],
                      brief=f"dm <on/off>` to turn game error DMs on/off. This command can only be used every 2min.",
                      no_pm=True)
    @commands.cooldown(1, 120, commands.BucketType.user)
    async def Dm(self, ctx, preff):
        if preff == 'on':
            self.client.db.update_dm_preff(ctx.author.id, 1)
            await ctx.send(f"DM preferences for user {ctx.author.name} changed to True")
        elif preff == 'off':
            self.client.db.update_dm_preff(ctx.author.id, 0)
            await ctx.send(f"DM preferences for user {ctx.author.name} changed to False")

    @commands.command(aliases=['lb'],
                      brief=f"lb <channel*>` to display the leaderboard of the specified channel. If no channel"
                            f" is specified, the leaderboard of the current channel will be shown.",
                      no_pm=True)
    async def Leaderboard(self, ctx, channel: discord.TextChannel = None):
        if channel is None:
            channel = ctx.channel
        data = self.client.db.get_lb(channel.id, (await get_configdata(self.client, ctx.guild.id, 'lb_size')))
        if not data:
            title = " ⚠️ Error ⚠️"
            description = f"No leaderboard available for this channel. \nAre you perhaps not in a game channel? Use" \
                          f" `{(await get_configdata(self.client, ctx.guild.id, 'command_prefix'))}lb <channel>`" \
                          f" instead!"
        else:
            description = ""
            lb_prefix = ['🥇', '🥈', '🥉'] + [str(i) for i in range(4, (
                await get_configdata(self.client, ctx.guild.id, 'lb_size')) + 1)]
            for entry in data:
                description += f"{lb_prefix[data.index(entry)]}: {(await self.client.fetch_user(entry[1])).mention}" \
                               f" - **{entry[2]}**\n"
            title = f"Leaderboard for {channel.name}"
        embed = discord.Embed(title=title, description=description, color=0xad3998)
        await ctx.send(embed=embed)
        for channel_id in (await get_configdata(self.client, ctx.guild.id, 'logger_ids')) + master_logger_id:
            if self.client.get_channel(channel_id) in ctx.guild.channels or channel_id in master_logger_id:
                await self.client.get_channel(channel_id).send(
                    embed=self.embed_logger(f"{ctx.author} requested the leaderboard for {channel.name} ",
                                            ctx.channel.id))

    @commands.command(aliases=[],
                      brief=f"score <channel*> <user*>` to display your (or the specified users) score for the game"
                            f" running in that channel. If no channel is specified, the score for the current channel"
                            f" will be shown.")
    async def Score(self, ctx, channel: discord.TextChannel = None, user: discord.Member = None):
        if channel is None:
            channel = ctx.channel
        if user is None:
            user = ctx.author
        data = self.client.db.get_score(channel.id, user.id)
        if data is None:
            title = " ⚠️ Error ⚠️"
            description = f"No score available for this channel. \nAre you perhaps not in a game channel? Use" \
                          f" `{(await get_configdata(self.client, ctx.guild.id, 'command_prefix'))}score <channel>`" \
                          f" instead!"
        else:
            title = f"Score for {channel.name}"
            description = f"{user.name} has received **{data[2]}** stars!"
        embed = discord.Embed(title=title, description=description, color=0xad3998)
        await ctx.send(embed=embed)


def setup(client):
    client.add_cog(tool_Commands(client))
