from typing import (
    Union,
    Optional,
    List
)

import discord
from discord.ext import commands

from Botty import Botty

SLOWMODE_GAMES = ("wordsnake", 'ntbpl', 'higherlower')

async def send_msg(int_ctx: Union[commands.Context, discord.Interaction], *,  msg: str, ephemeral: bool = True):
    """Send message logic that works for both commands.Context and discord.Interaction.

    :param int_ctx: ...
    :type int_ctx: Union[commands.Context, discord.Interaction]
    :param msg: The message to send
    :type msg: str
    :param ephemeral: ..., defaults to True
    :type ephemeral: bool, optional
    """
    if isinstance(int_ctx, commands.Context):
        await int_ctx.send(msg, ephemeral=ephemeral)
    elif int_ctx.response.is_done():
        await int_ctx.followup.send(msg, ephemeral=ephemeral)
    else:
        await int_ctx.response.send_message(msg, ephemeral=ephemeral)


async def update_prefix(int_ctx: Union[commands.Context, discord.Interaction], *, guild_id: int, new_prefix: str, bot: Botty):
    if not guild_id:
        return

    bot.cache.update_command_prefix(guild_id, new_prefix)
    await bot.PostgreSQL.update_prefix(guild_id, new_prefix)

    await send_msg(int_ctx, msg=f"The prefix has been updated to {new_prefix}")


async def remove_channels(int_ctx: Union[commands.Context, discord.Interaction], *, to_remove: List[int], guild_id: int, channel_type: str, bot: Botty):
    if not guild_id:
        return

    channel_list = bot.cache.get_channel_id(guild_id, channel_type)

    if not channel_list:
        return await send_msg(int_ctx, msg=f"Your selected channel type ({channel_type}) has no active channels.")

    removed_counter = 0
    removed_ids: List[Optional[int]]  = []
    for c_id in to_remove:
        if c_id in channel_list:
            channel_list.remove(c_id)
            removed_counter += 1
            removed_ids.append(c_id)

    new_channel_str = ",".join(str(i) for i in channel_list) or None
    removed_str = "\n•".join(f"<#{c_id}>" for c_id in removed_ids)

    if channel_type in SLOWMODE_GAMES:
        missing_perms = False
        for channel_id in removed_ids:
            channel = bot.get_channel(channel_id)
            if channel.permissions_for(channel.guild.me).manage_channels:
                await channel.edit(slowmode_delay=0, reason="Automated channel edit to remove the slow mode after a game has been removed.")
            elif channel.slowmode_delay != 0:
                missing_perms = True
        
        if missing_perms:
            await send_msg(int_ctx, msg="I do not have permission to disable slow mode in one or more of the selected channels."
                                        "This is a remainder to disable it yourself if needed. \U0001f603")

    bot.cache.update_channel_id(guild_id, channel_type, channel_list)  # type: ignore
    await bot.PostgreSQL.update_channel(guild_id, channel_type, new_channel_str)

    await send_msg(int_ctx, msg=f"Removed {removed_counter} channels from use for {channel_type};\n{removed_str}")


async def add_channels(int_ctx: Union[discord.Interaction, commands.Context], *, guild_id: int, channel_type: str, to_add: List[int], bot: Botty):
    if not guild_id:
        return

    channel_list = bot.cache.get_channel_id(guild_id, channel_type)

    added_counter = 0
    added_ids: List[Optional[int]] = []
    for c_id in to_add:
        if c_id not in channel_list:
            channel_list.append(c_id)
            added_counter += 1
            added_ids.append(c_id)
    
    new_channel_str = ",".join(str(i) for i in channel_list)
    added_str = "\n•".join(f"<#{c_id}>" for c_id in added_ids)

    bot.cache.update_channel_id(guild_id, channel_type, channel_list)  # type: ignore
    await bot.PostgreSQL.update_channel(guild_id, channel_type, new_channel_str)

    if channel_type in SLOWMODE_GAMES:
        missing_perms = False
        for channel_id in added_ids:
            channel = bot.get_channel(channel_id)
            if channel.permissions_for(channel.guild.me).manage_channels:
                await channel.edit(slowmode_delay=2, reason=f"Automated channel edit to prevent spam in a game of {channel_type}")
            else:
                missing_perms = True
        
        if missing_perms:
            await send_msg(int_ctx, msg="I do not have permission to enable slow mode in one or more of the selected channels."
                                        "It is recommend to enable slow mode in the channels to reduce spam during the games. \U0001f603")

    await send_msg(int_ctx, msg=f"Added {added_counter} channel for use with {channel_type};\n{added_str}")


async def update_game_setting(int_ctx: Union[discord.Interaction, commands.Context], *, guild_id: int, game_setting: str, value: int, bot: Botty):
    current_value = bot.cache.get_game_settings(guild_id, game_setting)
    if game_setting == "max_lb_size" and value > 20:
        value = 20
    elif game_setting == "ws_wrong_guesses" and value > 5:
        value = 5

    updated_setting_str = {
            "max_lb_size": "maximum amount of users displayed on a leaderboard",
            "hl_max_reply": "maximum consecutive replies by the same user in HigherLower",
            "ws_wrong_guesses": "maximum amount of tolerated wrong guesses in WordSnake",
            "hl_max_number": "maximum value of the number in HigherLower",
        }[game_setting]

    bot.cache.update_game_settings(guild_id, game_setting, value)
    await bot.PostgreSQL.update_game_setting(guild_id, game_setting, value)
    
    await send_msg(int_ctx, msg=f"Updated {updated_setting_str} from {current_value} to {value}.")
