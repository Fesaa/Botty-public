import asyncio
from typing import (
    Optional,
    Any,
    Iterable
)

import asyncpg

from Botty import Botty
from framework.enums import Game, Update
from framework.GameEvents import GameUpdateEvent


class BaseGame:

    def __init__(self,
                 game: Game,
                 bot: Botty,
                 channel_id: int,
                 guild_id: int,
                 current_player: int,
                 players: Optional[list[int]],
                 *,
                 snowflake: int = None
                 ) -> None:

        self.game = game
        self.bot = bot

        self.snowflake = snowflake or channel_id
        self.channel_id = channel_id
        self.guild_id = guild_id

        self.current_player = current_player
        self.players = players if players else [current_player]

    def debug_string(self, **extra) -> str:
        """Base debug string. Should be overwritten;

        def debug_string(self) -> str:
            return super().debug_string(#all the new stuff)
        """
        return '{' + \
            f'game: {self.game}, guild: {self.guild_id}, snowflake: {self.snowflake}, channel: {self.channel_id}, current_player: {self.current_player}, players: {", ".join(map(str, self.players))}, ' + \
            ", ".join(f"{key}: {value}" for key, value in extra.items()) + \
            '}'

    async def check_inactive(self, time_out: int, *args, **kwargs):
        snapshot = self.debug_string()
        await asyncio.sleep(time_out)
        if snapshot == self.debug_string():
            self.game_end()
            await self.graceful_shutdown(*args, **kwargs)

    async def graceful_shutdown(self, *args, **kwargs):
        """
        Implement as custom response to a failed check_inactive
        """
        ...

    def is_playing(self, player: int) -> bool:
        return player in self.players

    def next_player(self) -> int:
        """
        :return: the id of the next players, and updates the `current_player` var to that value
        :rtype: int
        """
        next_player: int = self.players[(self.players.index(self.current_player) + 1) % len(self.players)]
        self.current_player = next_player
        return next_player

    def add_player(self, player: int):
        if player not in self.players:
            self.players.append(player)

    def remove_player(self, *args) -> Any:
        """ 
        Should be implemented per game to allow for game specific end logic if the last player leaves
        """
        ...

    async def grand_some(self, score: int, *players: int):
        await self._grand_points(players, score)

    async def grand_everyone(self, score: int):
        await self._grand_points(self.players, score)

    async def grand_current_player(self, score: int):
        await self._grand_points([self.current_player], score)

    async def _grand_points(self, players: Iterable[int], score: int):
        query: str = \
            f"""
        INSERT INTO leaderboards
            (game, user_id, score, channel_id, guild_id)
        VALUES
            {", ".join(f'($1, {player}, 1, $2, $3)' for player in players)}
        ON CONFLICT 
            (game, user_id, channel_id)
        DO UPDATE SET
            score = leaderboards.score + $4;
        """
        async with self.bot.pool.acquire() as con:
            con: asyncpg.connection.Connection  # type: ignore
            async with con.transaction():
                await con.execute(query, self.game.value, self.channel_id, self.guild_id, score)

    def game_start(self):
        self.bot.dispatch("game_update", GameUpdateEvent(self.game, Update.ADD, self))

    def game_end(self):
        self.bot.dispatch("game_update", GameUpdateEvent(self.game, Update.REMOVE, self))
