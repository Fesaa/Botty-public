from asyncio import sleep
from collections import Counter
from discord.ext import commands
from discord.ui import View, button, Button
from discord import ButtonStyle, Embed, Interaction, Message, DMChannel

from Botty import Botty


DEFAULT_CONFIG = "0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0"
EMOJI_DICT = {"0": "⚪", "1": "🟡", "2": "🔴"}
COLOUR_DICT = {"yellow": "1", "red": "2"}


class RowFull(Exception):
    pass


def to_list(game_config: str) -> list:
    if game_config[-1] == ",":
        config_list = game_config[:-1].split(",")
    else:
        config_list = game_config.split(",")
    return config_list


def to_str(config_list: list) -> str:
    game_config = ""
    for info in config_list:
        game_config += info + ","
    return game_config[:-1]


def to_msg(config_list: list) -> str:
    to_send = ""
    for index in range(len(config_list)):
        if index % 7 != 0:
            to_send += EMOJI_DICT[config_list[index]]
        else:
            to_send += f"🟦\n🟦" + EMOJI_DICT[config_list[index]]

    return to_send.removeprefix("🟦") + "🟦"


def apply_move(config_list: list, row: int, colour: str) -> list:
    init_config = config_list[::]

    if row == 7:
        row = 0

    for index in [len(config_list) - 1 - i for i in range(len(config_list))]:
        if (index + 1) % 7 == row and config_list[index] == "0":
            config_list[index] = COLOUR_DICT[colour]
            break

    if init_config == config_list:
        raise RowFull
    else:
        return config_list


def check_win_state(config_list: list, colour: str) -> bool:
    check_for = COLOUR_DICT[colour]

    for index in range(len(config_list)):

        # Straight lines horizontal
        if (0 < (index + 1) % 7 <= 4) and config_list[index] == check_for:
            if (
                config_list[index + 1]
                == config_list[index + 2]
                == config_list[index + 3]
                == check_for
            ):
                return True

        # Diagonal lines up
        if (
            ((index + 1) % 7 >= 4 or (index + 1) % 7 == 0)
            and config_list[index] == check_for
            and index <= 21
        ):
            if (
                config_list[index + 6]
                == config_list[index + 12]
                == config_list[index + 18]
                == check_for
            ):
                return True

        # Diagonal lines down
        if ((0 < (index + 1) % 7 <= 4) and index < 21) and config_list[
            index
        ] == check_for:
            if (
                config_list[index + 8]
                == config_list[index + 16]
                == config_list[index + 24]
                == check_for
            ):
                return True

        # Straight lines veritcal
        if (index < 21) and config_list[index] == check_for:
            if (
                config_list[index + 7]
                == config_list[index + 14]
                == config_list[index + 21]
                == check_for
            ):
                return True
    return False


async def check_inactive(
    bot: Botty, current_data: dict, msg: Message, time_out: int
) -> None:
    await sleep(time_out)
    if current_data == bot.cache.get_connect_four(msg.id):
        bot.cache.remove_connect_four(msg.id)

        await msg.edit(
            embed=Embed(
                title="Failed game",
                description=f"Ended game due to inactivity (2min).",
                color=0xAD3998,
            ),
            view=View(),
        )


async def game_embed(
    bot: Botty, config: list, p1: int, p2: int, footer_text: str
) -> Embed:
    embed = Embed(title=" 🟡 Connect four 🔴", colour=0xAD3998)
    embed.add_field(
        name=f"Game of: {(await bot.fetch_user(p1)).name} - {(await bot.fetch_user(p2)).name}",
        value=to_msg(config),
    )
    embed.set_footer(text=footer_text)
    return embed


async def leave_function(bot: Botty, interaction: Interaction, button: Button):
    data = bot.cache.get_connect_four(interaction.message.id)  # type: ignore
    bot.cache.remove_connect_four(interaction.message.id)  # type: ignore

    if not data:
        return

    if data["player2"] == bot.user.id:
        if interaction.message:
            await interaction.message.delete()
        await interaction.response.send_message("Stopped your game", ephemeral=True)
    else:

        players = [data["player1"], data["player2"]]

        if interaction.user.id not in players:
            return await interaction.response.send_message(
                "You cannot leave a game you're not playing.", ephemeral=True
            )

        players.remove(interaction.user.id)
        winner = players[0]

        await bot.PostgreSQL.update_lb("ConnectFour", interaction.channel_id, winner, interaction.guild_id)

        await interaction.response.edit_message(
            embed=await game_embed(
                bot,
                to_list(data["config"]),
                data["player1"],
                data["player2"],
                f"{(await bot.fetch_user(winner)).name} won the game!"
                f" Since {(await bot.fetch_user(interaction.user.id)).name} left.",
            ),
            view=View(),
        )


async def register_move(
    bot: Botty, interaction: Interaction, row: int, view: View, button: Button
):
    data = bot.cache.get_connect_four(interaction.message.id)  # type: ignore

    if not data:
        return

    made_moves = (
        Counter(to_list(data["config"]))["1"] + Counter(to_list(data["config"]))["2"]
    )

    colour = {0: "yellow", 1: "red"}[made_moves % 2]

    if (made_moves % 2 == 0 and interaction.user.id == data["player1"]) or (
        made_moves % 2 == 1 and interaction.user.id == data["player2"]
    ):

        if made_moves < 42:

            config = apply_move(to_list(data["config"]), row, colour)

            try:
                temp = config[::]
                apply_move(temp, row, colour)
            except RowFull:
                button.disabled = True

            if check_win_state(config, colour):
                await interaction.response.edit_message(
                    embed=await game_embed(
                        bot,
                        config,
                        data["player1"],
                        data["player2"],
                        f"{(await bot.fetch_user(interaction.user.id)).name} won the game!",
                    ),
                    view=View(),
                )

                bot.cache.remove_connect_four(interaction.message.id)  # type: ignore
                await bot.PostgreSQL.update_lb(
                    "ConnectFour", interaction.channel_id, interaction.user.id, interaction.guild_id
                )
            else:

                players = [data["player1"], data["player2"]]
                players.remove(interaction.user.id)
                turn = players[0]

                await interaction.response.edit_message(
                    embed=await game_embed(
                        bot,
                        config,
                        data["player1"],
                        data["player2"],
                        f"{(await bot.fetch_user(turn)).name}'s turn!",
                    ),
                    view=view,
                )
                bot.cache.update_connect_four(
                    data["player1"],
                    data["player2"],
                    to_str(config),
                    interaction.message.id,  # type: ignore
                )

                await check_inactive(
                    bot,
                    bot.cache.get_connect_four(interaction.message.id),  # type: ignore
                    interaction.message,  # type: ignore
                    120,
                )

        else:
            await interaction.response.edit_message(
                embed=await game_embed(
                    bot,
                    config,
                    data["player1"],
                    data["player2"],
                    f"Games ends in a draw, all spaces are used!",
                ),
                view=View(),
            )
            bot.cache.remove_connect_four(interaction.message.id)  # type: ignore

    else:
        if interaction.user.id in [data["player1"], data["player2"]]:
            await interaction.response.send_message(
                "Wait for your turn", ephemeral=True
            )
        else:
            await interaction.response.send_message(
                "You are not playing!", ephemeral=True
            )


class ConnectFourGameView(View):
    def __init__(self, bot: Botty, timeout=None):
        self.bot = bot
        super().__init__(timeout=timeout)

    async def interaction_check(self, interaction: Interaction) -> bool:
        data = self.bot.cache.get_connect_four(interaction.message.id)  # type: ignore

        if not data:
            return False

        players = [data["player1"], data["player2"]]

        if interaction.user.id not in players:
            return False

        return True

    @button(emoji="1️⃣", style=ButtonStyle.blurple)
    async def _one(self, interaction: Interaction, button: Button):
        await register_move(self.bot, interaction, 1, self, button)

    @button(emoji="2️⃣", style=ButtonStyle.blurple)
    async def _two(self, interaction: Interaction, button: Button):
        await register_move(self.bot, interaction, 2, self, button)

    @button(emoji="3️⃣", style=ButtonStyle.blurple)
    async def _three(self, interaction: Interaction, button: Button):
        await register_move(self.bot, interaction, 3, self, button)

    @button(emoji="4️⃣", style=ButtonStyle.blurple)
    async def _four(self, interaction: Interaction, button: Button):
        await register_move(self.bot, interaction, 4, self, button)

    @button(emoji="5️⃣", style=ButtonStyle.blurple)
    async def _five(self, interaction: Interaction, button: Button):
        await register_move(self.bot, interaction, 5, self, button)

    @button(emoji="6️⃣", style=ButtonStyle.blurple)
    async def _six(self, interaction: Interaction, button: Button):
        await register_move(self.bot, interaction, 6, self, button)

    @button(emoji="7️⃣", style=ButtonStyle.blurple)
    async def _seven(self, interaction: Interaction, button: Button):
        await register_move(self.bot, interaction, 7, self, button)

    @button(label="Join", style=ButtonStyle.green, disabled=True)
    async def _join(self, interaction: Interaction, button: Button):
        ...

    @button(label="Leave", style=ButtonStyle.red)
    async def _leave_in_game(self, interaction: Interaction, button):
        await leave_function(self.bot, interaction, button)


class ConnectFourPreGameView(View):
    def __init__(self, bot: Botty, timeout=None):
        self.bot = bot
        super().__init__(timeout=timeout)

    @button(label="Join", style=ButtonStyle.green)
    async def _join(self, interaction: Interaction, button: Button):
        data = self.bot.cache.get_connect_four(interaction.message.id)  # type: ignore

        if not data:
            return

        if interaction.user.id == data["player1"]:
            await interaction.response.send_message(
                "You cannot join your own game.", ephemeral=True
            )
        else:
            self.bot.cache.update_connect_four(
                data["player1"],
                interaction.user.id,
                data["config"],
                interaction.message.id,  # type: ignore
            )
            button.disabled = True

            await interaction.response.edit_message(
                embed=await game_embed(
                    self.bot,
                    to_list(data["config"]),
                    data["player1"],
                    interaction.user.id,
                    f"{(await self.bot.fetch_user(data['player1'])).name}'s turn!",
                ),
                view=ConnectFourGameView(self.bot),
            )

    @button(label="Leave", style=ButtonStyle.red)
    async def _leave(self, interaction: Interaction, button):
        await leave_function(self.bot, interaction, button)


class ConnectFour(commands.Cog):
    def __init__(self, bot: Botty) -> None:
        self.bot = bot
        super().__init__()

    async def cog_check(self, ctx: commands.Context) -> bool:
        if isinstance(ctx.channel, DMChannel) or ctx.author.bot:
            return False
        return ctx.channel.id in self.bot.cache.get_channel_id(
            ctx.guild.id, "connectfour"
        )

    @commands.command(aliases=["connect-four", "cf", "c4", "ConnectFour"])
    async def connect_four(self, ctx: commands.Context):
        """
        Start a game of ConnectFour, shorter: c4
        """
        msg = await ctx.send(
            embed=await game_embed(
                self.bot,
                to_list(DEFAULT_CONFIG),
                ctx.author.id,
                self.bot.user.id,
                "Ask someone to join you!",
            ),
            view=ConnectFourPreGameView(self.bot),
        )

        self.bot.cache.update_connect_four(
            ctx.author.id, self.bot.user.id, DEFAULT_CONFIG, msg.id
        )

        data = self.bot.cache.get_connect_four(msg.id)
        if data:
            await check_inactive(self.bot, data, msg, 120)
        else:
            await ctx.send("An error occurred, please try again \U0001f622")


async def setup(bot: Botty):
    await bot.add_cog(ConnectFour(bot))
