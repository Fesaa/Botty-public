import json
import typing
import discord

from discord.app_commands import locale_str, TranslationContextTypes


class BottyTranslator(discord.app_commands.Translator):

    def __init__(self) -> None:
        super().__init__()
        self.f = open("utils/translations.json", "r+")
        self.translations = json.load(self.f)


    async def translate(self, string: locale_str, locale: discord.Locale, context: TranslationContextTypes) -> typing.Optional[str]:
        location = context.location.name

        if locale_translation := self.translations.get(locale.name, None):
            if location_translations := locale_translation.get(location, None):
                return location_translations.get(string.message, None)

        return None
    
    def close(self) -> None:
        self.f.close()
