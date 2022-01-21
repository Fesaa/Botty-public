from discord.ext import commands
from cogs.config_handler import get_configdata
from discord.channel import DMChannel
from discord import Embed


class help_Commands(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.client.remove_command('help')  # Custom help command

    @commands.command(no_pm=True, aliases=['h'])
    async def help(self, ctx, name=None):  # No name or not matching name will return default help
        if isinstance(ctx.channel, DMChannel):  # Prevents help in DM (guild is requirement for help)
            pass
        else:
            if not (await ctx.guild.query_members(user_ids=[474319793042751491])):  # icon handler
                icon_url = r"https://upload.wikimedia.org/wikipedia/commons/thumb/7/72/" \
                           r"Torchlight_help_icon.svg/1024px-Torchlight_help_icon.svg.png"
            else:
                icon_url = (await ctx.guild.query_members(user_ids=[474319793042751491]))[0].avatar_url
            if name is None:  # lower() function is used on name, str requirement
                name = "PlaceHolder for else"

            if name.lower() in ["polly", 'p', 'pl']:  # Polly help
                embed = Embed(title="How do I use Polly?", description=(
                    f"Very simple :)! The command goes like this:"
                    f" `{(await get_configdata(self.client, ctx.guild.id, 'command_prefix'))}"
                    f"poll <question> | <emoji name 1> <answer 1> | <emoji name 2> <answer 2> | ...`"
                    f"\nThat's it!"
                    f"\nYou can delete a poll by adding a ❌ to a poll! :)"),
                              color=0xad3998)
                embed.set_author(name="Fesa", url="https://github.com/Fesaa", icon_url=icon_url)
                embed.set_thumbnail(url=self.client.user.avatar_url)
                await ctx.send(embed=embed)

            elif name.lower() in ["cubelvl", 'cl', 'clvl', 'c']:  # Cube level help
                field_one_text = f" "
                field_two_text = (
                    f"`{(await get_configdata(self.client, ctx.guild.id, 'command_prefix'))}"
                    f"stats <game> <wins> <total played games>`, to calculate how much experience you have received"
                    f" from playing a game."
                    f"\nSome games have a slightly different syntax due to their stats:"
                    f"\nAmong Slimes: `{(await get_configdata(self.client, ctx.guild.id, 'command_prefix'))}"
                    f"stats_as <wins> <completed tasks> <total played games>`"
                    f"\nDuels: `{(await get_configdata(self.client, ctx.guild.id, 'command_prefix'))}stats_duels"
                    f" <kills> <total played games>`"
                    f"\nFFA: `{(await get_configdata(self.client, ctx.guild.id, 'command_prefix'))}stats_ffa <kills>`"
                    f"\nThe available games are"
                    f"\ntew, sew, tsw, ssw, tli, sli, td, bwb, as, duels, ffa")
                field_three_text = f" "
                for bot_commands in self.client.commands:
                    if bot_commands.cog_name == "cube_lvl":
                        if bot_commands.description == "Which level will I be?":
                            field_one_text += "`" + (await get_configdata(self.client, ctx.guild.id,
                                                                          'command_prefix'))\
                                              + bot_commands.brief + "\n"
                        elif bot_commands.description == "How good are my stats?":
                            field_three_text += "`" + (await get_configdata(self.client, ctx.guild.id,
                                                                            'command_prefix'))\
                                                + bot_commands.brief + "\n"
                embed = Embed(title="How do I use Cube Lvl?",
                              description="Cube Lvl has a few commands related to leveling up,"
                                          " and a few to which level you would've been if ...! ",
                              color=0xad3998)
                embed.add_field(name="Which level will I be?", value=field_one_text, inline=False)  # field one
                embed.add_field(name="How much of my level comes from ...?", value=field_two_text,
                                inline=False)  # field two
                embed.add_field(name="How good are my stats?", value=field_three_text, inline=False)  # field three
                embed.set_author(name="Fesa", url="https://github.com/Fesaa", icon_url=icon_url)
                embed.set_thumbnail(url=self.client.user.avatar_url)
                await ctx.send(embed=embed)

            elif name.lower() in ["wordsnake", 'ws', 'words', 'word_snake', 'w']:  # Word snake help
                embed = Embed(title="How do I play wordsnake?", url="https://youtu.be/mOyU-uyjN7Q",
                              description="Here is a quick guide! Read carefully :D", color=0xad3998)
                embed.set_author(name="Fesa", url="https://github.com/Fesaa", icon_url=icon_url)
                embed.set_thumbnail(url=self.client.user.avatar_url)
                embed.add_field(name="Goal",
                                value=f"Wordsnake is really simple! Create the longest possible snake by finding"
                                      f" a word that starts with the last letter of the previous word! \nGood luck :D",
                                inline=False)
                embed.add_field(name="To start a game",
                                value=f"Enter `{(await get_configdata(self.client, ctx.guild.id, 'command_prefix'))}"
                                      f"start <first word>`. And wait for someone else to continue. ",
                                inline=True)
                embed.add_field(name="To stop a game",
                                value=f"Enter `{(await get_configdata(self.client, ctx.guild.id, 'command_prefix'))}"
                                      f"reset`. Other players might not like you for it :) \nThe game will also"
                                      f" automatically stop when someone makes a mistake :(",
                                inline=True)
                embed.add_field(name="To join a game",
                                value=f"Don't be shy! You can join anytime, just reply with a word and be careful not"
                                      f" to make a mistake! :D",
                                inline=True)
                embed.add_field(name="Too hard?",
                                value=f"No one finds a new word? Enter"
                                      f" `{(await get_configdata(self.client, ctx.guild.id, 'command_prefix'))}"
                                      f"resetwords` to re-use all previously used words.",
                                inline=True)
                embed.add_field(name="Word count",
                                value=f"Enter `{(await get_configdata(self.client, ctx.guild.id, 'command_prefix'))}"
                                      f"count` to check the number of words in the snake.",
                                inline=True)
                await ctx.send(embed=embed)

            elif name.lower() in ["ntbpl", 'np', 'nl', 'n']:  # Name ot be picked later help
                embed = Embed(title='How do I play "name to be picked later"?',
                              description="Here is a quick guide! Read carefully :D \nAn *"
                                          " indicates that this argument is optional!",
                              color=0xad3998)
                embed.set_author(name="Fesa", url="https://github.com/Fesaa", icon_url=icon_url)
                embed.set_thumbnail(url=self.client.user.avatar_url)
                embed.add_field(name="Goal",
                                value=f"This game is really simple! The bot will give you a set of letters."
                                      f" Find a word that contains these letters in the same order.\n"
                                      f" E.g. `ers` => `person`.",
                                inline=False)
                embed.add_field(name="To start a game",
                                value=f"Enter `{(await get_configdata(self.client, ctx.guild.id, 'command_prefix'))}"
                                      f"begin <count*>`.\n E.g."
                                      f" `{(await get_configdata(self.client, ctx.guild.id, 'command_prefix'))}begin 3`"
                                      f".",
                                inline=True)
                embed.add_field(name="To stop a game",
                                value=f"Enter `{(await get_configdata(self.client, ctx.guild.id, 'command_prefix'))}"
                                      f"stop`.",
                                inline=True)
                embed.add_field(name="To join a game",
                                value=f"Don't be shy! You can join anytime, just reply with a word and be careful not"
                                      f" to make a mistake! :D",
                                inline=True)
                embed.add_field(name="Too hard?",
                                value=f"No one finds a word? Enter"
                                      f"`{(await get_configdata(self.client, ctx.guild.id, 'command_prefix'))}"
                                      f"clearwords` to re-use all previously used words..",
                                inline=True)
                embed.add_field(name="Skipping letters",
                                value=f"Sometimes you just can't find a word that fits the letter. You're not a walking"
                                      f" dictionary, I get that! So I added the"
                                      f" `{(await get_configdata(self.client, ctx.guild.id, 'command_prefix'))}"
                                      f"skip` command, if 3 people react to the command I will skip the letters"
                                      f" for you :D")
                embed.set_footer(text="Thank you for testing with me Caliditas!")
                await ctx.send(embed=embed)

            elif name.lower() in ['higher_lower', 'hl', 'higherlower']:  # Higher lower help
                embed = Embed(title="How do I play higher lower?",
                              description="Here is a quick guide! Read carefully :D", color=0xad3998)
                embed.set_author(name="Fesa", url="https://github.com/Fesaa", icon_url=icon_url)
                embed.set_thumbnail(url=self.client.user.avatar_url)
                embed.add_field(name="Goal",
                                value="Higher lower is really simple! I have a number between 0 and 1000 in memory, "
                                      "and you have to guess it. "
                                      "Upon guess I will add a reaction telling you if my number is higher or lower "
                                      "than your guess (⬆️, ⬇️). "
                                      f" If you guess the number, I will grant you a star ⭐!\n Keep in mind that you "
                                      f"can only guess "
                                      f"{(await get_configdata(self.client, ctx.guild.id, 'HL_max_reply'))} \nHappy "
                                      f"star hunting ")
                await ctx.send(embed=embed)

            elif name.lower() in ['connect_four', 'connect-four', 'cf', 'c4']:  # Connect four help
                embed = Embed(title="How do I play connect four?",
                              description="Here is a quick guide! Read carefully :D", color=0xad3998)
                embed.add_field(name="Goal",
                                value="The board consists of 6 rows and 7 columns. The starting player will be playing "
                                      "yellow, the other red. You'll be choosing a column to drop a coin in one after "
                                      "the other. With the soul objective to have 4 coins in a row! These rows can be "
                                      "made, horizontally, vertically or diagonally. You drop a coin by react to the "
                                      "embed. Best of luck! ")
                embed.set_author(name="Fesa", url="https://github.com/Fesaa", icon_url=icon_url)
                embed.set_thumbnail(url=self.client.user.avatar_url)
                await ctx.send(embed=embed)

            elif name.lower() in ['marriage', 'ma', 'mg', 'love']:  # Marriage cog help
                embed = Embed(title="How do I express my love?",
                              description="Here is some Discord relation ship advice! \nThis part of the bot "
                                          "completely works with slash commands ✨",
                              color=0xad3998)
                embed.add_field(name="Marrying",
                                value="You can propose to someone with `/marry <user>`! With a beautiful quote, "
                                      "the bot will announce your proposal. Your perhaps to be spouse can accept by "
                                      "clicking YES! Or defect by clicking NO :c \nProposed to the wrong person? Just "
                                      "react with NO yourself, be more careful next time.")
                embed.add_field(name="Divorce",
                                value="Not all that could have been perfect lasts forever, something you must let "
                                      "go... do this with `/divorce <user>`! ")
                embed.add_field(name="History",
                                value="Feeling interested in someone? You can take a look at their past and present "
                                      "love interests to see if you could be theirs, use `/history <user*>`. Defaults "
                                      "to yourself")
                embed.add_field(name="Weddings",
                                value=f"Always wondered who got married or divorced the most? Using"
                                      f" `{(await get_configdata(self.client, ctx.guild.id, 'HL_max_reply'))}"
                                      f"weddings` will give you an embed with a graph containing this information. ")
                embed.set_author(name="Fesa", url="https://github.com/Fesaa", icon_url=icon_url)
                embed.set_thumbnail(url=self.client.user.avatar_url)
                await ctx.send(embed=embed)

            elif name.lower() in ['hangman', 'hm']:  # Hangman help
                embed = Embed(title="How do I play hangman?", description="Here is a quick guide! Read carefully :D",
                              color=0xad3998)
                embed.add_field(name="Goal",
                                value="The hangman will take a word in memory and give you the amount of letters it "
                                      "contains. You can guess a letter by adding the emoji for it (🇦 for a as "
                                      "example) or **replying** with a single letter to the game.. When playing with "
                                      "more, this will be done turn by turn, if you believe to know the hangmans "
                                      "word. Guess by **replying** to the game with `!guess <word>`. Every wrong "
                                      "letter and wrong guess will bring you closer to death. Best of luck, "
                                      "these may be the final words you read. ")
                embed.set_author(name="Fesa", url="https://github.com/Fesaa", icon_url=icon_url)
                embed.set_thumbnail(url=self.client.user.avatar_url)
                await ctx.send(embed=embed)

            else:  # General help
                text = f" "
                for bot_commands in self.client.commands:
                    if bot_commands.cog_name == "tool_Commands":
                        text += bot_commands.name + ": " + "`" + (
                            await get_configdata(self.client, ctx.guild.id, 'command_prefix'))\
                                + bot_commands.brief + "\n "
                embed = Embed(title="How to ask for help?", color=0xad3998)
                embed.description = "All commands can be written with random capitalisation. \nAn * indicates that " \
                                    "the argument is not required \n\nI am coded for the following things: \n "
                embed.add_field(name="General commands",
                                value=text + "_User can be a name, tag or id from someone in the server._",
                                inline=False)
                embed.add_field(name="Polly",
                                value=f"""Polly is a simple but smart polling tool in which the possible asnwers
                                 can be depicted by any emoji. \nMore info:
                                  `{(await get_configdata(self.client, ctx.guild.id, 'command_prefix'))}help polly`""",
                                inline=True)
                embed.add_field(name="Cube lvl v5",
                                value=("Cube level generates all the statictics about your Cubecraft experience."
                                       f"\nMore info:"
                                       f"`{(await get_configdata(self.client, ctx.guild.id, 'command_prefix'))}"
                                       f"help CubeLvl`"),
                                inline=True)
                embed.add_field(name="Word Snake",
                                value=("Word Snake is a fun little game you play together! Don't make the other lose!"
                                       f"\nMore info:"
                                       f"`{(await get_configdata(self.client, ctx.guild.id, 'command_prefix'))}"
                                       f"help WordSnake`"),
                                inline=True)
                embed.add_field(name="ntbpl", value=(
                    "ntbpl is a fun but hard game you play against each other! Try to get first on the lb"
                    f"\nMore info:`{(await get_configdata(self.client, ctx.guild.id, 'command_prefix'))}help ntbpl`"))
                embed.add_field(name="Higher lower",
                                value=f"Higher lower is a fun guessing game with numbers! \nMore info:"
                                      f"`{(await get_configdata(self.client, ctx.guild.id, 'command_prefix'))}"
                                      f"help higher_lower`")
                embed.add_field(name="Connect four",
                                value=f"A children classic since 1974! \nMore info:"
                                      f" `{(await get_configdata(self.client, ctx.guild.id, 'command_prefix'))}"
                                      f"help connect_four` ")
                embed.add_field(name="Hangman",
                                value=f"A stick figure guessing game played alone or up to 4 players."
                                      f" \nMore info:"
                                      f"  `{(await get_configdata(self.client, ctx.guild.id, 'command_prefix'))}"
                                      f"help hangman`")
                embed.add_field(name="Marriage",
                                value=f"Fell in love someone, can't wait to marry them? Not to worry, do so on Discord!"
                                      f" \nMore info:"
                                      f" `{(await get_configdata(self.client, ctx.guild.id, 'command_prefix'))}"
                                      f"help marriage`")
                embed.set_author(name="Fesa", url="https://github.com/Fesaa", icon_url=icon_url)
                embed.set_thumbnail(url=self.client.user.avatar_url)
                await ctx.send(embed=embed)


def setup(client):
    client.add_cog(help_Commands(client))
