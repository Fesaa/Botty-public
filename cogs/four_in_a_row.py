import asyncio
from discord.errors import Forbidden, NotFound
from discord.ext import commands
from collections import Counter
from discord import Embed
from discord.message import Message
from cogs.config_handler import get_configdata, master_logger_id
from imports.functions import time

DEFAULT_CONFIG = '0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0'
DEFAULT_NUMBERS = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣']
MOVE_SWITCHER = {'1️⃣': '1', '2️⃣': '2', '3️⃣': '3', '4️⃣': '4', '5️⃣': '5', '6️⃣': '6', '7️⃣': '7'}
EMOJI_DICT = {'0': '⚪', '1': '🟡', '2': '🔴'}
COLOUR_DICT = {'yellow': '1', 'red': '2'}


class RowFull(Exception):
    pass


def to_list(game_config):
    if game_config[-1] == ',':
        config_list = game_config[:-1].split(',')
    else:
        config_list = game_config.split(',')
    return config_list


def to_str(config_list):
    game_config = ""
    for info in config_list:
        game_config += info + ","
    return game_config[:-1]


def to_msg(config_list):
    to_send = ''
    for index in range(len(config_list)):
        if index % 7 != 0:
            to_send += (EMOJI_DICT[config_list[index]])
        else:
            to_send += f"🟦\n🟦" + EMOJI_DICT[config_list[index]]

    return to_send.removeprefix('🟦') + '🟦'


def apply_move(config_list, row, colour):
    bconfig = config_list[::]
    for index in [len(config_list) - 1 - i for i in range(len(config_list))]:
        if row != '7':
            if (index + 1) % 7 == int(row) and config_list[index] == '0':
                config_list[index] = COLOUR_DICT[colour]
                break
        else:
            if (index + 1) % 7 == 0 and config_list[index] == '0':
                config_list[index] = COLOUR_DICT[colour]
                break
    if bconfig == config_list:
        raise RowFull
    else:
        return config_list


def check_win_state(config_list, colour):
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


async def clear_rec(msg: Message):
    await msg.clear_reactions()


class four_in_a_row(commands.Cog):

    def __init__(self, client):
        self.client = client

    def embed_logger(self, txt_log, channel_id, error_type=None):
        if error_type == 's':
            colour = 0x1034a6
        else:
            colour = 0xad3998
        embed = Embed(title='📖 Info 📖', colour=colour)
        embed.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
        embed.add_field(name=" 🟡 Connect four 🔴", value=txt_log)
        embed.set_footer(text=f'🆔 {channel_id} ⏳' + time())
        return embed

    @commands.Cog.listener()
    async def on_ready(self):
        for guilds in self.client.guilds:  # Annouces c4 is loaded
            for channel_id in (await get_configdata(self.client, guilds.id, 'logger_ids')):
                try:
                    await self.client.get_channel(channel_id).send(
                        embed=self.embed_logger(" Connect four has been loaded.", channel_id))
                except AttributeError:
                    pass
        for channel_id in master_logger_id:
            await self.client.get_channel(channel_id).send(embed=self.embed_logger(" Connect four has been loaded.",
                                                                                   channel_id)
                                                   )

    async def game_embed(self, msg, p1_id, p2_id, footer_text):
        embed = Embed(title=" 🟡 Connect four 🔴", colour=0xad3998)
        embed.add_field(
            name=f"Game of: {(await self.client.fetch_user(p1_id)).name} - "
                 f"{(await self.client.fetch_user(p2_id)).name}", value=msg)
        embed.set_footer(text=footer_text)
        return embed

    @commands.command(aliases=['connect-four', 'cf', 'c4'])
    async def connect_four(self, ctx):
        if ctx.channel.id in (await get_configdata(self.client, ctx.guild.id, 'connect4_id')):
            await ctx.message.delete()
            if self.client.db.get_isowner4game(ctx.author.id):
                if self.client.db.get_dm_preff(ctx.author.id) == 1:
                    try:
                        await (await ctx.author.create_dm()).send(
                            'You already playing a game! Finish or stop that one first')
                    except Forbidden:
                        pass

            elif self.client.db.get_running4game(ctx.channel.id) < 4:
                start_msg = await ctx.send(
                    f'{ctx.author.name} has started a game of connect four, someone else has to react with ▶'
                    f' to join! You can stop the game by reacting with ❌.')
                await start_msg.add_reaction('▶')
                await start_msg.add_reaction('❌')
                self.client.db.update_4data(ctx.channel.id, ctx.author.id, 0, DEFAULT_CONFIG, start_msg.id)
                for channel_id in (await get_configdata(self.client, ctx.guild.id, 'logger_ids')) + master_logger_id:
                    if self.client.get_channel(channel_id) in ctx.guild.channels or channel_id in master_logger_id:
                        await self.client.get_channel(channel_id).send(
                            embed=self.embed_logger(f' {ctx.author} started a game', ctx.channel.id, 's'))
                await asyncio.sleep(60)
                try:
                    if self.client.db.get_4data(start_msg.id)[2] == 0:
                        self.client.db.delete_4game(start_msg.id)
                        await start_msg.delete()
                        await ctx.send(
                            f"{ctx.author.mention} no one joined after 60 seconds,"
                            f" I stopped your request to safe server space.")
                except TypeError:
                    pass
            else:
                await ctx.send('Three games are already running in this channel, wait until one ends.')

    @commands.Cog.listener()
    async def on_reaction_add(self, rec, user):
        if rec.message.channel.id in (await get_configdata(self.client, rec.message.guild.id, 'connect4_id')):
            if user == self.client.user:
                pass
            elif str(rec) == '▶':
                data = self.client.db.get_4data(rec.message.id)
                if data is None:
                    pass
                elif data[1] != user.id:
                    await (await rec.message.channel.fetch_message(data[4])).delete()
                    new_game_msg = await rec.message.channel.send(embed=(await self.game_embed(to_msg(to_list(data[3])),
                                                                                               data[1], user.id,
                                                                                               "Yellow's turn!")))
                    await rec.message.channel.send(f"<@{data[1]}> and <@{user.id}> your connect four game has started!")
                    self.client.db.update_4data(rec.message.channel.id, data[1], user.id, DEFAULT_CONFIG,
                                                new_game_msg.id)
                    for emoji in DEFAULT_NUMBERS:
                        try:
                            await new_game_msg.add_reaction(emoji)
                        except NotFound:
                            pass
                    data = self.client.db.get_4data(new_game_msg.id)
                    await asyncio.sleep(120)
                    if data == self.client.db.get_4data(new_game_msg.id):
                        self.client.db.delete_4game(new_game_msg.id)
                        await new_game_msg.edit(embed=(await self.game_embed(to_msg(to_list(data[3])),
                                                                             data[1], data[2],
                                                                             "Game stopped due to inactivity.")))
                        await rec.message.channel.send(
                            f"<@{data[1]}>, <@{data[2]}> I stopped your game due to inactivity."
                            f" No one has been granted points.")

            elif str(rec) in DEFAULT_NUMBERS:
                data = self.client.db.get_4data(rec.message.id)
                if data is not None:
                    made_moves = Counter(to_list(data[3]))['1'] + Counter(to_list(data[3]))['2']
                    await rec.remove(user)
                    if made_moves % 2 == 0 and user.id == data[1]:
                        try:
                            new_game_config = apply_move(to_list(data[3]), MOVE_SWITCHER[str(rec)], 'yellow')
                            await rec.message.edit(embed=(await self.game_embed(to_msg(new_game_config),
                                                                                data[1], data[2], "Red's turn!")))
                            if check_win_state(new_game_config, 'yellow'):
                                await rec.message.edit(embed=(await self.game_embed(
                                    to_msg(new_game_config),
                                    data[1], data[2],
                                    f"Yellow, {(await self.client.fetch_user(data[1])).name},"
                                    f" won the game!")))
                                self.client.db.delete_4game(rec.message.id)
                                self.client.db.add_user_data('connect_four', data[1], rec.message.channel.id)
                                await clear_rec(rec.message)
                                for channel_id in (await get_configdata(self.client, rec.message.guild.id,
                                                                        'logger_ids')) + master_logger_id:
                                    if self.client.get_channel(
                                            channel_id) in rec.message.guild.channels or channel_id in master_logger_id:
                                        await self.client.get_channel(channel_id).send(
                                            embed=self.embed_logger(f'{user} won a game!', rec.message.channel.id, 's'))
                            else:
                                self.client.db.update_4data(rec.message.channel.id, data[1], data[2],
                                                            to_str(new_game_config), rec.message.id)
                        except RowFull:
                            await rec.message.edit(embed=(await self.game_embed(to_msg(to_list(data[3])),
                                                                                data[1], data[2],
                                                                                "That row is full,"
                                                                                " try an other row Yellow!")))
                    elif made_moves % 2 != 0 and user.id == data[2]:
                        try:
                            new_game_config = apply_move(to_list(data[3]), MOVE_SWITCHER[str(rec)], 'red')
                            await rec.message.edit(embed=(await self.game_embed(to_msg(new_game_config),
                                                                                data[1], data[2], "Yellow's turn!")))
                            if check_win_state(new_game_config, 'red'):
                                await rec.message.edit(embed=(await self.game_embed(
                                    to_msg(new_game_config),
                                    data[1], data[2],
                                    f"Red, {(await self.client.fetch_user(data[2])).name}, won the game!")))
                                self.client.db.delete_4game(rec.message.id)
                                self.client.db.add_user_data('connect_four', data[2], rec.message.channel.id)
                                await clear_rec(rec.message)
                                for channel_id in (await get_configdata(self.client, rec.message.guild.id,
                                                                        'logger_ids')) + master_logger_id:
                                    if self.client.get_channel(
                                            channel_id) in rec.message.guild.channels or channel_id in master_logger_id:
                                        await self.client.get_channel(channel_id).send(
                                            embed=self.embed_logger(f'{user} won a game!', rec.message.channel.id, 's'))
                            else:
                                self.client.db.update_4data(rec.message.channel.id, data[1], data[2],
                                                            to_str(new_game_config), rec.message.id)
                        except RowFull:
                            await rec.message.edit(embed=(await self.game_embed(to_msg(to_list(data[3])),
                                                                                data[1], data[2],
                                                                                "That row is full, try an other row "
                                                                                "Red!")))
                    if made_moves == 42:
                        self.client.db.delete_4game(rec.message.id)
                        await rec.message.edit(embed=(await self.game_embed(to_msg(to_list(data[3])),
                                                                            data[1], data[2],
                                                                            "Draw, all spaces are uses.")))
                data = self.client.db.get_4data(rec.message.id)
                await asyncio.sleep(120)
                if data == self.client.db.get_4data(rec.message.id):
                    self.client.db.delete_4game(rec.message.id)
                    await rec.message.edit(embed=(await self.game_embed(to_msg(to_list(data[3])),
                                                                        data[1], data[2],
                                                                        "Game stopped due to inactivity.")))
                    made_moves = Counter(to_list(data[3]))['1'] + Counter(to_list(data[3]))['2']
                    if made_moves <= 21:
                        await rec.message.channel.send(
                            f"<@{data[1]}>, <@{data[2]}> I stopped your game due to inactivity. No one has been "
                            f"granted points.")
                    else:
                        if made_moves % 2 == 0:
                            self.client.db.add_user_data('connect_four', data[2], rec.message.channel.id)
                            await rec.message.channel.send(
                                f"<@{data[1]}>, <@{data[2]}> I stopped your game due to inactivity. <@{data[2]}> "
                                f"received the point.")
                        else:
                            self.client.db.add_user_data('connect_four', data[1], rec.message.channel.id)
                        await rec.message.channel.send(
                            f"<@{data[1]}>, <@{data[2]}> I stopped your game due to inactivity. <@{data[1]}> received "
                            f"the point.")
                    await clear_rec(rec.message)
            elif str(rec) == '❌':
                data = self.client.db.get_4data(rec.message.id)
                if data is not None:
                    if data[1] == user.id or data[2] == user.id:
                        await clear_rec(rec.message)
                        self.client.db.delete_4game(rec.message.id)
                        made_moves = Counter(to_list(data[3]))['1'] + Counter(to_list(data[3]))['2']
                        if made_moves >= 21:
                            await rec.message.channel.send(
                                f'{user.name} ended the game after more than 20 moves. Their opponent has been '
                                f'granted a star in return!')
                            if data[1] == user.id:
                                self.client.db.add_user_data('connect_four', data[2], rec.message.channel.id)
                            else:
                                self.client.db.add_user_data('connect_four', data[1], rec.message.channel.id)
                        else:
                            await rec.message.channel.send(
                                f'{user.name} ended the game after less than 21 moves. No one has been granted a star '
                                f'for this game.')
                        for channel_id in (await get_configdata(self.client, rec.message.guild.id,
                                                                'logger_ids')) + master_logger_id:
                            if self.client.get_channel(
                                    id) in rec.message.guild.channels or channel_id in master_logger_id:
                                await self.client.get_channel(channel_id).send(
                                    embed=self.embed_logger(f'{user} ended the game!', rec.message.channel.id, 's'))


def setup(client):
    client.add_cog(four_in_a_row(client))
