from typing import (
    TypedDict,
    Optional,
    List,
    Dict
)

from utils.ConnectFourGame import ConnectFourGame


class SettingsDict(TypedDict):
    max_lb_size: Optional[int]
    hl_max_reply: Optional[int]
    ws_wrong_guesses: Optional[int]
    hl_max_number: Optional[int]


class BottyCache:
    def __init__(self) -> None:
        self.command_prefix: Dict[int, str] = {}
        self.channel_id: Dict[
            int, Dict[str, List[Optional[int]]]
        ] = {}
        self.game_setting: Dict[int, SettingsDict] = {}
        self.connect_four: Dict[int, ConnectFourGame] = {}

    def get_command_prefix(self, guild_id: int) -> str:
        return self.command_prefix.get(guild_id, "!")

    def update_command_prefix(self, guild_id: int, command_prefix: str) -> None:
        self.command_prefix[guild_id] = command_prefix

    def get_channel_id(
        self, guild_id: int, channel_type: str
    ) -> list[Optional[int]]:
        if self.channel_id.get(guild_id, None):
            return self.channel_id[guild_id].get(channel_type, [])

        self.channel_id[guild_id] = {}
        return []

    def get_all_used_channels(self, guild_id: int) -> list[Optional[int]]:
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
    
    def check_channel_game(self, guild_id: int, channel_id: int) -> List[Optional[str]]:
        if self.channel_id.get(guild_id, None):
            out: List[Optional[str]] = []
            for game_type, channels in self.channel_id[guild_id].items():
                if channel_id in channels and game_type != 'cubelvl':
                    out.append(game_type)
            return out
        return []

    def get_game_settings(self, guild_id: int, game_setting: str) -> Optional[int]:
        if self.game_setting.get(guild_id, None):
            return self.game_setting[guild_id].get(game_setting, None)  # type: ignore

        self.game_setting[guild_id] = {}  # type: ignore
        return None

    def get_all_games_settings(self, guild_id: int) -> Optional[SettingsDict]:
        return self.game_setting.get(guild_id, None)

    def update_game_settings(
        self, guild_id: int, game_setting: str, setting: int
    ) -> None:
        if self.game_setting.get(guild_id, None):
            self.game_setting[guild_id][game_setting] = setting  # type: ignore
            return

        self.game_setting[guild_id] = {}  # type: ignore
        self.game_setting[guild_id][game_setting] = setting  # type: ignore

    def add_connect_four(self, msg_id: int, game: ConnectFourGame) -> None:
        self.connect_four[msg_id] = game

    def get_connect_four(self, msg_id: int) -> Optional[ConnectFourGame]:
        return self.connect_four.get(msg_id, None)

    def remove_connect_four(self, msg_id: int) -> None:
        self.connect_four.pop(msg_id, None)