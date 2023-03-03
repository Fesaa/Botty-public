from enum import Enum


class Game(Enum):
    WORDSNAKE = "wordsnake"
    NTBPL = "ntbpl"
    HIGHERLOWER = "higherlower"
    HANGMAN = "hangman"
    CONNECTFOUR = "connectfour"

class Update(Enum):
    ADD: 1
    REMOVE: 0