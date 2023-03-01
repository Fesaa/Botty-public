from typing import (
    TypedDict,
    Optional,
    List
)

class _ConfigDiscordDefaults(TypedDict):
    DEFAULT_LB_SIZE: int
    DEFAULT_CHANNEL: str
    DEFAULT_MAX_REPLY: int
    DEFAULT_WS_GUESSES: int
    DEFAULT_HL_MAX_NUMBER: int

class _DiscordWebhook(TypedDict):
    TOKEN: str
    ID: int


class _ConfigDiscord(TypedDict):
    TOKEN: str
    APPLICATION_ID: int
    DEFAULT_PREFIX: str
    DEFAULTS: _ConfigDiscordDefaults
    WEBHOOK: _DiscordWebhook


class _ConfigServerPostgreSQL(TypedDict):
    host: str
    database: str
    user: str
    password: str


class _ConfigServer(TypedDict):
    POSTGRESQL: _ConfigServerPostgreSQL


class _Botty(TypedDict):
    COLOUR: Optional[int]
    OWNER_IDS: List[int]


class Config(TypedDict):
    DISCORD: _ConfigDiscord
    SERVER: _ConfigServer
    BOTTY: _Botty
