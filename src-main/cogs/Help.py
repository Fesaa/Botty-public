from discord.ext import commands
from discord import ButtonStyle, Embed, Guild, Interaction, Member,SelectOption
from discord.ui import View, Select, Button

POSSIBLE_GAMES = ['ConnectFour', 'HangMan', 'HigherLower', 'NTBPL', 'WordSnake']

def HelpHomeEmbed(bot: commands.Bot) -> Embed:
    e = Embed(title="Botty Help Menu", description='All commands can be written with random capitalization.\nAn * indicates that the argument is not required. Use the buttons below for more specific help!',
              colour = 0xad3998)
    e.add_field(name="Traditional Commands vs Slash Commands",
                value="While Slash Commands are a better way to use discord, most simple low use commands are still traditional commands to keep the Slash Commands menu from cluttering.",
                inline=False)
    commands = [i.name for i in bot.commands if i.name not in ['sync_slash', 'poll']]
    commands.sort()
    e.add_field(name="All Traditional commands",
                value=", ".join(commands),
                inline=False)
    e.set_thumbnail(url=bot.user.avatar.url)
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
            await interaction.response.edit_message(embed=HelpHomeEmbed(self.bot), view=HelpView(self.bot, self.guild, interaction.user))
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


class HelpConfigButton(Button):

    def __init__(self, bot: commands.bot, guild: Guild, user: Member, selected_game: str = None, selected_help: str = None):

        self.bot = bot
        self.guild = guild
        self.user = user
        self.selected_game = selected_game
        self.selected_help =selected_help
        super().__init__(label='Config Help', style=ButtonStyle.gray, emoji='⚙️', disabled= not user.guild_permissions.administrator, row=0)
    
    async def callback(self, interaction: Interaction):
        e = Embed(title="Config Help", description="All the Config Slash Commands can only be used by user with administrative privileges.", colour = 0xad3998)
        e.add_field(name="`/config command_prefix`", value="Used to change the command prefix. Default: `!` \nTagging me always works.", inline=False)
        e.add_field(name="`/config game_settings`", value="Used to change specific game limitations. These are all server wide, and can't be chosen on a per channel basis.", inline=False)
        e.add_field(name="`/config perms`", value="Used to change which game/bot component uses which channel. Or which role is required to use a bot component", inline=False)
        e.set_thumbnail(url=self.bot.user.avatar.url)
        await interaction.response.edit_message(embed=e, view=HelpView(bot=self.bot, guild=self.guild, user=self.user, selected_game=self.selected_game, selected_help='Config'))

class HelpPollyButton(Button):

    def __init__(self, bot: commands.bot, guild: Guild, user: Member, selected_game: str = None, selected_help: str = None):

        self.bot = bot
        self.guild = guild
        self.user = user
        self.selected_game = selected_game
        self.selected_help =selected_help
        super().__init__(label='Polly Help', style=ButtonStyle.blurple, emoji='📜',
                         disabled= not (user.guild_permissions.administrator or bool(set([i.id for i in user.roles]) & set(self.bot.db.get_channel(guild.id, 'Polly_role_id')))),
                         row=0)
    
    async def callback(self, interaction: Interaction):
        e = Embed(title="Polly Help", description=f"Make simple polls with: `{self.bot.db.get_prefix(self.guild.id)}poll <question> | <emoji name 1> <answer 1> | <emoji name 2> <answer 2> | ...`", colour = 0xad3998)
        e.add_field(name='Example', value=f'{self.bot.db.get_prefix(self.guild.id)}poll Would you rather | deciduous_tree Live in a tree house forever forever 🌳 🏠 | tropical_fish Live in an underwater house forever.')
        e.set_thumbnail(url=self.bot.user.avatar.url)
        await interaction.response.edit_message(embed=e, view=HelpView(bot=self.bot, guild=self.guild, user=self.user, selected_game=self.selected_game, selected_help='Polly'))

class HelpCubeLvlButton(Button):
    def __init__(self, bot: commands.bot, guild: Guild, user: Member, selected_game: str = None, selected_help: str = None):

        self.bot = bot
        self.guild = guild
        self.user = user
        self.selected_game = selected_game
        self.selected_help =selected_help
        super().__init__(label='CubeLvl Help', style=ButtonStyle.blurple, emoji='🧮', row=0)
    
    async def callback(self, interaction: Interaction):
        e = Embed(title="CubeLvl Help", description="Calculate simple and more complicated CubeCraft matter about experience and stats", colour = 0xad3998)
        e.add_field(name='`/cubelvl level`', value='Return the difference between two levels. Default to difference with level 1 with 0 xp.', inline=False)
        e.add_field(name='`/cubelvl multies`', value='Returns the needed multies to reach a level, or the level you will reach after using n multies.', inline=False)
        e.add_field(name='`/cubelvl stats`', value='Return which level an amount of wins would give you.', inline=False)
        e.add_field(name=f'{self.bot.db.get_prefix(self.guild.id)}ratio_<game>', value='Returns some extra stats for SkyWars (sw), Eggwars (ew) or TowerDefense (td).'\
                                                                                       '\nParameters are the stats given by CubeCraft in the same order.', inline=False)
        e.set_thumbnail(url=self.bot.user.avatar.url)
        await interaction.response.edit_message(embed=e, view=HelpView(bot=self.bot, guild=self.guild, user=self.user, selected_game=self.selected_game, selected_help='CubeLvl'))

class HelpHomeButton(Button):

    def __init__(self, bot: commands.bot, guild: Guild, user: Member, selected_game: str = None, selected_help: str = None):

        self.bot = bot
        self.guild = guild
        self.user = user
        self.selected_game = selected_game
        self.selected_help =selected_help
        super().__init__(label='Home', style=ButtonStyle.blurple, emoji='🏠', row=0)
    
    async def callback(self, interaction: Interaction):
        await interaction.response.edit_message(embed=HelpHomeEmbed(self.bot), view=HelpView(self.bot, self.guild, interaction.user))


class HelpView(View):

    def __init__(self, bot: commands.bot, guild: Guild, user: Member, selected_game: str = 'Home', selected_help: str = 'Home', timeout: int = None):

        super().__init__(timeout=timeout)

        games = [i for i in POSSIBLE_GAMES if bot.db.get_channel(guild.id, i) != []]
        games.append('Home')

        if selected_help == 'Config':
            self.add_item(HelpGameSelect(bot=bot, games=games, guild=guild, user=user, selected_game=selected_game, selected_help=selected_help))
            self.add_item(HelpHomeButton(bot=bot, guild=guild, user=user, selected_game=selected_game, selected_help=selected_help))
            self.add_item(HelpPollyButton(bot=bot, guild=guild, user=user, selected_game=selected_game, selected_help=selected_help))
            self.add_item(HelpCubeLvlButton(bot=bot, guild=guild, user=user, selected_game=selected_game, selected_help=selected_help))
        elif selected_help == 'Polly':
            self.add_item(HelpGameSelect(bot=bot, games=games, guild=guild, user=user, selected_game=selected_game, selected_help=selected_help))
            self.add_item(HelpConfigButton(bot=bot, guild=guild, user=user, selected_game=selected_game, selected_help=selected_help))
            self.add_item(HelpHomeButton(bot=bot, guild=guild, user=user, selected_game=selected_game, selected_help=selected_help))
            self.add_item(HelpCubeLvlButton(bot=bot, guild=guild, user=user, selected_game=selected_game, selected_help=selected_help))
        elif selected_help == 'CubeLvl':
            self.add_item(HelpGameSelect(bot=bot, games=games, guild=guild, user=user, selected_game=selected_game, selected_help=selected_help))
            self.add_item(HelpConfigButton(bot=bot, guild=guild, user=user, selected_game=selected_game, selected_help=selected_help))
            self.add_item(HelpPollyButton(bot=bot, guild=guild, user=user, selected_game=selected_game, selected_help=selected_help))
            self.add_item(HelpHomeButton(bot=bot, guild=guild, user=user, selected_game=selected_game, selected_help=selected_help))
        elif selected_help == 'Home':
            self.add_item(HelpGameSelect(bot=bot, games=games, guild=guild, user=user, selected_game=selected_game, selected_help=selected_help))
            self.add_item(HelpConfigButton(bot=bot, guild=guild, user=user, selected_game=selected_game, selected_help=selected_help))
            self.add_item(HelpPollyButton(bot=bot, guild=guild, user=user, selected_game=selected_game, selected_help=selected_help))
            self.add_item(HelpCubeLvlButton(bot=bot, guild=guild, user=user, selected_game=selected_game, selected_help=selected_help))

class HelpCog(commands.Cog):

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        super().__init__()
    
    @commands.command(name='help')
    async def _help(self, ctx: commands.Context):
        await ctx.send(embed=HelpHomeEmbed(self.bot), view=HelpView(self.bot, ctx.guild, ctx.author))


async def setup(bot: commands.Bot):
    await bot.add_cog(HelpCog(bot))