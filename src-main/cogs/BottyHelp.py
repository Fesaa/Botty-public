import discord

from discord.ext import commands
from discord import ButtonStyle, Embed, Guild, Interaction, Member,SelectOption
from discord.ui import View, Select, Button

POSSIBLE_GAMES = ['ConnectFour', 'HangMan', 'HigherLower', 'NTBPL', 'WordSnake']

def HelpHomeEmbed(bot: commands.Bot, author: discord.Member) -> Embed:
    e = Embed(title="Botty Help Menu", description='All commands can be written with random capitalization.\nAn * indicates that the argument is not required. Use the buttons below for more specific help!',
              colour = 0xad3998, timestamp=discord.utils.utcnow())
    commands = [i.name for i in bot.commands]
    commands.sort()
    e.add_field(name="All commands",
                value=", ".join(commands),
                inline=False)
    e.set_thumbnail(url=bot.user.avatar.url)
    e.set_footer(text=f"Requested by {author}", icon_url=author.avatar.url)
    return e

class HelpGameSelect(Select):

    def __init__(self, bot: commands.bot, games: list[str], guild: Guild, user: Member, selected_game: str = None, selected_help: str = None):

        options = [
            SelectOption(label='Home', description='Go back to the home help page!', emoji='🏠'),
            SelectOption(label='ConnectFour', description='How do I play ConnectFour?', emoji='🟡'),
            SelectOption(label='HangMan', description='How do I play HangMan?', emoji='🪢'),
            SelectOption(label='HigherLower', description='How do I play HigherLower', emoji='↕️'),
            SelectOption(label='NTBPL', description='How do I play NTBPL?', emoji='❓'),
            SelectOption(label="WordSnake", description="How do I play WordSnake?", emoji='🐍')
        ]
        options = [i for i in options if i.label in games and i.label != selected_game]

        self.bot = bot
        self.guild = guild
        self.user = user
        self.selected_game = selected_game
        self.selected_help =selected_help
        super().__init__(custom_id='game_help_choice', placeholder='Get help with one of my games!', options=options, row=1)
    
    async def callback(self, interaction: Interaction):
        choice = self.values[0]

        if choice == 'Home':
            await interaction.response.edit_message(embed=HelpHomeEmbed(self.bot, interaction.user), view=HelpView(self.bot, self.guild, interaction.user))
        elif choice == 'ConnectFour':
            e = Embed(title='ConnectFour Help', description=f'A children classic since 1974! Start a game with `{self.bot.db.get_prefix(self.guild.id)}c4`!', colour = 0xad3998)
            e.add_field(name='Quick guide', value="The board consists of a 6x7 grid. The starting player will be playing yellow, the other red."
                                                  " You'll be choosing a column to drop a coin in one after the other by clicking on the buttons!" 
                                                  " With the soul objective to have 4 coins in a row! These rows can be made; horizontally, vertically or diagonally.")
            e.set_thumbnail(url=self.bot.user.avatar.url)
            await interaction.response.edit_message(embed=e, view=HelpView(bot=self.bot, guild=self.guild, user=self.user, selected_game='ConnectFour'))
        elif choice == 'HangMan':
            e = Embed(title='HangMan Help', description=f'Try to find the hidden word before you get hang! \nStart a game with `{self.bot.db.get_prefix(self.guild.id)}hm`', colour = 0xad3998)
            e.add_field(name='Quick guide', value='You can play the game alone or with more players, feel free to join or leave at any time by using the appropriate buttons.'
                                                  ' In order of joining you will have to take action, you can either guess a letter by selecting one with the menus or submit' 
                                                  ' a guess by pressing guess.')
            e.set_thumbnail(url=self.bot.user.avatar.url)
            await interaction.response.edit_message(embed=e, view=HelpView(bot=self.bot, guild=self.guild, user=self.user, selected_game='HangMan'))
        elif choice == 'HigherLower':
            e = Embed(title='HigherLower Help', description=f'All the channels I play in are in a continues state of playing. Simple send a number between **1** and'
                                                            f' **{self.bot.db.get_game_setting(self.guild.id, "HL_max_number")}**.' 
                                                            f' You can guess **{self.bot.db.get_game_setting(self.guild.id, "HL_max_reply")}** times in a row!', colour = 0xad3998)
            e.set_thumbnail(url=self.bot.user.avatar.url)
            await interaction.response.edit_message(embed=e, view=HelpView(bot=self.bot, guild=self.guild, user=self.user, selected_game='HigherLower'))
        elif choice == 'NTBPL':
            e = Embed(title='NTBPL Help', description='I give you an amount of letters. And you send a word that contains these letters in the same order!', colour = 0xad3998)
            e.add_field(name=f'`{self.bot.db.get_prefix(self.guild.id)}begin <count*>`', value=f'Used to beging a game. The count is always between 1 and 5. If no count is'
                                                      f' given, I will choose one for you.', inline=False)
            e.add_field(name=f'`{self.bot.db.get_prefix(self.guild.id)}clearwords`', value='Used to clear the list of used words. Remember, every word can only be used once.', inline=False)
            e.add_field(name='What does this emoji mean?', value='✅: Your word was accepted\n❌: I don\'t think this is an English word\n🔁: Somebody already used this word before you!', inline=False)
            e.set_thumbnail(url=self.bot.user.avatar.url)
            await interaction.response.edit_message(embed=e, view=HelpView(bot=self.bot, guild=self.guild, user=self.user, selected_game='NTBPL'))
        elif choice == 'WordSnake':
            e = Embed(title='WordSnake Help', description='Create the longest possible snake by finding a word that starts with the last letter of the previous word!', colour = 0xad3998)
            e.add_field(name=f'`{self.bot.db.get_prefix(self.guild.id)}start <word*>`', value='Used to start a game, if no word is given I will pick one!')
            e.add_field(name=f'`{self.bot.db.get_prefix(self.guild.id)}count`', value='Used to display the current length of the snake!')
            e.add_field(name=f'`{self.bot.db.get_prefix(self.guild.id)}resetwords`', value='Used to reset all the used words. If it gets a bit too hard :)')
            e.set_thumbnail(url=self.bot.user.avatar.url)
            await interaction.response.edit_message(embed=e, view=HelpView(bot=self.bot, guild=self.guild, user=self.user, selected_game='WordSnake'))


class HelpHomeButton(Button):

    def __init__(self, bot: commands.bot, guild: Guild, user: Member, selected_game: str = None, selected_help: str = None):

        self.bot = bot
        self.guild = guild
        self.user = user
        self.selected_game = selected_game
        self.selected_help =selected_help
        super().__init__(label='Home', style=ButtonStyle.blurple, emoji='🏠', row=0)
    
    async def callback(self, interaction: Interaction):
        await interaction.response.edit_message(embed=HelpHomeEmbed(self.bot, interaction.user), view=HelpView(self.bot, self.guild, interaction.user))

class DestructButton(Button):

    def __init__(self):
        super().__init__(style=ButtonStyle.blurple, emoji='<:stop_check:754948796365930517>', row=0)
    
    async def callback(self, interaction: Interaction):
        await interaction.response.defer()
        await interaction.message.delete()

class HelpView(View):

    def __init__(self, bot: commands.bot, guild: Guild, user: Member, selected_game: str = 'Home', selected_help: str = 'Home', timeout: int = None):
        self.user = user
        super().__init__(timeout=timeout)

        games = [i for i in POSSIBLE_GAMES if bot.db.get_channel(guild.id, i) != []]
        games.append('Home')

        if games != ['Home']:
            self.add_item(HelpGameSelect(bot=bot, games=games, guild=guild, user=user, selected_game=selected_game, selected_help=selected_help))
            self.add_item(HelpHomeButton(bot=bot, guild=guild, user=user, selected_game=selected_game, selected_help=selected_help))
        
        self.add_item(DestructButton())
    
    async def interaction_check(self, interaction):
        """Only allow the author that invoke the command to be able to use the interaction"""
        return interaction.user == self.user

class HelpCog(commands.Cog):

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        super().__init__()
    
    @commands.command(name='bottyhelp')
    async def bottyhelp(self, ctx: commands.Context):
        """
        A interactive help for the various games I offer!
        """
        await ctx.message.delete()
        await ctx.send(embed=HelpHomeEmbed(self.bot, ctx.author), view=HelpView(self.bot, ctx.guild, ctx.author))


async def setup(bot: commands.Bot):
    await bot.add_cog(HelpCog(bot))