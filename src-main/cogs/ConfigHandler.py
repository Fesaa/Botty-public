import json
import random
import typing
import discord

from discord.ext import commands


# Default values
DEFAULT_PREFIX = "!"
DEFAULT_LB_SIZE = 15
DEFAULT_CHANNEL = ''
DEFAULT_MAX_REPLY = 3
DEFAULT_WS_GUESSES = 1
DEFAULT_HL_MAX_NUMBER = 1000
config = json.load(open('config.json'))

# General
token = config['General']['Discord Token']
bot_id = config['General']['Bot-id']
# Database
host = config['mysql']['host']
Database = config['mysql']['database']
user = config['mysql']['user']
password = config['mysql']['password']


async def get_prefix(bot: commands.Bot, msg: discord.Message):
    if isinstance(msg.channel, discord.DMChannel):
        return commands.when_mentioned_or(DEFAULT_PREFIX)(bot, msg)
    else:
        return commands.when_mentioned_or(bot.db.get_prefix(msg.guild.id))(bot, msg)

class ConfigHandler(commands.Cog):

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        super().__init__()
    
    @commands.Cog.listener()
    async def on_ready(self):
        for guild in self.bot.guilds:
            if self.bot.db.get_prefix(guild.id) is None:
                self.bot.db.innit_guild(guild.id, DEFAULT_PREFIX, DEFAULT_LB_SIZE, DEFAULT_MAX_REPLY, DEFAULT_WS_GUESSES, DEFAULT_HL_MAX_NUMBER)
            
    
    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        self.bot.db.innit_guild(guild.id, DEFAULT_PREFIX, DEFAULT_LB_SIZE, DEFAULT_MAX_REPLY, DEFAULT_WS_GUESSES)
    
    @commands.command()
    @commands.is_owner()
    async def sync(self, ctx: commands.Context, guilds: commands.Greedy[discord.Object], spec: typing.Optional[typing.Literal["~"]] = None) -> None:
        if not guilds:
            if spec == "~":
                synced = await ctx.bot.tree.sync(guild=ctx.guild)
            elif spec == "*":
                ctx.bot.tree.copy_global_to(guild=ctx.guild)
                synced = await ctx.bot.tree.sync(guild=ctx.guild)
            elif spec == "^":
                ctx.bot.tree.clear_commands(guild=ctx.guild)
                await ctx.bot.tree.sync(guild=ctx.guild)
                synced = []
            else:
                synced = await ctx.bot.tree.sync()

            await ctx.send(
                f"Synced {len(synced)} commands {'globally' if spec is None else 'to the current guild.'}"
            )
            return

        ret = 0
        for guild in guilds:
            try:
                await ctx.bot.tree.sync(guild=guild)
            except discord.HTTPException:
                pass
            else:
                ret += 1

        await ctx.send(f"Synced the tree to {ret}/{len(guilds)}.")

    @commands.hybrid_group(name='config', description='Config commands. User needs administrative perms to use these commands.')
    @discord.app_commands.default_permissions()
    @discord.app_commands.guild_only()
    async def _config(self, ctx: commands.Context):
        ...
    
    @_config.command(name='prefix', description='Change my prefix')
    async def _prefix(self, ctx: commands.Context, new_prefix: str):
        self.bot.db.update_prefix(ctx.guild.id, new_prefix)
        await ctx.reply(f"The prefix has been updated to {new_prefix}", ephemeral=True)

    async def snowflake_autocomplete(self, interaction: discord.Interaction, current: str) -> typing.List[discord.app_commands.Choice[str]]:
        if interaction.namespace.action == 'remove' and interaction.namespace.channel_type != '':
            channels = self.bot.db.get_channel(interaction.guild_id, interaction.namespace.channel_type)
            choices = [self.bot.get_channel(i) for i in channels]
        else:
            choices = [channel for channel in interaction.guild.channels]

            choices = [channel for channel in choices if current in channel.name]
        
        return [discord.app_commands.Choice(name=channel.name, value=str(channel.id)) for channel in choices][:25]

    
    @_config.command(name='perms', description='Update channel/roles')
    @discord.app_commands.autocomplete(snowflake=snowflake_autocomplete)
    @discord.app_commands.choices(
            channel_type = [
                discord.app_commands.Choice(name="WordSnake", value='WordSnake'),
                discord.app_commands.Choice(name='NTBPL', value='NTBPL'),
                discord.app_commands.Choice(name='HigherLower', value='HigherLower'),
                discord.app_commands.Choice(name='ConnectFour', value='ConnectFour'),
                discord.app_commands.Choice(name='HangMan', value='HangMan'),
                discord.app_commands.Choice(name='CubeLvl', value='CubeLvl'),
                discord.app_commands.Choice(name='Polly', value='Polly'),
                discord.app_commands.Choice(name='Polly Roles', value='Polly_role_id'),
                discord.app_commands.Choice(name='Logging', value='Log')
            ],
            action = [
                discord.app_commands.Choice(name='Remove', value='remove'),
                discord.app_commands.Choice(name='Add', value='add'),
                discord.app_commands.Choice(name='List', value='list')
            ])
    async def _perms(self, ctx: commands.Context, channel_type: str, action: str, snowflake: str):
        adder_type = 'channel'
        adder_symbol = '#'
        
        channel_list: list = self.bot.db.get_channel(ctx.guild.id, channel_type)

        if action == 'add':
            channel_list.append(snowflake)
            self.bot.db.update_channel(ctx.guild.id, channel_type, ','.join([str(i) for i in channel_list]))
            await ctx.send(f'Added <{adder_symbol}{snowflake}> as {adder_type} used for {channel_type}')

            if channel_type == 'HigherLower':
                if self.bot.db.get_HigherLower_data(snowflake) is None:
                    self.bot.db.HigherLower_game_switch(snowflake, True)
                    self.bot.db.update_HigherLower_data(snowflake, 0, random.randint(1, self.bot.db.get_game_setting(ctx.guild.id, 'HL_max_number')), self.bot.user.id)

        elif action == 'remove':
            channel_list.remove(int(snowflake))
            new_channel_list = None if ','.join([str(i) for i in channel_list]) == '' else ','.join([str(i) for i in channel_list])
            self.bot.db.update_channel(ctx.guild.id, channel_type, new_channel_list)
            await ctx.send(f'Removed <{adder_symbol}{snowflake}> from {adder_type}s used for {channel_type}')

        elif action == 'list':
            l = [f'<{adder_symbol}{i}>' for i in channel_list][:10]
            if not l:
                await ctx.send(f'No active {adder_type}s for {channel_type}.')
                return
            await ctx.send(f"Active {adder_type}(s) for {channel_type}" + "\n".join(l))
    
    @_config.command(name='game_settings', description='Change the settings of games')
    @discord.app_commands.default_permissions(administrator=True)
    @discord.app_commands.choices(
        game_setting = [
            discord.app_commands.Choice(name='Maximum amount of users displayed on a leaderboard (Default: 15, Max: 20)', value='max_lb_size'),
            discord.app_commands.Choice(name='Maximum consecutive replies by the same user in HigherLower (Default: 3)', value='HL_max_reply'),
            discord.app_commands.Choice(name='Maximum amount of tolerated wrong guesses in WordSnake (Default 1, Max: 5)', value='WS_wrong_guesses'),
            discord.app_commands.Choice(name="Maximum value of the number in HigherLower (Default: 1000)", value="HL_max_number")
        ]
    )
    async def _game_settings(self, ctx: commands.Context, game_setting: str, value: int):
        if game_setting not in ['max_lb_size', 'HL_max_reply', 'WS_wrong_guesses', 'HL_max_number']:
            await ctx.send('This is not a valid setting. Feel free to use the help command if needed!', ephemeral=True)
            return
            
        value = abs(value)
        current_setting = self.bot.db.get_game_setting(ctx.guild.id, game_setting)
        updated_setting = {
            'max_lb_size': 'maximum amount of users displayed on a leaderboard',
            'HL_max_reply': 'maximum consecutive replies by the same user in HigherLower',
            'WS_wrong_guesses': 'maximum amount of tolerated wrong guesses in WordSnake',
            'HL_max_number': 'maximum value of the number in HigherLower'
        }[game_setting]

        if game_setting == 'max_lb_size' and value > 20:
            value = 20
        elif game_setting == 'WS_wrong_guesses' and value > 5:
            value = 5

        self.bot.db.update_game_setting(ctx.guild.id, game_setting, value)
        await ctx.send(f"Updated {updated_setting} from {current_setting} to {value}.")
                
async def setup(bot: commands.Bot):
    await bot.add_cog(ConfigHandler(bot))