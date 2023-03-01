import os
import typing
import asyncio
import discord

from discord import Embed
from discord.ext import commands, menus  # type: ignore

from Botty import Botty
from utils.functions import similar
from utils.MyMenuPages import MyMenuPages
from utils.config_functions import (
    update_prefix,
    remove_channels,
    add_channels,
    update_game_setting
)

# Default values
CHANNEL_TYPES_OPTIONS = [
        discord.SelectOption(label="WordSnake", value="wordsnake", emoji="🐍"),
        discord.SelectOption(label="NTBPL", value="ntbpl", emoji="❓"),
        discord.SelectOption(label="HigherLower", value="higherlower", emoji="↕️"),
        discord.SelectOption(label="ConnectFour", value="connectfour", emoji="🟡"),
        discord.SelectOption(label="HangMan", value="hangman", emoji="🪢"),
        discord.SelectOption(label="CubeLvl", value="cubelvl", emoji="🟦"),
        discord.SelectOption(label="Logging", value="log", emoji="\U0001f4d6"),
    ]

CHANNEL_TYPES_CHOICE = [
        discord.app_commands.Choice(name="WordSnake", value="wordsnake"),
        discord.app_commands.Choice(name="NTBPL", value="ntbpl"),
        discord.app_commands.Choice(name="HigherLower", value="higherlower"),
        discord.app_commands.Choice(name="ConnectFour", value="connectfour"),
        discord.app_commands.Choice(name="HangMan", value="hangman"),
        discord.app_commands.Choice(name="CubeLvl", value="cubelvl"),
        discord.app_commands.Choice(name="Logging", value="log"),
    ]

GAME_SETTINGS_OPTIONS = [
        discord.SelectOption(
            label="Maximum amount of users displayed on a leaderboard",
            value="max_lb_size",
            description="Maximum 20 users on one page.",
        ),
        discord.SelectOption(
            label="Maximum consecutive replies by the same user in HigherLower",
            value="hl_max_reply",
        ),
        discord.SelectOption(
            label="Maximum amount of tolerated wrong guesses in WordSnake",
            value="ws_wrong_guesses",
            description="Maximum 5 wrong guesses.",
        ),
        discord.SelectOption(
            label="Maximum value of the number in HigherLower",
            value="hl_max_number",
        ),
    ]

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



class ChannelSelect(discord.ui.Select):
    def __init__(
        self,
        *,
        placeholder: typing.Optional[str] = None,
        channel_list: typing.List[discord.TextChannel] = [],
    ) -> None:

        options = [discord.SelectOption(label=channel.name, value=str(channel.id), emoji="\U0001f310") for channel in channel_list]

        super().__init__(
            placeholder=placeholder,
            min_values=1,
            max_values=len(options),
            options=options,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        return await interaction.response.defer()


class ChannelSelectView(discord.ui.View):
    def __init__(
        self,
        bot: Botty,
        action: bool,
        channel_type: str,
        guild: discord.Guild,
        *,
        timeout: typing.Optional[float] = 180
        ):

        self.bot = bot
        self.action = action
        self.channel_type = channel_type
        super().__init__(timeout=timeout)

        used_channels = self.bot.cache.get_channel_id(guild.id, channel_type)
        if self.action:
            available_channels = [channel for channel in guild.channels
                if channel.id not in used_channels and isinstance(channel, discord.TextChannel)]
        else:
            available_channels = [channel for channel in guild.channels
                if channel.id in used_channels and isinstance(channel, discord.TextChannel)]

        partial_channel_list = []
        for index, channel in enumerate(available_channels):
            partial_channel_list.append(channel)

            if (index % 25 == 0 or index == len(available_channels) - 1) and (index > 0 or len(available_channels) == 1):
                self.add_item(ChannelSelect(placeholder="Pick your channels", channel_list=partial_channel_list))
                partial_channel_list = []


    @discord.ui.button(label="Submit", style=discord.ButtonStyle.primary, emoji="\U00002714")
    async def _submit(self, interaction: discord.Interaction, button):
        selected_ids = []
        for values in [child.values for child in self.children if isinstance(child, discord.ui.Select)]:
            for channel_id in values:
                selected_ids.append(int(channel_id))

        if self.action:
            return await add_channels(interaction, guild_id=interaction.guild_id, channel_type=self.channel_type, to_add=selected_ids, bot=interaction.client)
        await remove_channels(interaction, to_remove=selected_ids, guild_id=interaction.guild_id, channel_type=self.channel_type, bot=interaction.client)


class ChooseChannelTypeView(discord.ui.View):

    def __init__(
        self, bot: Botty, action: bool, *, timeout: typing.Optional[float] = 180
    ):
        self.bot = bot
        self.action = action
        super().__init__(timeout=timeout)

    @discord.ui.select(
        placeholder="Choose the module to modify used channels for",
        options=CHANNEL_TYPES_OPTIONS,
    )
    async def _selected_channel(self, interaction: discord.Interaction, select):
        await interaction.response.send_message(
            f'Select all the channels to {"add" if self.action else "remove"}, use the submit button to finalize your selection.',
            view=ChannelSelectView(self.bot, self.action, self.children[0].values[0], interaction.guild), ephemeral=True) # type: ignore


class ChannelOptionView(discord.ui.View):
    def __init__(self, bot: Botty, *, timeout: typing.Optional[float] = 180):
        self.bot = bot
        super().__init__(timeout=timeout)

    @discord.ui.button(label="Add", style=discord.ButtonStyle.green, emoji="\U00002795", row=0)
    async def _add_channel(self, interaction: discord.Interaction, button):
        await interaction.response.send_message("Select the module you would like to add channels to",
            view=ChooseChannelTypeView(self.bot, True), ephemeral=True)

    @discord.ui.button(label="Remove", style=discord.ButtonStyle.red, emoji="\U00002796", row=0)
    async def _remove_channel(self, interaction: discord.Interaction, button):
        await interaction.response.send_message("Select the module you would like to remove channels from",
            view=ChooseChannelTypeView(self.bot, False), ephemeral=True)


class GameSettingsModal(discord.ui.Modal):
    def __init__(
        self,
        bot: Botty,
        *,
        placeholders: typing.Tuple[str, ...],
        timeout: typing.Optional[float] = None,
    ) -> None:

        self.bot = bot
        super().__init__(title="Change your game settings", timeout=timeout)

        labels = {
            "max_lb_size": "Maximum leaderboard size",
            "hl_max_reply": "Maximum HigherLower replies",
            "ws_wrong_guesses": "Maximum WordSnake mistakes",
            "hl_max_number": "Maximum HigherLower number",
        }

        for setting_type, label, placeholder in zip(labels.keys(), labels.values(), placeholders):
            self.add_item(discord.ui.TextInput(label=label, style=discord.TextStyle.short, placeholder=placeholder, required=False, custom_id=setting_type))


    async def on_submit(self, interaction: discord.Interaction) -> None:
        values = {
                child.custom_id: int(child.value) if child.value.isdigit() else None  # type: ignore
                for child in self.children 
                if isinstance(child, discord.ui.TextInput)
                }

        for setting, value in values.items():
            print(setting, value)
            if value:
                await update_game_setting(interaction, guild_id=interaction.guild_id, game_setting=setting, value=value, bot=interaction.client)

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:  # type: ignore
        return await interaction.response.send_message(f"An error occurred, please try again. If the issue isn't resolving, please contact {self.bot.owner}",ephemeral=True)


class PrefixConfigView(discord.ui.Modal):
    def __init__(
        self, bot: Botty, current_prefix: str, *, timeout: typing.Optional[float] = None
    ) -> None:
        self.bot = bot
        super().__init__(title=f"Choose your new prefix", timeout=timeout)
        self.add_item(discord.ui.TextInput(label="New Prefix", style=discord.TextStyle.short, required=True, placeholder=current_prefix, custom_id="new_prefix"))

    async def on_submit(self, interaction: discord.Interaction) -> None:
        new_prefix = self.children[0].value or DEFAULT_PREFIX  # type: ignore
        await update_prefix(interaction, guild_id=interaction.guild_id, new_prefix=new_prefix, bot=interaction.client)

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:  # type: ignore
        await interaction.response.send_message(
            f"An error occurred, please try again. If the issue isn't resolving, please contact {self.bot.owner}",
            ephemeral=True,
        )


class ConfigView(discord.ui.View):
    def __init__(self, bot: Botty, *, timeout: typing.Optional[float] = 180):
        self.bot = bot
        super().__init__(timeout=timeout)

    @discord.ui.button(
        label="Prefix", style=discord.ButtonStyle.green, emoji="\U00002049", row=0
    )
    async def _prefix_button(self, interaction: discord.Interaction, button):
        if not interaction.guild_id:
            return
        await interaction.response.send_modal(
            PrefixConfigView(self.bot, self.bot.cache.get_command_prefix(interaction.guild_id))
        )

    @discord.ui.button(
        label="Game Settings",
        style=discord.ButtonStyle.blurple,
        emoji="\U00002699",
        row=0,
    )
    async def _game_setting_button(self, interaction: discord.Interaction, button):
        placeholders = tuple(str(v) for v in self.bot.cache.get_all_games_settings(interaction.guild.id).values())  # type: ignore
        return await interaction.response.send_modal(GameSettingsModal(bot=self.bot, placeholders=placeholders))

    @discord.ui.button(
        label="Channels", style=discord.ButtonStyle.secondary, emoji="\U0001f310", row=0
    )
    async def _channels_button(self, interaction: discord.Interaction, button):
        if len(interaction.guild.channels) > 100:  # type: ignore
            return await interaction.response.send_message(
                "This guild has too many channel to display with Selects, please use the slash commands to add or remove channels to a module.",
                ephemeral=True,
            )
        await interaction.response.send_message(
            "Select one of the action to proceed.",
            view=ChannelOptionView(self.bot),
            ephemeral=True,
        )


class ChannelPageSource(menus.ListPageSource):
    def __init__(self, data, options: str):
        self.option = options
        super().__init__(data, per_page=6)

    async def format_page(self, menu, entries):
        page = menu.current_page
        max_page = self.get_max_pages()
        starting_number = page * self.per_page + 1
        page_content = "\n\n".join(entries)
        embed = Embed(
            title=f"Channels in use for {self.option}",
            description=page_content,
            color=0xAD3998,
            timestamp=discord.utils.utcnow(),
        )
        author = menu.ctx.author
        embed.set_footer(text=f"Requested by {author}", icon_url=author.avatar.url)
        return embed


class ConfigHandler(commands.Cog):
    """
    Configure all modular parts of Botty!
    Slash command permissions have to be set in the integration tab of your server.
    """

    def __init__(self, bot: Botty) -> None:
        self.bot = bot
        super().__init__()

    @property
    def display_emoji(self) -> discord.PartialEmoji:
        return discord.PartialEmoji(name='\U00002699')

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        defaults = self.bot.default_values
        await self.bot.PostgreSQL.init_guild(
            guild.id,
            self.bot.config["DISCORD"]["DEFAULT_PREFIX"],
            defaults.default_lb_size,
            defaults.default_max_reply,
            defaults.default_ws_guesses,
            defaults.default_hl_max_number,
        )

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild):
        await self.bot.PostgreSQL.remove_guild(guild.id)

    @commands.command(hidden=True)
    @commands.is_owner()
    async def close(self, ctx: commands.Context):
        await asyncio.wait_for(self.bot.pool.close(), 60)
        await self.bot.close()

    @commands.command(hidden=True)
    @commands.is_owner()
    async def sync(
        self,
        ctx: commands.Context,
        guilds: commands.Greedy[discord.Object],
        spec: typing.Optional[typing.Literal["~"]] = None,
    ) -> None:
        """
        Command for syncing app_commands, can only be used by my owners.
        """
        if not guilds:
            if spec == "~":
                synced = await self.bot.tree.sync(guild=ctx.guild)
            elif spec == "*":
                self.bot.tree.copy_global_to(guild=ctx.guild)
                synced = await self.bot.tree.sync(guild=ctx.guild)
            elif spec == "^":
                self.bot.tree.clear_commands(guild=ctx.guild)
                await self.bot.tree.sync(guild=ctx.guild)
                synced = []
            else:
                synced = await self.bot.tree.sync()

            await ctx.send(
                f"Synced {len(synced)} commands {'globally' if spec is None else 'to the current guild.'}"
            )
            return

        ret = 0
        for guild in guilds:
            try:
                await self.bot.tree.sync(guild=guild)
            except discord.HTTPException:
                pass
            else:
                ret += 1

        await ctx.send(f"Synced the tree to {ret}/{len(guilds)}.")

    @commands.command(name="reload",hidden=True)
    @commands.is_owner()
    async def _reload(self, ctx: commands.Context, *names: str):
        """
        Command for reloading Cogs, can only be used by my owners.
        """
        files = ([f"cogs.{name}" for name in names] or [ f"cogs.{name[:-3]}"for name in os.listdir("./cogs") if name.endswith(".py") and name != "ConfigHandler.py"])
        successful_reloads = []
        failed_reloads = []

        e = Embed(title="Cog reloads", colour=0xAD3998, timestamp=discord.utils.utcnow())

        stray_cogs = []
        similar_cogs = []

        for file in files:
            if file[5:] not in self.bot.cogs:
                suggestions = [cog for cog in self.bot.cogs if similar(file.lower(), cog.lower()) > 0.5]
                if suggestions:
                    similar_cogs.append((file, suggestions))
                else:
                    stray_cogs.append(file)

            try:
                await self.bot.reload_extension(file)
                successful_reloads.append(file)
            except (
                commands.errors.ExtensionNotLoaded,
                commands.errors.ExtensionNotFound,
            ):
                failed_reloads.append(file)

        if similar_cogs:
            field_value = ""

            for index, missing_cog in enumerate(similar_cogs):
                field_value += f'·{missing_cog[0][5:]} -> {", ".join(missing_cog[1])}\n'

                if len(field_value) > 1000 or index + 1 == len(similar_cogs):
                    e.add_field(name="The following cogs could not be found, did you mistype?", value=field_value, inline=False,)

        if stray_cogs:
            field_value = ""

            for index, missing_cog in enumerate(stray_cogs):  # type: ignore
                field_value += f"{missing_cog[5:]}\n"

                if len(field_value) > 1000 or index + 1 == len(stray_cogs):
                    e.add_field(name="The following cogs could not be found, no suggestions found", value=field_value, inline=False)

        succ_value = "\u200b"
        failed_value = "\u200b"

        for index, file in enumerate(successful_reloads):
            succ_value += f"{file}\n"

            if len(succ_value) > 1000 or index == len(successful_reloads) - 1:
                e.add_field(name="Successful!", value=succ_value, inline=False)
                succ_value = "\u200b"

        for index, file in enumerate(failed_reloads):
            failed_value += f"{file}\n"

            if len(failed_value) > 1000 or index == len(failed_reloads) - 1:
                e.add_field(name="Failed!", value=failed_value, inline=False)
                failed_value = "\u200b"

        if failed_reloads:
            await ctx.send(embed=e)
        else:
            await ctx.send("\N{OK HAND SIGN}")

    @commands.command(hidden=True)
    @commands.is_owner()
    async def load(self, ctx: commands.Context, *, module: str):
        """Loads a module."""
        try:
            await self.bot.load_extension(module)
        except commands.ExtensionError as e:
            await ctx.send(f"{e.__class__.__name__}: {e}")
        else:
            await ctx.send("\N{OK HAND SIGN}")

    @commands.command(hidden=True)
    @commands.is_owner()
    async def unload(self, ctx: commands.Context, *, module: str):
        """Unloads a module."""
        try:
            await self.bot.unload_extension(module)
        except commands.ExtensionError as e:
            await ctx.send(f"{e.__class__.__name__}: {e}")
        else:
            await ctx.send("\N{OK HAND SIGN}")

    @commands.command(hidden=True)
    @commands.is_owner()
    async def list_cogs(self, ctx: commands.Context):
        """Lists all cogs."""
        await ctx.send(", ".join(self.bot.cogs))

    @commands.hybrid_group(name="config", description="Config commands.")
    @discord.app_commands.default_permissions(administrator=True)
    @discord.app_commands.guild_only()
    @commands.has_guild_permissions(administrator=True)
    async def _config(self, ctx: commands.Context):
        """
        Configure various attributes, for more info use !help config.
        In order to use any of these commands you'll need administrative privileges in the server.
        This requirement can be changed for the Slash Command variants by other admins.
        Recommended to use Slash Commands, these have better auto complete options
        """
        ...

    @_config.command(name="prefix", description="Change my prefix")
    async def _prefix(self, ctx: commands.Context, new_prefix: str = None):
        """
        Change or display the default prefix. Tagging me always works.
        """

        if not new_prefix:
            return await ctx.reply(f"My current prefix is {self.bot.cache.get_command_prefix(ctx.guild.id)}")

        new_prefix = new_prefix or self.bot.config["DISCORD"]["DEFAULT_PREFIX"]
        await update_prefix(ctx, guild_id=ctx.guild.id, new_prefix=new_prefix, bot=self.bot)
    
    @commands.command(name="prefix")
    async def prefix(self, ctx: commands.Context):
        return await ctx.reply(f"My current prefix is {self.bot.cache.get_command_prefix(ctx.guild.id)}")


    @_config.group( name="channels", description="Update and view used channels per type")
    @discord.app_commands.default_permissions(administrator=True)
    @discord.app_commands.guild_only()
    @commands.has_guild_permissions(administrator=True)
    async def _channels(self, ctx: commands.Context):
        """
        Remove, Add or List all channels where one of my features works.
        There is no information loss when removing a channel for a game!
        """
        ...

    async def snowflake_autocomplete(
        self, interaction: discord.Interaction, current: str
    ) -> typing.List[discord.app_commands.Choice[str]]:
        if interaction.namespace.channel_type != "":
            channels = await self.bot.PostgreSQL.get_channel(
                interaction.guild_id, interaction.namespace.channel_type
            )
            choices = [self.bot.get_channel(i) for i in channels]
        else:
            choices = [channel for channel in interaction.guild.channels]  # type: ignore

        choices = [channel for channel in choices if current in channel.name]

        return [
            discord.app_commands.Choice(name=channel.name, value=str(channel.id))
            for channel in choices
        ][:25]

    @_channels.command(name="remove", description="Remove a channel of use")
    @discord.app_commands.autocomplete(snowflake=snowflake_autocomplete)
    @discord.app_commands.choices(channel_type=CHANNEL_TYPES_CHOICE)
    @commands.has_guild_permissions(administrator=True)
    async def _remove(self, ctx: commands.Context, channel_type: str, snowflake: str):
        """
        Remove a channel for use.
        While using slash commands, only used channels appear.
        """
        if channel_type not in (i.value for i in CHANNEL_TYPES_CHOICE):
            return await ctx.send("You've selected an invalid channel type, please try again.")

        if not snowflake.isdigit():
            channel_list = [[i for i in ctx.guild.channels if i.name == snowflake][0].id]
        else:
            channel_list = [int(snowflake)]
        
        await remove_channels(ctx, to_remove=channel_list, guild_id=ctx.guild.id, channel_type=channel_type, bot=self.bot)
            
        

    @_channels.command(name="add", description="Add a channel for use")
    @discord.app_commands.choices(channel_type=CHANNEL_TYPES_CHOICE)
    @commands.has_guild_permissions(administrator=True)
    async def _add(self, ctx: commands.Context, channel_type: str, snowflake: discord.TextChannel):
        """
        Add a channel for use.
        You are able to have two games in the same channel, this is not recommended!
        """
        if channel_type not in (i.value for i in CHANNEL_TYPES_CHOICE):
            return await ctx.send("You've selected an invalid channel type, please try again.")
        await add_channels(int_ctx=ctx, guild_id=ctx.guild.id, channel_type=channel_type, to_add=[snowflake.id], bot=self.bot)

    @_channels.command( name="list", description="Receive a list with all channels in use")
    @discord.app_commands.choices(channel_type=CHANNEL_TYPES_CHOICE)
    @commands.has_guild_permissions(administrator=True)
    async def _list(self, ctx: commands.Context, channel_type: str):
        """
        List channels. If more than 10 in use, only 10 will be displayed.
        """
        channel_list: list = self.bot.cache.get_channel_id(ctx.guild.id, channel_type)
        channel_list = [f"<#{i}>" for i in channel_list]

        if not channel_list:
            await ctx.send(f"No active channels for {channel_type}.")
            return

        msg = await ctx.send("List on her way!", ephemeral=True)
        formatter = ChannelPageSource(channel_list, channel_type)
        menu = MyMenuPages(formatter, delete_message_after=True)
        await menu.start(ctx)
        try:
            await msg.delete()
        except discord.errors.NotFound:
            pass

    @_config.command(name="game_settings", description="Change the settings of games")
    @discord.app_commands.choices(game_setting=GAME_SETTINGS_CHOICE)
    @commands.has_guild_permissions(administrator=True)
    async def _game_settings(self, ctx: commands.Context, game_setting: str, value: int):
        """
        Change game settings. These will be used in all active channels.
        """

        if game_setting not in ("max_lb_size", "hl_max_reply", "ws_wrong_guesses", "hl_max_number"):
            return await ctx.send("This is not a valid setting. Feel free to use the help command if needed!", ephemeral=True,)

        value = abs(value)
        await update_game_setting(ctx, guild_id=ctx.guild.id, game_setting=game_setting, value=value, bot=self.bot)

    @_config.command(name="interactive", description="Interactive menu to change config options")
    @commands.has_guild_permissions(administrator=True)
    async def _interactive(self, ctx: commands.Context):
        """
        Interactive menu to change config options. Makes use of Modals, Buttons and SelectMenus. As alternative to the slash commands.
        Recommended to use the slash command, this way no messages visible to anyone will be send.
        """
        await ctx.send(
            "Use the buttons to change any of my settings. You might be required to use slash commands, depending on the size of your guild.",
            view=ConfigView(self.bot),
            ephemeral=True,
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(ConfigHandler(bot))
