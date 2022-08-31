import discord

from discord.ext import menus  # type: ignore


class MyMenuPages(discord.ui.View, menus.MenuPages):
    def __init__(self, source, ctx=None, *, delete_message_after=False):
        super().__init__(timeout=60)
        self._source = source
        self.current_page = 0
        self.ctx = ctx
        self.message = None
        self.delete_message_after = delete_message_after

    async def start(self, ctx, *, channel=None, wait=False):
        # We wont be using wait/channel, you can implement them yourself. This is to match the MenuPages signature.
        await self._source._prepare_once()
        self.ctx = ctx
        self.message = await self.send_initial_message(ctx, ctx.channel)

    async def _get_kwargs_from_page(self, page):
        """This method calls ListPageSource.format_page class"""
        value = await super()._get_kwargs_from_page(page)
        if "view" not in value:
            value.update({"view": self})
        return value

    async def interaction_check(self, interaction):
        return interaction.user == self.ctx.author

    @discord.ui.button(
        emoji="\U000023ea",
        style=discord.ButtonStyle.blurple,
    )
    async def first_page(self, interaction, button):
        await self.show_page(0)
        await interaction.response.defer()

    @discord.ui.button(emoji="\U00002b05\U0000fe0f", style=discord.ButtonStyle.blurple)
    async def before_page(self, interaction, button):
        await self.show_checked_page(self.current_page - 1)
        await interaction.response.defer()

    @discord.ui.button(emoji="\U0001f4a5", style=discord.ButtonStyle.blurple)
    async def stop_page(self, interaction, button):
        await interaction.response.defer()
        self.stop()
        if self.delete_message_after:
            await self.message.delete(delay=0)

    @discord.ui.button(emoji="\U000027a1\U0000fe0f", style=discord.ButtonStyle.blurple)
    async def next_page(self, interaction, button):
        await self.show_checked_page(self.current_page + 1)
        await interaction.response.defer()

    @discord.ui.button(emoji="\U000023e9", style=discord.ButtonStyle.blurple)
    async def last_page(self, interaction, button):
        await self.show_page(self._source.get_max_pages() - 1)
        await interaction.response.defer()
