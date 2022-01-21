from time import strptime

from discord import Embed
from discord.file import File
from discord.member import Member
from discord_slash import SlashContext, cog_ext
from discord_slash.context import ComponentContext
from discord_slash.utils.manage_commands import create_option
from discord_slash.utils.manage_components import create_button, create_actionrow
from discord_slash.model import ButtonStyle
from discord.ext import commands
from datetime import datetime
from random import choice, randint
from operator import itemgetter
import matplotlib.pyplot as plt

guilds = []


def add_dict(dict_obj: dict, key: str):
    if key in dict_obj:
        dict_obj[key] += 1
    else:
        dict_obj[key] = 1


class mariage(commands.Cog):

    def __init__(self, client: commands.Bot):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        global guilds
        guilds = [guild.id for guild in self.client.guilds]

    @cog_ext.cog_slash(
        name="marry",
        description="Ask someone to marry you!",
        guild_ids=guilds,
        options=[
            create_option(
                name="user",
                description="Select your loved one!",
                required=True,
                option_type=6
            )
        ]
    )
    async def _marry(self, ctx: SlashContext, user):
        if user == ctx.author or user.bot:
            await ctx.send(embed=Embed(title="Narcissus, est, quod te?",
                                       description="You cannot marry yourself."
                                                   " And you human are not worthy of love from a bot.",
                                       color=0xad3998
                                       ))
        else:
            data = self.client.db.get_marriagestatus(ctx.author.id, ctx.guild_id)
            action_take = False
            is_married = False
            for status in data:
                if status[1] == user.id:
                    if status[2] == 'married':
                        is_married = True
                        action_take = True
                    if status[2] == 'requested':
                        action_take = True
            if action_take:
                if is_married:
                    await ctx.send(embed=Embed(title="Love birds",
                                               description=f"You are already married to them!! :heart: \n"
                                                           f"I hope you didn't forgot, and just wanted to marry again!",
                                               color=0xad3998
                                               ))
                else:
                    await ctx.send(embed=Embed(title="Be patient",
                                               description=f"You have already asked them to marry you!"
                                                           f" Be patience for their answer :) ",
                                               color=0xad3998
                                               ))
            if not action_take:
                love_quotes = [
                    "“As he read, I fell in love the way you fall asleep: slowly, and then all at once.” – John Green",
                    "“Loved you yesterday, love you still, always have, always will.” – Elaine Davis",
                    "“Love is never lost. If not reciprocated, it will flow back and soften and purify the heart.”"
                    " – Washington Irving",
                    "“You know you’re in love when you can’t fall asleep because reality is finally better than your"
                    " dreams.” – Dr. Seuss",
                    "“Love is like the wind, you can’t see it but you can feel it.” – Nicholas Sparks",
                    "“I love you without knowing how, or when, or from where. I love you simply, without problems or"
                    " pride: I love you in this way because I do not know any other way of loving but this, in which"
                    " there is no I or you, so intimate that your hand upon my chest is my hand, so intimate that when"
                    " I fall asleep your eyes close.” – Pablo Neruda"
                    ]
                embed = Embed(title="",
                              description=f"{choice(love_quotes)} \n{user.mention} would you like to marry"
                                          f" {ctx.author.mention}? ",
                              color=0xad3998
                              )
                msg = await ctx.send(embed=embed,
                                     components=[
                                         create_actionrow(
                                             create_button(style=ButtonStyle.green,
                                                           label="YES",
                                                           custom_id="marry_yes"
                                                           ),
                                             create_button(style=ButtonStyle.red,
                                                           label="NO",
                                                           custom_id="marry_no"
                                                           )
                                         )
                                     ]
                                     )
                self.client.db.update_marriagestatus(ctx.author.id, user.id, 'requested',
                                                     datetime.now().strftime('%d/%m/%y %H:%M'), msg.id, ctx.guild_id)

    @cog_ext.cog_component()
    async def marry_yes(self, ctx: ComponentContext):
        data = self.client.db.get_marriagestatus(ctx.author.id, ctx.guild_id)
        for status in data:
            if status[1] == ctx.author.id and status[2] == 'requested' and status[4] == ctx.origin_message_id:
                self.client.db.delete_requeste_marriage(status[0], status[1], ctx.guild_id)
                self.client.db.update_marriagestatus(status[0], status[1], 'married',
                                                     datetime.now().strftime('%d/%m/%y %H:%M'), randint(0, 10000000),
                                                     ctx.guild_id)
                marriage_msg = [
                    "“A happy marriage is a long conversation which always seems too short.” —André Maurois",
                    'Marriage is like a graph—it has its ups and downs and as long as things bounce back up again,'
                    ' you’ve got a good marriage. If it heads straight down, then you’ve got some problems!"'
                    ' —Julie Andrews',
                    '“Being deeply loved by someone gives you strength, while loving someone deeply gives you courage.”'
                    ' —Lao Tzu',
                    '“I love you not only for what you are, but for what I am when I am with you.” —Roy Croft'

                    ]
                await ctx.edit_origin(embed=Embed(title="",
                                                  description=f"{choice(marriage_msg)} \n<@{status[0]}> and"
                                                              f" <@{status[1]}>  are now married! ",
                                                  color=0xad3998

                                                  ), components=[])

    @cog_ext.cog_component()
    async def marry_no(self, ctx: ComponentContext):
        data = self.client.db.get_marriagestatus(ctx.author.id, ctx.guild_id)
        for status in data:
            if status[1] == ctx.author.id and status[2] == 'requested' and status[4] == ctx.origin_message_id:
                self.client.db.delete_requeste_marriage(status[0], status[1], ctx.guild_id)
                self.client.db.update_marriagestatus(status[0], status[1], 'turned down', status[3],
                                                     randint(0, 10000000), ctx.guild_id)
                mariage_reject_msg = [
                    "It is not your fault, not even mine; it is the time that does not fall into what we planned"
                    " for our life. Let the relationship be the same for a while and when the darkness goes, we"
                    " will be together again.",
                    "You are the loveliest person I have ever met, but bonding together in a relationship forever"
                    " is not exactly the same. Being with you makes me feel good, but we both need time to move"
                    " together for the life.",
                    "Don’t take me wrong, but we are too young to share such responsibility right now; every relation"
                    " needs time to blossom, so does ours; I want to be with you forever, but hold my hand for now.",
                    "You are not the same as I am, you have your qualities, which are beautiful indeed, but we are not"
                    " made for each other couple in this life; it hurts you, but it is the truth that I want to tell.",
                    "I know it is hurting, but marriage is a commitment of love and togetherness; we have just started"
                    " a journey together, let us be matured and then we promise each other for the life long"
                    " relationship."

                    ]
                await ctx.edit_origin(embed=Embed(title="",
                                                  description=f"{choice(mariage_reject_msg)} \n"
                                                              f" <@{status[1]}> has turned <@{status[0]}>"
                                                              f" down. Who will calm their minds :c",
                                                  color=0xad3998
                                                  ), components=[])
            elif status[0] == ctx.author.id and status[2] == 'requested' and status[4] == ctx.origin_message_id:
                self.client.db.delete_requeste_marriage(status[0], status[1], ctx.guild_id)
                mistake_qoutes = [
                    "“Anyone who has never made a mistake has never tried anything new.”― Albert Einstein",
                    "“Isn't it nice to think that tomorrow is a new day with no mistakes in it yet?”― L.M. Montgomery",
                    "“When you find your path, you must not be afraid. You need to have sufficient courage to"
                    " make mistakes. Disappointment, defeat, and despair are the tools God uses to show us the"
                    " way.”― Paulo Coelho, Brida",
                    "“Nowadays most people die of a sort of creeping common sense, and discover when it is too"
                    " late that the only things one never regrets are one's mistakes.”― Oscar Wilde,"
                    " The Picture of Dorian Gray",
                    ]
                await ctx.edit_origin(embed=Embed(title="",
                                                  description=f"{choice(mistake_qoutes)} \nOne should be more careful"
                                                              f" to choose whom they ask to be with!",
                                                  color=0xad3998
                                                  ), components=[])

    @cog_ext.cog_slash(
        name="divorce",
        description="Divorce your spouse :(",
        guild_ids=guilds,
        options=[
            create_option(
                name="user",
                description="Select your unlucky partner",
                required=True,
                option_type=6
            )
        ]
    )
    async def _divorce(self, ctx: SlashContext, user):
        data = self.client.db.get_marriagestatus(ctx.author_id, ctx.guild_id)
        found_love = False
        for commitment in data:
            if (commitment[0] == user.id or commitment[1] == user.id) and commitment[2] == 'married':
                self.client.db.divorce_marriage(commitment[4], datetime.now().strftime('%d/%m/%y %H:%M'))
                found_love = True
                break
        if found_love:
            await ctx.send(f"You divorced <@{user.id}>")
        else:
            await ctx.send(f"You did not have a relation with <@{user.id}>. Do you hate them this much??")

    @cog_ext.cog_slash(
        name="history",
        description="Get a users relation ship history",
        guild_ids=guilds,
        options=[
            create_option(
                name="user",
                description="Who do you want to stalk?",
                required=False,
                option_type=6
            )
        ]
    )
    async def _history(self, ctx: SlashContext, user=None):
        if user is None:
            user = ctx.author
        data = self.client.db.get_marriagestatus(user.id, ctx.guild_id)
        data = sorted(data, key=itemgetter(3))
        to_send = ""
        for status in data:
            if status[2] == 'divorced':
                to_send +=\
                    f"<@{status[0]}> and <@{status[1]}> got married on {status[3]}, but later divorced" \
                    f" on {status[5]}. They were married for" \
                    f" {strptime(status[5], '%d/%m/%y %H:%M') - strptime(status[3], '%d/%m/%y %H:%M')}" \
                    f" :broken_heart: \n"
            elif status[2] == 'turned down':
                to_send += f"<@{status[0]}> got turned down by <@{status[1]}> on {status[3]}. :broken_heart: \n"
            elif status[2] == 'married':
                to_send += f"<@{status[0]}> and <@{status[1]}> are happily married since the {status[3]}! :heart: \n"
            elif status[2] == 'requested':
                to_send += f"<@{status[0]}> has a marriage proposal for <@{status[1]}> that has been left" \
                           f" unanswered. \n"
        if to_send == "":
            await ctx.send(embed=Embed(title=f"Relation ship history of {user.name}",
                                       description="This user has yet to be engaged in love",
                                       color=0xad3998
                                       ))
        else:
            await ctx.send(embed=Embed(title=f"Relation ship history of {user.name}",
                                       description=to_send,
                                       color=0xad3998
                                       ))

    @cog_ext.cog_slash(
        name="ship",
        description="Find some love percentage! *Completely fake*",
        guild_ids=guilds,
        options=[
            create_option(
                name="user",
                description="Select your loved one",
                required=True,
                option_type=6
            )
        ]
    )
    async def _ship(self, ctx: SlashContext, user: Member):
        data = self.client.db.get_ship(ctx.author_id, user.id)
        if data is None:
            data = self.client.db.get_ship(user.id, ctx.author_id)
        if data is None or data[3] != datetime.now().strftime('%d'):
            self.client.db.update_ship(ctx.author_id, user.id, choice(
                [randint(0, 25), randint(25, 50), randint(25, 50), randint(50, 75), randint(50, 75), randint(50, 75),
                 randint(75, 100), randint(75, 100), randint(75, 100), randint(75, 100)]),
                                       datetime.now().strftime('%d'))
            data = self.client.db.get_ship(ctx.author_id, user.id)
        if data[2] < 25:
            msg_list = [
                "“It's so hard to forget pain, but it's even harder to remember sweetness. We have no scar to show for"
                " happiness. We learn so little from peace.” ― Chuck Palahniuk",
                "“Turn your wounds into wisdom.” ― Oprah Winfrey",
                "“If pain must come, may it come quickly. Because I have a life to live, and I need to live it in the"
                " best way possible. If he has to make a choice, may he make it now. Then I will either wait for him"
                " or forget him.” ― Paulo Coelho",
                "“The worst part of holding the memories is not the pain. It's the loneliness of it. Memories need to"
                " be shared.” ― Lois Lowry",
                "“It has been said, 'time heals all wounds.' I do not agree. The wounds remain. In time, the mind,"
                " protecting its sanity, covers them with scar tissue and the pain lessens. But it is never gone.”"
                " ― Rose Fitzgerald Kennedy",
                "“Time was passing like a hand waving from a train I wanted to be on. I hope you never have to think"
                " about anything as much as I think about you.” ― jonathan safran foer",
                ]
        elif data[2] < 50:
            msg_list = [
                "One of the hardest question you'll ever face in life choosing whether to walk away or to try harder."
                " - Ziad K. Abdelnour",
                "It is not that I don't love you, I just can't take an other loss - unknown",
                "“Be thankful for wrong relationships. They teach you, change you, strengthen you and prepare"
                " you for the right one.” - unknown",
                "“It’s better to be with no one than to be with the wrong one.” - unknown",
                "Sometimes there is so much we feel, yet so little we say. I am sorry - unknown"
                ]
        elif data[2] < 75:
            msg_list = ["""""What comes easy won't last long, and what lasts long won't come easy." —​ Francis Kong""",
                        "Falling in love is easy, but staying in love is very special. And that might just be with you"
                        " - unknown",
                        "You don't run from the people who need you. You fight for them. You fight beside them."
                        " No matter"
                        " the cost. No matter the risk.” ― Rick Yancey",
                        "“There is never a time or place for true love. It happens accidentally, in a heartbeat, in"
                        " a single flashing, throbbing moment.” – Sarah Dessen",
                        "“To love is to burn, to be on fire.” – Jane Aust"
                        ]
        elif data[2] < 90:
            msg_list = ["“True love stories never have endings.” – Richard Bach",
                        "“True love will triumph in the end – which may or may not be a lie, but if it is a lie, it’s"
                        " the most beautiful lie we have.” – John Green",
                        '"True love is eternal, infinite, and always like itself. It is equal and pure, without violent'
                        ' demonstrations: it is seen with white hairs and is always young in the heart.” –'
                        ' Honore de Balzac',
                        "“I believe in true love, and I believe in happy endings. And I believe.” – Christie Brinkley",
                        "“It is so difficult in the world for people to find love, true love.” – LaToya Jackson"
                        ]
        else:
            msg_list = ["“Never marry the one you can live with, marry the one you cannot live without.” – Unknown",
                        "“Experts on romance say for a happy marriage there has to be more than a passionate love."
                        " For a lasting union, they insist, there must be a genuine liking for each other. Which,"
                        " in my book, is a good definition for friendship.” – Marilyn Monroe",
                        "“So it’s not gonna be easy. It’s going to be really hard; we’re gonna have to work at this"
                        " everyday, but I want to do that because I want you. I want all of you, forever, everyday."
                        " You and me… everyday.” – Nicholas Sparks",
                        "“The secret to a happy marriage is if you can be at peace with someone within four walls,"
                        " if you are content because the one you love is near to you, either upstairs or downstairs,"
                        " or in the same room, and you feel that warmth that you don’t find very often, then that is"
                        " what love is all about.” – Bruce Forsyth",
                        "“Marriage is not a noun; it’s a verb. It isn’t something you get. It’s something you do. It’s"
                        " the way you love your partner every day.” – Barbara De Angelis",
                        "“Marriage stands the test of times when both you and your spouse work towards making things"
                        " better. And we are tested the most when we face adversities. If you can sail through the"
                        " adversities as one, as a team, then you have won half the battle.” – Unknown"
                        ]
        qoute = choice(msg_list)
        await ctx.send(embed=Embed(title="Your love story",
                                   description=f"{qoute} \n ❤️ <@{data[0]}> and <@{data[1]}>"
                                               f" have a daily love rating of __**{data[2]}%**__ ❤️",
                                   color=0xad3998))

    @commands.command()
    async def weddings(self, ctx: commands.Context):
        data = self.client.db.get_all_marriage(ctx.guild.id)
        if data:
            graph_data_total = {}
            graph_data_divorces = {}
            graph_data_total_name = {}
            for status in data:
                if status[2] == 'married' or status[2] == 'divorced':
                    add_dict(graph_data_total, status[0])
                    add_dict(graph_data_total, status[1])
                if status[2] == 'divorced':
                    add_dict(graph_data_divorces, status[0])
                    add_dict(graph_data_divorces, status[1])
            for key in graph_data_total:
                name = await self.client.fetch_user(key)
                try:
                    divorces = f" -- {graph_data_divorces[key]}"
                except KeyError:
                    divorces = " -- 0"
                graph_data_total_name[name.name + divorces] = graph_data_total[key]
            graph_data_total_name = dict(sorted(graph_data_total_name.items(), key=lambda item: item[1]))
            plt.bar(*zip(*graph_data_total_name.items()))
            plt.title(f'Total marriages for {ctx.guild.name}')
            plt.xticks(rotation=90)
            plt.savefig(f'cogs/marriage_png/marriages_{ctx.guild.id}.png', bbox_inches='tight')
            embed = Embed(title=f"Total weddings (and divorces) of {ctx.guild.name}",
                          description="Weddings can be seen in the graph itself, the amount of divorces is shown"
                                      " after each users name. ",
                          color=0xad3998)
            file = File(f'cogs/marriage_png/marriages_{ctx.guild.id}.png', filename="image.png")
            embed.set_image(url="attachment://image.png")
            await ctx.send(file=file, embed=embed)


def setup(client):
    client.add_cog(mariage(client))
