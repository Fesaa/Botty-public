import asyncio
import contextlib
import io
import os
import textwrap
import traceback
from difflib import SequenceMatcher
from typing import (
    Optional,
    Literal,
    Any
)

import discord
from discord import Embed
from discord.ext import commands, menus  # type: ignore

from Botty import Botty


def similar(str1, str2):
    return SequenceMatcher(None, str1, str2).ratio()


class AdminCommands(commands.Cog):

    def __init__(self, bot: Botty):
        self.bot = bot
        self._last_result: Optional[Any] = None
        super().__init__()

    async def cog_check(self, ctx: commands.Context[Botty]) -> bool:
        return ctx.author.id in self.bot.owner_ids

    @property
    def display_emoji(self) -> discord.PartialEmoji:
        return discord.PartialEmoji(name='\U00002699')

    @commands.command(hidden=True)
    async def close(self, ctx: commands.Context):
        await asyncio.wait_for(self.bot.pool.close(), 60)
        await self.bot.close()

    @commands.command(hidden=True)
    async def sync(
            self,
            ctx: commands.Context,
            guilds: commands.Greedy[discord.Object],
            spec: Optional[Literal["~"]] = None,
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

    @commands.command(name="reload", hidden=True)
    async def _reload(self, ctx: commands.Context, *names: str):
        """
        Command for reloading Cogs, can only be used by my owners.
        """
        files = ([f"cogs.{name}" for name in names] or [f"cogs.{name[:-3]}" for name in os.listdir("./cogs") if
                                                        name.endswith(".py") and name != "ConfigHandler.py"])
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
                    e.add_field(name="The following cogs could not be found, did you mistype?", value=field_value,
                                inline=False, )

        if stray_cogs:
            field_value = ""

            for index, missing_cog in enumerate(stray_cogs):  # type: ignore
                field_value += f"{missing_cog[5:]}\n"

                if len(field_value) > 1000 or index + 1 == len(stray_cogs):
                    e.add_field(name="The following cogs could not be found, no suggestions found", value=field_value,
                                inline=False)

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
    async def load(self, ctx: commands.Context, *, module: str):
        """Loads a module."""
        try:
            await self.bot.load_extension(module)
        except commands.ExtensionError as e:
            await ctx.send(f"{e.__class__.__name__}: {e}")
        else:
            await ctx.send("\N{OK HAND SIGN}")

    @commands.command(hidden=True)
    async def unload(self, ctx: commands.Context, *, module: str):
        """Unloads a module."""
        try:
            await self.bot.unload_extension(module)
        except commands.ExtensionError as e:
            await ctx.send(f"{e.__class__.__name__}: {e}")
        else:
            await ctx.send("\N{OK HAND SIGN}")

    @commands.command(hidden=True)
    async def list_cogs(self, ctx: commands.Context):
        """Lists all cogs."""
        await ctx.send(", ".join(self.bot.cogs))

    def cleanup_code(self, content: str) -> str:
        if content.startswith("```") and content.endswith("```"):
            return "\n".join(content.split("\n")[1:-1])
        return content.strip("` \n")

    def string_shortener(self, s: str) -> str:
        if len(s) < 1000:
            return s
        begin = "\n".join(s[:500].split("\n")[:-1])
        end = "\n".join(s[-500:].split("\n")[1:])
        return f"{begin}\n...\n{end}"

    @commands.command(name="cli", hidden=True)
    async def _cli(self, ctx: commands.Context, *, cmd: str):
        async def kill_proc(proc: asyncio.subprocess.Process, count) -> None:

            if count == 10:
                return proc.kill()

            if proc.returncode is None:
                await asyncio.sleep(1)
                return await kill_proc(proc, count + 1)

            return

        async with ctx.typing():
            try:
                proc = await asyncio.create_subprocess_shell(cmd, stdout=asyncio.subprocess.PIPE)
                result = await asyncio.gather(proc.communicate(), kill_proc(proc, 0))
                stdout, stderr = result[0][0], result[0][1]
                out = self.string_shortener(stdout.decode("utf-8")) if stdout else ""
                err = self.string_shortener(stderr.decode("utf-8")) if stderr else ""
            except FileNotFoundError:
                out, err = "", f"{cmd}: file not found"
            except PermissionError:
                out, err = "", f"Permission denied: {cmd}"

            e = Embed(
                title=f"CLI command execution",
                description=cmd,
                colour=discord.Colour.blurple(),
                timestamp=discord.utils.utcnow(),
            )

            if out:
                e.add_field(name="Output", value=f"```\n{out}```")
            if err:
                e.add_field(name="Error", value=f"```\n{err}```")

            e.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar.url)

            await ctx.send(embed=e)

    @commands.command(name="eval", hidden=True)
    async def _eval(self, ctx: commands.Context, *, body: str):

        env = {
            "bot": self.bot,
            "ctx": ctx,
            "channel": ctx.channel,
            "author": ctx.author,
            "guild": ctx.guild,
            "message": ctx.message,
            "_": self._last_result,
        }

        env.update(globals())

        body = self.cleanup_code(body)
        stdout = io.StringIO()

        to_compile = f'async def func():\n{textwrap.indent(body, "  ")}'

        try:
            exec(to_compile, env)
        except Exception as e:
            return await ctx.send(embed=Embed(title="Error:", description=f"```py\n{e.__class__.__name__}: {e}\n```"))

        func = env["func"]
        try:
            with contextlib.redirect_stdout(stdout):
                ret = await func()
        except Exception as e:
            value = stdout.getvalue()
            await ctx.send(embed=Embed(title="Error:", description=f"```py\n{value}{traceback.format_exc()}\n```"))
        else:
            value = stdout.getvalue()
            if ret is None:
                if value:
                    await ctx.send(embed=Embed(title="Eval", description=f"```py\n{value}\n```"))
            else:
                self._last_result = ret
                await ctx.send(embed=Embed(title="Eval", description=f"```py\n{value}{ret}\n```"))


async def setup(bot: Botty):
    await bot.add_cog(AdminCommands(bot))
