import discord

from discord.ext import commands

class ToolCommands(commands.Cog):

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        super().__init__()
    
    @commands.command(aliases=['avt'], no_pm=True)
    async def avatar(self, ctx, user: discord.Member = None):
        """
        A users avatar
        """
        if user is None:
            user = ctx.author
        embed = discord.Embed(title=f"Avatar of {user}", color=0xad3998)
        embed.description = f"Links: \n [png]({str(user.avatar.url).replace('webp', 'png')}) | [jpg]" \
                            f"({str(user.avatar.url).replace('webp', 'jpg')}) | [webp]({user.avatar.url})"
        embed.set_image(url=user.avatar.url)
        await ctx.send(embed=embed)
    
    @commands.command(no_pm=True)
    async def info(self, ctx: commands.Context, user: discord.Member = None):
        """
        Small embed with information about the Member.
        """
        if user is None:
            user = ctx.author
        embed = discord.Embed(title=f"Some (ir)relevant info about {user}", color=0xad3998)

        if user.activity is None:
            act = None
        else:
            act = str(user.activity.type).removeprefix('ActivityType.')

        embed.description = (f"Name: {user.name} | Nick: {user.nick}\n"
                             f"Bot: {user.bot}\n"
                             f"id: {user.id}\n"
                             f"Acc made at: {user.created_at.strftime('%d-%m-%y %H:%M')}\n"
                             f"Joined guild at: {user.joined_at.strftime('%d-%m-%y %H:%M')}\n"
                             f"On mobile: {user.is_on_mobile()}\n"
                             f"Status: {user.status}\n"
                             f"Activity: {act}")
        embed.set_author(name=user.name, url=f" https://discordapp.com/users/{user.id}/", icon_url=user.avatar.url)
        embed.set_thumbnail(url="https://media1.tenor.com/images/b25bb53205e7087790cd133ff960c222/tenor.gif?itemid=7914122")

        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name='leaderboard', description='Fetch the leaderboard for a game in a specific channel!', aliases=['lb'])
    @discord.app_commands.choices(
        game = [
            discord.app_commands.Choice(name='ConnectFour', value='ConnectFour'),
            discord.app_commands.Choice(name='HangMan', value='HangMan'),
            discord.app_commands.Choice(name='HigherLower', value='HigherLower'),
            discord.app_commands.Choice(name='NTBPL', value='NTBPL'),
            discord.app_commands.Choice(name='Wordsnake', value='WordSnake')
        ]
    )
    async def _leaderboard(self, ctx: commands.Context, game: str = None, channel: discord.TextChannel = None):
        """
        Display the leaderboard for a game per channel, shorter: lb \n
        Only calling lb will display the leaderboard for this channel you are in. This might cause some weird points if the channel was used for more than one game.
        """

        if not channel:
            channel = ctx.channel
        
        max_lb_size = self.bot.db.get_game_setting(ctx.guild.id, 'max_lb_size')
        data = self.bot.db.get_lb(channel.id, max_lb_size, game)

        if data:
            description = ""
            lb_prefix = ['🥇', '🥈', '🥉'] + [str(i) for i in range(4, max_lb_size + 1)]
            for entry in data:
                description += f"{lb_prefix[data.index(entry)]}: <@{entry[1]}> - **{entry[2]}**\n"

            if ctx.author.id not in [i[1] for i in data]:
                description += f'Your score: {self.bot.db.get_score(game, channel.id, ctx.author.id)}'

            title = f"⭐ {game if game else ''} leaderboard for {channel.name} ! 🌟"
            embed = discord.Embed(title=title, description=description, color=0xad3998)
            await ctx.send(embed=embed)
        else:
            await ctx.send(game + "has not been played in" if game else "No leaderboard for" + channel.mention , ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(ToolCommands(bot))