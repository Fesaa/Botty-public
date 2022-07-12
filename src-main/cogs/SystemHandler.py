import discord
import asyncio

from discord.ext import commands

from Botty import Botty

class SystemHandler(commands.Cog):

    def __init__(self, bot: Botty) -> None:
        self.bot = bot
        super().__init__()
    
    def is_me(ctx: commands.Context):
        return ctx.author.id == 474319793042751491
    
    @commands.command(name="cli")
    @commands.check(is_me)
    async def _cli(self, ctx: commands.Context, cmd: str, *opt: str):
        try:
            proc = await asyncio.create_subprocess_exec(cmd, *opt, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
            stdout, stderr = await proc.communicate()
            out = stdout.decode("utf-8")
            err = stderr.decode("utf-8")
        except FileNotFoundError:
            out, err = "", f"{cmd}: command not found"

        e = discord.Embed(title=f'CLI command execution',description=f'{cmd} {" ".join(opt)}' ,colour=discord.Colour.blurple(), timestamp=discord.utils.utcnow())
        if out:
            if len(out) > 1000:
                out = out[:1000]
                out = "\n".join(out.split('\n')[:-1]) + '...'
            e.add_field(name='Output', value=f'```\n{out}```')
        if err:
            if len(err) > 1000:
                err = err[:1000] + '...'
            e.add_field(name='Error', value=f'```\n{err}```')
        
        e.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar.url)

        await ctx.send(embed=e)

async def setup(bot: Botty):
    await bot.add_cog(SystemHandler(bot))