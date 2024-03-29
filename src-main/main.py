import logging.handlers
import logging 
import os
import pathlib
import sys

import discord

os.chdir(os.path.dirname(os.path.abspath(__file__)))

from Botty import Botty


logger = logging.getLogger("discord")
logger.setLevel(logging.INFO)
logging.getLogger("discord.http").setLevel(logging.INFO)

handler = logging.handlers.RotatingFileHandler(
    filename=pathlib.Path("./_logs/") / "discord.log",
    encoding="utf-8",
    maxBytes=32 * 1024 * 1024,  # 32 MiB
    backupCount=5,  # Rotate through 5 files
)
dt_fmt = "%Y-%m-%d %H:%M:%S"
formatter = logging.Formatter(
    "[{asctime}] [{levelname:<8}] {name}: {message}", dt_fmt, style="{"
)
handler.setFormatter(formatter)

stream = logging.StreamHandler()
stream.setFormatter(formatter)

logger.addHandler(handler)
logger.addHandler(stream)

bottyLogger = logging.getLogger("botty")
bottyLogger.setLevel(logging.INFO)
bottyLogger.addHandler(stream)

def main():
    bot = Botty()
    try:
        bot.run(log_handler=None)
    except discord.LoginFailure:
        logging.error("Invalid token", file=sys.stderr)


if __name__ == "__main__":
    main()
