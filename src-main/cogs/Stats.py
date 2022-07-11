import typing
import discord
import pkg_resources

from discord.ext import commands, tasks, menus

from Botty import Botty
from imports.MyMenuPages import MyMenuPages
import imports.time as time

class CommandsStatsPageSource(menus.ListPageSource):

    def __init__(self, data):
        super().__init__(data, per_page=9)
    
    async def format_page(self, menu, entries):
        page = menu.current_page
        max_page = self.get_max_pages()

        e = discord.Embed(title=f"Commands [{page + 1}/{max_page}]", color=0xad3998, timestamp=discord.utils.utcnow())
        for info in entries:
            info: dict
            command_name = info[0]
            uses = info[1]
            e.add_field(name=command_name, value=uses, inline=True)

        author = menu.ctx.author
        e.set_footer(text=f"Requested by {author}", icon_url=author.avatar.url)
        return e

class Stats(commands.Cog):

    def __init__(self, bot: Botty) -> None:
        self.bot = bot

        self.update_command_stats_loop.start()

        super().__init__()
    
    async def cog_load(self) -> None:
        if not hasattr(self, 'command_stats'):
            self.command_stats = {}
            for guild in self.bot.guilds:
                self.command_stats[guild.id] = self.bot.db.stats_get_guild_info(guild.id)['users']
        return await super().cog_load()
    
    @commands.Cog.listener()
    async def on_ready(self):
        if not hasattr(self, 'command_stats'):
            self.command_stats = {}
            for guild in self.bot.guilds:
                self.command_stats[guild.id] = self.bot.db.stats_get_guild_info(guild.id)['users']

    def get_bot_uptime(self, *, brief: bool = False) -> str:
        return time.human_timedelta(self.bot.uptime, accuracy=None, brief=brief, suffix=False)
    
    def update_guild_stats(self, guild_id: int):
        self.bot.db.stats_update_guild_info(guild_id, self.command_stats[guild_id])
    
    def update_guild_stat_cache(self, ctx: commands.Context):
        if ctx.guild.id not in self.command_stats:
            self.command_stats[ctx.guild.id] = {}
        d = self.command_stats[ctx.guild.id]

        if ctx.author.id not in d:
            d[ctx.author.id] = {}
        
        name = ctx.command.full_parent_name
        if len(name) > 0:
            name += " "
        name += ctx.command.name
        
        if name not in d[ctx.author.id]:
            d[ctx.author.id][name] = 1
        else:
            d[ctx.author.id][name] += 1
        
        self.command_stats[ctx.guild.id] = d
    
    def total_command_executions(self, ctx: commands.Context):
        return sum([i for i in self.bot.db.stats_get_guild_info(ctx.guild.id)['global'].values()])
    
    @commands.Cog.listener()
    async def on_command_completion(self, ctx: commands.Context):
        self.update_guild_stat_cache(ctx)
    
    @tasks.loop(seconds=10)
    async def update_command_stats_loop(self):

        if not hasattr(self, 'command_stats'):
            return

        for guild_id in self.command_stats.keys():
            self.update_guild_stats(guild_id)

    @commands.command()
    async def uptime(self, ctx: commands.Context):
        """Tells you how long the bot has been up for."""
        await ctx.send(f'Uptime: **{self.get_bot_uptime()}**')
    
    @commands.command()
    @commands.is_owner()
    async def commandstats(self, ctx: commands.Context, user: typing.Optional[discord.Member]=None):
        self.update_guild_stats(ctx.guild.id)
        command_list: dict = self.bot.db.stats_get_guild_info(ctx.guild.id)['users' if user else 'global']
        
        if not user:
            command_list = [(command, uses) for command, uses in command_list.items()]
        else:
            command_list = [(command, uses) for command, uses in command_list[user.id].items()]

        formatter = CommandsStatsPageSource(command_list)
        menu = MyMenuPages(formatter, delete_message_after=True)
        await menu.start(ctx)

    
    @commands.command()
    async def about(self, ctx: commands.Context):
        """Tells you information about the bot itself."""

        embed = discord.Embed()
        embed.colour = discord.Colour.blurple()

        embed.set_author(name=str(self.bot.owner), icon_url=self.bot.owner.display_avatar.url)

        # statistics
        total_members = 0
        total_unique = len(self.bot.users)

        text = 0
        voice = 0
        guilds = 0
        for guild in self.bot.guilds:
            guilds += 1
            if guild.unavailable:
                continue

            total_members += guild.member_count or 0
            for channel in guild.channels:
                if isinstance(channel, discord.TextChannel):
                    text += 1
                elif isinstance(channel, discord.VoiceChannel):
                    voice += 1

        embed.add_field(name='Members', value=f'{total_members} total\n{total_unique} unique')
        embed.add_field(name='Channels', value=f'{text + voice} total\n{text} text\n{voice} voice')

        version = pkg_resources.get_distribution('discord.py').version
        embed.add_field(name='Guilds', value=guilds)
        embed.add_field(name='Commands Run', value=self.total_command_executions(ctx)+1)
        embed.add_field(name='Uptime', value=self.get_bot_uptime(brief=True))
        embed.set_footer(text=f'Made with discord.py v{version}', icon_url='http://i.imgur.com/5BFecvA.png')
        embed.timestamp = discord.utils.utcnow()
        await ctx.send(embed=embed)

async def setup(bot: Botty):
    await bot.add_cog(Stats(bot))