from __future__ import annotations

import discord
import itertools

from discord.ext import menus, commands  # type: ignore
from typing import (
    Union,
    Any,
    Optional
)

from Botty import Botty
import utils.time as time
from utils.MyMenuPages import MyMenuPages


class GroupHelpPageSource(menus.ListPageSource):
    def __init__(self, group: Union[commands.Group, commands.Cog], entries: list[commands.Command], *, prefix: str):
        super().__init__(entries=entries, per_page=6)
        self.group: Union[commands.Group, commands.Cog] = group
        self.prefix: str = prefix
        self.title: str = f'{self.group.qualified_name} Commands'
        self.description: str = self.group.description

    async def format_page(self, menu: MyMenuPages, commands: list[commands.Command]):
        embed = discord.Embed(title=self.title, description=self.description, colour=discord.Colour.dark_teal())

        for command in commands:
            signature = f'{command.qualified_name} {command.signature}'
            embed.add_field(name=signature, value=command.short_doc or 'No help given...', inline=False)

        maximum = self.get_max_pages()
        if maximum > 1:
            embed.set_author(name=f'Page {menu.current_page + 1}/{maximum} ({len(self.entries)} commands)')

        embed.set_footer(text=f'Use "{self.prefix}help command" for more info on a command.')
        return embed


class HelpSelectMenu(discord.ui.Select['HelpMenu']):
    def __init__(self, entries: dict[commands.Cog, list[commands.Command]], bot: Botty):
        super().__init__(
            placeholder='Select a category...',
            min_values=1,
            max_values=1,
            row=0,
        )
        self.commands: dict[commands.Cog, list[commands.Command]] = entries
        self.bot: Botty = bot
        self.__fill_options()

    def __fill_options(self) -> None:
        self.add_option(
            label='Index',
            emoji='\U0001f3e0',
            value='__index',
            description='General bot usage',
        )
        for cog, commands in self.commands.items():
            if not commands:
                continue
            description = cog.description.split('\n', 1)[0] or None
            emoji = getattr(cog, 'display_emoji', None)
            self.add_option(label=cog.qualified_name, value=cog.qualified_name, description=description, emoji=emoji)

    async def callback(self, interaction: discord.Interaction):
        assert self.view is not None
        value = self.values[0]
        if value == '__index':
            await self.view.rebind(HomePageSource(), interaction)
        else:
            cog = self.bot.get_cog(value)
            if cog is None:
                await interaction.response.send_message('Somehow this category does not exist?', ephemeral=True)
                return

            commands = self.commands[cog]
            if not commands:
                await interaction.response.send_message('This category has no commands for you', ephemeral=True)
                return

            source = GroupHelpPageSource(cog, commands, prefix=self.view.ctx.clean_prefix)
            await self.view.rebind(source, interaction)


class HomePageSource(menus.PageSource):
    def is_paginating(self) -> bool:
        return True

    def get_max_pages(self) -> Optional[int]:
        return 2

    async def get_page(self, page_number: int) -> Any:
        self.index = page_number
        return self

    def format_page(self, menu: HelpMenu, page: Any):
        embed = discord.Embed(title='Botty Help', colour=discord.Colour.dark_teal())
        embed.description = f"""
        Welcome to Botty help!

        Use "{menu.ctx.clean_prefix}help command" for more info on a command.
        Use "{menu.ctx.clean_prefix}help category" for more info on a category.
        Use the dropdown menu below to select a category.
        """
        
        created_at = time.format_dt(menu.ctx.bot.user.created_at, 'F')
        if self.index == 0:
            embed.add_field(
                name='Who am I?',
                value=(
                    "I'm Fesa's personal bot! Born because of the CubeCraft levelling system. With being born at "
                    f'{created_at} I am still quite young \U0001f642. I can mostly be used for minigames, but also offer tags and maybe more soon!.'
                    'You can get more information on my commands by using the dropdown below.\n\n'
                    "I'm also open source. You can see my sometimes up to date code on [GitHub](https://github.com/Fesaa/Botty-public)!"
                ),
                inline=False,
            )
        elif self.index == 1:
            entries = (
                ('<argument>', 'This means the argument is __**required**__.'),
                ('[argument]', 'This means the argument is __**optional**__.'),
                ('[A|B]', 'This means that it can be __**either A or B**__.'),
                (
                    '[argument...]',
                    'This means you can have multiple arguments.\n'
                    'Now that you know the basics, it should be noted that...\n'
                    '__**You do not type in the brackets!**__',
                ),
            )

            for name, value in entries:
                embed.add_field(name=name, value=value, inline=False)

        return embed


class HelpMenu(MyMenuPages):
    def __init__(self, source: menus.PageSource, ctx: commands.Context):
        super().__init__(source, ctx=ctx, delete_message_after=True)
        self._update_labels(0)

    def add_categories(self, commands: dict[commands.Cog, list[commands.Command]]) -> None:
        self.clear_items()
        self.add_item(HelpSelectMenu(commands, self.ctx.bot))
        self.fill_items()

    async def rebind(self, source: menus.PageSource, interaction: discord.Interaction) -> None:
        self._source = source
        self.current_page = 0

        await self.source._prepare_once()
        page = await self.source.get_page(0)
        self._update_labels(0)
        kwargs = await self._get_kwargs_from_page(page)
        kwargs.pop("view")
        await interaction.response.edit_message(**kwargs, view=self)


class MyHelp(commands.HelpCommand):
    context: commands.Context

    def get_command_signature(self, command: commands.Command) -> str:
        parent = command.full_parent_name
        if len(command.aliases) > 0:
            aliases = '|'.join(command.aliases)
            fmt = f'[{command.name}|{aliases}]'
            if parent:
                fmt = f'{parent} {fmt}'
            alias = fmt
        else:
            alias = command.name if not parent else f'{parent} {command.name}'
        return f'{alias} {command.signature}'
    
    async def send_bot_help(self, mapping):
        bot: Botty = self.context.bot

        def key(command: commands.Command) -> str:
            cog: commands.Cog = command.cog
            return cog.qualified_name if cog else '\U0010ffff'

        async def predicate(cmd: commands.Command) -> bool:
            predicates = cmd.checks
            if not predicates:
                return True
            return await discord.utils.async_all(predicate(self.context) for predicate in predicates)
            
        entries = sorted([i for i in bot.commands if not i.hidden], key=key)
        all_commands: dict[commands.Cog, list[commands.Command]] = {}
        for name, children in itertools.groupby(entries, key=key):
            if name == '\U0010ffff' or name == "HelpCog":
                continue

            cog = bot.get_cog(name)
            assert cog is not None
            all_commands[cog] = sorted(children, key=lambda c: c.qualified_name)

        menu = HelpMenu(HomePageSource(), ctx=self.context)
        menu.add_categories(all_commands)
        await menu.start(self.context)
    
    async def send_cog_help(self, cog: commands.Cog):
        entries = [i for i in cog.get_commands() + cog.get_app_commands() if not i.hidden]
        menu = HelpMenu(GroupHelpPageSource(cog, entries, prefix=self.context.clean_prefix), ctx=self.context)
        await menu.start(self.context)

    def common_command_formatting(self, embed_like, command: commands.Command):
        embed_like.title = self.get_command_signature(command)
        if command.description:
            embed_like.description = f'{command.description}\n\n{command.help}'
        else:
            embed_like.description = command.help or 'No help found...'

    async def send_command_help(self, command):
        embed = discord.Embed(colour=discord.Colour.dark_teal())
        self.common_command_formatting(embed, command)
        await self.context.send(embed=embed)

    async def send_group_help(self, group):
        subcommands = group.commands
        if len(subcommands) == 0:
            return await self.send_command_help(group)

        entries = await self.filter_commands(subcommands, sort=True)
        if len(entries) == 0:
            return await self.send_command_help(group)

        source = GroupHelpPageSource(group, entries, prefix=self.context.clean_prefix)
        self.common_command_formatting(source, group)
        menu = HelpMenu(source, ctx=self.context)
        await menu.start(self.context)

class Help(commands.Cog):
    def __init__(self, bot: Botty):
        self.bot = bot

        help_command = MyHelp()
        help_command.cog = self
        bot.help_command = help_command


async def setup(bot):
    await bot.add_cog(Help(bot))
