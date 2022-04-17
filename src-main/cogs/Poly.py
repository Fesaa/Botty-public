from discord import utils
from emoji import emojize
from discord.ext import commands

class BreakIt(Exception):
    pass

class Polly(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(
        brief=f"poll <question> | <emoji name 1> <answer 1> | <emoji name 2> <answer 2> | ...`"
              f" - Starts a poll, only works in a specified channel.")
    async def poll(self, ctx: commands.Context, *, arg: str):
        if (bool(set(self.bot.db.get_channel(ctx.guild.id, 'Polly_role_id')) & set([i.id for i in ctx.author.roles])) or ctx.author.guild_permissions.administrator) \
            and ctx.channel.id in self.bot.db.get_channel(ctx.guild.id, 'Polly'):

            pollinfo = arg.split('|')
            question = pollinfo[0]
            answer_list = []
            emoji_list = []
            await ctx.message.delete()
            for entry in pollinfo[1:]:
                entry_list = entry.removeprefix(" ").removesuffix(" ").replace("  ", " ").split(' ')
                if emojize(":" + entry_list[0] + ":", use_aliases=True) != ":" + entry_list[0] + ":":
                    emoji_list.append(entry_list[0])
                    answer_list.append(" ".join(entry_list[1:]))
                else:
                    emoji = utils.get(ctx.guild.emojis, name=entry_list[0])
                    if emoji is not None:
                        emoji_list.append(emoji)
                        answer_list.append(entry_list[1])
                    else:
                        await (await ctx.author.create_dm()).send(
                            f"{entry_list[0]} is not the name of an emoji. The poll will not be made.")
                        raise BreakIt
            text = question + "\n"
            for entry in emoji_list:
                try:
                    text += emojize(":" + entry + ":", use_aliases=True) + " - " + answer_list[
                        emoji_list.index(entry)] + "\n"
                except TypeError:
                    text += "<:" + entry.name + ":" + str(entry.id) + ">" + " - " + answer_list[
                        emoji_list.index(entry)] + "\n"
            polmsg = await ctx.channel.send(text)
            for entry in emoji_list:
                try:
                    await polmsg.add_reaction(emojize(":" + entry + ":", use_aliases=True))
                except TypeError:
                    await polmsg.add_reaction(entry)
        else:
            await ctx.send("Are you in the right channel? Do you have the right roles?", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Polly(bot))
