from discord.ext import commands
from discord import ButtonStyle, Embed, Interaction, Message
from discord.ui import View, button, Button
from asyncio import sleep
from collections import Counter


DEFAULT_CONFIG = '0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0'
EMOJI_DICT = {'0': '⚪', '1': '🟡', '2': '🔴'}
COLOUR_DICT = {'yellow': '1', 'red': '2'}

class RowFull(Exception):
    pass


def to_list(game_config: str) -> list:
    if game_config[-1] == ',':
        config_list = game_config[:-1].split(',')
    else:
        config_list = game_config.split(',')
    return config_list

def to_str(config_list: list) -> str:
    game_config = ""
    for info in config_list:
        game_config += info + ","
    return game_config[:-1]

def to_msg(config_list: list) -> str:
    to_send = ''
    for index in range(len(config_list)):
        if index % 7 != 0:
            to_send += (EMOJI_DICT[config_list[index]])
        else:
            to_send += f"🟦\n🟦" + EMOJI_DICT[config_list[index]]

    return to_send.removeprefix('🟦') + '🟦'

def apply_move(config_list: list, row: int, colour: str) -> list:
    init_config = config_list[::]

    if row == 7:
        row = 0

    for index in [len(config_list) - 1 - i for i in range(len(config_list))]:
        if (index + 1) % 7 == row and config_list[index] == '0':
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
            if config_list[index + 1] == config_list[index + 2] == config_list[index + 3] == check_for:
                return True

        # Diagonal lines up
        if ((index + 1) % 7 >= 4 or (index + 1) % 7 == 0) and config_list[index] == check_for and index <= 21:
            if config_list[index + 6] == config_list[index + 12] == config_list[index + 18] == check_for:
                return True

        # Diagonal lines down
        if ((0 < (index + 1) % 7 <= 4) and index < 21) and config_list[index] == check_for:
            if config_list[index + 8] == config_list[index + 16] == config_list[index + 24] == check_for:
                return True

        # Straight lines veritcal
        if (index < 21) and config_list[index] == check_for:
            if config_list[index + 7] == config_list[index + 14] == config_list[index + 21] == check_for:
                return True
    return False

async def check_inactive(bot: commands.Bot, current_data: dict, msg: Message, time_out: int) -> None:
    await sleep(time_out)
    if current_data == bot.db.get_ConnectFour_data(msg.id):
        bot.db.ConnectFour_game_switch(msg.id, False)

        await msg.edit(embed=Embed(title="Failed game", description=f"Ended game due to inactivity (2min).", color=0xad3998 ), view=View())

async def game_embed(bot: commands.bot, config: list, p1: int, p2: int, footer_text: str) -> Embed:
        embed = Embed(title=" 🟡 Connect four 🔴", colour=0xad3998)
        embed.add_field(
            name=f"Game of: {(await bot.fetch_user(p1)).name} - {(await bot.fetch_user(p2)).name}", value=to_msg(config))
        embed.set_footer(text=footer_text)
        return embed

async def leave_function(bot: commands.bot, interaction: Interaction, button: Button):
    data = bot.db.get_ConnectFour_data(interaction.message.id)
    bot.db.ConnectFour_game_switch(interaction.message.id, False)

    if data['player2'] == bot.user.id:
        await interaction.message.delete()
        await interaction.response.send_message('Stopped your game', ephemeral=True)
    else:

        players = [data['player1'], data['player2']]
        players.remove(interaction.user.id)
        winner = players[0]

        bot.db.update_lb('ConnectFour', interaction.channel_id, winner)

        await interaction.response.edit_message(embed=await game_embed(bot, to_list(data['config']), data['player1'], data['player2'],
                                                                        f"{(await bot.fetch_user(winner)).name} won the game!"\
                                                                        f" Since {(await bot.fetch_user(interaction.user.id)).name} left." ), view=View())

async def register_move(bot: commands.bot, interaction: Interaction, row: int, view: View, button: Button):
    data = bot.db.get_ConnectFour_data(interaction.message.id)

    made_moves = Counter(to_list(data['config']))['1'] + Counter(to_list(data['config']))['2']

    colour = {
        0: 'yellow',
        1: 'red'
    }[made_moves % 2]

    if (made_moves % 2 == 0 and interaction.user.id == data['player1']) or (made_moves % 2 == 1 and interaction.user.id == data['player2']):

        if made_moves < 42:

            config = apply_move(to_list(data['config']), row, colour)

            try:
                temp = config[::]
                apply_move(temp, row, colour)
            except RowFull:
                button.disabled = True


            if check_win_state(config, colour):
                await interaction.response.edit_message(embed=await game_embed(bot, config, data['player1'], data['player2'],
                                                                            f"{(await bot.fetch_user(interaction.user.id)).name} won the game!" ), view=View())
                
                bot.db.ConnectFour_game_switch(interaction.message.id, False)
                bot.db.update_lb('ConnectFour', interaction.channel_id, interaction.user.id)
            else:

                players = [data['player1'], data['player2']]
                players.remove(interaction.user.id)
                turn = players[0]

                await interaction.response.edit_message(embed=await game_embed(bot, config, data['player1'], data['player2'],
                                                                            f"{(await bot.fetch_user(turn)).name}'s turn!" ), view=view)
                bot.db.update_ConnectFour_data(interaction.message.id, data['player1'], data['player2'], to_str(config))

                await check_inactive(bot, bot.db.get_ConnectFour_data(interaction.message.id),interaction.message, 120)

        else:
            await interaction.response.edit_message(embed=await game_embed(bot, config, data['player1'], data['player2'],
                                                                            f"Games ends in a draw, all spaces are used!" ), view=View())
            bot.db.ConnectFour_game_switch(interaction.message.id, False)
    
    else:
        if interaction.user.id in [data['player1'], data['player2']]:
            await interaction.response.send_message("Wait for your turn", ephemeral=True)
        else:
            await interaction.response.send_message('You are not playing!', ephemeral=True)
    

class ConnectFourGameView(View):

    def __init__(self, bot: commands.bot, timeout=180):
        self.bot = bot
        super().__init__(timeout=timeout)
    
    @button(emoji='1️⃣', style=ButtonStyle.blurple)
    async def _one(self, interaction: Interaction, button: Button):
        await register_move(self.bot, interaction, 1, self, button)

    @button(emoji='2️⃣', style=ButtonStyle.blurple)
    async def _two(self, interaction: Interaction, button: Button):
        await register_move(self.bot, interaction, 2, self, button)

    @button(emoji='3️⃣', style=ButtonStyle.blurple)
    async def _three(self, interaction: Interaction, button: Button):
        await register_move(self.bot, interaction, 3, self, button)

    @button(emoji='4️⃣', style=ButtonStyle.blurple)
    async def _four(self, interaction: Interaction, button: Button):
        await register_move(self.bot, interaction, 4, self, button)

    @button(emoji='5️⃣', style=ButtonStyle.blurple)
    async def _five(self, interaction: Interaction, button: Button):
        await register_move(self.bot, interaction, 5, self, button)

    @button(emoji='6️⃣', style=ButtonStyle.blurple)
    async def _six(self, interaction: Interaction, button: Button):
        await register_move(self.bot, interaction, 6, self, button)

    @button(emoji='7️⃣', style=ButtonStyle.blurple)
    async def _seven(self, interaction: Interaction, button: Button):
        await register_move(self.bot, interaction, 7, self, button)
    
    @button(label='Join', style=ButtonStyle.green, disabled=True)
    async def _join(self, interaction: Interaction, button: Button):
        pass

    @button(label='Leave', style=ButtonStyle.red)
    async def _leave(self, interaction: Interaction, button):
        await leave_function(self.bot, interaction, button)
        

class ConnectFourPreGameView(View):

    def __init__(self, bot: commands.bot, timeout=180):
        self.bot = bot
        super().__init__(timeout=timeout)
    
    @button(label='Join', style=ButtonStyle.green)
    async def _join(self, interaction: Interaction, button: Button):
        data = self.bot.db.get_ConnectFour_data(interaction.message.id)

        if interaction.user.id == data['player1']:
            await interaction.response.send_message('You cannot join your own game.', ephemeral=True)
        else:
            self.bot.db.update_ConnectFour_data(interaction.message.id, data['player1'], interaction.user.id, data['config'])
            button.disabled = True

            await interaction.response.edit_message(embed=await game_embed(self.bot, to_list(data['config']), data['player1'],
                                                                        interaction.user.id, f"{(await self.bot.fetch_user(data['player1'])).name}'s turn!"),
                                                                        view=ConnectFourGameView(self.bot))

    @button(label='Leave', style=ButtonStyle.red)
    async def _leave(self, interaction: Interaction, button):
        await leave_function(self.bot, interaction, button)


class ConnectFourCog(commands.Cog):

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        super().__init__()
    
    @commands.command(aliases=['connect-four', 'cf', 'c4', 'ConnectFour'])
    async def connect_four(self, ctx: commands.Context):
        if ctx.channel.id in self.bot.db.get_channel(ctx.guild.id, 'ConnectFour'):

            msg = await ctx.send(embed=await game_embed(self.bot, to_list(DEFAULT_CONFIG), ctx.author.id, self.bot.user.id, "Ask someone to join you!"), view=ConnectFourPreGameView(self.bot))

            self.bot.db.ConnectFour_game_switch(msg.id, True)
            self.bot.db.update_ConnectFour_data(msg.id, ctx.author.id, self.bot.user.id, DEFAULT_CONFIG)

            data = self.bot.db.get_ConnectFour_data(msg.id)
            await check_inactive(self.bot, data, msg, 120)


async def setup(bot: commands.Bot):
    await bot.add_cog(ConnectFourCog(bot))