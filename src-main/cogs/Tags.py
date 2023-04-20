import asyncio
import typing

import asyncpg
import discord
from discord.ext import commands

from Botty import Botty


class TagName(commands.clean_content):
    def __init__(self, *, lower: bool = False):
        self.lower: bool = lower
        super().__init__()

    async def convert(self, ctx: commands.Context, argument: str) -> str:
        converted = await super().convert(ctx, argument)
        lower = converted.lower().strip()

        if not lower:
            raise commands.BadArgument('Missing tag name.')

        if len(lower) > 100:
            raise commands.BadArgument('Tag name is a maximum of 100 characters.')

        first_word, _, _ = lower.partition(' ')

        # get tag command.
        root: commands.GroupMixin = ctx.bot.get_command('tag')  # type: ignore
        if first_word in root.all_commands:
            raise commands.BadArgument('This tag name starts with a reserved word.')

        return converted if not self.lower else lower


class Tags(commands.Cog):
    """
    A tag system; add, edit and delete tags to your liking!
    No need to remember common phrases!
    """
    def __init__(self, bot: Botty) -> None:
        self.bot = bot
        super().__init__()

        self._tags_being_made: typing.Dict[int, typing.List[str]] = {}

    @property
    def display_emoji(self) -> discord.PartialEmoji:
        return discord.PartialEmoji(name='\U0001f250')

    def tag_is_being_made(self, guild_id: int, name: str) -> bool:
        if tags := self._tags_being_made.get(guild_id, None):
            return name in tags
        return False
    
    def add_tag(self, guild_id: int, name: str) -> None:
        if self._tags_being_made.get(guild_id, None):
            self._tags_being_made[guild_id].append(name)
        self._tags_being_made[guild_id] = [name]
    
    def remove_tag(self, guild_id: int, name: str) -> None:
        if tags := self._tags_being_made.get(guild_id, None):
            if name in tags:
                tags.remove(name)

            if tags:
                self._tags_being_made[guild_id] = tags
            else:
                self._tags_being_made.pop(guild_id)

    async def _add_tag(self, guild_id: int, owner_id: int, tag: str, desc: str) -> None:
        async with self.bot.pool.acquire() as con:
            con: asyncpg.connection.Connection  # type: ignore
            async with con.transaction():
                await con.execute(
                    "INSERT INTO tag (guild_id, tag_name, tag_description, owner_id) VALUES ($1, LOWER($2), $3, $4);",
                    guild_id,
                    tag,
                    desc,
                    owner_id,
                )

    async def _update_tag(self, guild_id: int, tag: str, desc: str) -> None:
        async with self.bot.pool.acquire() as con:
            con: asyncpg.connection.Connection  # type: ignore
            async with con.transaction():
                await con.execute(
                    "UPDATE tag SET description = $1 WHERE (guild_id = $2 OR guild_id = $3) AND tag_name = $4;",
                    desc,
                    guild_id,
                    000000000000000000,
                    tag,
                )

    async def _delete_tag(self, guild_id: int, tag: str) -> None:
        async with self.bot.pool.acquire() as con:
            con: asyncpg.connection.Connection  # type: ignore
            async with con.transaction():
                await con.execute(
                    "DELETE FROM tag WHERE guild_id = $1 AND tag = $2", guild_id, tag
                )
    
    async def _get_tag_suggestions(self, guild_id: int, tag: str) -> typing.List[typing.Optional[str]]:
        async with self.bot.pool.acquire() as con:
            con: asyncpg.connection.Connection  # type: ignore
            query = "SELECT tag.tag_name FROM tag WHERE guild_id = $1 ORDER BY similarity(tag.tag_name, $2);"
            tags = await con.fetch(query, guild_id, tag)
            return [tag["tag_name"] for tag in tags[:20]]

    async def _get_tag(
        self, guild_id: int, tag: str, search_global: bool = True
    ) -> typing.Optional[asyncpg.Record]:
        async with self.bot.pool.acquire() as con:
            con: asyncpg.connection.Connection  # type: ignore
            fetch_query = "SELECT * FROM tag WHERE "

            if search_global:
                fetch_query += "(guild_id = $1 OR guild_id = '000000000000000000') "
            else:
                fetch_query += "guild_id = $1 "

            fetch_query += "AND tag_name = LOWER($2)"
            return await con.fetchrow(fetch_query, guild_id, tag)

    @commands.group(name="tag", invoke_without_command=True)
    async def _tag(self, ctx: commands.Context, *tag_tuple: str):
        """
        Remove or Delete the tags of this server, you need manage_channels permissions to do so.
        If a subcommand is not called, then this will search the tag database
        for the tag requested.
        """
        tag = " ".join(tag_tuple).lower()
        data = await self._get_tag(ctx.guild.id, tag)

        if data:
            return await ctx.send(data["description"], reference=ctx.message.reference)

        suggestion_tags = await self._get_tag_suggestions(ctx.guild.id, tag)
        if suggestion_tags:
            sug = "\n• ".join(suggestion_tags)[:500]
            return await ctx.send(f"Could not find this tag, did you mean\n• {sug}")

    @_tag.command(name="add")
    async def add(
        self,
        ctx: commands.Context,
        glob: typing.Optional[typing.Literal["global"]],
        tag: str,
        *,
        desc: typing.Annotated[str, commands.clean_content],
    ):
        """
        Add a tag to the server, if duplicate a confirmation button will appear.
        This tag is server-specific and cannot be used in other servers.
        """

        if glob and ctx.author.id in self.bot.owner_ids:
            guild_id = 000000000000000000
        else:
            guild_id = ctx.guild.id

        tag = tag.lower()
        tag_check = await self._get_tag(guild_id, tag, guild_id == 0)

        if len(desc) > 2000:
            return await ctx.send("Tag content is a maximum of 2000 characters. \U0001f615")

        if tag_check:
            return await ctx.send("Tag already exists.")

        await self._add_tag(guild_id, ctx.author.id, tag, desc)
        await ctx.send("\N{OK HAND SIGN}")

    @_tag.command(name="delete")
    async def _delete(
        self,
        ctx: commands.Context,
        glob: typing.Optional[typing.Literal["global"]],
        *tag_tuple: str,
    ):
        """
        Delete a tag from the server.
        """

        if glob and ctx.author.id in self.bot.owner_ids:
            guild_id = 000000000000000000
        else:
            guild_id = ctx.guild.id

        tag = " ".join(tag_tuple).lower()
        tag_check = await self._get_tag(guild_id, tag, guild_id == 0)

        if not tag_check:
            suggestion_tags = await self._get_tag_suggestions(ctx.guild.id, tag)
            if suggestion_tags:
                sug = "\n• ".join(suggestion_tags)[:500]
                return await ctx.send(f"Could not find this tag, did you mean\n• {sug}")
            return


        if tag_check.get("owner_id", None) != ctx.author.id and not ctx.author.guild_permissions.manage_channels:
            return await ctx.send('You need "Manage Channels" permissions to delete other users tags.')

        await self._delete_tag(guild_id, tag)
        return await ctx.send("\N{OK HAND SIGN}")

        

    @_tag.command(name="edit")
    async def _edit(
        self,
        ctx: commands.Context,
        glob: typing.Optional[typing.Literal["global"]],
        tag: str,
        *,
        desc: typing.Annotated[str, commands.clean_content],
    ):
        """
        Edit a tag from the server.
        """

        if glob and ctx.author.id in self.bot.owner_ids:
            guild_id = 000000000000000000
        else:
            guild_id = ctx.guild.id

        tag = tag.lower()
        tag_check = await self._get_tag(guild_id, tag, guild_id == 0)

        if not tag_check:
            suggestion_tags = await self._get_tag_suggestions(ctx.guild.id, tag)
            if suggestion_tags:
                sug = "\n• ".join(suggestion_tags)[:500]
                return await ctx.send(f"Could not find this tag, did you mean\n• {sug}")
            return

        if tag_check.get("owner_id", None) != ctx.author.id and not ctx.author.guild_permissions.manage_channels:
            return await ctx.send('You need "Manage Channels" permissions to edit other users tags.')
    
        if len(desc) > 2000:
            return await ctx.send("Tag content is a maximum of 2000 characters. \U0001f615")

        await self._update_tag(guild_id, tag, desc)
        return await ctx.send("\N{OK HAND SIGN}")

    @_tag.command(name='make')
    async def _make(self, ctx: commands.Context):
        """Step by step guide to make a tag. Takes no arguments.
        """

        original = ctx.message
        converter = TagName(lower=True)

        await ctx.send("Hi \U0001f603, what would you like the tag's name to be?")

        def check(m: discord.Message) -> bool:
            return m.channel == ctx.channel and m.author == ctx.author

        try:
            name_msg: discord.Message = await self.bot.wait_for("message", check=check, timeout=60)
        except asyncio.TimeoutError:
            return await ctx.send("You took too long, you can always start over. \U0001f44b")
        
        try:
            ctx.message = name_msg
            name = await converter.convert(ctx, name_msg.content)
        except commands.BadArgument as e:
            return await ctx.send(f'{e}. Redo the command "{ctx.prefix}tag make" to retry.')
        finally:
            ctx.message = original
        
        if self.tag_is_being_made(ctx.guild.id, name):
            return await ctx.send(f'Sorry. This tag is currently being made by someone. Redo the command "{ctx.prefix}tag make" to retry.')

        exists = await self._get_tag(ctx.guild.id, name, False)

        if exists:
            return await ctx.send(f'Sorry. A tag with that name already exists. Redo the command "{ctx.prefix}tag make" to retry.')

        self.add_tag(ctx.guild.id, name)
        await ctx.send(f"Lovely, your tag's name is {name}! What would you like as tag context?\nUse {ctx.prefix}abort to abort the process.")

        try:
            context_msg: discord.Message = await self.bot.wait_for('message', check=check, timeout=300.0)
        except asyncio.TimeoutError:
            self.remove_tag(ctx.guild.id, name)
            return await ctx.send("You took too long, you can always start over. \U0001f44b")
        
        if context_msg.content == f"{ctx.prefix}abort":
            self.remove_tag(ctx.guild.id, name)
            return await ctx.send("Aborting...")
        elif context_msg.content:
            clean_content = await commands.clean_content().convert(ctx, context_msg.content)
        else:
            clean_content = context_msg.content

        if context_msg.attachments:
            clean_content = f"{clean_content}\n{context_msg.attachments[0].url}"
        
        if len(clean_content) > 2000:
            return await ctx.send("Tag content is a maximum of 2000 characters. \U0001f615")

        await self._add_tag(ctx.guild.id, ctx.author.id, name, clean_content)
        await ctx.send("\N{OK HAND SIGN}")

async def setup(bot: Botty):
    await bot.add_cog(Tags(bot))
