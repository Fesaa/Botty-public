import asyncio
import asyncpg
import json

from typing import Any

def mapper(any: Any) -> str:
        if isinstance(any, str):
            return "'" + any.replace("'", "''") + "'"
        elif isinstance(any, int):
            return str(int(any))
        return str(any)


def main():
    asyncio.run(migration())

async def migration():
    with open("migration.json", "r") as f:
        cred = json.load(f)
    
    old_pool = await asyncpg.create_pool(cred["old"])
    new_pool = await asyncpg.create_pool(cred["new"])
    async with old_pool.acquire() as old_con:
        async with new_pool.acquire() as new_con:
            await channel_ids_migration(old_con, new_con)
            await prefix_migration(old_con, new_con)
            await guild_settings_migration(old_con, new_con)
            await scoreboard_migration(old_con, new_con)
            await tag_migration(old_con, new_con)
            await used_word_migration(old_con, new_con)
            await word_snake_migration(old_con, new_con)
            await trivia_migration(old_con, new_con)

# Channel IDs
async def channel_ids_migration(old_con: asyncpg.Connection, new_con: asyncpg.Connection):
    old_data = await old_con.fetch("""
    SELECT
        guild_id,
        wordsnake,
        ntbpl,
        higherlower,
        connectfour,
        hangman
    FROM
        channel_ids;
    """)

    migration_query: str = """
    INSERT INTO
        channel_ids
        (guild_id, channel_type, channel_id)
        VALUES
    """

    for data in old_data:
        guild_id = data["guild_id"]
        values = " "
        for key in data.keys():
            if key != "guild_id":
                if data[key] is not None:
                    for channel_id in data[key].split(","):
                        values += f"({guild_id}, '{key}', {channel_id}),"
        if values != " ":
            migration_query += values

    await new_con.execute(migration_query.removesuffix(",") + ";")

# Command prefixes
async def prefix_migration(old_con: asyncpg.Connection, new_con: asyncpg.Connection):
    old_data = await old_con.fetch("""
    SELECT
        guild_id,
        command_prefix
    FROM
        command_prefix;
    """
    )
    migration_query = f"""
    INSERT INTO
        prefixes
        (guild_id,prefix)
    VALUES
        {",".join(f"({d['guild_id']}, '{d['command_prefix']}')" for d in old_data)};
    """
    await new_con.execute(migration_query)

# Guild settings
async def guild_settings_migration(old_con: asyncpg.Connection, new_con: asyncpg.Connection):
    old_data = await old_con.fetch("""
    SELECT
        guild_id,
        max_lb_size,
        hl_max_reply,
        ws_wrong_guesses,
        hl_max_number
    FROM
        game_settings;
    """
    )
    migration_query = f"""
    INSERT INTO
        guild_settings
        (guild_id,lb_size,hl_max_reply,ws_wrong_guesses,hl_max_number)
    VALUES
        {",".join(f"({','.join(map(str, d.values()))})" for d in old_data)};
    """
    await new_con.execute(migration_query)

async def scoreboard_migration(old_con: asyncpg.Connection, new_con: asyncpg.Connection):
    old_data = await old_con.fetch("""
    SELECT
        guild_id,
        game,
        user_id,
        score,
        channel_id
    FROM
        leaderboards;
    """
    )

    migration_query = f"""
    INSERT INTO
        scoreboard
        (guild_id,game,user_id,score,channel_id)
    VALUES
        {",".join(f"({','.join(map(mapper, d.values()))})" for d in old_data)};
    """
    await new_con.execute(migration_query)

async def tag_migration(old_con: asyncpg.Connection, new_con: asyncpg.Connection):
    old_data = await old_con.fetch("""
    SELECT
        guild_id,
        tag,
        description,
        owner_id
    FROM
        tag;
    """
    )

    migration_query = f"""
    INSERT INTO
        tag
        (guild_id,tag_name,tag_description,owner_id)
    VALUES
        {",".join(f"({','.join(map(mapper, d.values()))})" for d in old_data)};
    """ 
    await new_con.execute(migration_query)

async def used_word_migration(old_con: asyncpg.Connection, new_con: asyncpg.Connection):
    old_data = await old_con.fetch("""
    SELECT
        game,
        word,
        channel_id
    FROM
        usedwords;
    """
    )

    migration_query = f"""
    INSERT INTO
        used_words
        (game, word, channel_id)
    VALUES
        {",".join(f"({','.join(map(mapper, d.values()))})" for d in old_data)}
    ON CONFLICT
        (game, word, channel_id)
    DO NOTHING;
    """ 
    await new_con.execute(migration_query)

async def word_snake_migration(old_con: asyncpg.Connection, new_con: asyncpg.Connection):
    #MANUALLY FIX GUILD_IDs !!!!!!!
    old_data = await old_con.fetch("""
    SELECT
        channel_id,
        last_user_id,
        last_word,
        count,
        allowed_mistakes,
        msg_id
    FROM
        wordsnake_game_data;
    """
    )

    migration_query = f"""
    INSERT INTO
        word_snake  
        (guild_id, channel_id, current_player,last_word,count,mistakes,msg_id)
    VALUES
        {",".join(f"(1,{','.join(map(mapper, d.values()))})" for d in old_data)};
    """
    await new_con.execute(migration_query)

async def trivia_migration(old_con: asyncpg.Connection, new_con: asyncpg.Connection):
    old_data = await old_con.fetch("""
    SELECT
        category,
        category_key,
        difficulty,
        question,
        correct_answer,
        incorrect_answers,
        custom_id
    FROM
        trivia_questions;
    """)

    questions_migration_query = f"""
    INSERT INTO
        trivia_questions
        (id, category, category_key,question,difficulty)
    VALUES
        {",".join(f"({d['custom_id']}, {mapper(d['category'])}, '{d['category_key']}', {mapper(d['question'])}, '{d['difficulty']}')" for d in old_data)};
    """
    answers_migration_query = f"""
    INSERT INTO
        trivia_answers
        (id, answer, correct)
    VALUES
        {",".join(f"({d['custom_id']}, {mapper(d['correct_answer'])}, 'true')" for d in old_data)},
        {",".join(f"({d['custom_id']}, {mapper(wrong_answer)}, 'false')" for d in old_data for wrong_answer in d['incorrect_answers'].split("§§§"))};
    """

    await new_con.execute(questions_migration_query)
    await new_con.execute(answers_migration_query)

if __name__ == "__main__":
    main()