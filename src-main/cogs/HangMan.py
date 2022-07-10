import asyncio
from discord import ButtonStyle, Embed, Interaction, SelectOption, Message, TextStyle
from discord.ui import View, Select, button, TextInput, Modal
from discord.ext import commands

from imports.functions import get_HangMan_word, time

HANGMANPICS = ["https://media.discordapp.net/attachments/869315104271904768/874025738238562344/01.png",
               "https://media.discordapp.net/attachments/869315104271904768/874025739098419300/02.png",
               "https://media.discordapp.net/attachments/869315104271904768/874025741354934272/04.png",
               "https://media.discordapp.net/attachments/869315104271904768/874025742797783150/05.png",
               "https://media.discordapp.net/attachments/869315104271904768/874025743678586960/06.png",
               "https://media.discordapp.net/attachments/869315104271904768/874025745524088843/07.png",
               "https://media.discordapp.net/attachments/869315104271904768/874025746828509204/08.png",
               "https://media.discordapp.net/attachments/869315104271904768/874025747881275422/09.png"]


def hangman_str(word: str, letters: list) -> list[str, int, bool]:
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

def splitletters(used_letters: str) -> list:
    alphabet0 = 'abcdefghijklm'
    alphabet1 = 'nopqrstuvwxyz'

    used_letters = "".join(sorted(used_letters))

    s0, s1 = "", ""
    
    contains0 = False
    contains1 = False
    
    for letter in reversed(alphabet0):
        if letter in used_letters:
            s1 = used_letters.split(letter)[1]
            contains0 = True
            break
    
    for letter in alphabet1:
        if letter in used_letters:
            s0 = used_letters.split(letter)[0]
            contains1 = True
            break

    if contains0 and not contains1:
        return [used_letters, ""]
    elif contains1 and not contains0:
        return ["", used_letters]
    else:
        return [s0, s1]

async def check_inactive(bot: commands.Bot, current_data: dict, msg: Message, time_out: int):
    await asyncio.sleep(time_out)
    if current_data == bot.db.get_HangMan_data(msg.id):
        bot.db.HangMan_game_switch(msg.id, False)

        await msg.edit(embed=Embed(title="Failed game", description=f"Ended game due to inactivity (2min).", color=0xad3998 ), view=View())

async def letter_select(self, interaction: Interaction):
    sub_letter = self.values[0]

    data = self.bot.db.get_HangMan_data(interaction.message.id)
    players = [int(i) for i in data['players'].split(',')]
    used_letters = list(data['used_letters'])

    if interaction.user.id in players:

        turn = data['user_id']
        
        if turn == players[-1]:
            next_turn = players[0]
        else:
            next_turn = players[players.index(turn) + 1]
        
        if interaction.user.id == turn:
            used_letters.append(sub_letter)

            HM_str_data = hangman_str(data['word'], used_letters)
            
            if HM_str_data[2]:
                self.bot.db.HangMan_game_switch(interaction.message.id, False)
                self.bot.db.update_lb('HangMan', interaction.channel_id, interaction.user.id)

                await interaction.response.edit_message(embed=Embed(title="You won!",
                                                            description=f"The word you were looking for is **{data['word']}**, congratulations!",
                                                            color=0xad3998
                                                            ), view=View()
                                                )
            elif HM_str_data[1] < 8:
                embed = Embed(title="Hangman!",
                                description=f"#Letters: {len(data['word'])}\n <@{next_turn}>\n{HM_str_data[0]}",
                                color=0xad3998
                                )
                embed.set_image(url=HANGMANPICS[HM_str_data[1]])

                self.bot.db.update_HangMan_data(interaction.message.id, data['word'], "".join(used_letters), next_turn, data['players'])

                await interaction.response.edit_message(embed=embed, view=DropDownView("".join(used_letters), self.bot))

                await check_inactive(self.bot, self.bot.db.get_HangMan_data(interaction.message.id), interaction.message, 120)
            
            else:
                self.bot.db.HangMan_game_switch(interaction.message.id, False)

                await interaction.response.edit_message(embed=Embed(title="Failed game", 
                                                            description=f"The word you were looking for is **{data['word']}**. You have been hang before finding it :c",
                                                            color=0xad3998), view=View())
        else:
            await interaction.response.send_message("Please wait for your turn!", ephemeral=True)

        
    else:
        await interaction.response.send_message("You are not part of this game, click the **Join** button to join the game!", ephemeral=True)


class DropDownAM(Select):

    def __init__(self, used_letters: str, bot: commands.Bot):

        self.bot = bot

        options = [
            SelectOption(emoji='🇦', label='A',value='a'),
            SelectOption(emoji='🇧', label='B',value='b'),
            SelectOption(emoji='🇨', label='C',value='c'),
            SelectOption(emoji='🇩', label='D',value='d'),
            SelectOption(emoji='🇪', label='E',value='e'),
            SelectOption(emoji='🇫', label='F',value='f'),
            SelectOption(emoji='🇬', label='G',value='g'),
            SelectOption(emoji='🇭', label='H',value='h'),
            SelectOption(emoji='🇮', label='I',value='i'),
            SelectOption(emoji='🇯', label='J',value='j'),
            SelectOption(emoji='🇰', label='K',value='k'),
            SelectOption(emoji='🇱', label='L',value='l'),
            SelectOption(emoji='🇲', label='M',value='m'),
        ]

        options = [i for i in options if i.value not in used_letters]

        super().__init__(custom_id="choose_letter_am", placeholder="Which letter will you guess? A - M", options=options, row=0)
    
    async def callback(self, interaction: Interaction):
        await letter_select(self, interaction)

class DropDownNZ(Select):

    def __init__(self, used_letters: str, bot: commands.Bot):

        self.bot = bot

        options = [
            SelectOption(emoji='🇳', label='N',value='n'),
            SelectOption(emoji='🇴', label='O',value='o'),
            SelectOption(emoji='🇵', label='P',value='p'),
            SelectOption(emoji='🇶', label='Q',value='q'),
            SelectOption(emoji='🇷', label='R',value='r'),
            SelectOption(emoji='🇸', label='S',value='s'),
            SelectOption(emoji='🇹', label='T',value='t'),
            SelectOption(emoji='🇺', label='U',value='u'),
            SelectOption(emoji='🇻', label='V',value='v'),
            SelectOption(emoji='🇼', label='W',value='w'),
            SelectOption(emoji='🇽', label='X',value='x'),
            SelectOption(emoji='🇾', label='Y',value='y'),
            SelectOption(emoji='🇿', label='Z',value='z')
        ]

        options = [i for i in options if i.value not in used_letters]

        super().__init__(custom_id="choose_letter_nz", placeholder="Which letter will you guess? N - Z", options=options, row=1)
    
    async def callback(self, interaction: Interaction):
       await letter_select(self, interaction)

class WordGuess(Modal):
    guess = TextInput(label="word_guess", style=TextStyle.short)
    

    def __init__(self, bot: commands.Bot, title: str = "Guess the word!") -> None:
        super().__init__(title=title)
        self.bot = bot
    
    async def on_submit(self, interaction: Interaction):
        data = self.bot.db.get_HangMan_data(interaction.message.id)
        sub_word = interaction.data['components'][0]['components'][0]['value']

        if data['user_id'] == interaction.user.id:
            
            if data['word'].lower() == sub_word.lower():
                self.bot.db.HangMan_game_switch(interaction.message.id, False)
                self.bot.db.update_lb('HangMan', interaction.channel_id, interaction.user.id)

                await interaction.response.edit_message(embed=Embed(title="You won!",
                                                            description=f"The word you were looking for is **{data['word']}**, congratulations!",
                                                            color=0xad3998
                                                            ), view=View()
                                                )
            else:

                turn = data['user_id']
                players = [int(i) for i in data['players'].split(',')]
        
                if turn == players[-1]:
                    next_turn = players[0]
                else:
                    next_turn = players[players.index(turn) + 1]
                
                self.bot.db.update_HangMan_data(interaction.message.id, data['word'], data['used_letters'], next_turn, data['players'])

                HM_str_data = hangman_str(data['word'], data['used_letters'])
                embed = Embed(title="Hangman!",
                                description=f"#Letters: {len(data['word'])}\n <@{next_turn}>\n{HM_str_data[0]}",
                                color=0xad3998
                                )
                embed.set_image(url=HANGMANPICS[HM_str_data[1]])
                await interaction.response.edit_message(embed=embed, view=DropDownView(data['used_letters'], self.bot))
                await interaction.message.reply("Wrong guess, you lost your turn!", ephemeral=True)

        
        else:
            await interaction.response.send_message("Please wait for your turn!", ephemeral=True)

class DropDownView(View):

    def __init__(self, used_letters: str, bot: commands.Bot):
        super().__init__(timeout=None)
        self.bot = bot

        letters = splitletters(used_letters)

        self.add_item(DropDownAM(letters[0], bot))
        self.add_item(DropDownNZ(letters[1], bot))
    

    @button(custom_id='join', label="Join", style=ButtonStyle.green, row=2)
    async def _join(self, interaction: Interaction, button):
        data = self.bot.db.get_HangMan_data(interaction.message.id)
        players = [int(i) for i in data['players'].split(',')]

        if interaction.user.id in players:
            await interaction.response.send_message('You are already playing.', ephemeral=True)
        else:
            players.append(interaction.user.id)
            self.bot.db.update_HangMan_data(data['msg_id'], data['word'], data['used_letters'], data['user_id'], ','.join([str(i) for i in players]))
            await interaction.response.send_message("You can play now, wait for your turn :)!", ephemeral=True)



    @button(custom_id='leave', label="Leave", style=ButtonStyle.red, row=2)
    async def _leave(self, interaction: Interaction, button):
        data = self.bot.db.get_HangMan_data(interaction.message.id)
        players = [int(i) for i in data['players'].split(',')]

        if interaction.user.id not in players:
            await interaction.response.send_message('You are not playing.', ephemeral=True)
        else:

            if interaction.user.id == (turn := data['user_id']):
                if turn == players[-1]:
                    next_turn = players[0]
                else:
                    next_turn = players[players.index(turn) + 1]
                
                HM_str_data = hangman_str(data['word'], data['used_letters'])
                
                embed = Embed(title="Hangman!",
                                description=f"#Letters: {len(data['word'])}\n <@{next_turn}>\n{HM_str_data[0]}",
                                color=0xad3998
                                )
                embed.set_image(url=HANGMANPICS[HM_str_data[1]])

                await interaction.message.edit(embed=embed, view=DropDownView(data['used_letters'], self.bot))

            else:
                next_turn = data['user_id']

            players.remove(interaction.user.id)

            if len(players) > 0:
                self.bot.db.update_HangMan_data(data['msg_id'], data['word'], data['used_letters'], next_turn, ','.join([str(i) for i in players]))
                await interaction.response.send_message("You're not playing anymore, sad to see you go :(!", ephemeral=True)
            else:
                self.bot.db.HangMan_game_switch(data['msg_id'], False)
                await interaction.response.edit_message(embed=Embed(title="Failed game", description=f"Ended game due to no players.", color=0xad3998 ), view=View())

    @button(custom_id='guess', label="Guess your word!", emoji='🔍', style=ButtonStyle.blurple, row=2)
    async def _guess(self, interaction: Interaction, button):
        await interaction.response.send_modal(WordGuess(self.bot))


class HangMan(commands.Cog):

    def __init__(self, bot: commands.Bot) -> None:
        super().__init__()
        self.bot = bot
    
    def embed_logger(self, txt_log, channel_id, error_type=None):
        if error_type == 'succ':
            colour = 0x00a86b
        elif error_type == 'fail':
            colour = 0xb80f0a
        elif error_type == 's':
            colour = 0x1034a6
        else:
            colour = 0xad3998
        embed = Embed(title='📖 Info 📖', colour=colour)
        embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar.url)
        embed.add_field(name="Hangman", value=txt_log)
        embed.set_footer(text=f'🆔 {channel_id} ⏳' + time())
        return embed
        
    @commands.command(aliases=['hg', 'hm'])
    async def hangman(self, ctx: commands.Context):
        """
        Start a game of HangMan, shorter: hm
        """
        if ctx.channel.id in self.bot.db.get_channel(ctx.guild.id, 'HangMan'):
            word = get_HangMan_word()

            embed = Embed(title="Hangman!",
                                  description=f"#Letters: {len(word)}\n <@{ctx.author.id}>"
                                              f" \n{hangman_str(word, [])[0]}",
                                  color=0xad3998
                                  )
            embed.set_image(url=HANGMANPICS[hangman_str(word, [""])[1]])
            msg = await ctx.send(embed=embed, view=DropDownView("", self.bot))

            self.bot.db.HangMan_game_switch(msg.id, True)
            self.bot.db.update_HangMan_data(msg.id, word, "", ctx.author.id, str(ctx.author.id))

            for channel_id in self.bot.db.get_channel(ctx.guild.id, 'Log'):
                    await self.bot.get_channel(channel_id).send(embed=self.embed_logger(f'{ctx.author} start a game of hangman, the word is {word}."', ctx.channel.id, 's'))
            
            await check_inactive(self.bot, self.bot.db.get_HangMan_data(msg.id), msg, 120)


async def setup(bot: commands.Bot):
    await bot.add_cog(HangMan(bot))