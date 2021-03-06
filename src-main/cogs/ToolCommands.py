import re
import aiohttp
import typing
import discord
import datetime

from discord.ext import commands, menus

import imports.time as time
from imports.MyMenuPages import MyMenuPages
from Botty import Botty

class UrbanDictionaryPageSource(menus.ListPageSource):
    BRACKETED = re.compile(r'(\[(.+?)\])')

    def __init__(self, data: list[dict[str, typing.Any]]):
        super().__init__(entries=data, per_page=1)

    def cleanup_definition(self, definition: str, *, regex=BRACKETED) -> str:
        def repl(m):
            word = m.group(2)
            return f'[{word}](http://{word.replace(" ", "-")}.urbanup.com)'

        ret = regex.sub(repl, definition)
        if len(ret) >= 2048:
            return ret[0:2000] + ' [...]'
        return ret

    async def format_page(self, menu: MyMenuPages, entry: dict[str, typing.Any]):
        maximum = self.get_max_pages()
        title = f'{entry["word"]}: {menu.current_page + 1} out of {maximum}' if maximum else entry['word']
        embed = discord.Embed(title=title, colour=0xE86222, url=entry['permalink'])
        embed.set_footer(text=f'by {entry["author"]}')
        embed.description = self.cleanup_definition(entry['definition'])

        try:
            up, down = entry['thumbs_up'], entry['thumbs_down']
        except KeyError:
            pass
        else:
            embed.add_field(name='Votes', value=f'\N{THUMBS UP SIGN} {up} \N{THUMBS DOWN SIGN} {down}', inline=False)

        try:
            date = discord.utils.parse_time(entry['written_on'][0:-1])
        except (ValueError, KeyError):
            pass
        else:
            embed.timestamp = date

        return embed


class ToolCommands(commands.Cog):

    def __init__(self, bot: Botty) -> None:
        self.bot = bot
        super().__init__()
    
    @commands.command(aliases=['avt'], no_pm=True)
    async def avatar(self, ctx, user: discord.Member = None):
        """
        A users avatar
        """
        if user is None:
            user = ctx.author
        embed = discord.Embed(title=f"Avatar of {user}", color=0xad3998)
        embed.description = f"Links: \n [png]({str(user.avatar.url).replace('webp', 'png')}) | [jpg]" \
                            f"({str(user.avatar.url).replace('webp', 'jpg')}) | [webp]({user.avatar.url})"
        embed.set_image(url=user.avatar.url)
        await ctx.send(embed=embed)
    
    @commands.command(no_pm=True)
    async def info(self, ctx: commands.Context, user: typing.Union[discord.Member, discord.User] = None):
        """
        Small embed with information about the Member.
        """
        user = user or ctx.author
        embed = discord.Embed()
        roles = [role.name.replace('@', '@\u200b') for role in getattr(user, 'roles', [])]
        embed.set_author(name=str(user))

        def format_date(dt: datetime.datetime):
            if dt is None:
                return 'N/A'
            return f'{time.format_dt(dt, "F")} ({time.format_relative(dt)})'
        
        embed.add_field(name='Name | Nick | ID', value=f'{user.name} | {user.nick} | {user.id}', inline=False)
        embed.add_field(name='Joined', value=format_date(getattr(user, 'joined_at', None)), inline=False)
        embed.add_field(name='Created', value=format_date(user.created_at), inline=False)
        embed.add_field(name='On Mobile | status', value=f'{user.is_on_mobile()} | {user.status}', inline=False)

        voice = getattr(user, 'voice', None)
        if voice is not None:
            vc = voice.channel
            other_people = len(vc.members) - 1
            voice = f'{vc.name} with {other_people} others' if other_people else f'{vc.name} by themselves'
            embed.add_field(name='Voice', value=voice, inline=False)
        
        if roles:
            embed.add_field(name='Roles', value=', '.join(roles) if len(roles) < 10 else f'{len(roles)} roles', inline=False)
        
        colour = user.colour
        if colour.value:
            embed.colour = colour
            
        embed.set_thumbnail(url=user.display_avatar.url)

        if isinstance(user, discord.User):
            embed.set_footer(text='This member is not in this server.')

        await ctx.send(embed=embed)
    
    @commands.command(name='urban')
    async def _urban(self, ctx: commands.Context, *, word: str):
        """Searches urban dictionary."""

        url = 'http://api.urbandictionary.com/v0/define'
        async with aiohttp.ClientSession() as cs:
            async with cs.get(url, params={'term': word}) as resp:
                if resp.status != 200:
                    return await ctx.send(f'An error occurred: {resp.status} {resp.reason}')

                js = await resp.json()
                data = js.get('list', [])
                if not data:
                    return await ctx.send('No results found, sorry.')

        pages = MyMenuPages(UrbanDictionaryPageSource(data), ctx=ctx, delete_message_after=True)
        await pages.start(ctx)
    
    @commands.hybrid_command(name='leaderboard', description='Fetch the leaderboard for a game in a specific channel!', aliases=['lb'])
    @discord.app_commands.choices(
        game = [
            discord.app_commands.Choice(name='ConnectFour', value='ConnectFour'),
            discord.app_commands.Choice(name='HangMan', value='HangMan'),
            discord.app_commands.Choice(name='HigherLower', value='HigherLower'),
            discord.app_commands.Choice(name='NTBPL', value='NTBPL'),
            discord.app_commands.Choice(name='Wordsnake', value='WordSnake')
        ]
    )
    async def _leaderboard(self, ctx: commands.Context, game: str = None, channel: discord.TextChannel = None):
        """
        Display the leaderboard for a game per channel, shorter: lb \n
        Only calling lb will display the leaderboard for this channel you are in. This might cause some weird points if the channel was used for more than one game.
        """

        if not channel:
            channel = ctx.channel
        
        max_lb_size = self.bot.db.get_game_setting(ctx.guild.id, 'max_lb_size')
        data = self.bot.db.get_lb(channel.id, max_lb_size, game)

        if data:
            description = ""
            lb_prefix = ['????', '????', '????'] + [str(i) for i in range(4, max_lb_size + 1)]
            for entry in data:
                description += f"{lb_prefix[data.index(entry)]}: <@{entry[1]}> - **{entry[2]}**\n"

            if ctx.author.id not in [i[1] for i in data]:
                description += f'Your score: {self.bot.db.get_score(game, channel.id, ctx.author.id)}'

            title = f"??? {game if game else ''} leaderboard for {channel.name} ! ????"
            embed = discord.Embed(title=title, description=description, color=0xad3998)
            await ctx.send(embed=embed)
        else:
            await ctx.send(game + "has not been played in" if game else "No leaderboard for" + channel.mention , ephemeral=True)

async def setup(bot: Botty):
    await bot.add_cog(ToolCommands(bot))