from typing import (
    Optional,
    TYPE_CHECKING
)

if TYPE_CHECKING:
    from discord.ext import commands

    from framework.BaseGame import BaseGame
    from framework.enums import Game, Update, DebugRequest


class GameChannelUpdateEvent:

    def __init__(self, game: 'Game', update_type: 'Update', channels: list[int]) -> None:
        self.game = game
        self.update_type = update_type
        self.channels = channels


class GameDebugEvent:

    def __init__(self, ctx: 'commands.Context', game: 'Game', debug_type: 'DebugRequest', *, snowflake: Optional[int]):
        self.game = game
        self.debug_type = debug_type
        self.snowflake = snowflake
        self.ctx = ctx

class GameUpdateEvent:

    def __init__(self, game: 'Game', update_type: 'Update', game_data: 'BaseGame') -> None:
        self.game = game
        self.update_type = update_type
        self.game_data = game_data
