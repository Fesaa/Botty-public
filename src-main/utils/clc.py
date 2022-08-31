from math import sqrt


class Cubelvl:
    def __init__(self, level):
        self.level = level
        self.xp = 900 * (level - 1) + 100 * (level - 1) ** 2

    def __str__(self):
        return str(self.level)

    def __call__(self):
        return self.xp

    def win(self, mode):
        if mode == "ew":
            return round(self.xp / 250)
        if mode == "sw":
            return round(self.xp / 125)
        if mode == "li":
            return round(self.xp / 120)
        if mode == "mt":
            return round(self.xp / 100)

    def levelafterxp(self, gainedxp):
        return round(-9 / 2 + sqrt(81 / 4 + (self.xp + gainedxp) / 100) + 1)


def lvlxp(x):  # xp = total xp => level
    return round(-9 / 2 + 1 / 10 * sqrt(2025 + x) + 1)


def xpm(
    amountthanks, amountmulti
):  # xp gained from amountmulti multipliers, amountthanks = #thanks
    return round(amountmulti * amountthanks * 100)


def m(
    xp, amountthank
):  # Amount of multipliers needed for a certain amount of xp with amountthank /thanks
    return round(xp / (100 * amountthank))
