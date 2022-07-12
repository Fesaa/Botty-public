import discord
from discord.ext import menus, commands
from itertools import starmap, chain

from imports.MyMenuPages import MyMenuPages
from Botty import Botty

class HelpPageSource(menus.ListPageSource):
    def __init__(self, data, helpcommand):
        super().__init__(data, per_page=6)
        self.helpcommand = helpcommand

    def format_command_help(self, no, command: commands.Command):
        signature = self.helpcommand.get_command_signature(command)
        docs = self.helpcommand.get_command_brief(command)
        return f"{no}. {signature}\n{docs}"
    
    async def format_page(self, menu, entries):
        page = menu.current_page
        max_page = self.get_max_pages()
        starting_number = page * self.per_page + 1
        iterator = starmap(self.format_command_help, enumerate(entries, start=starting_number))
        page_content = "\n\n".join(iterator)
        embed = discord.Embed(
            title=f"Help Command[{page + 1}/{max_page}]", 
            description=page_content,
            color=0xad3998,
            timestamp=discord.utils.utcnow()
        )
        author = menu.ctx.author
        embed.set_footer(text=f"Requested by {author}", icon_url=author.avatar.url)
        return embed

class MyHelp(commands.MinimalHelpCommand):


    def get_command_brief(self, command: commands.Command):
        return command.short_doc or "Command is not documented."    
    
    async def send_bot_help(self, mapping: dict):
        added_help = False
        cmds = []
        for cog, s in mapping.items():
            for cmd in s:
                if cmd.name == 'help':
                    cmds.append(cmd) if not added_help else ""
                    added_help = True
                    continue
                cmds.append(cmd)
                
        filtered = await self.filter_commands(cmds, sort=True)
        all_commands = filtered
        formatter = HelpPageSource(all_commands, self)
        menu = MyMenuPages(formatter, delete_message_after=True)
        await menu.start(self.context)

class Help(commands.Cog):
    def __init__(self, bot: Botty):
       self.bot = bot
        
       help_command = MyHelp()
       help_command.cog = self 
       bot.help_command = help_command


async def setup(bot):
    await bot.add_cog(Help(bot))
