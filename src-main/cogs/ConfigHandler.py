import os
import json
import random
import typing
import discord

from discord.ext import commands, menus

from imports.MyMenuPages import MyMenuPages


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

class ChannelPageSource(menus.ListPageSource):

    def __init__(self, data, options: str):
        self.option = options
        super().__init__(data, per_page=6)
    
    async def format_page(self, menu, entries):
        page = menu.current_page
        max_page = self.get_max_pages()
        starting_number = page * self.per_page + 1
        page_content = "\n\n".join(entries)
        embed = discord.Embed(
            title=f"Channels in use for {self.option}", 
            description=page_content,
            color=0xad3998,
            timestamp=discord.utils.utcnow()
        )
        author = menu.ctx.author
        embed.set_footer(text=f"Requested by {author}", icon_url=author.avatar.url)
        return embed

class ConfigHandler(commands.Cog):

    CHANNEL_TYPES = [
                discord.app_commands.Choice(name="WordSnake", value='WordSnake'),
                discord.app_commands.Choice(name='NTBPL', value='NTBPL'),
                discord.app_commands.Choice(name='HigherLower', value='HigherLower'),
                discord.app_commands.Choice(name='ConnectFour', value='ConnectFour'),
                discord.app_commands.Choice(name='HangMan', value='HangMan'),
                discord.app_commands.Choice(name='CubeLvl', value='CubeLvl'),
                discord.app_commands.Choice(name='Polly', value='Polly'),
                discord.app_commands.Choice(name='Polly Roles', value='Polly_role_id'),
                discord.app_commands.Choice(name='Logging', value='Log')
            ]

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
    
    @commands.command(hidden=True)
    @commands.is_owner()
    async def sync(self, ctx: commands.Context, guilds: commands.Greedy[discord.Object], spec: typing.Optional[typing.Literal["~"]] = None) -> None:
        """
        Command for syncing app_commands, can only be used by my owners.
        """
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
    
    @commands.command(name='reload', hidden=True)
    @commands.is_owner()
    async def _reload(self, ctx: commands.Context, *names: str):
        """
        Command for reloading Cogs, can only be used by my owners.
        """
        files = [f'cogs.{name}' for name in names] if names else [f'cogs.{name[:-3]}' for name in os.listdir('./cogs') if name.endswith('.py') and name != 'ConfigHandler.py']
        successful_reloads = []
        failed_reloads = []

        for file in files:
            try:
                await self.bot.reload_extension(file)
                successful_reloads.append(file)
            except commands.errors.ExtensionFailed:
                failed_reloads.append(file)
        
        e = discord.Embed(title='Cog reloads', colour=0xad3998, timestamp=discord.utils.utcnow())

        succ_value = "\u200b"
        failed_value = "\u200b"

        for index, file in enumerate(successful_reloads):
            succ_value += f"{file}\n"

            if len(succ_value) > 1000 or index == len(successful_reloads) - 1:
                e.add_field(name='Successful!', value=succ_value, inline=False)
                succ_value = "\u200b"
        
        for index, file in enumerate(failed_reloads):
            failed_value += f'{file}\n'

            if len(failed_value) > 1000 or index == len(successful_reloads) - 1:
                e.add_field(name='Failed!', value=failed_value, inline=False)
        
        await ctx.send(embed=e)

    @commands.hybrid_group(name='config', description='Config commands.')
    @discord.app_commands.default_permissions()
    @discord.app_commands.guild_only()
    async def _config(self, ctx: commands.Context):
        """
        Configure various attributes, for more info use !help config.
        In order to use any of these commands you'll need administrative privileges in the server.
        This requirement can be changed for the Slash Command variants by other admins.
        Recommended to use Slash Commands, these have better auto complete options
        """
        ...
    
    @_config.command(name='prefix', description='Change my prefix')
    async def _prefix(self, ctx: commands.Context, new_prefix: str):
        """ 
        Change the default prefix. Tagging me always works.
        """
        self.bot.db.update_prefix(ctx.guild.id, new_prefix)
        await ctx.reply(f"The prefix has been updated to {new_prefix}", ephemeral=True)

    @_config.group(name="channels", description='Update and view used channels per type')
    @discord.app_commands.default_permissions()
    @discord.app_commands.guild_only()
    async def _channels(self, ctx: commands.Context):
        """ 
        Remove, Add or List all channels where one of my features works.
        There is no information loss when removing a channel for a game!
        """
        ...
    
    async def snowflake_autocomplete(self, interaction: discord.Interaction, current: str) -> typing.List[discord.app_commands.Choice[str]]:
        if interaction.namespace.channel_type != '':
            channels = self.bot.db.get_channel(interaction.guild_id, interaction.namespace.channel_type)
            choices = [self.bot.get_channel(i) for i in channels]
        else:
            choices = [channel for channel in interaction.guild.channels]

        choices = [channel for channel in choices if current in channel.name]
        
        return [discord.app_commands.Choice(name=channel.name, value=str(channel.id)) for channel in choices][:25]
    
    @_channels.command(name='remove', description="Remove a channel of use")
    @discord.app_commands.autocomplete(snowflake=snowflake_autocomplete)
    @discord.app_commands.choices(channel_type=CHANNEL_TYPES)
    async def _remove(self, ctx: commands.Context, channel_type: str, snowflake: str):
        """
        Remove a channel for use. 
        While using slash commands, only used channels appear.
        """
        if not snowflake.isdigit():
            snowflake = str([i for i in ctx.guild.channels if i.name == snowflake][0].id)
        channel_list: list = self.bot.db.get_channel(ctx.guild.id, channel_type)
        channel_list.remove(int(snowflake))

        new_channel_list = None if ','.join([str(i) for i in channel_list]) == '' else ','.join([str(i) for i in channel_list])
        self.bot.db.update_channel(ctx.guild.id, channel_type, new_channel_list)
        await ctx.send(f'Removed <#{snowflake}> from channels used for {channel_type}')
    
    @_channels.command(name='add', description="Add a channel for use")
    @discord.app_commands.choices(channel_type=CHANNEL_TYPES)
    async def _add(self, ctx: commands.Context, channel_type: str, snowflake: discord.TextChannel):
        """
        Add a channel for use.
        You are able to have two games in the same channel, this is not recommended!
        """
        channel_list: list = self.bot.db.get_channel(ctx.guild.id, channel_type)
        channel_list.append(snowflake.id)

        self.bot.db.update_channel(ctx.guild.id, channel_type, ','.join([str(i) for i in channel_list]))
        await ctx.send(f'Added <#{snowflake.id}> as channel used for {channel_type}')

        if channel_type == 'HigherLower':
            if self.bot.db.get_HigherLower_data(snowflake) is None:
                self.bot.db.HigherLower_game_switch(snowflake, True)
                self.bot.db.update_HigherLower_data(snowflake, 0, random.randint(1, self.bot.db.get_game_setting(ctx.guild.id, 'HL_max_number')), self.bot.user.id)
    
    @_channels.command(name='list', description='Receive a list with all channels in use')
    @discord.app_commands.choices(channel_type=CHANNEL_TYPES)
    async def _list(self, ctx: commands.Context, channel_type: str):
        """
        List channels. If more than 10 in use, only 10 will be displayed.
        """
        channel_list: list = self.bot.db.get_channel(ctx.guild.id, channel_type)
        channel_list = [f'<#{i}>' for i in channel_list]

        if not channel_list:
            await ctx.send(f'No active channels for {channel_type}.')
            return
        
        await ctx.send('Preparing MenuPages', ephemeral=True, delete_after=5)
        formatter = ChannelPageSource(channel_list, channel_type)
        menu = MyMenuPages(formatter, delete_message_after=True)
        await menu.start(ctx)
    
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
        """
        Change game settings. These will be used in all active channels.
        """

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