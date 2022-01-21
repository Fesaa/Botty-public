from discord import Embed
import discord
from discord.channel import DMChannel
from discord.ext import commands
from discord.reaction import Reaction
from discord.user import User
from cogs.config_handler import get_configdata, master_logger_id
from imports.functions import *
from random import randint


class ntbpl(commands.Cog):

    def __init__(self, client: commands.Bot):
        self.client = client

    def embed_logger(self, txt_log, channel_id, error_type=None):
        if error_type == 'succ':
            colour = 0x00a86b
        elif error_type == 'error':
            colour = 0xf05e23
        elif error_type == 'fail':
            colour = 0xb80f0a
        elif error_type == 's':
            colour = 0x1034a6
        else:
            colour = 0xad3998
        embed = Embed(title='📖 Info 📖', colour=colour)
        embed.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
        embed.add_field(name="Name to be picked later", value=txt_log)
        embed.set_footer(text=f'🆔 {channel_id} ⏳' + time())
        return embed

    @commands.Cog.listener()
    async def on_ready(self):
        for channel_id in master_logger_id:  # Control for Bot admin
            await self.client.get_channel(channel_id).send(
                embed=self.embed_logger(" Name to be picked later has been loaded.", channel_id))

        for guilds in self.client.guilds:  # Reminder game was running
            for ids in (await get_configdata(self.client, guilds.id, 'ntbpl_channel_id')):
                data = self.client.db.get_ntbpl_data(ids)
                if data is not None:
                    await self.client.get_channel(ids).send(
                        f"A game was running! I will present to you {data[2]} letters in a specific order,"
                        f" you will have to reply with a word that has those letters in the same order!\n"
                        f"The letters now are: **{data[4]}**")

    @commands.command(aliases=["b"], no_pm=True)
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def begin(self, ctx: commands.Context, count=None):
        if ctx.channel.id in (await get_configdata(self.client, ctx.guild.id, 'ntbpl_channel_id')):
            if 5 >= int(count) >= 2:  # Check if count is allowed
                sub_count = count

            else:  # Not given or out of bounds -> choose random
                sub_count = randint(2, 5)

            if sub_count is not None:
                self.client.db.change_ntbpl_data(ctx.channel.id, self.client.user.id, sub_count, 1, 0, 0, 0, 0)

                data = self.client.db.get_ntbpl_data(ctx.channel.id)

                await ctx.send(
                    f"A game has started! I will present to you {data[2]} letters in a specific order,"
                    f" you will have to reply with a word that has those letters in the same order!\n"
                    f"The letters now are: **{data[4]}**")

                # Logging
                for channel_id in (await get_configdata(self.client, ctx.guild.id, 'logger_ids')) + master_logger_id:
                    if self.client.get_channel(channel_id) in ctx.guild.channels or channel_id in master_logger_id:
                        await self.client.get_channel(channel_id).send(
                            embed=self.embed_logger(f' {ctx.author} started a game with {sub_count} lettters',
                                                    ctx.channel.id, 's'))

    @commands.command(no_pm=True)
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def stop(self, ctx):
        if ctx.channel.id in (await get_configdata(self.client, ctx.guild.id, 'ntbpl_channel_id')):
            if self.client.db.get_ntbpl_data(ctx.channel.id) is None:  # No game to stop
                await ctx.send(
                    f"No game was running, you can start a game with"
                    f" `{(await get_configdata(self.client, ctx.guild.id, 'command_prefix'))}begin <count>`!")

            else:
                self.client.db.stop_ntbpl(ctx.channel.id)

                await ctx.send(
                    f"Stopped the game, you can start a game with"
                    f" `{(await get_configdata(self.client, ctx.guild.id, 'command_prefix'))}begin <count>`! ")

                # Logging
                for channel_id in (await get_configdata(self.client, ctx.guild.id, 'logger_ids')) + master_logger_id:
                    if self.client.get_channel(channel_id) in ctx.guild.channels or channel_id in master_logger_id:
                        await self.client.get_channel(channel_id).send(
                            embed=self.embed_logger(f' {ctx.author} stopped the game', ctx.channel.id, 's'))

    @commands.Cog.listener()
    async def on_message(self, msg):
        if isinstance(msg.channel, discord.channel.DMChannel) or msg.author.bot:
            pass
        elif msg.channel.id not in (await get_configdata(self.client, msg.guild.id, 'ntbpl_channel_id')):
            pass
        elif msg.content[0] == (await get_configdata(self.client, msg.guild.id, 'command_prefix')):
            pass
            # Pass for DM, Bot, no game channel or starts with command prefix
        elif self.client.db.get_ntbpl_data(msg.channel.id) is not None:  # Game running
            data = self.client.db.get_ntbpl_data(msg.channel.id)

            sub_word = msg.content.partition(' ')[0]  # Lets you type after submission

            if msg.author.id != data[1]:  # New author
                if data[4] in sub_word.lower() and not self.client.db.check_init('ntbpl', sub_word,
                                                                                 msg.channel.id) and allowed_word(
                        sub_word):  # Letters, new word and English
                    self.client.db.add_word('ntbpl', sub_word, msg.channel.id)
                    self.client.db.add_user_data('ntbpl', msg.author.id, msg.channel.id)
                    self.client.db.change_ntbpl_data(msg.channel.id, msg.author.id, data[2], 1, 0, 0, 0, 0)

                    await msg.add_reaction('✅')

                    data = self.client.db.get_ntbpl_data(msg.channel.id)
                    await msg.channel.send(f"The new letters are **{data[4]}**")

                    # Logging
                    for channel_id in\
                            (await get_configdata(self.client, msg.guild.id, 'logger_ids')) + master_logger_id:
                        if self.client.get_channel(channel_id) in msg.guild.channels or channel_id in master_logger_id:
                            await self.client.get_channel(channel_id).send(
                                embed=self.embed_logger(f' {msg.author} found the word {sub_word}', msg.channel.id,
                                                        'succ'))
                else:
                    if self.client.db.check_init('ntbpl', sub_word, msg.channel.id):  # Already used
                        await msg.add_reaction('🔁')

                    else:  # Not english or not with the letters
                        await msg.add_reaction('❌')
            else:
                await msg.delete()

    @commands.command(no_pm=True)
    async def skip(self, ctx: commands.Context):
        if ctx.message.channel.id in \
                (await get_configdata(self.client, ctx.guild.id, 'ntbpl_channel_id')):  # In game channel
            data = self.client.db.get_ntbpl_data(ctx.channel.id)

            if data is not None:  # Game running
                self.client.db.ntbpl_skip_handler(ctx.channel.id, 0, 0, 1, ctx.message.id)

                await ctx.message.add_reaction('🇸')

    @commands.Cog.listener()
    async def on_reaction_add(self, rec: Reaction, user: User):
        if isinstance(rec.message.channel, DMChannel):
            pass
        elif user.bot or rec.message.channel.id not in \
                (await get_configdata(self.client, rec.message.guild.id, 'ntbpl_channel_id')):
            pass
        # Pass for DM, Bot and not in game channel
        elif str(rec) == '🇸':  # Skip reaction
            data = self.client.db.get_ntbpl_data(rec.message.channel.id)

            if data[7] == 1 and int(rec.message.id) == int(data[8]):  # Want to skip, on the skip msg
                if data[5] < 3:  # Add skip
                    self.client.db.ntbpl_skip_handler(rec.message.channel.id, data[5] + 1, 0, 1, data[8])

                    data = self.client.db.get_ntbpl_data(rec.message.channel.id)

                if data[5] == 3:  # Change skip to True (1 in data[6])
                    self.client.db.ntbpl_skip_handler(rec.message.channel.id, data[5], 1, 1, data[8])

                    data = self.client.db.get_ntbpl_data(rec.message.channel.id)

                if data[6]:  # Skip
                    self.client.db.change_ntbpl_data(data[0], data[1], data[2], 1, 0, 0, 0, 0)

                    data = self.client.db.get_ntbpl_data(rec.message.channel.id)

                    await self.client.get_channel(rec.message.channel.id).send(f"The new letters are **{data[4]}**")

    @commands.Cog.listener()
    async def on_reaction_remove(self, rec: Reaction, user: User):
        if isinstance(rec.message.channel, DMChannel):
            pass
        elif user.bot or rec.message.channel.id not in\
                (await get_configdata(self.client, rec.message.guild.id, 'ntbpl_channel_id')):
            pass
        # Pass for DM, Bot and not in game channel
        elif str(rec) == '🇸':
            data = self.client.db.get_ntbpl_data(rec.message.channel.id)

            if data[7] == 1 and rec.message.id == data[8]:  # Remove a "want skip"
                self.client.db.ntbpl_skip_handler(rec.message.channel.id, data[5] - 1, 0, 1, data[8])

    @commands.command(aliases=['cw'], no_pm=True)
    @commands.cooldown(1, 300, commands.BucketType.user)
    async def clearwords(self, ctx: commands.Context):
        if ctx.message.channel.id in (await get_configdata(self.client, ctx.guild.id, 'ntbpl_channel_id')):
            self.client.db.clear_db('ntbpl', ctx.channel.id)

            await ctx.message.delete()
            await ctx.send("The used words have been reset")

            # Logging
            for channel_id in (await get_configdata(self.client, ctx.guild.id, 'logger_ids')) + master_logger_id:
                if self.client.get_channel(channel_id) in ctx.guild.channels or channel_id in master_logger_id:
                    await self.client.get_channel(channel_id).send(
                        embed=self.embed_logger(f' {ctx.author} cleared the words', ctx.channel.id, 's'))


def setup(client):
    client.add_cog(ntbpl(client))
