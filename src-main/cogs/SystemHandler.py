import discord
import asyncio

from discord.ext import commands

from Botty import Botty

def string_shortener(s: str) -> str:
        if len(s) < 1000:
            return s 
        begin = "\n".join(s[:500].split('\n')[:-1])
        end = "\n".join(s[-500:].split('\n')[1:])
        return f'{begin}\n...\n{end}'

class SystemHandler(commands.Cog):

    def __init__(self, bot: Botty) -> None:
        self.bot = bot
        super().__init__()
    
    def is_me(ctx: commands.Context) -> bool:
        return ctx.author.id == 474319793042751491
 
    @commands.command(name="cli")
    @commands.check(is_me)
    async def _cli(self, ctx: commands.Context, cmd: str, *opt: str):
        async with ctx.typing():
            try:
                proc = await asyncio.create_subprocess_exec(cmd, *opt, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
                stdout, stderr = await proc.communicate()
                out = string_shortener(stdout.decode("utf-8"))
                err = string_shortener(stderr.decode("utf-8"))
            except FileNotFoundError:
                out, err = "", f"{cmd}: file not found"
            except PermissionError:
                out, err = "", f"Permission denied: {cmd}"

            e = discord.Embed(title=f'CLI command execution',description=f'{cmd} {" ".join(opt)}' ,colour=discord.Colour.blurple(), timestamp=discord.utils.utcnow())
            
            if out:
                e.add_field(name='Output', value=f'```\n{out}```')
            if err:
                e.add_field(name='Error', value=f'```\n{err}```')
            
            e.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar.url)

            await ctx.send(embed=e)

async def setup(bot: Botty):
    await bot.add_cog(SystemHandler(bot))