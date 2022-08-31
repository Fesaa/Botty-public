import typing

from datetime import datetime

from utils.functions import similar


class HangManDict(typing.TypedDict):
    word: str
    used_letters: str
    user_id: int
    players: str
    msg_id: int
    start_time: datetime


class BottyCache:
    def __init__(self) -> None:
        self.command_prefix: typing.Dict[int, str] = {}
        self.channel_id: typing.Dict[
            int, typing.Dict[str, typing.List[typing.Optional[int]]]
        ] = {}
        self.game_setting: typing.Dict[int, typing.Dict[str, typing.Optional[int]]] = {}
        self.connect_four: typing.Dict[int, dict] = {}
        self.hangman: typing.Dict[int, HangManDict] = {}
        self.higherlower: typing.Dict[int, dict] = {}
        self.tag: typing.Dict[int, typing.List[dict]] = {}
        pass

    def get_command_prefix(self, guild_id: int) -> str:
        return self.command_prefix.get(guild_id, "!")

    def update_command_prefix(self, guild_id: int, command_prefix: str) -> None:
        self.command_prefix[guild_id] = command_prefix

    def get_channel_id(
        self, guild_id: int, channel_type: str
    ) -> list[typing.Optional[int]]:
        if self.channel_id.get(guild_id, None):
            return self.channel_id[guild_id].get(channel_type, [])

        self.channel_id[guild_id] = {}
        return []

    def get_all_used_channels(self, guild_id: int) -> list[typing.Optional[int]]:
        if self.channel_id.get(guild_id, None):
            out = []
            for channels in self.channel_id[guild_id].values():
                out += channels
            return out

        self.channel_id[guild_id] = {}
        return []

    def update_channel_id(self, guild_id: int, channel_type: str, l: list[int]) -> None:
        if self.channel_id.get(guild_id, None):
            self.channel_id[guild_id][channel_type] = [int(i) for i in l]
            return

        self.channel_id[guild_id] = {}
        self.channel_id[guild_id][channel_type] = [int(i) for i in l]
    
    def check_channel_game(self, guild_id: int, channel_id: int) -> typing.List[typing.Optional[str]]:
        if self.channel_id.get(guild_id, None):
            out: typing.List[typing.Optional[str]] = []
            for game_type, channels in self.channel_id[guild_id].items():
                if channel_id in channels and game_type != 'cubelvl':
                    out.append(game_type)
            return out
        return []

    def get_game_settings(
        self, guild_id: int, game_setting: str
    ) -> typing.Optional[int]:
        if self.game_setting.get(guild_id, None):
            return self.game_setting[guild_id].get(game_setting, None)

        self.game_setting[guild_id] = {}
        return None

    def update_game_settings(
        self, guild_id: int, game_setting: str, setting: int
    ) -> None:
        if self.game_setting.get(guild_id, None):
            self.game_setting[guild_id][game_setting] = setting
            return

        self.game_setting[guild_id] = {}
        self.game_setting[guild_id][game_setting] = setting

    def get_connect_four(self, msg_id: int) -> typing.Optional[dict]:
        return self.connect_four.get(msg_id, None)

    def update_connect_four(
        self, player1: int, player2: int, config: str, msg_id: int
    ) -> None:
        self.connect_four[msg_id] = {
            "player1": player1,
            "player2": player2,
            "config": config,
            "msg_id": msg_id,
        }

    def remove_connect_four(self, msg_id: int) -> None:
        self.connect_four.pop(msg_id, None)

    def get_hangman(self, msg_id: int) -> typing.Optional[HangManDict]:
        return self.hangman.get(msg_id, None)

    def update_hangman(
        self, word: str, used_letters: str, user_id: int, players: str, msg_id: int, start_time: datetime
    ) -> typing.Optional[HangManDict]:
        self.hangman[msg_id] = {
            "word": word,
            "used_letters": used_letters,
            "user_id": user_id,
            "players": players,
            "msg_id": msg_id,
            "start_time": start_time
        }
        return self.hangman[msg_id]

    def remove_hangman(self, msg_id: int) -> None:
        self.hangman.pop(msg_id, None)

    def get_higherlower(self, channel_id: int) -> typing.Optional[dict]:
        return self.higherlower.get(channel_id, None)

    def update_higherlower(
        self, count: int, number: int, last_user_id: int, channel_id: int
    ) -> dict:
        self.higherlower[channel_id] = {
            "count": count,
            "number": number,
            "last_user_id": last_user_id,
            "channel_id": channel_id,
        }
        return self.higherlower[channel_id]

    def add_tag(self, guild_id: int, tag: str, owner_id: int) -> None:
        if self.tag.get(guild_id, None):
            return (self.tag[guild_id]).append({"tag": tag, "owner_id": owner_id})

        self.tag[guild_id] = [{"tag": tag, "owner_id": owner_id}]

    def remove_tag(self, guild_id: int, tag: str) -> None:
        if self.tag.get(guild_id, None):
            self.tag[guild_id] = [
                tag_info for tag_info in self.tag[guild_id] if tag_info["tag"] != tag
            ]
            return

    def check_tag(
        self, guild_id: int, tag: str, owner_id: int
    ) -> typing.Tuple[bool, bool]:
        if self.tag.get(guild_id, None):
            return (
                tag in [tag_info["tag"] for tag_info in self.tag[guild_id]],
                any(
                    [
                        tag_info
                        for tag_info in self.tag[guild_id]
                        if tag_info["tag"] == tag and tag_info["owner_id"] == owner_id
                    ]
                ),
            )
        return (False, False)

    def get_tag_suggestions(self, tag: str, guild_id: int = 000000000000000000) -> list:
        if self.tag.get(guild_id, None):
            return [
                t
                for t in [info["tag"] for info in self.tag[guild_id]]
                if similar(tag.lower(), t.lower()) > 0.5
            ]
        return []

    def __str__(self) -> str:
        return (
            "Channel Ids: \n"
            + str(self.channel_id)
            + "\nCommand Prefixes: \n"
            + str(self.command_prefix)
            + "\nGame Settings: \n"
            + str(self.game_setting)
            + "\nConnect Four: \n"
            + str(self.connect_four)
            + "\nHangMan: \n"
            + str(self.hangman)
            + "\nHigherLower: \n"
            + str(self.higherlower)
            + "\nTags: \n"
            + str(self.tag)
        )
