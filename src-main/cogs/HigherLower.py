from discord import Embed, Message
from discord.ext import commands
from imports.functions import time
from random import randint

from cogs.ConfigHandler import get_prefix


class HigherLower(commands.Cog):

    def __init__(self, bot: commands.Bot) -> None:
        super().__init__()
        self.bot = bot
    
    def embed_logger(self, txt_log, channel_id, error_type=None):
        if error_type == 'succ':
            colour = 0x00a86b
        elif error_type == 'error':
            colour = 0xf05e23
        else:
            colour = 0xad3998
        embed = Embed(title='📖 Info 📖', colour=colour)
        embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar.url)
        embed.add_field(name="higher_lower", value=txt_log)
        embed.set_footer(text=f'🆔 {channel_id} ⏳' + time())
        return embed
    
    @commands.Cog.listener()
    async def on_ready(self): 
        for guild in self.bot.guilds:
            for channel_id in self.bot.db.get_channel(guild.id, 'HigherLower'):
                if (data := self.bot.db.get_HigherLower_data(channel_id)) is None:
                    self.bot.db.HigherLower_game_switch(channel_id, True)
                    self.bot.db.update_HigherLower_data(channel_id, 0, randint(1, self.bot.db.get_game_setting(guild.id, 'HL_max_number')), self.bot.user.id)
    
    @commands.Cog.listener()
    async def on_message(self, msg: Message):
        if msg.author.bot:
            pass
        elif msg.channel.id in self.bot.db.get_channel(msg.guild.id, 'HigherLower'):
            data = self.bot.db.get_HigherLower_data(msg.channel.id)

            if data and not (msg.author.bot or msg.content[0] in (await get_prefix(self.bot, msg))):

                if data['count'] == self.bot.db.get_game_setting(msg.guild.id, 'HL_max_reply') and data['last_user_id'] == msg.author.id:
                    await msg.delete()
                
                    for channel_id in self.bot.db.get_channel(msg.guild.id, 'Log'):
                        await self.bot.get_channel(channel_id).send(embed=self.embed_logger(f'{msg.author.name} tried to guess more than the maximum consecutive replies allowed.',
                                                                    msg.channel.id, 'error'))
                else:

                    try:
                        sub_count = int(msg.content.split(' ')[0])

                        if data['last_user_id'] != msg.author.id:
                            self.bot.db.update_HigherLower_data(msg.channel.id, 0, data['number'], msg.author.id)
                            data = self.bot.db.get_HigherLower_data(msg.channel.id)
                        
                        if sub_count < data['number']:
                            self.bot.db.update_HigherLower_data(msg.channel.id, data['count'] + 1, data['number'], msg.author.id)
                            await msg.add_reaction('⬆️')
                        elif sub_count > data['number']:
                            self.bot.db.update_HigherLower_data(msg.channel.id, data['count'] + 1, data['number'], msg.author.id)
                            await msg.add_reaction('⬇️')
                        else:
                            await msg.add_reaction('⭐')
                            await msg.channel.send(f"{msg.author.mention} Correct my love! I have granted you a star ⭐")

                            self.bot.db.update_HigherLower_data(msg.channel.id, 0, randint(1, self.bot.db.get_game_setting(msg.guild.id, 'HL_max_number')), self.bot.user.id)
                            self.bot.db.update_lb('HigherLower', msg.channel.id, msg.author.id)
                    except ValueError:
                        await msg.delete()

                        for channel_id in self.bot.db.get_channel(msg.guild.id, 'Log'):
                            await self.bot.get_channel(channel_id).send(embed=self.embed_logger(f'{msg.author.name} thought letters are numbers.',
                                                                        msg.channel.id, 'error'))
                                                
async def setup(bot: commands.Bot):
    await bot.add_cog(HigherLower(bot))