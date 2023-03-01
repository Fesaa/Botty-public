import typing
import asyncpg


class PostgreSQL:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self.pool = pool

    # ========================================================================================
    # Config

    async def init_guild(
        self,
        guild_id: int,
        command_prefix: str,
        max_lb_size: int,
        HL_max_reply: int,
        WS_wrong_guesses: int,
        HL_max_number: int,
    ) -> None:
        async with self.pool.acquire() as con:
            con: asyncpg.connection.Connection  # type: ignore
            async with con.transaction():
                query_one = "INSERT INTO game_settings (guild_id, max_lb_size, HL_max_reply, WS_wrong_guesses, HL_max_number) VALUES ($1, $2, $3, $4, $5);"
                await con.execute(
                    query_one,
                    guild_id,
                    max_lb_size,
                    HL_max_reply,
                    WS_wrong_guesses,
                    HL_max_number,
                )
                query_two = "INSERT INTO channel_ids (guild_id) VALUES ($1)"
                await con.execute(query_two, guild_id)
                query_three = "INSERT INTO command_prefix (guild_id, command_prefix) VALUES ($1, $2);"
                await con.execute(query_three, guild_id, command_prefix)

    async def remove_guild(self, guild_id: int):
        async with self.pool.acquire() as con:
            con: asyncpg.connection.Connection  # type: ignore
            async with con.transaction():
                ntbpl_channels = await self.get_channel(guild_id, "ntbpl")
                ws_channels = await self.get_channel(guild_id, "wordsnake")
                query = "DELETE FROM game_settings WHERE guild_id = $1; DELETE FROM channel_ids WHERE guild_id = $1; DELETE FROM command_prefix WHERE guild_id = $1; DELETE FROM stats WHERE guild_id = $1; DELETE FROM tag WHERE guild_id = $1;"
                await con.execute(query, guild_id)
                for c_id in ntbpl_channels:
                    query = "DELETE FROM ntbpl_game_data WHERE channel_id = $1; DELETE FROM usedwords WHERE channel_id = $1;"
                    await con.execute(query, c_id)
                for c_id in ws_channels:
                    query = "DELETE FROM wordsnake_game_data WHERE channel_id = $1; DELETE FROM usedwords WHERE channel_id = $1;"
                    await con.execute(query, c_id)

    # ========================================================================================
    # Prefix

    async def get_prefix(self, guild_id: int) -> typing.Optional[str]:
        async with self.pool.acquire() as con:
            con: asyncpg.connection.Connection  # type: ignore
            row = await con.fetchrow(
                "SELECT * FROM command_prefix WHERE guild_id = $1;", guild_id
            )

        if row:
            return row["command_prefix"]
        return None

    async def update_prefix(self, guild_id: int, prefix: str) -> None:
        async with self.pool.acquire() as con:
            con: asyncpg.connection.Connection  # type: ignore
            async with con.transaction():
                await con.execute(
                    "UPDATE command_prefix SET command_prefix = $1 WHERE guild_id = $2;",
                    prefix,
                    guild_id,
                )

    # ========================================================================================
    # Channels

    async def get_channel(self, guild_id: int, channel_type: str) -> list:
        async with self.pool.acquire() as con:
            con: asyncpg.connection.Connection  # type: ignore
            row = await con.fetchrow(
                "SELECT * FROM channel_ids WHERE guild_id = $1;", guild_id
            )

        channels = row.get(channel_type, None)

        if channels:
            return [int(i) for i in channels.split(",")]
        return []

    async def update_channel(
        self, guild_id: int, channel_type: str, channel_ids: str
    ) -> None:
        async with self.pool.acquire() as con:
            con: asyncpg.connection.Connection  # type: ignore
            async with con.transaction():
                await con.execute(
                    "UPDATE channel_ids SET "
                    + channel_type
                    + " = $1 WHERE guild_id = $2;",
                    channel_ids,
                    guild_id,
                )

    # ========================================================================================
    # Settings

    async def get_game_setting(
        self, guild_id: int, game_setting: str
    ) -> typing.Optional[int]:
        async with self.pool.acquire() as con:
            con: asyncpg.connection.Connection  # type: ignore
            row = await con.fetchrow(
                "SELECT * FROM game_settings WHERE guild_id = $1;", guild_id
            )

        return row.get(game_setting, None)

    async def update_game_setting(
        self, guild_id: int, game_setting: str, new_settings: int
    ) -> None:
        async with self.pool.acquire() as con:
            con: asyncpg.connection.Connection  # type: ignore
            async with con.transaction():
                await con.execute(
                    "UPDATE game_settings SET "
                    + game_setting
                    + " = $1 WHERE guild_id = $2;",
                    new_settings,
                    guild_id,
                )

    # ========================================================================================
    # Used Words

    async def add_word(self, game: str, channel_id: int, word: str) -> None:
        async with self.pool.acquire() as con:
            con: asyncpg.connection.Connection  # type: ignore
            async with con.transaction():
                await con.execute(
                    "INSERT INTO usedwords (game, channel_id, word) VALUES ($1, $2, LOWER($3));",
                    game,
                    channel_id,
                    word,
                )

    async def clear_words(self, game: str, channel_id: int) -> None:
        async with self.pool.acquire() as con:
            con: asyncpg.connection.Connection  # type: ignore
            async with con.transaction():
                await con.execute(
                    "DELETE FROM usedwords WHERE game = $1 AND channel_id = $2;",
                    game,
                    channel_id,
                )

    async def check_used_word(self, game: str, channel_id: int, word: str) -> bool:
        async with self.pool.acquire() as con:
            con: asyncpg.connection.Connection  # type: ignore
            row = await con.fetchrow(
                "SELECT word FROM usedwords WHERE game = $1 AND channel_id = $2 AND LOWER(word) = LOWER($3);",
                game,
                channel_id,
                word,
            )
        return row is not None

    # ========================================================================================
    # User Leaderboards

    async def update_lb(self, game: str, channel_id: int, user_id: int, guild_id: int) -> None:
        async with self.pool.acquire() as con:
            con: asyncpg.connection.Connection  # type: ignore
            async with con.transaction():
                update_query = "INSERT INTO leaderboards (game, user_id, score, channel_id, guild_id) VALUES ($1, $2, 1, $3, $4) ON CONFLICT (game, user_id, channel_id) DO UPDATE SET score = leaderboards.score + 1;"
                await con.execute(update_query, game, user_id, channel_id, guild_id)

    async def get_lb(self, guild_id: int,  lb_size: int, game: str = None, channel_id: int = None) -> list:
        async with self.pool.acquire() as con:
            con: asyncpg.connection.Connection  # type: ignore

            if not channel_id:

                if game:
                    return await con.fetch(
                        "SELECT user_id,SUM(score) FROM leaderboards WHERE guild_id = $1 AND game = $2 GROUP BY user_id ORDER BY SUM(score) DESC LIMIT $3",
                        guild_id,
                        game,
                        lb_size,
                    )
                return await con.fetch(
                    "SELECT user_id,SUM(score) FROM leaderboards WHERE guild_id = $1 GROUP BY user_id ORDER BY SUM(score) DESC LIMIT $2",
                    guild_id,
                    lb_size,
                )
            if game:

                return await con.fetch(
                    "SELECT user_id,score FROM leaderboards WHERE guild_id = $1 AND game = $2 AND channel_id =$3 ORDER BY score DESC LIMIT $4",
                    guild_id,
                    game,
                    channel_id,
                    lb_size,
                )

            return await con.fetch(
                "SELECT user_id,SUM(score) FROM leaderboards WHERE guild_id = $1 AND channel_id = $2 GROUP BY user_id ORDER BY SUM(score) DESC LIMIT $3",
                guild_id,
                channel_id,
                lb_size,
            )
            


    async def get_score(self, user_id: int, game: str = None, channel_id: int = None) -> int:
        async with self.pool.acquire() as con:
            con: asyncpg.connection.Connection  # type: ignore

            if channel_id:
                if game:
                    return (
                        await con.fetchrow(
                            "SELECT score FROM leaderboards WHERE channel_id = $1 AND game = $2 AND user_id = $3",
                            channel_id,
                            game,
                            user_id,
                        )
                    )["sum"] or 0

                return (
                    await con.fetchrow(
                        "SELECT SUM(score) FROM leaderboards WHERE channel_id = $1 AND user_id = $2",
                        channel_id,
                        user_id,
                    )
                )["sum"] or 0
            
            if game:
                    return (
                        await con.fetchrow(
                            "SELECT score FROM leaderboards WHERE game = $1 AND user_id = $2",
                            game,
                            user_id,
                        )
                    )["sum"] or 0

            return (
                await con.fetchrow(
                    "SELECT SUM(score) FROM leaderboards WHERE user_id = $1",
                    user_id,
                )
            )["sum"] or 0

    # ========================================================================================
    # Games

    async def get_game_data(
        self, game: str, channel_id: int
    ) -> typing.Optional[asyncpg.Record]:
        async with self.pool.acquire() as con:
            con: asyncpg.connection.Connection  # type: ignore
            return await con.fetchrow(
                f"SELECT * FROM {game}_game_data WHERE channel_id = $1", channel_id
            )

    async def game_switch(self, game: str, channel_id: int, switch: bool) -> None:
        async with self.pool.acquire() as con:
            con: asyncpg.connection.Connection  # type: ignore
            async with con.transaction():
                if not switch:
                    return await con.execute(
                        f"DELETE FROM {game}_game_data WHERE channel_id = $1;",
                        channel_id,
                    )
                return await con.execute(
                    f"INSERT INTO {game}_game_data (channel_id) VALUES ($1);",
                    channel_id,
                )