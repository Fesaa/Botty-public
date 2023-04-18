import datetime
import re
import typing

import asyncpg
import aiohttp
import discord
from discord import Embed
from discord.ext import commands, menus  # type: ignore

import utils.time as time
from Botty import Botty
from utils.MyMenuPages import MyMenuPages
from framework import GameSetting, GameConfigUpdateEvent, CHANNEL_TYPES_CHOICE, Game


class UrbanDictionaryPageSource(menus.ListPageSource):
    BRACKETED = re.compile(r"(\[(.+?)\])")

    def __init__(self, data: list[dict[str, typing.Any]]):
        super().__init__(entries=data, per_page=1)

    def cleanup_definition(self, definition: str, *, regex=BRACKETED) -> str:
        def repl(m):
            word = m.group(2)
            return f'[{word}](http://{word.replace(" ", "-")}.urbanup.com)'

        ret = regex.sub(repl, definition)
        if len(ret) >= 2048:
            return ret[0:2000] + " [...]"
        return ret

    async def format_page(self, menu: MyMenuPages, entry: dict[str, typing.Any]):
        maximum = self.get_max_pages()
        title = (
            f'{entry["word"]}: {menu.current_page + 1} out of {maximum}'
            if maximum
            else entry["word"]
        )
        embed = Embed(title=title, colour=0xE86222, url=entry["permalink"])
        embed.set_footer(text=f'by {entry["author"]}')
        embed.description = self.cleanup_definition(entry["definition"])

        try:
            up, down = entry["thumbs_up"], entry["thumbs_down"]
        except KeyError:
            pass
        else:
            embed.add_field(
                name="Votes",
                value=f"\N{THUMBS UP SIGN} {up} \N{THUMBS DOWN SIGN} {down}",
                inline=False,
            )

        try:
            date = discord.utils.parse_time(entry["written_on"][0:-1])
        except (ValueError, KeyError):
            pass
        else:
            embed.timestamp = date

        return embed


class ToolCommands(commands.Cog):
    """
    A few helpful commands for user information and scores!
    """
    def __init__(self, bot: Botty) -> None:
        self.bot = bot
        super().__init__()

        self.lb_sizes: dict[int, int] = {}

    async def cog_load(self) -> None:
        async with self.bot.pool.acquire() as con:
            con: asyncpg.Connection
            guild_globals = await con.fetch("SELECT guild_id,lb_size FROM guild_settings;")
            for guild in guild_globals:
                self.lb_sizes[guild['guild_id']] = guild['lb_size']

            channel_overwrites = await con.fetch('SELECT channel_id,setting_value FROM channel_settings WHERE setting_type = $1;', GameSetting.MAX_LB_SIZE.value)
            for channel in channel_overwrites:
                self.lb_sizes[channel['channel_id']] = channel['setting_value']

    @property
    def display_emoji(self) -> discord.PartialEmoji:
        return discord.PartialEmoji(name='\U0001f6e0')

    @commands.Cog.listener()
    async def on_config_update(self, e: GameConfigUpdateEvent):
        if e.setting != GameSetting.MAX_LB_SIZE:
            return

        if e.channels:
            for channel in e.channels:
                self.lb_sizes[channel] = e.new_value
            query = f"""
            INSERT INTO
                channel_settings
                (channel_id, setting_value,setting_type)
            VALUES
                {','.join(f'({channel}, $1, $2)' for channel in e.channels)}
            ON CONFLICT
                (channel_id, setting_type)
            DO UPDATE SET
                setting_value = EXCLUDED.setting_value;
            """
            await self.bot.exec_sql(query, e.new_value, GameSetting.MAX_LB_SIZE.value)
            await e.ctx.send(f'Updated {e.setting.pretty()} to {e.new_value} in {len(e.channels)} channels.')
        else:
            query = f"""
            INSERT INTO
                channel_settings
                (channel_id, setting_value,setting_type)
            VALUES
                ($1, $2, $3)
            ON CONFLICT
                (channel_id, setting_type)
            DO UPDATE SET
                setting_value = EXCLUDED.setting_value;
            """
            await self.bot.exec_sql(query, e.ctx.guild.id, e.new_value, GameSetting.MAX_LB_SIZE.value)
            await e.ctx.send(f'Updated {e.setting.pretty()} to {e.new_value}.')


    @commands.command(aliases=["avt"], no_pm=True)
    @commands.cooldown(10, 60, commands.BucketType.guild)
    async def avatar(self, ctx: commands.Context, user: discord.Member = None):
        """
        Display a members avatar
        """
        if user is None:
            user = ctx.author

        user = await self.bot.fetch_user(user.id)


        if not user.avatar:
            return await ctx.send("User has no avatar")
        embed = Embed(title=f"Avatar of {user}", color=0xAD3998)
        embed.description = (
            f"Links: \n [png]({str(user.avatar.url).replace('webp', 'png')}) | [jpg]"
            f"({str(user.avatar.url).replace('webp', 'jpg')}) | [webp]({user.avatar.url})"
        )
        embed.set_image(url=user.avatar.url)
        await ctx.send(embed=embed)

    @commands.command(no_pm=True)
    @commands.cooldown(10, 60, commands.BucketType.guild)
    async def banner(self, ctx: commands.Context, user: discord.Member = None):
        """
        Displays a members banner
        """
        if user is None:
            user = ctx.author
        
        user = await self.bot.fetch_user(user.id)

        if not user.banner:
            return await ctx.send("User has no banner")
        embed = Embed(title=f"Banner of {user}", color=0xAD3998)
        embed.description = (
            f"Links: \n [png]({str(user.banner.url).replace('webp', 'png')}) | [jpg]"
            f"({str(user.banner.url).replace('webp', 'jpg')}) | [webp]({user.banner.url})"
        )
        embed.set_image(url=user.banner.url)
        await ctx.send(embed=embed)

    @commands.command(no_pm=True)
    async def info(
        self,
        ctx: commands.Context,
        user: typing.Union[discord.Member, discord.User] = None,
    ):
        """
        Small embed with information about a user
        """
        user = user or ctx.author
        embed = Embed()
        roles = [role.name.replace("@", "@\u200b") for role in getattr(user, "roles", [])]
        embed.set_author(name=str(user))

        def format_date(dt: datetime.datetime):
            if dt is None:
                return "N/A"
            return f'{time.format_dt(dt, "F")} ({time.format_relative(dt)})'

        embed.add_field(
            name="Name | Nick | ID",
            value=f"{user.name} | {getattr(user, 'nick', None)} | {user.id}",
            inline=False,
        )
        embed.add_field(
            name="Joined",
            value=format_date(getattr(user, "joined_at", None)),  # type: ignore
            inline=False,
        )
        embed.add_field(
            name="Created", value=format_date(user.created_at), inline=False
        )

        voice = getattr(user, "voice", None)
        if voice is not None:
            vc = voice.channel
            other_people = len(vc.members) - 1
            voice = (
                f"{vc.name} with {other_people} others"
                if other_people
                else f"{vc.name} by themselves"
            )
            embed.add_field(name="Voice", value=voice, inline=False)

        if roles:
            embed.add_field(
                name="Roles",
                value=", ".join(roles) if len(roles) < 10 else f"{len(roles)} roles",
                inline=False,
            )

        colour = user.colour
        if colour.value:
            embed.colour = colour

        embed.set_thumbnail(url=user.display_avatar.url)

        if isinstance(user, discord.User):
            embed.set_footer(text="This member is not in this server.")

        await ctx.send(embed=embed)

    @commands.command(name="urban")
    async def _urban(self, ctx: commands.Context, *, word: str):
        """Searches urban dictionary."""

        url = "http://api.urbandictionary.com/v0/define"
        async with aiohttp.ClientSession() as cs:
            async with cs.get(url, params={"term": word}) as resp:
                if resp.status != 200:
                    return await ctx.send(f"An error occurred: {resp.status} {resp.reason}")

                js = await resp.json()
                data = js.get("list", [])
                if not data:
                    return await ctx.send("No results found, sorry.")

        pages = MyMenuPages(UrbanDictionaryPageSource(data), ctx=ctx, delete_message_after=True)
        await pages.start(ctx)


    async def get_lb_data(self, channel: int, *, game: str) -> list[asyncpg.Record]:
        async with self.bot.pool.acquire() as con:
            con: asyncpg.Connection
            if not game:
                query = """
                SELECT 
                    user_id,SUM(score)
                FROM
                    scoreboard
                WHERE
                    channel_id = $1
                AND
                    user_id != $2
                GROUP BY
                    user_id
                ORDER BY DESC;
                """
                return await con.fetch(query, channel, self.bot.user.id)
            else:
                query = """
                SELECT 
                    user_id,SUM(score)
                FROM
                    scoreboard
                WHERE
                    channel_id = $1
                AND
                    game = $2
                AND
                    user_id != $3
                GROUP BY
                    user_id
                ORDER BY DESC;
                """
                return await con.fetch(query, channel, game, self.bot.user.id)

    @commands.hybrid_command(name="scoreboard",description="Fetch a scoreboard")
    @discord.app_commands.describe(channel="In a specific channel?", game="For a specific game?")
    @discord.app_commands.choices(game=CHANNEL_TYPES_CHOICE)
    @discord.app_commands.guild_only()
    async def _leaderboard(
        self,
        interaction: commands.Context,
        channel: discord.TextChannel = None,
        game: str = None,
    ):
        """
        Display the scoreboard for a game per channel\n
        Calling the scoreboard without any options cal display unwanted values. Be sure the specific what you are requesting. 
        """
        if not interaction.guild or not interaction.channel:
            return
        max_lb_size = self.lb_sizes.get(interaction.channel.id, None) or self.lb_sizes.get(interaction.guild.id, 15)
        if not channel:
            channel = interaction.channel

        if not game:
            title = f"⭐ Scores for all games in {channel.name}🌟"
        else:
            title = f"⭐ {game} scores for {channel.name}🌟"
            try:
                Game[game.upper()]
            except KeyError:
                return await interaction.send("Game not found. Please try again", ephemeral=True)

        data = await self.get_lb_data(channel.id, game=game)

        if not data:
            return await interaction.send("No scores where found for you query \U0001f641", ephemeral=True)
        description = ""
        lb_prefix = ["🥇", "🥈", "🥉"] + [str(i) for i in range(4, max_lb_size + 1)]
        for index, entry in enumerate(data[:max_lb_size]):
            description += f"{lb_prefix[index]}: <@{entry['user_id']}> - **{entry.get('score', entry.get('sum', 'unknown'))}**\n"
        e = Embed(title=title, description=description, color=0xAD3998)
        await interaction.send(embed=e)



async def setup(bot: Botty):
    await bot.add_cog(ToolCommands(bot))
