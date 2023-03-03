from framework.enums import *


class GameChannelUpdateEvent:

    def __init__(self, game: Game, type: Update) -> None:
        self.game = game
        self.update_type = type