from re import match
import typing
from enchant import Dict
from datetime import datetime
from random import choice, randint
from difflib import SequenceMatcher


d = Dict("en_GB")


def similar(str1, str2):
    return SequenceMatcher(None, str1, str2).ratio()


def check(word):
    return d.check(word.lower()) or d.check(word)


def allowed_word(word: str) -> bool:
    if word:
        return match(r"^[a-zA-Z]+$", word.lower()) and check(word) and len(word) >= 2  # type: ignore
    else:
        return False


def get_word() -> typing.List[typing.List[str]]:
    with open("utils/words.txt", "r") as f:
        return [(line.strip()).split() for line in f]


def time() -> str:
    return str(datetime.now().strftime("%d/%m/%y %H:%M:%S"))


async def get_NTBPL_letters(bot, count: int, channel_id: int) -> str:
    while True:
        word = choice(get_word())[0]
        if d.check(word):
            if not (await bot.PostgreSQL.check_used_word("ntbpl", channel_id, word)):
                if match(r"^[a-zA-Z]+$", word.lower()):
                    if len(word) > count + 2:
                        break
    print(time() + " A possible solution to the current letters is: " + word)
    spil = randint(1, len(word) - count - 1)
    return word[spil : spil + count]


def get_HangMan_word() -> str:

    while True:
        word = choice(get_word())[0]
        if 5 <= len(word) <= 19 and d.check(word):
            break

    return word
