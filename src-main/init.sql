CREATE TABLE IF NOT EXISTS prefixes (
    guild_id BIGINT NOT NULL,
    prefix VARCHAR NOT NULL
);

CREATE TABLE IF NOT EXISTS channel_ids (
    guild_id BIGINT NOT NULL,
    channel_type VARCHAR(20) NOT NULL,
    channel_id BIGINT NOT NULL
);

CREATE TABLE IF NOT EXISTS guild_settings (
    guild_id BIGINT PRIMARY KEY NOT NULL,
    lb_size INT NOT NULL,
    hl_max_reply INT NOT NULL,
    ws_wrong_guesses INT NOT NULL,
    hl_max_number INT NOT NULL
);

CREATE TABLE IF NOT EXISTS channel_settings (
    channel_id BIGINT NOT NULL,
    setting_type VARCHAR(20) NOT NULL,
    setting_value INT NOT NULL,
    PRIMARY KEY (channel_id, setting_type)
);

CREATE TABLE IF NOT EXISTS scoreboard (
    guild_id BIGINT NOT NULL,
    channel_id BIGINT NOT NULL,
    game VARCHAR(20) NOT NULL,
    user_id BIGINT NOT NULL,
    score INT NOT NULL,
    PRIMARY KEY (channel_id, game, user_id)
);

CREATE TABLE IF NOT EXISTS tag (
    guild_id BIGINT NOT NULL,
    tag_name VARCHAR NOT NULL,
    tag_description VARCHAR NOT NULL,
    owner_id BIGINT NOT NULL,
    PRIMARY KEY (guild_id, tag_name)
);

CREATE TABLE IF NOT EXISTS trivia_questions (
    id SERIAL PRIMARY KEY,
    category VARCHAR NOT NULL,
    category_key VARCHAR NOT NULL,
    question VARCHAR NOT NULL,
    difficulty VARCHAR NOT NULL
);

CREATE TABLE IF NOT EXISTS trivia_answers (
    id INT NOT NULL,
    answer VARCHAR NOT NULL,
    correct BOOL NOT NULL,
    FOREIGN KEY (id)
        REFERENCES trivia_questions (id)
);

CREATE TABLE IF NOT EXISTS used_words (
    channel_id BIGINT NOT NULL,
    game VARCHAR(20) NOT NULL,
    word VARCHAR NOT NULL,
    PRIMARY KEY (channel_id, game, word)
);

CREATE TABLE IF NOT EXISTS word_snake (
    channel_id BIGINT PRIMARY KEY NOT NULL,
    guild_id BIGINT NOT NULL,
    current_player BIGINT NOT NULL,
    count INT NOT NULL,
    last_word VARCHAR NOT NULL,
    msg_id BIGINT NOT NULL,
    mistakes INT NOT NULL
);