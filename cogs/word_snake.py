import discord
from discord.errors import Forbidden
from discord.ext import commands
from discord.message import Message
from imports.functions import *
from cogs.config_handler import master_logger_id, get_configdata
from random import choice


class word_snake(commands.Cog):

    def __init__(self, client: commands.Bot):
        self.client = client

    def embed_logger(self, txt_log, channel_id, error_type=None):
        if error_type == 'succ':
            colour = 0x00a86b
        elif error_type == 'error':
            colour = 0xf05e23
        elif error_type == 'fail':
            colour = 0xb80f0a
        elif error_type == 's':  # system game commands
            colour = 0x1034a6
        else:
            colour = 0xad3998
        embed = discord.Embed(title='📖 Info 📖', colour=colour)
        embed.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
        embed.add_field(name="word_snake ", value=txt_log)
        embed.set_footer(text=f'🆔 {channel_id} ⏳' + time())
        return embed

    @commands.Cog.listener()
    async def on_ready(self):  # Control for Bot admin
        for channel_id in master_logger_id:
            await self.client.get_channel(channel_id).send(embed=self.embed_logger(" word_snake has been loaded.",
                                                                                   channel_id))

        for guilds in self.client.guilds:  # Running game reminder
            for channel_id in (await get_configdata(self.client, guilds.id, 'word_snake__channel_id')):
                data = self.client.db.get_game_date('word_snake', channel_id)
                if data is not None:
                    await self.client.get_channel(channel_id).send(
                        f"I've just come back from being offline! Here is a quick reminder of where you were"
                        f" :D\nCurrent Word: **{data[3]}** \nCurrent Count: **{data[4]}**")

    @commands.command(aliases=['s'], no_pm=True)
    async def start(self, ctx, first_word=None):
        if ctx.channel.id in (await get_configdata(self.client, ctx.guild.id, 'word_snake__channel_id')):
            data = self.client.db.get_game_date('word_snake', ctx.channel.id)

            if first_word is None:  # Get random word if none is given
                first_word = choice(get_word())[0]

            if data is None and allowed_word(first_word):  # No game running + English word
                await ctx.send(f'The game has begun! \nFind a word that starts with **{first_word[-1].lower()}**.')

                self.client.db.change_game_data(ctx.author.id, first_word, ctx.message.id, ctx.channel.id, 'word_snake')
                self.client.db.ws_allowed_mistake(ctx.channel.id, 1)
                self.client.db.add_word('word_snake', first_word, ctx.channel.id)

                # Logging
                for channel_id in (await get_configdata(self.client, ctx.guild.id, 'logger_ids')) + master_logger_id:
                    if self.client.get_channel(channel_id) in ctx.guild.channels or channel_id in master_logger_id:
                        await self.client.get_channel(channel_id).send(
                            embed=self.embed_logger(f' {ctx.author.name} started a game with word ' + first_word + '.',
                                                    ctx.channel.id, 's'))

            elif data is not None:  # Already game running in the channel
                await ctx.message.delete()
                if self.client.db.get_dm_preff(ctx.author.id) == 1:
                    try:
                        await (await ctx.message.author.create_dm()).send(
                            f'A game was already running, you can always join in! The current word is **{data[3]}**!')
                    except Forbidden:
                        pass
            else:  # Not an English word
                await ctx.send("This is not a word in the English language, please only use a-z and A-Z!")

    @commands.command(aliases=["r"], no_pm=True)  # Reset game, not words
    async def reset(self, ctx: commands.Context):
        if ctx.channel.id in (await get_configdata(self.client, ctx.guild.id, 'word_snake__channel_id')):
            await ctx.message.delete()

            if self.client.db.get_game_date('word_snake', ctx.channel.id) is None:  # No running game
                await ctx.send(
                    f"No game to stop, start a game by using"
                    f" `{(await get_configdata(self.client, ctx.guild.id, 'command_prefix'))}start <first word*>`")

            else:
                self.client.db.reset_game('word_snake', ctx.channel.id)

                await ctx.send(
                    f'The game has stopped. If you would like to reset the words do'
                    f' `{(await get_configdata(self.client, ctx.guild.id, "command_prefix"))}resetwords`')

                # Logging
                for channel_id in (await get_configdata(self.client, ctx.guild.id, 'logger_ids')) + master_logger_id:
                    if self.client.get_channel(channel_id) in ctx.guild.channels or channel_id in master_logger_id:
                        await self.client.get_channel(channel_id).send(
                            embed=self.embed_logger(f' {ctx.author.name} reseted the game.', ctx.channel.id, 's'))

    @commands.command(aliases=['c'], no_pm=True)  # Display current count
    async def count(self, ctx):
        if ctx.channel.id in (await get_configdata(self.client, ctx.guild.id, 'word_snake__channel_id')):
            await ctx.message.delete()
            if self.client.db.get_game_date('word_snake', ctx.channel.id) is None:  # No game running
                count = None
            else:
                count = self.client.db.get_game_date('word_snake', ctx.channel.id)[4]
            await ctx.send(f"You have been playing for **{count}** words!")

    @commands.command(aliases=['rw'], no_pm=True)  # Reset words
    async def resetwords(self, ctx: commands.Context):
        if ctx.channel.id in (await get_configdata(self.client, ctx.guild.id, 'word_snake__channel_id')):
            self.client.db.clear_db('word_snake', ctx.channel.id)

            await ctx.message.delete()
            await ctx.send("The used words have been reset")

            # Logging
            for channel_id in (await get_configdata(self.client, ctx.guild.id, 'logger_ids')) + master_logger_id:
                if self.client.get_channel(channel_id) in ctx.guild.channels or channel_id in master_logger_id:
                    await self.client.get_channel(channel_id).send(
                        embed=self.embed_logger(f' {ctx.author.name} reseted the used words.', ctx.channel.id, 's'))

    @commands.Cog.listener()
    async def on_message(self, msg):
        if self.client.db.get_game_date('word_snake', msg.channel.id) is None:
            pass
        elif msg.author.bot:
            pass
        elif msg.content[0] == (await get_configdata(self.client, msg.guild.id, 'command_prefix')):
            pass
        # Pass for DM, no game, bot or msg starts with command prefix
        else:
            data = self.client.db.get_game_date('word_snake', msg.channel.id)
            word = data[3]
            if data[2] == msg.author.id:  # Trying to play on their own
                await msg.delete()

                if self.client.db.get_dm_preff(msg.author.id) == 1:  # Wants DM
                    try:
                        dmchannel = await msg.author.create_dm()
                        await dmchannel.send(
                            f"You replied last time sneaky human! Please do not say two words in a row yourself!"
                            f"\nThe correct word is thus still, **{word}**!")
                    except Forbidden:  # Blocked / DM disabled
                        pass

            elif not self.client.db.check_init('word_snake', msg.content, msg.channel.id):  # New word
                if allowed_word(msg.content):  # English
                    if msg.content[0].lower() != word[-1].lower():  # reject word - wrong
                        if data[6] == 1 and word[0].lower() == msg.content[0].lower():
                            self.client.db.ws_allowed_mistake(msg.channel.id, 0)

                            await msg.delete()

                            if self.client.db.get_dm_preff(msg.author.id) == 1:  # Wants DM
                                try:
                                    await (await msg.author.create_dm()).send(
                                        f"You replied with a word that matched the previous word,"
                                        f" I'll go ahead and give you the benefit of the doubt."
                                        f" So I deleted your msg so the game doesn't end.\n"
                                        f"Keep in mind that this can only happen once per word.")
                                except Forbidden:  # Blocked / DM disabled
                                    pass

                                # Logging
                                for channel_id in (await get_configdata(self.client, msg.guild.id,
                                                                        'logger_ids')) + master_logger_id:
                                    if self.client.get_channel(channel_id) in msg.guild.channels or\
                                            channel_id in master_logger_id:
                                        await self.client.get_channel(channel_id).send(embed=self.embed_logger(
                                            f'{msg.author} used up the allowed_mistake for the present word.',
                                            msg.channel.id, 'error'))
                        else:  # Wrong word + not fitting last one
                            self.client.db.reset_game('word_snake', msg.channel.id)

                            await msg.channel.send(
                                f"Your worded started with **{msg.content[0].lower()}**,"
                                f" whilst it should have started with **"
                                f"{word[-1].lower()}**.\nYou managed to reach **{data[4]}** words this game!"
                                f" \nThe game has stopped and the word has been reset.")

                            # Logging
                            for channel_id in (
                                      await get_configdata(self.client, msg.guild.id, 'logger_ids')) + master_logger_id:
                                if self.client.get_channel(channel_id) in msg.guild.channels or\
                                        channel_id in master_logger_id:
                                    await self.client.get_channel(channel_id).send(
                                        embed=self.embed_logger(f'{msg.author} failed and ended the game.',
                                                                msg.channel.id, 'fail'))

                    else:  # accept word
                        self.client.db.change_game_data(msg.author.id, msg.content, msg.id, msg.channel.id,
                                                        'word_snake')
                        self.client.db.ws_allowed_mistake(msg.channel.id, 1)
                        self.client.db.add_word('word_snake', msg.content, msg.channel.id)
                        self.client.db.add_user_data('word_snake', msg.author.id, msg.channel.id)

                        await msg.add_reaction('✅')

                else:  # Not English -> won't punish for it
                    await msg.delete()

                    if self.client.db.get_dm_preff(msg.author.id) == 1:  # Wants DM
                        try:
                            await (await msg.author.create_dm()).send(
                                f"I only accept English words with at least 2 letters. (a-z or A-Z)"
                                f" The current word is therefore still, **{word}**!")
                        except Forbidden:  # Blocked / DM disabled
                            pass

                    # Logging
                    for channel_id in\
                            (await get_configdata(self.client, msg.guild.id, 'logger_ids')) + master_logger_id:
                        if self.client.get_channel(channel_id) in msg.guild.channels or channel_id in master_logger_id:
                            await self.client.get_channel(channel_id).send(embed=self.embed_logger(
                                f'{msg.author} submitted a word out of rule bounds - {msg.content}', msg.channel.id,
                                'fail'))
            else:  # Used word
                await msg.delete()

                if self.client.db.get_dm_preff(msg.author.id) == 1:  # Wants DM
                    try:
                        await (await msg.author.create_dm()).send(
                            f"This word is already used, try an other one. The current word is therefore still,"
                            f" **{word}**!")
                    except Forbidden:  # Blocked / DM disabled
                        pass

                # Logging
                for channel_id in (await get_configdata(self.client, msg.guild.id, 'logger_ids')) + master_logger_id:
                    if self.client.get_channel(channel_id) in msg.guild.channels or channel_id in master_logger_id:
                        await self.client.get_channel(channel_id).send(
                            embed=self.embed_logger(f'{msg.author} submitted an used word.', msg.channel.id, 'error'))

    # Safety measures -> last user deleting/editing msg to troll
    @commands.Cog.listener()
    async def on_message_delete(self, msg: Message):
        if msg.channel.id in (await get_configdata(self.client, msg.guild.id, 'word_snake__channel_id')):
            data = self.client.db.get_game_date('word_snake', msg.channel.id)

            if msg.author.bot or data is None:  # No game running, bot
                pass

            elif data[2] == msg.author.id:  # Is last user
                if msg.content == data[3] and msg.id == data[5]:
                    await msg.channel.send(embed=discord.Embed(title=f"Warning! Deleted message by {msg.author.name}",
                                                               description=f"The last word is: **{msg.content}**"))

                    # Logging
                    for channel_id in\
                            (await get_configdata(self.client, msg.guild.id, 'logger_ids')) + master_logger_id:
                        if self.client.get_channel(channel_id) in msg.guild.channels or channel_id in master_logger_id:
                            await self.client.get_channel(channel_id).send(
                                embed=self.embed_logger(f'{msg.author} deleted their msg, which was the last word.',
                                                        msg.channel.id, 'error'))

    @commands.Cog.listener()
    async def on_message_edit(self, msg1: Message, msg2):
        if msg1.channel.id in (await get_configdata(self.client, msg1.guild.id, 'word_snake__channel_id')):
            data = self.client.db.get_game_date('word_snake', msg1.channel.id)
            if msg1.author.bot or data is None:  # No game running, bot
                pass

            elif data[2] == msg1.author.id:  # Last user
                if msg1.content == data[3] and msg1.id == data[5]:
                    await msg1.channel.send(embed=discord.Embed(title=f"Warning! Edited message by {msg1.author.name}",
                                                                description=f"The last word is: **{msg1.content}**"))

                    # Logging
                    for Channel_id in\
                            (await get_configdata(self.client, msg1.guild.id, 'logger_ids')) + master_logger_id:
                        if self.client.get_channel(Channel_id) in msg1.guild.channels or Channel_id in master_logger_id:
                            await self.client.get_channel(Channel_id).send(embed=self.embed_logger(
                                f'{msg1.author} edited their last msg, which was the last word.', msg1.channel.id,
                                'error'))


def setup(client):
    client.add_cog(word_snake(client))
