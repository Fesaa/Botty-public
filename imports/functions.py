import datetime
import enchant
import re

d = enchant.Dict('en_GB')


def check(word):
    if d.check(word.lower()) or d.check(word):
        return True
    else:
        return False


def allowed_word(word):
    if re.match(r"^[a-zA-Z]+$", word.lower()) and check(word) and len(word) >= 2:
        return True
    else:
        return False


def time():
    return str(datetime.datetime.now().strftime("%d/%m/%y -- %H:%M:%S"))


def get_word():
    with open("imports/words.txt", "r") as f:
        return [(line.strip()).split() for line in f]
