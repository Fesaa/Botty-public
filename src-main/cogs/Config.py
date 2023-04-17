from typing import (
    TYPE_CHECKING,
    Optional
)

import asyncpg
import discord
from discord.ext import commands

from framework import (
    Game,
    GameChannelUpdateEvent,
    Update,
    GameSetting,
    GameConfigUpdateEvent,
    CHANNEL_TYPES_CHOICE
)

if TYPE_CHECKING:
    from Botty import Botty


GAME_SETTINGS_CHOICE = [
        discord.app_commands.Choice(
            name="Maximum amount of player displayed on a scoreboard (Default: 15, Max: 20)",
            value="max_lb_size",
        ),
        discord.app_commands.Choice(
            name="Maximum consecutive replies by the same player in HigherLower (Default: 3)",
            value="hl_max_reply",
        ),
        discord.app_commands.Choice(
            name="Maximum amount of tolerated wrong guesses in WordSnake (Default 1, Max: 5)",
            value="ws_wrong_guesses",
        ),
        discord.app_commands.Choice(
            name="Maximum value of the number in HigherLower (Default: 1000)",
            value="hl_max_number",
        ),
    ]

class ConfigCog(commands.Cog):
    """
    Configure Botty to your liking.
    It is recommended to use slash commands, but text commands are an option.
    """

    def __init__(self, bot: 'Botty') -> None:
        super().__init__()
        self.bot = bot

    @property
    def display_emoji(self) -> discord.PartialEmoji:
        return discord.PartialEmoji(name='\U00002699')

    async def exec_sql(self, query: str, *val):
        async with self.bot.pool.acquire() as con:
            con: asyncpg.Connection
            await con.execute(query, *val)

    @commands.Cog.listener
    async def on_guild_join(self, guild: discord.Guild):
        defaults = self.bot.default_values
        await self.exec_sql("INSERT INTO prefixes (guild_id, prefix) VALUES ($1, $2);", guild.id, self.bot.config["DISCORD"]["DEFAULT_PREFIX"])
        await self.exec_sql("""
        INSERT INTO
            guild_settings
            (guild_id, lb_size, hl_max_reply, ws_wrong_guesses, hl_max_number)
        VALUES
            ($1, $2, $3, $4, $5);
        """, guild.id, defaults.default_lb_size, defaults.default_max_reply, defaults.default_ws_guesses, defaults.default_hl_max_number)

    @commands.command(name="prefix")
    @commands.guild_only()
    async def _prefix(self, ctx: commands.Context['Botty']):
        """All prefixes being used on the server"""
        await ctx.send(f"I listen for the following prefixes in this server: {','.join(f'`{prefix}`' for prefix in (await self.bot.get_prefix(ctx.message)))}")

    @commands.hybrid_group(name="config")
    @discord.app_commands.default_permissions(administrator=True)
    @discord.app_commands.guild_only()
    @commands.has_guild_permissions(administrator=True)
    @commands.guild_only()
    async def _config_group(self, _: commands.Context['Botty']):
        """Base config command group."""
        ...

    @_config_group.group(name="prefix")
    async def _manage_prefix_group(self, _: commands.Context['Botty']):
        """Manage which prefixes are used in your server"""
        ...

    @_manage_prefix_group.command(name="add")
    async def _add_prefix(self, ctx: commands.Context['Botty'], prefix: str):
        """Add an extra prefix to listen for in your server"""
        if not prefix:
            return await ctx.send("Please provide a new prefix.", ephemeral=True)
        if self.bot.prefixes.get(ctx.guild.id, []).count(prefix) == 0:
            if self.bot.prefixes.get(ctx.guild.id, None):
                self.bot.prefixes[ctx.guild.id].append(prefix)
            else:
                self.bot.prefixes[ctx.guild.id] = [prefix]
            await self.exec_sql("INSERT INTO prefixes (guild_id, prefix) VALUES ($1, $2)", ctx.guild.id, prefix)
            return await ctx.send(f"Added `{prefix}` as a possible prefix!", ephemeral=True)
        return await ctx.send("You were already using this prefix. Nothing changed.", ephemeral=True)

    async def current_prefixes(self, interaction: discord.Interaction, current: str) -> list[discord.app_commands.Choice[str]]:
        return [
            discord.app_commands.Choice(name=prefix, value=prefix)
            for prefix in
            self.bot.prefixes.get(interaction.guild_id, [])
        ][::25]

    @_manage_prefix_group.command(name="remove")
    @discord.app_commands.autocomplete(prefix=current_prefixes)
    async def _remove_prefix(self, ctx: commands.Context['Botty'], prefix: str):
        """Remove a prefix for your server"""
        if prefix not in self.bot.prefixes.get(ctx.guild.id, []):
            return await ctx.send("Cannot remove non existing prefix.", ephemeral=True)

        self.bot.prefixes.get(ctx.guild.id, []).remove(prefix)
        await self.exec_sql("DELETE FROM prefixes WHERE guild_id = $1 AND prefix = $2;", ctx.guild.id, prefix)
        return await ctx.send(f"Removed `{prefix}` as a possible prefix.", ephemeral=True)

    @_config_group.group(name="channels")
    async def _manage_channels_group(self, _: commands.Context['Botty']):
        """Manage which games are played in which channel"""
        ...
    @_manage_channels_group.command(name="add")
    @discord.app_commands.choices(game=CHANNEL_TYPES_CHOICE)
    async def _add_channel(self, ctx: commands.Context['Botty'], game: str, channel: discord.TextChannel):
        """Add channels to be used as game channels
        """
        try:
            game: Game = Game[game.upper()]
        except KeyError:
            return await ctx.send("Invalid game. Please try again.", ephemeral=True)

        self.bot.dispatch('game_channel_update', GameChannelUpdateEvent(game, Update.ADD, ctx, channel.id))

    @_manage_channels_group.command(name="remove")
    @discord.app_commands.choices(game=CHANNEL_TYPES_CHOICE)
    async def _remove_channel(self, ctx: commands.Context['Botty'], game: str, channel: discord.TextChannel):
        """Remove channels to from being as game channels
        """
        try:
            game: Game = Game[game.upper()]
        except KeyError:
            return await ctx.send("Invalid game. Please try again.", ephemeral=True)

        self.bot.dispatch('game_channel_update', GameChannelUpdateEvent(game, Update.REMOVE, ctx, channel.id))

    @_manage_channels_group.command(name="list")
    @discord.app_commands.choices(game=CHANNEL_TYPES_CHOICE)
    async def _list_channel(self, ctx: commands.Context['Botty'], game: str):
        """Lists channels in use for a game
        """
        try:
            game: Game = Game[game.upper()]
        except KeyError:
            return await ctx.send("Invalid game. Please try again.", ephemeral=True)

        #TODO implement !!! See ConfigHandler for paginator !!!


    def config_value_transformer(setting: GameSetting, value: int) -> int:
        if setting == GameSetting.HL_MAX_NUMBER:
            return abs(value)
        if setting == GameSetting.HL_MAX_REPLY:
            return abs(value)
        if setting == GameSetting.MAX_LB_SIZE:
            return max(min(abs(value), 20), 5)
        if setting == GameSetting.WS_WRONG_GUESSES:
            return min(abs(value), 5)

    @_config_group.command(name="set")
    @discord.app_commands.choices(setting=GAME_SETTINGS_CHOICE)
    @discord.app_commands.describe(channel="Overwrites the guild setting in this specific channel")
    async def _manage_settings(self, ctx: commands.Context['Botty'], setting: str, value: int, channel: Optional[discord.TextChannel]):
        """Change game settings
        """
        try:
            setting: GameSetting = GameSetting[setting.upper()]
        except KeyError:
            return await ctx.send("Invalid setting. Please try again.", ephemeral=True)

        value = self.config_value_transformer(value)

        if channel:
            e = GameConfigUpdateEvent(setting, ctx, value, channel.id)
        else:
            e = GameConfigUpdateEvent(setting, ctx, value)
        self.bot.dispatch('config_update', e)





async def setup(bot: 'Botty'):
    await bot.add_cog(ConfigCog(bot))