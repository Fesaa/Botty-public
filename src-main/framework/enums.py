from enum import Enum


class Game(Enum):
    WORDSNAKE = "wordsnake"
    NTBPL = "ntbpl"
    HIGHERLOWER = "higherlower"
    HANGMAN = "hangman"
    CONNECTFOUR = "connectfour"


class Update(Enum):
    REMOVE: 0
    ADD: 1


class DebugRequest(Enum):
    CHANNELS: 0
    GAMEINFO: 0

