from random import randint
from discord import Guild, Interaction, Message, Role, app_commands, Object, TextChannel
from discord.app_commands import Choice
from discord.ext import commands
from json import load
from discord.channel import DMChannel

# Default values
DEFAULT_PREFIX = "!"
DEFAULT_LB_SIZE = 15
DEFAULT_CHANNEL = ''
DEFAULT_MAX_REPLY = 3
DEFAULT_WS_GUESSES = 1
DEFAULT_HL_MAX_NUMBER = 1000
config = load(open('config.json'))

# General
token = config['General']['Discord Token']
bot_id = config['General']['Bot-id']
# Database
host = config['mysql']['host']
Database = config['mysql']['database']
user = config['mysql']['user']
password = config['mysql']['password']


async def get_prefix(bot: commands.Bot, msg: Message):
    if isinstance(msg.channel, DMChannel):
        return commands.when_mentioned_or(DEFAULT_PREFIX)(bot, msg)
    else:
        return commands.when_mentioned_or(bot.db.get_prefix(msg.guild.id))(bot, msg)


class ConfigHandler(commands.Cog):

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        super().__init__()
        ConfigHandler.bot = self.bot
        self.bot.tree.add_command(self.ConfigCommands())
    
    @commands.Cog.listener()
    async def on_ready(self):
        for guild in self.bot.guilds:
            if self.bot.db.get_prefix(guild.id) is None:
                self.bot.db.innit_guild(guild.id, DEFAULT_PREFIX, DEFAULT_LB_SIZE, DEFAULT_MAX_REPLY, DEFAULT_WS_GUESSES, DEFAULT_HL_MAX_NUMBER)
            
    
    @commands.Cog.listener()
    async def on_guild_join(self, guild: Guild):
        self.bot.db.innit_guild(guild.id, DEFAULT_PREFIX, DEFAULT_LB_SIZE, DEFAULT_MAX_REPLY, DEFAULT_WS_GUESSES)

    @commands.command(name='reconnect')
    async def _reconnect(self, ctx: commands.Context):
        self.bot.db.reconnect()
        ctx.reply("Reconnected successfully")


    class ConfigCommands(app_commands.Group, name='config', description='Config commands. User needs administrative perms to use these commands.'):

        def __init__(self, *args, **kwargs) -> None:
            super().__init__(*args, **kwargs)
            self.bot = ConfigHandler.bot
            
        @app_commands.command(name='command_prefix', description='Change my prefix')
        @app_commands.default_permissions(administrator=True)
        async def _command_prefix(self, interaction: Interaction, new_prefix: str):
            self.bot.db.update_prefix(interaction.guild_id, new_prefix)
            await interaction.response.send_message(f"The prefix has been updated to {new_prefix}", ephemeral=True)
        

        @app_commands.command(name='perms', description='Update channel/roles')
        @app_commands.default_permissions(administrator=True)
        @app_commands.choices(
            channel_type = [
                Choice(name="WordSnake", value='WordSnake'),
                Choice(name='NTBPL', value='NTBPL'),
                Choice(name='HigherLower', value='HigherLower'),
                Choice(name='ConnectFour', value='ConnectFour'),
                Choice(name='HangMan', value='HangMan'),
                Choice(name='CubeLvl', value='CubeLvl'),
                Choice(name='Polly', value='Polly'),
                Choice(name='Polly Roles', value='Polly_role_id'),
                Choice(name='Logging', value='Log')
            ],
            action = [
                Choice(name='Remove', value='remove'),
                Choice(name='Add', value='add'),
                Choice(name='List', value='list')
            ]
        )
        async def _channel(self, interaction: Interaction, channel_type: str, action: str, channel: TextChannel = None, role: Role = None):

            if channel_type == 'Polly_role_id':
                adder = role
                adder_type = 'role'
                adder_symbol = "@&"
            else:
                adder = channel
                adder_type = 'channel'
                adder_symbol = '#'


            s = self.bot.db.get_channel(interaction.guild_id, channel_type)
            s: list
            if action == 'add':
                s.append(adder.id)
                self.bot.db.update_channel(interaction.guild_id, channel_type, ','.join([str(i) for i in s]))
                await interaction.response.send_message(f'Added <{adder_symbol}{adder.id}> as {adder_type} used for {channel_type}')

                if channel_type == 'HigherLower':
                    if (data := self.bot.db.get_HigherLower_data(channel.id)) is None:
                        self.bot.db.HigherLower_game_switch(channel.id, True)
                        self.bot.db.update_HigherLower_data(channel.id, 0, randint(1, self.bot.db.get_game_setting(channel.guild.id, 'HL_max_number')), self.bot.user.id)

            elif action == 'remove':
                try:
                    s.remove(adder.id)
                    new_s = ','.join([str(i) for i in s])   
                    if new_s == '':
                        new_s = None
                    self.bot.db.update_channel(interaction.guild_id, channel_type, new_s)
                    await interaction.response.send_message(f'Removed <{adder_symbol}{adder.id}> from {adder_type}s used for {channel_type}')
                except ValueError:
                    await interaction.response.send_message(f'This <{adder_symbol}{adder.id}> was not used for {channel_type}')
            else:
                l = [f'<{adder_symbol}{i}>' for i in s]
                if len(l) > 10:
                    l = l[:10]
                    await interaction.response.send_message(f'More than 10 active {adder_type}s for {channel_type}, displaying first 10.\n' + "\n".join(l))
                elif l == []:
                    await interaction.response.send_message(f'No active {adder_type}s for {channel_type}.')
                else:
                    await interaction.response.send_message(f"Active {adder_type}(s) for {channel_type}" + "\n".join(l))
                

        @app_commands.command(name='game_settings', description='Change the settings of games')
        @app_commands.default_permissions(administrator=True)
        @app_commands.choices(
            game_setting = [
                Choice(name='Maximum amount of users displayed on a leaderbord (Default: 15, Max: 20)', value='max_lb_size'),
                Choice(name='Maximum consecutive replies by the same user in HigherLower (Default: 3)', value='HL_max_reply'),
                Choice(name='Maximum amount of tolerated wrong guesses in WordSnake (Default 1, Max: 5)', value='WS_wrong_guesses'),
                Choice(name="Maximum value of the number in HigherLower (Default: 1000)", value="HL_max_number")
            ]
        )
        async def _game_settings(self, interaction: Interaction, game_setting: str, value: int):
            value = abs(value)
            current_setting = self.bot.db.get_game_setting(interaction.guild_id, game_setting)
            updated_setting = {
                'max_lb_size': 'maximum amount of users displayed on a leaderbord',
                'HL_max_reply': 'maximum consecutive replies by the same user in HigherLower',
                'WS_wrong_guesses': 'maximum amount of tolerated wrong guesses in WordSnake',
                'HL_max_number': 'maximum value of the number in HigherLower'
            }[game_setting]

            if game_setting == 'max_lb_size' and value > 20:
                value = 20
            elif game_setting == 'WS_wrong_guesses' and value > 5:
                value = 5

            self.bot.db.update_game_setting(interaction.guild_id, game_setting, value)
            await interaction.response.send_message(f"Updated {updated_setting} from {current_setting} to {value}.")

async def setup(bot: commands.Bot):
    await bot.add_cog(ConfigHandler(bot))
