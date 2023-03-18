from typing import (
    Optional,
    TYPE_CHECKING
)

if TYPE_CHECKING:
    from discord.ext import commands

    from Botty import Botty
    from framework.BaseGame import BaseGame
    from framework.enums import Game, Update, DebugRequest, GameSetting


class GameChannelUpdateEvent:

    def __init__(self, game: 'Game', update_type: 'Update', ctx: 'commands.Context[Botty]', *channels: int) -> None:
        self.game = game
        self.update_type = update_type
        self.channels = channels
        self.ctx = ctx

class GameConfigUpdateEvent:

    def __init__(self, setting: 'GameSetting', ctx: 'commands.Context[Botty]', value: int, *channels: int):
        self.setting = setting
        self.ctx = ctx
        self.new_value = value
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
