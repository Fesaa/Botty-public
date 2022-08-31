import io
import typing
import discord
import asyncio
import textwrap
import contextlib
import traceback

from discord import Embed
from discord.ext import commands

from Botty import Botty


def string_shortener(s: str) -> str:
    if len(s) < 1000:
        return s
    begin = "\n".join(s[:500].split("\n")[:-1])
    end = "\n".join(s[-500:].split("\n")[1:])
    return f"{begin}\n...\n{end}"


class SystemHandler(commands.Cog):
    def __init__(self, bot: Botty) -> None:
        self.bot = bot
        self._last_result: typing.Optional[typing.Any] = None
        super().__init__()

    def cog_check(self, ctx: commands.Context) -> bool:
        return ctx.author.id == 474319793042751491

    def cleanup_code(self, content: str) -> str:
        if content.startswith("```") and content.endswith("```"):
            return "\n".join(content.split("\n")[1:-1])
        return content.strip("` \n")

    @commands.command(name="cli", hidden=True)
    async def _cli(self, ctx: commands.Context, cmd: str, *opt: str):
        async def kill_proc(proc: asyncio.subprocess.Process, count) -> None:

            if count == 10:
                return proc.kill()

            if proc.returncode is None:
                await asyncio.sleep(1)
                return await kill_proc(proc, count + 1)

            return

        async with ctx.typing():
            try:
                proc: asyncio.subprocess.Process = await asyncio.create_subprocess_exec(
                    cmd,
                    *opt,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                result = await asyncio.gather(proc.communicate(), kill_proc(proc, 0))
                stdout, stderr = result[0][0], result[0][1]
                out = string_shortener(stdout.decode("utf-8"))
                err = string_shortener(stderr.decode("utf-8"))
            except FileNotFoundError:
                out, err = "", f"{cmd}: file not found"
            except PermissionError:
                out, err = "", f"Permission denied: {cmd}"

            e = Embed(
                title=f"CLI command execution",
                description=f'{cmd} {" ".join(opt)}',
                colour=discord.Colour.blurple(),
                timestamp=discord.utils.utcnow(),
            )

            if out:
                e.add_field(name="Output", value=f"```\n{out}```")
            if err:
                e.add_field(name="Error", value=f"```\n{err}```")

            e.set_footer(
                text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar.url
            )

            await ctx.send(embed=e)

    @commands.command(name="eval", hidden=True)
    async def _eval(self, ctx: commands.Context, *, body: str):

        if ctx.guild.id != 781938561175388190:
            return

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
            return await ctx.send(
                embed=Embed(
                    title="Error:",
                    description=f"```py\n{e.__class__.__name__}: {e}\n```",
                )
            )

        func = env["func"]
        try:
            with contextlib.redirect_stdout(stdout):
                ret = await func()
        except Exception as e:
            value = stdout.getvalue()
            await ctx.send(
                embed=Embed(
                    title="Error:",
                    description=f"```py\n{value}{traceback.format_exc()}\n```",
                )
            )
        else:
            value = stdout.getvalue()
            if ret is None:
                if value:
                    await ctx.send(
                        embed=Embed(title="Eval", description=f"```py\n{value}\n```")
                    )
            else:
                self._last_result = ret
                await ctx.send(
                    embed=Embed(title="Eval", description=f"```py\n{value}{ret}\n```")
                )


async def setup(bot: Botty):
    await bot.add_cog(SystemHandler(bot))
