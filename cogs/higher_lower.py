import discord
from discord.ext import commands
from imports.functions import time
from cogs.config_handler import get_configdata, master_logger_id
from random import randint


class higher_lower(commands.Cog):

    def __init__(self, client):
        self.client = client

    def embed_logger(self, txt_log, channel_id, error_type=None):
        if error_type == 'succ':
            colour = 0x00a86b
        elif error_type == 'error':
            colour = 0xf05e23
        else:
            colour = 0xad3998
        embed = discord.Embed(title='📖 Info 📖', colour=colour)
        embed.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
        embed.add_field(name="higher_lower", value=txt_log)
        embed.set_footer(text=f'🆔 {channel_id} ⏳' + time())
        return embed

    @commands.Cog.listener()
    async def on_ready(self):
        for channel_id in master_logger_id:  # Control for Bot admin
            await self.client.get_channel(channel_id).send(embed=self.embed_logger("higher_lower has been loaded.",
                                                                                   channel_id))

        for guilds in self.client.guilds:  # Makes sure every HL channel has a number in memory
            for channel_id in (await get_configdata(self.client, guilds.id, 'HL_channel_id')):
                if channel_id != 0:
                    data = self.client.db.get_HLdata(channel_id)
                    if data is None:
                        self.client.db.update_HLdata(channel_id, randint(0, 1000), 0, 0)

    @commands.Cog.listener()
    async def on_message(self, msg):
        if isinstance(msg.channel,
                      discord.channel.DMChannel) or msg.author == self.client.user:
            pass
        elif msg.channel.id not in (await get_configdata(self.client, msg.guild.id, 'HL_channel_id')):
            pass
        elif msg.content[0] == (await get_configdata(self.client, msg.guild.id, 'command_prefix')):
            pass
        else:
            data = self.client.db.get_HLdata(msg.channel.id)
            if data[3] == (await get_configdata(self.client, msg.guild.id, 'HL_max_reply')) and \
                    data[2] == msg.author.id:  # Max guessed check
                await msg.delete()
                if self.client.db.get_dm_preff(msg.author.id) == 1:
                    try:
                        await (await msg.author.create_dm()).send(
                            "You already guessed tree times in a row without getting the answer. You can try again")
                    except AttributeError:
                        pass
                for channel_id in (await get_configdata(self.client, msg.guild.id, 'logger_ids')) + master_logger_id:
                    if self.client.get_channel(channel_id) in msg.guild.channels or channel_id in master_logger_id:
                        await self.client.get_channel(channel_id).send(
                            embed=self.embed_logger(f' {msg.author.name} tried to guess more than 3 times in a row',
                                                    msg.channel.id, 'error'))
            else:
                try:
                    submitted_count = int(msg.content.partition(' ')[0])  # Can type after guess
                    if data[2] != msg.author.id:
                        self.client.db.update_HLdata(msg.channel.id, data[1], msg.author.id, 0)
                        data = self.client.db.get_HLdata(msg.channel.id)
                    if submitted_count < data[1]:
                        self.client.db.update_HLdata(msg.channel.id, data[1], msg.author.id, data[3] + 1)
                        await msg.add_reaction('⬆️')
                    elif submitted_count > data[1]:
                        self.client.db.update_HLdata(msg.channel.id, data[1], msg.author.id, data[3] + 1)
                        await msg.add_reaction('⬇️')
                    else:
                        await msg.add_reaction('⭐')
                        await msg.channel.send(f"{msg.author.mention} Correct my love! I have granted you a star ⭐")
                        self.client.db.update_HLdata(msg.channel.id, randint(0, 1000), msg.author.id, 0)
                        self.client.db.add_user_data('HL', msg.author.id, msg.channel.id)
                        for channel_id in\
                                (await get_configdata(self.client, msg.guild.id, 'logger_ids')) + master_logger_id:
                            if self.client.get_channel(channel_id) in msg.guild.channels or \
                                    channel_id in master_logger_id:
                                await self.client.get_channel(channel_id).send(embed=self.embed_logger(
                                    f' {msg.author.name} found the right number! {submitted_count}', msg.channel.id,
                                    's'))
                except ValueError:
                    await msg.delete()
                    if self.client.db.get_dm_preff(msg.author.id) == 1:
                        try:
                            await (await msg.author.create_dm()).send(
                                "Your message has to start with a number!"
                                " You can talk all the garbage you want after that 💯")
                        except AttributeError:
                            pass
                    for channel_id in\
                            (await get_configdata(self.client, msg.guild.id, 'logger_ids')) + master_logger_id:
                        if self.client.get_channel(channel_id) in msg.guild.channels or channel_id in master_logger_id:
                            await self.client.get_channel(channel_id).send(
                                embed=self.embed_logger(f' {msg.author.name} thought letters are numbers.',
                                                        msg.channel.id, 'error'))


def setup(client):
    client.add_cog(higher_lower(client))
