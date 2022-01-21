import asyncio
import discord
from discord.ext import commands
from discord.message import Message
from random import choice, randint
from enchant import Dict
from cogs.config_handler import get_configdata, master_logger_id
from re import match
from imports.functions import time, get_word

HANGMANPICS = ["https://media.discordapp.net/attachments/869315104271904768/874025738238562344/01.png",
               "https://media.discordapp.net/attachments/869315104271904768/874025739098419300/02.png",
               "https://media.discordapp.net/attachments/869315104271904768/874025741354934272/04.png",
               "https://media.discordapp.net/attachments/869315104271904768/874025742797783150/05.png",
               "https://media.discordapp.net/attachments/869315104271904768/874025743678586960/06.png",
               "https://media.discordapp.net/attachments/869315104271904768/874025745524088843/07.png",
               "https://media.discordapp.net/attachments/869315104271904768/874025746828509204/08.png",
               "https://media.discordapp.net/attachments/869315104271904768/874025747881275422/09.png"]

REACTIONS = ['🇦', '🇧', '🇨', '🇩', '🇪', '🇫', '🇬', '🇭', '🇮', '🇯', '🇰', '🇱', '🇲', '🇳', '🇴', '🇵', '🇶', '🇷',
             '🇸', '🇹', '🇺', '🇻', '🇼', '🇽', '🇾', '🇿']
SWITCHER = {'🇦': 'a',
            '🇧': 'b',
            '🇨': 'c',
            '🇩': 'd',
            '🇪': 'e',
            '🇫': 'f',
            '🇬': 'g',
            '🇭': 'h',
            '🇮': 'i',
            '🇯': 'j',
            '🇰': 'k',
            '🇱': 'l',
            '🇲': 'm',
            '🇳': 'n',
            '🇴': 'o',
            '🇵': 'p',
            '🇶': 'q',
            '🇷': 'r',
            '🇸': 's',
            '🇹': 't',
            '🇺': 'u',
            '🇻': 'v',
            '🇼': 'w',
            '🇽': 'x',
            '🇾': 'y',
            '🇿': 'z',
            '▶️': '5'}


def hangman_str(word: str, letters: list) -> list:
    hg_str = ""
    wrong_letters = 0
    for letter in word.lower():
        if letter in letters:
            hg_str += " " + letter + " "
        else:
            hg_str += r" \_ "
    for letter in letters:
        if letter not in word.lower():
            wrong_letters += 1
    if r" \_ " in hg_str:
        found = False
    else:
        found = True
    return [hg_str, wrong_letters, found]


def prune_list(listp: list, item: str) -> list:
    while True:
        try:
            listp.remove(item)
        except ValueError:
            break
    return listp


async def clear_rec(msg: Message):
    while msg.reactions:
        for reaction in msg.reactions:
            await reaction.clear()


class hang_man(commands.Cog):

    def __init__(self, client: commands.Bot):
        self.client = client

    def embed_logger(self, txt_log, channel_id, error_type=None):
        if error_type == 'succ':
            colour = 0x00a86b
        elif error_type == 'fail':
            colour = 0xb80f0a
        elif error_type == 's':
            colour = 0x1034a6
        else:
            colour = 0xad3998
        embed = discord.Embed(title='📖 Info 📖', colour=colour)
        embed.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
        embed.add_field(name="Hangman", value=txt_log)
        embed.set_footer(text=f'🆔 {channel_id} ⏳' + time())
        return embed

    @commands.command(aliases=['hg', 'hm'])
    async def hangman(self, ctx: commands.Context):
        if ctx.channel.id in (await get_configdata(self.client, ctx.guild.id, 'hangman_id')):
            d = Dict('en_GB')  # spellings dict

            while True:  # Word to find
                word = choice(get_word())[0]
                if 5 <= len(word) <= 19 and d.check(word):
                    break

            embed = discord.Embed(title="Hangman!",
                                  description=f"#Letters: {len(word)}\n <@{ctx.author.id}>"
                                              f" \n{hangman_str(word, [])[0]}",
                                  color=0xad3998
                                  )
            embed.set_image(url=HANGMANPICS[hangman_str(word, [""])[1]])
            msg = await ctx.send(embed=embed)

            self.client.db.hangman_game_handler(msg.id, "", self.client.user.id, f"{ctx.author.id}", word)

            await msg.add_reaction('▶️')

            # Logging
            for channel_id in (await get_configdata(self.client, ctx.guild.id, 'logger_ids')) + master_logger_id:
                try:
                    await self.client.get_channel(channel_id).send(
                        embed=self.embed_logger(f"{ctx.author} start a game of hangman, the word is {word}.",
                                                ctx.channel.id, 's'))
                except AttributeError:
                    pass

            # Auto stop after inactivity
            data = self.client.db.get_hangman(msg.id)
            await asyncio.sleep(120)
            if data == self.client.db.get_hangman(msg.id):
                self.client.db.delete_hangman(msg.id)
                await msg.delete()
                await ctx.send(f"<@{ctx.author.id}> stopped your game due to inactivity")

    @commands.Cog.listener()
    async def on_reaction_add(self, rec, user):
        if user == self.client.user:
            pass
        else:
            data = self.client.db.get_hangman(rec.message.id)
            if data is not None:
                players = [int(i) for i in prune_list(data[4].split(','), '')]

                if data[3] == self.client.user.id or data[3] == players[-1]:  # id of player who is allowed to answer
                    turn = players[0]
                else:
                    turn = players[players.index(data[3]) + 1]

                if turn == players[-1]:  # id of player who has to answer next
                    next_turn = players[0]
                else:
                    next_turn = players[players.index(turn) + 1]

                used_letters = data[2].split(',')  # List of submitted letters

                try:  # Get submitted letter, return 5 for ▶️ and 0 for anything else (=> rec will be deleted)
                    sub_letter = SWITCHER[str(rec)]
                except KeyError:
                    sub_letter = 0

                if str(rec) == '▶️' and len(players) < 5:
                    if user.id not in players:  # New player, add to list
                        players.append(user.id)
                        self.client.db.hangman_game_handler(data[0], data[2], data[3], ''.join(
                            [str(player) + ',' for player in prune_list(players, '')]), data[1])

                elif str(rec) in REACTIONS and sub_letter not in used_letters and user.id == turn:
                    used_letters.append(sub_letter)

                    if hangman_str(data[1], used_letters)[2]:  # Check if word has been found
                        self.client.db.delete_hangman(rec.message.id)
                        self.client.db.add_user_data('hangman', user.id, rec.message.channel.id)
                        await rec.message.edit(embed=discord.Embed(title="You won!",
                                                                   description=f"The word you were looking for is "
                                                                               f"**{data[1]}**, congratulations!",
                                                                   color=0xad3998
                                                                   ))
                        await clear_rec(rec.message)
                        for channel_id in (await get_configdata(self.client, rec.message.guild.id,
                                                                'logger_ids')) + master_logger_id:
                            try:
                                await self.client.get_channel(channel_id).send(
                                    embed=self.embed_logger(f"{user} won the game!", rec.message.channel.id, 'succ'))
                            except AttributeError:
                                pass

                    elif hangman_str(data[1], used_letters)[1] < 8:  # Word not found, guess less than 8
                        embed = discord.Embed(title="Hangman!",
                                              description=f"#Letters: {len(data[1])}\n <@{next_turn}>"
                                                          f" \n{hangman_str(data[1], used_letters)[0]}",
                                              color=0xad3998
                                              )
                        embed.set_image(url=HANGMANPICS[hangman_str(data[1], used_letters)[1]])
                        await rec.message.edit(embed=embed)
                        self.client.db.hangman_game_handler(data[0],
                                                            ''.join([letter + ',' for letter in
                                                                     prune_list(used_letters, '')]),
                                                            user.id,
                                                            ''.join([str(player) + ',' for player in
                                                                     prune_list(players, '')]),
                                                            data[1]
                                                            )

                        # Auto stop after inactivity
                        data = self.client.db.get_hangman(rec.message.id)
                        await asyncio.sleep(120)
                        if data == self.client.db.get_hangman(rec.message.id):
                            self.client.db.delete_hangman(rec.message.id)
                            await rec.message.edit(embed=discord.Embed(title="Failed game",
                                                                       description=f"Ended game due to inactivity"
                                                                                   f" (2min).",
                                                                       color=0xad3998
                                                                       ))

                    else:  # word not found, all guessed have been used
                        self.client.db.delete_hangman(rec.message.id)
                        await rec.message.edit(embed=discord.Embed(title="Failed game",
                                                                   description=f"The word you were looking for is"
                                                                               f" **{data[1]}**. You have been hang"
                                                                               f" before finding it :c",
                                                                   color=0xad3998
                                                                   ))

                        await clear_rec(rec.message)

                        # Logging
                        for channel_id in (await get_configdata(self.client, rec.message.guild.id,
                                                                'logger_ids')) + master_logger_id:
                            try:
                                await self.client.get_channel(channel_id).send(
                                    embed=self.embed_logger(f"{user} got hang, and lost the game.!",
                                                            rec.message.channel.id, 'fail'))
                            except AttributeError:
                                pass
                else:  # Invalid reaction
                    await rec.remove(user)

    @commands.command(aliases=['gués'])
    async def guess(self, ctx, guess):
        if ctx.message.reference is not None:
            data = self.client.db.get_hangman(ctx.message.reference.message_id)

            if data is not None:
                players = [int(i) for i in prune_list(data[4].split(','), '')]

                if data[3] == self.client.user.id or data[3] == players[-1]:  # get id of player who is allowed to guess
                    turn = players[0]
                else:
                    turn = players[players.index(data[3]) + 1]

                used_letters = data[2].split(',')  # List of submitted letters
                if ctx.author.id == turn:
                    if guess.lower() == data[1]:  # Guessed right
                        self.client.db.add_user_data('hangman', ctx.author.id, ctx.channel.id)
                        self.client.db.delete_hangman(data[0])
                        await ctx.message.reference.cached_message.edit(
                            embed=discord.Embed(title="You won!",
                                                description=f"The word you were looking for is **{data[1]}**,"
                                                            f" congratulations!",
                                                color=0xad3998
                                                ))
                        await clear_rec(ctx.message.reference.cached_message)

                        # Logging
                        for channel_id in (await get_configdata(self.client, ctx.guild.id,
                                                                'logger_ids')) + master_logger_id:
                            try:
                                await self.client.get_channel(channel_id).send(
                                    embed=self.embed_logger(f"{ctx.author} won the game!", ctx.channel.id, 'succ'))
                            except AttributeError:
                                pass
                    else:  # Guessed wrong
                        if hangman_str(data[1], used_letters)[1] < 7:  # Not all guesses used
                            await ctx.send('You guessed wrong. And are now one step closer to death.')

                            rint = str(randint(0, 20))  # Place holder for wrong guess
                            self.client.db.hangman_game_handler(data[0], data[2] + rint + ",", ctx.author.id, data[4],
                                                                data[1])
                            embed = discord.Embed(title="Hangman!",
                                                  description=f"#Letters: {len(data[1])} \n"
                                                              f"{hangman_str(data[1], used_letters)[0]}",
                                                  color=0xad3998
                                                  )
                            embed.set_image(url=HANGMANPICS[hangman_str(data[1], used_letters + [rint])[1]])
                            await ctx.message.reference.cached_message.edit(embed=embed)

                            # Auto stop after inactivity
                            data = self.client.db.get_hangman(ctx.message.reference.message_id)
                            await asyncio.sleep(120)
                            if data == self.client.db.get_hangman(ctx.message.reference.message_id):
                                self.client.db.delete_hangman(ctx.message.reference.message_id)
                                await ctx.message.reference.cached_message.edit(
                                    embed=discord.Embed(title="Failed game",
                                                        description=f"Ended game due to inactivity (2min).",
                                                        color=0xad3998
                                                        ))

                        else:  # Used last guess
                            self.client.db.delete_hangman(ctx.message.reference.cached_message.id)

                            await ctx.message.reference.cached_message.edit(
                                embed=discord.Embed(title="Failed game",
                                                    description=f"The word you were looking for is **{data[1]}**."
                                                                f" You have been hang before finding it :c",
                                                    color=0xad3998
                                                    ))

                            # Logging
                            for channel_id in (
                                                      await get_configdata(self.client, ctx.guild.id,
                                                                           'logger_ids')) + master_logger_id:
                                try:
                                    await self.client.get_channel(channel_id).send(
                                        embed=self.embed_logger(f"{ctx.author} got hang, and lost the game.!",
                                                                ctx.channel.id, 'fail'))
                                except AttributeError:
                                    pass

                else:  # Not allowed to guess
                    await ctx.message.delete()
        else:  # Guess without game reference
            await ctx.message.delete()

    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message):
        if msg.reference is not None:
            data = self.client.db.get_hangman(msg.reference.message_id)

            if data is not None:
                if match(r"^[a-zA-Z]+$", msg.content) and len(msg.content) == 1:  # Only submitted 1 letter
                    players = [int(i) for i in prune_list(data[4].split(','), '')]

                    if data[3] == self.client.user.id or data[3] == players[-1]:  # player_id, allowed answer
                        turn = players[0]
                    else:
                        turn = players[players.index(data[3]) + 1]

                    if turn == players[-1]:  # id of player who has to answer next
                        next_turn = players[0]
                    else:
                        next_turn = players[players.index(turn) + 1]

                    if data is not None:
                        used_letters = data[2].split(',')  # List of submitted letters

                        sub_letter = msg.content.lower()

                        if sub_letter not in used_letters and msg.author.id == turn:  # New letter + allowed to guess
                            used_letters.append(sub_letter)

                            if hangman_str(data[1], used_letters)[1] < 8:  # Guesses left
                                if not hangman_str(data[1], used_letters)[2]:  # Not found
                                    embed = discord.Embed(title="Hangman!",
                                                          description=f"#Letters: {len(data[1])}\n <@{next_turn}>"
                                                                      f" \n{hangman_str(data[1], used_letters)[0]}",
                                                          color=0xad3998
                                                          )
                                    embed.set_image(url=HANGMANPICS[hangman_str(data[1], used_letters)[1]])
                                    await msg.reference.cached_message.edit(embed=embed)

                                    self.client.db.hangman_game_handler(data[0],
                                                                        ''.join([letter + ',' for letter in
                                                                                 prune_list(used_letters, '')]),
                                                                        msg.author.id, ''.join(
                                            [str(player) + ',' for player in prune_list(players, '')]),
                                                                        data[1])

                                    # Auto stop after inactivity
                                    data = self.client.db.get_hangman(msg.reference.message_id)
                                    await asyncio.sleep(120)
                                    if data == self.client.db.get_hangman(msg.reference.message_id):
                                        self.client.db.delete_hangman(msg.reference.message_id)
                                        await msg.reference.cached_message.edit(
                                            embed=discord.Embed(title="Failed game",
                                                                description=f"Ended game due to inactivity (2min).",
                                                                color=0xad3998
                                                                ))

                                else:  # Found word
                                    self.client.db.delete_hangman(msg.reference.cached_message.id)

                                    self.client.db.add_user_data('hangman', msg.author.id,
                                                                 msg.reference.cached_message.channel.id)

                                    await msg.reference.cached_message.edit(
                                        embed=discord.Embed(title="You won!",
                                                            description=f"The word you were looking for is **{data[1]}"
                                                                        f"**, congratulations!",
                                                            color=0xad3998
                                                            ))
                                    await clear_rec(msg.reference.cached_message)

                                    # Logging
                                    for channel_id in (await get_configdata(self.client, msg.guild.id,
                                                                            'logger_ids')) + master_logger_id:
                                        try:
                                            await self.client.get_channel(channel_id).send(
                                                embed=self.embed_logger(f"{msg.author} won the game!", msg.channel.id,
                                                                        'succ'))
                                        except AttributeError:
                                            pass
                            else:  # No guesses left
                                self.client.db.delete_hangman(msg.reference.cached_message.id)

                                await msg.reference.cached_message.edit(
                                    embed=discord.Embed(title="Failed game",
                                                        description=f"The word you were looking for is **{data[1]}**."
                                                                    f" You have been hang before finding it :c",
                                                        color=0xad3998
                                                        ))
                                await clear_rec(msg.reference.cached_message)

                                # Logging
                                for channel_id in (await get_configdata(self.client, msg.guild.id,
                                                                        'logger_ids')) + master_logger_id:
                                    try:
                                        await self.client.get_channel(channel_id).send(
                                            embed=self.embed_logger(f"{msg.author} got hang, and lost the game.!",
                                                                    msg.channel.id, 'fail'))
                                    except AttributeError:
                                        pass
                else:  # Submitted something more than one letter
                    await msg.delete()


def setup(client):
    client.add_cog(hang_man(client))
