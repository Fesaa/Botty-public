from discord import Embed, Message
from discord.ext import commands
from imports.functions import *
from cogs.config_handler import get_prefix
from random import choice


class WordSnake(commands.Cog):

    def __init__(self, bot: commands.Bot) -> None:
        super().__init__()
        self.bot = bot

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
        embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar.url)
        embed.add_field(name="word_snake ", value=txt_log)
        embed.set_footer(text=f'🆔 {channel_id} ⏳' + time())
        return embed
    
    @commands.Cog.listener()
    async def on_ready(self): 
        for guild in self.bot.guilds:
            for channel_id in self.bot.db.get_channel(guild.id, 'WordSnake'):
                if data := self.bot.db.get_WordSnake_data(channel_id):
                    await self.bot.get_channel(channel_id).send(f"I've just come back from being offline! Here is a quick reminder of where you were"
                                                                f" :D\nCurrent Word: **{data['last_word']}** \nCurrent Count: **{data['count']}**")

    @commands.command(aliases=['s'], no_pm=True)
    async def start(self, ctx: commands.Context, first_word: str=None):
        if ctx.channel.id in self.bot.db.get_channel(ctx.guild.id, 'WordSnake'):
            data = self.bot.db.get_WordSnake_data(ctx.channel.id)
        
            if first_word is None:
                first_word = "5"
                while not allowed_word(first_word):
                    first_word = choice(get_word())[0]
            
            if data is None and allowed_word(first_word):
                await ctx.send(f'The game has begun! \nFind a word that starts with **{first_word[-1].lower()}**.')

                self.bot.db.WordSnake_game_switch(ctx.channel.id, True)
                self.bot.db.update_WordSnake_data(ctx.channel.id, ctx.author.id, first_word, ctx.message.id, 0)
                self.bot.db.allowed_mistakes(ctx.channel.id, self.bot.db.get_game_setting(ctx.guild.id, 'WS_wrong_guesses'))
                self.bot.db.add_word('WordSnake', ctx.channel.id, first_word)

                for channel_id in self.bot.db.get_channel(ctx.guild.id, 'Log'):
                    await self.bot.get_channel(channel_id).send(embed=self.embed_logger(f'{ctx.author.name} started a game with word {first_word}.', ctx.channel.id, 's'))
            
            elif data is not None:
                await ctx.message.delete()
            else:
                await ctx.send("This is not a word in the English language, please only use a-z and A-Z!")
    
    @commands.command(aliases=['c'], no_pm=True)
    async def count(self, ctx: commands.Context):
        if ctx.channel.id in self.bot.db.get_channel(ctx.guild.id, 'WordSnake'):
            data = self.bot.db.get_WordSnake_data(ctx.channel.id)
            await ctx.message.delete()
            if data is None:
                await ctx.send(f'No game was running, start one with `{(await get_prefix(self.bot, ctx.message))[-1]}start <word*>`!')
            else:
                await ctx.send(f"You have been playing for **{data['count']}** words!")
    
    @commands.command(aliases=['rw'], no_pm=True)
    async def resetwords(self, ctx: commands.Context):
        if ctx.channel.id in self.bot.db.get_channel(ctx.guild.id, 'WordSnake'):
            self.bot.db.clear_words('WordSnake', ctx.channel.id)

            await ctx.message.delete()
            await ctx.send("The used words have been reset")

            for channel_id in self.bot.db.get_channel(ctx.guild.id, 'Log'):
                 await self.bot.get_channel(channel_id).send(embed=self.embed_logger(f' {ctx.author.name} reset the used words.', ctx.channel.id, 's'))
    
    @commands.Cog.listener()
    async def on_message_delete(self, msg: Message):
        if msg.channel.id in self.bot.db.get_channel(msg.guild.id, 'WordSnake'):
            data = self.bot.db.get_WordSnake_data(msg.channel.id)

            if data:
                if data['msg_id'] == msg.id:
                    await msg.channel.send(embed=Embed(title=f"Warning! Deleted message by {msg.author.name}",description=f"The last word is: **{msg.content}**", colour=0xad3998))
        
                    for channel_id in self.bot.db.get_channel(msg.guild.id, 'Log'):
                        await self.bot.get_channel(channel_id).send(embed=self.embed_logger(f'{msg.author} deleted their msg, which was the last word.', msg.channel.id, 'error'))
    
    @commands.Cog.listener()
    async def on_message_edit(self, msg1: Message, msg2: Message):
        if msg1.channel.id in self.bot.db.get_channel(msg1.guild.id, 'WordSnake'):
            data = self.bot.db.get_WordSnake_data(msg1.channel.id)

            if data:
                if data['msg_id'] == msg1.id:
                    await msg1.channel.send(embed=Embed(title=f"Warning! Edited message by {msg1.author.name}",description=f"The last word is: **{msg1.content}**", colour=0xad3998))
        
                for channel_id in self.bot.db.get_channel(msg1.guild.id, 'Log'):
                    await self.bot.get_channel(channel_id).send(embed=self.embed_logger(f'{msg1.author} edited their last msg, which was the last word.', msg1.channel.id,'error'))
    
    @commands.Cog.listener()
    async def on_message(self, msg: Message):
        if msg.author.bot:
            pass
        elif msg.channel.id in self.bot.db.get_channel(msg.guild.id, 'WordSnake'):
            data = self.bot.db.get_WordSnake_data(msg.channel.id)

            if data and not msg.content[0] in (await get_prefix(self.bot, msg)):
                if data['last_user_id'] == msg.author.id:
                    await msg.delete()

                elif not self.bot.db.check_used_word('WordSnake', msg.channel.id, msg.content):
                    if allowed_word(msg.content):
                        if msg.content[0].lower() == data['last_word'][-1].lower():

                            self.bot.db.update_WordSnake_data(msg.channel.id, msg.author.id, msg.content, msg.id, data['count'] + 1)
                            self.bot.db.allowed_mistakes(msg.channel.id, self.bot.db.get_game_setting(msg.guild.id, 'WS_wrong_guesses'))
                            self.bot.db.add_word('WordSnake', msg.channel.id, msg.content)
                            self.bot.db.update_lb('WordSnake', msg.channel.id, msg.author.id)

                            await msg.add_reaction('✅')
                            
                        elif msg.content[0].lower() == data['last_word'][0].lower() and data['allowed_mistakes'] > 0:

                            self.bot.db.allowed_mistakes(msg.channel.id, data['allowed_mistakes'] - 1)
                            await msg.delete()

                            for channel_id in self.bot.db.get_channel(msg.guild.id, 'Log'):
                                await self.bot.get_channel(channel_id).send(embed=self.embed_logger(f'{msg.author} used an allowed mistakes point, {data["allowed_mistakes"] - 1} remaining.',
                                msg.channel.id, 'error'))
                        else:

                            self.bot.db.WordSnake_game_switch(msg.channel.id, False)

                            await msg.channel.send(f"Your worded started with **{msg.content[0].lower()}**, whilst it should have started with ** {data['last_word'][-1].lower()}**."
                                                   f"\nYou managed to reach **{data['count']}** words this game! \nThe game has stopped, you can start a new one with"
                                                   f"`{(await get_prefix(self.bot, msg))[-1]}start <word*>` and reset the words with `{(await get_prefix(self.bot, msg))[-1]}resetwords` if you'd like.")
                            
                            for channel_id in self.bot.db.get_channel(msg.guild.id, 'Log'):
                                await self.bot.get_channel(channel_id).send(embed=self.embed_logger(f'{msg.author} failed and ended the game.', msg.channel.id, 'fail'))
                    
                    else:
                        await msg.delete()

                        for channel_id in self.bot.db.get_channel(msg.guild.id, 'Log'):
                            await self.bot.get_channel(channel_id).send(embed=self.embed_logger(f'{msg.author} submitted a word out of rule bounds - {msg.content}', msg.channel.id, 'fail'))
                
                else:
                    await msg.delete()

                    for channel_id in self.bot.db.get_channel(msg.guild.id, 'Log'):
                        await self.bot.get_channel(channel_id).send(embed=self.embed_logger(f'{msg.author} submitted an used word.', msg.channel.id, 'error'))


async def setup(bot: commands.Bot):
    await bot.add_cog(WordSnake(bot))