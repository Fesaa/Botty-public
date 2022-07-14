from discord import Embed, Message, DMChannel
from discord.ext import commands
from imports.functions import *
from random import randint

from cogs.ConfigHandler import get_prefix
from Botty import Botty


class Ntbpl(commands.Cog):

    def __init__(self, bot: Botty) -> None:
        self.bot = bot
    
    async def cog_check(self, ctx: commands.Context) -> bool:
        if isinstance(ctx.channel, DMChannel) or ctx.author.bot:
            return False
        return ctx.channel.id in self.bot.db.get_channel(ctx.guild.id, 'NTBPL')
    
    def embed_logger(self, txt_log: str, channel_id: int, error_type: str = None) -> Embed:
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
        embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar.url)
        embed.add_field(name="Name to be picked later", value=txt_log)
        embed.set_footer(text=f'🆔 {channel_id} ⏳' + time())
        return embed
     
    @commands.command(aliases=["b"], no_pm=True)
    async def begin(self, ctx: commands.Context, count: str=None):
        """
        Begin a game of NTBPL, will overwrite the current game.
        """
        try:
            count = abs(int(count)) % 5
        except (ValueError, TypeError):
            count = randint(2,5)
        
        new_letters = get_NTBPL_letters(self.bot, count, ctx.channel.id)
        if self.bot.db.get_NTBPL_data(ctx.channel.id) is None:
            self.bot.db.NTBPL_game_switch(ctx.channel.id, True)
        self.bot.db.update_NTBPL_data(ctx.channel.id, count, new_letters, self.bot.user.id)

        await ctx.send(f"A game has started! I will present to you {count} letters in a specific order,"
                        f" you will have to reply with a word that has those letters in the same order!\n"
                        f"The letters now are: **{new_letters}**")
        
        for channel_id in self.bot.db.get_channel(ctx.guild.id, 'Log'):
                await self.bot.get_channel(channel_id).send(embed=self.embed_logger(f' {ctx.author} started a game with {count} letters.', ctx.channel.id, 's'))
    
    @commands.command(aliases=['cw'], no_pm=True)
    async def clearwords(self, ctx: commands.Context):
        """
        Clear all used words
        """
        self.bot.db.clear_words('NTBPL', ctx.channel.id)

        await ctx.message.delete()
        await ctx.send("The used words have been reset")

        for channel_id in self.bot.db.get_channel(ctx.guild.id, 'Log'):
                await self.bot.get_channel(channel_id).send(embed=self.embed_logger(f' {ctx.author.name} reset the used words.', ctx.channel.id, 's'))

    @commands.Cog.listener()
    async def on_message(self, msg: Message):
        if msg.author.bot:
            return
        elif msg.channel.id in self.bot.db.get_channel(msg.guild.id, 'NTBPL'):
            data = self.bot.db.get_NTBPL_data(msg.channel.id)
            sub_word = msg.content.split(' ')[0]

            if data and not (msg.author.bot or msg.content[0] in (await get_prefix(self.bot, msg))):

                if data['last_user_id'] == msg.author.id:
                    await msg.delete()
                elif not self.bot.db.check_used_word('NTBPL', msg.channel.id, sub_word):
                    if allowed_word(sub_word):

                        new_letters = get_NTBPL_letters(self.bot, data['count'], msg.channel.id)
                        self.bot.db.update_NTBPL_data(msg.channel.id, data['count'], new_letters, msg.author.id)
                        self.bot.db.add_word('NTBPL', msg.channel.id, sub_word)
                        self.bot.db.update_lb('NTBPL', msg.channel.id, msg.author.id)

                        await msg.add_reaction('✅')
                        await msg.channel.send(f"The new letters are **{new_letters}**")
                    
                    else:
                        await msg.add_reaction('❌')
                else:
                    await msg.add_reaction('🔁')

async def setup(bot: Botty):
    await bot.add_cog(Ntbpl(bot))