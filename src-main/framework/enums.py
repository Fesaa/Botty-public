from enum import Enum

import discord

class Game(Enum):
    WORDSNAKE = "wordsnake"
    NTBPL = "ntbpl"
    HIGHERLOWER = "higherlower"
    HANGMAN = "hangman"
    CONNECTFOUR = "connectfour"

class GameSetting(Enum):
    HL_MAX_NUMBER = "hl_max_number"
    HL_MAX_REPLY = "hl_max_reply"
    WS_WRONG_GUESSES = "ws_wrong_guesses"
    MAX_LB_SIZE = "max_lb_size"

    def pretty(self):
        return {
            "hl_max_number": "HigherLower max Number",
            "hl_max_reply": "HigherLower max uninterrupted guesses",
            "ws_wrong_guesses": "WordSnake max previous word matching guesses",
            "max_lb_size": "Max size of the scoreboard"
        }[self.value]


class Update(Enum):
    REMOVE = 0
    ADD = 1


class DebugRequest(Enum):
    CHANNELS = 0
    GAMEINFO = 1


CHANNEL_TYPES_CHOICE = [
        discord.app_commands.Choice(name="WordSnake", value=Game.WORDSNAKE.value),
        discord.app_commands.Choice(name="NTBPL", value=Game.NTBPL.value),
        discord.app_commands.Choice(name="HigherLower", value=Game.HIGHERLOWER.value),
        discord.app_commands.Choice(name="ConnectFour", value=Game.CONNECTFOUR.value),
        discord.app_commands.Choice(name="HangMan", value=Game.HANGMAN.value),
        discord.app_commands.Choice(name="CubeLvl", value="cubelvl"),
    ]
