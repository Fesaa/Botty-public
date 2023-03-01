import discord

from discord.ext import menus, commands  # type: ignore
from typing import (
    Dict,
    Any
)


class MyMenuPages(discord.ui.View, menus.MenuPages):
    def __init__(self, source:  menus.PageSource, ctx: commands.Context, *, delete_message_after=False):
        super().__init__(timeout=180)
        self._source = source
        self.current_page = 0
        self.ctx = ctx
        self.message: discord.Message | None = None
        self.delete_message_after = delete_message_after

    async def on_timeout(self) -> None:
        if self.message:
            await self.message.edit(view=discord.ui.View())
        return await super().on_timeout()

    def fill_items(self) -> None:

        if self.source.is_paginating():
            max_pages = self.source.get_max_pages()
            use_last_and_first = max_pages is not None and max_pages >= 2
            if use_last_and_first:
                self.add_item(self.first_page)
            self.add_item(self.before_page)
            self.add_item(self.next_page)
            if use_last_and_first:
                self.add_item(self.last_page)
            self.add_item(self.stop_page)

    def _update_labels(self, page_number: int) -> None:

        self.first_page.disabled = False
        self.before_page.disabled = False
        self.next_page.disabled = False
        self.last_page.disabled = False

        max_pages = self.source.get_max_pages()
        if max_pages is not None:
            if (page_number + 1) >= max_pages:
                self.next_page.disabled = True
                self.last_page.disabled = True
            if page_number == 0:
                self.before_page.disabled = True
                self.first_page.disabled = True

    async def start(self, ctx: commands.Context, *, channel=None, wait=False):
        # We wont be using wait/channel, you can implement them yourself. This is to match the MenuPages signature.
        await self._source._prepare_once()
        self.ctx = ctx
        self.message = await self.send_initial_message(ctx, ctx.channel)

    async def _get_kwargs_from_page(self, page: int) -> Dict[str, Any]:
        value = await discord.utils.maybe_coroutine(self.source.format_page, self, page)  # type: ignore
        if isinstance(value, dict):
            return value
        elif isinstance(value, str):
            return {'content': value, 'embed': None, "view": self}
        elif isinstance(value, discord.Embed):
            return {'embed': value, 'content': None, "view": self}
        else:
            return {}

    async def interaction_check(self, interaction: discord.Interaction):
        return interaction.user == self.ctx.author

    @discord.ui.button(label="First",style=discord.ButtonStyle.gray)
    async def first_page(self, interaction: discord.Interaction, button):
        self.current_page = 0
        self._update_labels(self.current_page)
        page = await self.source.get_page(self.current_page)
        kwargs = await self._get_kwargs_from_page(page)
        kwargs.pop("view")
        await interaction.response.edit_message(**kwargs, view=self)

    @discord.ui.button(label="Back", style=discord.ButtonStyle.blurple)
    async def before_page(self, interaction: discord.Interaction, button):
        self.current_page -= 1
        self._update_labels(self.current_page)
        page = await self.source.get_page(self.current_page)
        kwargs = await self._get_kwargs_from_page(page)
        kwargs.pop("view")
        await interaction.response.edit_message(**kwargs, view=self)

    @discord.ui.button(label="Quit", style=discord.ButtonStyle.red)
    async def stop_page(self, interaction: discord.Interaction, button):
        await interaction.response.defer()
        self.stop()
        if self.delete_message_after and self.message:
            await self.message.delete(delay=0)

    @discord.ui.button(label="Next", style=discord.ButtonStyle.blurple)
    async def next_page(self, interaction: discord.Interaction, button):
        self.current_page += 1
        self._update_labels(self.current_page)
        page = await self.source.get_page(self.current_page)
        kwargs = await self._get_kwargs_from_page(page)
        kwargs.pop("view")
        await interaction.response.edit_message(**kwargs, view=self)

    @discord.ui.button(label="Last", style=discord.ButtonStyle.gray)
    async def last_page(self, interaction: discord.Interaction, button):
        self.current_page = self._source.get_max_pages() - 1
        self._update_labels(self.current_page)
        page = await self.source.get_page(self.current_page)
        kwargs = await self._get_kwargs_from_page(page)
        kwargs.pop("view")
        await interaction.response.edit_message(**kwargs, view=self)
