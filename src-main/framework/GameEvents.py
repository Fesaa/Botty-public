from typing import (
    Optional
)

from discord.ext import commands

from framework.enums import *


class GameChannelUpdateEvent:

    def __init__(self, game: Game, update_type: Update, channels: list[int]) -> None:
        self.game = game
        self.update_type = update_type
        self.channels = channels


class GameDebugEvent:

    def __init__(self, ctx: commands.Context, game: Game, debug_type: DebugRequest, *, channel: Optional[int]):
        self.game = game
        self.debug_type = debug_type
        self.channel = channel
        self.ctx = ctx
