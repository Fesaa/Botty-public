from mysql.connector import connect
from cogs.config_handler import host, Database, user, password
from imports.functions import time, get_word
from random import randint, choice
from enchant import Dict
from re import match


class database:

    def __init__(self):
        global config
        global db_connection
        global cursor

        db_connection = connect(host=host, database=Database, user=user, password=password, buffered=True,
                                auth_plugin='mysql_native_password')
        cursor = db_connection.cursor()

    def add_user_data(self, game: str, user_id: int, channel_id: int):
        insert_query = "INSERT INTO `leaderboards` (`game`,`user_id`,`channel_id` ,`score`)" \
                       " VALUES (%s,%s, %s,'1') ON DUPLICATE KEY UPDATE `score` = `score` + 1;"
        cursor.execute(insert_query, (game, user_id, channel_id,))
        db_connection.commit()

    def get_lb(self, channel_id: int, lb_size: int):
        get_query = "SELECT * FROM `leaderboards` WHERE `channel_id` = %s ORDER BY `score` DESC LIMIT %s ;"
        cursor.execute(get_query, (channel_id, lb_size))
        data = cursor.fetchall()
        return data

    def get_score(self, channel_id, user_id):
        get_guery = "SELECT * FROM  `leaderboards` WHERE `channel_id` = %s AND `user_id` = %s;"
        cursor.execute(get_guery, (channel_id, user_id))
        data = cursor.fetchone()
        return data

    def get_game_date(self, game, channel_id: int):  # word_snake
        get_query = "SELECT * FROM `game_data` WHERE `game` = %s AND `channel_id` = %s;"
        cursor.execute(get_query, (game, channel_id,))
        data = cursor.fetchone()
        return data

    def reset_game(self, game, channel_id):  # word_snake
        insert_query = "DELETE FROM `game_data` WHERE `game` = %s AND `channel_id` = %s;"
        cursor.execute(insert_query, (game, channel_id))
        db_connection.commit()

    def change_game_data(self, last_user_id, last_word, last_word_id, channel_id, game):  # word_snake
        insert_query = "INSERT INTO `game_data` (`last_user_id`, `last_word`, `word_count`, `last_word_id`," \
                       " `channel_id`, `game`, `allowed_mistake`) VALUES(%s, %s, '1', %s, %s, %s, `allowed_mistake`)" \
                       "  ON DUPLICATE KEY UPDATE `last_user_id` = %s,`last_word` = %s,`word_count` =" \
                       " `word_count` + 1, `last_word_id` = %s, `allowed_mistake`= `allowed_mistake`;"
        cursor.execute(insert_query, (last_user_id, last_word, last_word_id, channel_id, game,
                                      last_user_id, last_word, last_word_id,))
        db_connection.commit()

    def ws_allowed_mistake(self, channel_id, allowed_mistake):
        update_query = "UPDATE `game_data` SET `allowed_mistake` = %s WHERE `channel_id` = %s;"
        cursor.execute(update_query, (allowed_mistake, channel_id))
        db_connection.commit()

    def add_word(self, game, word, channel_id):  # word_snake
        insert_query = "INSERT INTO `usedwords` (`game`, `word`, `channel_id`) VALUES (%s, %s, %s);"
        cursor.execute(insert_query, (game, word.lower(), channel_id))
        db_connection.commit()

    def clear_db(self, game: str, channel_id):  # used words
        delete_query = "DELETE FROM `usedwords` WHERE `game` = %s AND `channel_id` = %s;"
        cursor.execute(delete_query, (game, channel_id))
        db_connection.commit()

    def check_init(self, game, word, channel_id):  # used words
        check_query = "SELECT `word` FROM `usedwords` WHERE `game` = %s AND `word` = %s AND `channel_id` = %s"
        cursor.execute(check_query, (game, word.lower(), channel_id))
        if cursor.fetchone() is None:
            return False
        else:
            return True

    def change_ntbpl_data(self, channel_id: int, owner_id: int, count: int, running: int, skips: int, allowed_skip: int,
                          want_skip: int, skip_msg_id: int):
        d = Dict('en_GB')

        while True:
            letter_list = choice(get_word())[0]
            if letter_list is None:
                letter_list = choice(get_word())[0]
            if d.check(letter_list):
                if not database.check_init(self, 'ntbpl', letter_list, channel_id):
                    if match(r"^[a-zA-Z]+$", letter_list.lower()):
                        if len(letter_list) > int(count) + 2:
                            break
        print(time() + " A possible solution to the current letters is: " + letter_list)  # Failsafe
        spil = randint(1, len(letter_list) - int(count) - 1)
        letters = letter_list[spil: spil + int(count)]
        insert_query = "INSERT INTO `ntbpl_data` (`channel_id`, `owner_id`, `count`, `running`, `letters` ,`skips`," \
                       " `allowed_skip`, `want_skip`, `skip_msg_id`) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)" \
                       " ON DUPLICATE KEY UPDATE `owner_id`= %s, `count` = %s, `running` = %s,`letters` = %s," \
                       " `skips` = %s, `allowed_skip` = %s, `want_skip` = %s, `skip_msg_id` = %s;"
        cursor.execute(insert_query, (channel_id, owner_id, count, running, letters, skips, allowed_skip, want_skip,
                                      skip_msg_id, owner_id, count, running, letters, skips, allowed_skip, want_skip,
                                      skip_msg_id))
        db_connection.commit()

    def get_ntbpl_data(self, channel_id: int):
        get_query = "SELECT * FROM `ntbpl_data` WHERE `channel_id` = %s;"
        cursor.execute(get_query, (channel_id,))
        data = cursor.fetchone()
        db_connection.commit()
        return data

    def stop_ntbpl(self, channel_id):
        delete_query = "DELETE FROM `ntbpl_data` WHERE `channel_id` = %s;"
        cursor.execute(delete_query, (channel_id,))
        db_connection.commit()

    def ntbpl_skip_handler(self, channel_id, skips, allowed_skip, want_skip, skip_msg_id):
        update_query = "UPDATE `ntbpl_data` SET `skips` = %s , `allowed_skip` = %s, `want_skip` = %s," \
                       " `skip_msg_id` = %s WHERE `channel_id` = %s;"
        cursor.execute(update_query, (skips, allowed_skip, want_skip, skip_msg_id, channel_id,))
        db_connection.commit()

    def update_dm_preff(self, user_id, preff):
        update_query = "INSERT INTO `dm_preff` (`user_id`, `preff`) VALUES (%s, %s)" \
                       " ON DUPLICATE KEY UPDATE `preff` = %s;"
        cursor.execute(update_query, (user_id, preff, preff,))
        db_connection.commit()

    def get_dm_preff(self, user_id):
        get_guery = "SELECT * FROM `dm_preff` WHERE `user_id` = %s"
        cursor.execute(get_guery, (user_id,))
        data = cursor.fetchone()
        if data is None or data[1] == 1:
            return 1
        else:
            return 0

    def get_guild_info(self, guild_id):
        get_guery = "SELECT * FROM `config` WHERE `guild_id` = %s;"
        cursor.execute(get_guery, (guild_id,))
        data = cursor.fetchone()
        db_connection.commit()
        return data

    def update_guild_info(self, guild_id, command_prefix, log_channel_id, polly_channel_id, polly_maker_id,
                          clvl_channel_id, ws_channel_id, lb_size, ntbpl_channel_id, HL_channel_id, HL_max_reply,
                          connect4_id, hangman_id):
        update_guery = (
            "INSERT INTO `config` (`guild_id`, `command_prefix`, `log_channel_id`, `polly_channel_id`,"
            " `polly_maker_id`,`clvl_channel_id`, `ws_channel_id`, `lb_size`, `ntbpl_channel_id`, `HL_channel_id`,"
            " `HL_max_reply`, `connect4_id`, `hangman_id`) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
            "ON DUPLICATE KEY UPDATE `command_prefix` =%s, `log_channel_id`=%s, `polly_channel_id`=%s,"
            " `polly_maker_id`=%s, `clvl_channel_id`=%s,"
            "`ws_channel_id`=%s, `lb_size`=%s, `ntbpl_channel_id`=%s, `HL_channel_id` = %s, `HL_max_reply` = %s,"
            " `connect4_id` =%s, `hangman_id` =%s;")
        cursor.execute(update_guery, (guild_id, command_prefix, log_channel_id, polly_channel_id, polly_maker_id,
                                      clvl_channel_id, ws_channel_id, lb_size, ntbpl_channel_id, HL_channel_id,
                                      HL_max_reply, connect4_id, hangman_id, command_prefix, log_channel_id,
                                      polly_channel_id, polly_maker_id, clvl_channel_id, ws_channel_id, lb_size,
                                      ntbpl_channel_id, HL_channel_id, HL_max_reply, connect4_id, hangman_id,))
        db_connection.commit()

    def delete_guild_data(self, guild_id):
        delete_guery = "DELETE FROM `config` WHERE `guild_id` = %s;"
        cursor.execute(delete_guery, (guild_id,))
        db_connection.commit()

    def get_HLdata(self, channel_id):
        get_guery = "SELECT * FROM `higher_lower` WHERE `channel_id` = %s;"
        cursor.execute(get_guery, (channel_id,))
        data = cursor.fetchone()
        db_connection.commit()
        return data

    def update_HLdata(self, channel_id, number, user_id, count):
        update_guery = "INSERT INTO `higher_lower` (`channel_id`, `number`, `user_id`, `count`)" \
                       " VALUES (%s, %s, %s, %s) ON DUPLICATE KEY UPDATE `number` = %s, `user_id` = %s, `count` = %s;"
        cursor.execute(update_guery, (channel_id, number, user_id, count, number, user_id, count,))
        db_connection.commit()

    def get_4data(self, msg_id):
        get_guery = "SELECT * FROM `four_in_a_row` WHERE `msg_id` = %s;"
        cursor.execute(get_guery, (msg_id,))
        data = cursor.fetchone()
        db_connection.commit()
        return data

    def update_4data(self, channel_id, player1, player2, game_config, msg_id):
        update_guery = "INSERT INTO `four_in_a_row` (`channel_id`, `player1`, `player2`, `game_config`, `msg_id`)" \
                       " VALUES (%s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE `player2` = %s, `game_config` =%s," \
                       " `msg_id` =%s;"
        cursor.execute(update_guery, (channel_id, player1, player2, game_config, msg_id, player2, game_config, msg_id,))
        db_connection.commit()

    def get_running4game(self, channel_id):
        get_guery = "SELECT * FROM `four_in_a_row` WHERE `channel_id` = %s;"
        cursor.execute(get_guery, (channel_id,))
        data = cursor.fetchall()
        db_connection.commit()
        if data is None:
            return 0
        else:
            return len(data)

    def get_isowner4game(self, user_id):
        get_guery = "SELECT * FROM `four_in_a_row` WHERE `player1` = %s;"
        cursor.execute(get_guery, (user_id,))
        data = cursor.fetchone()
        db_connection.commit()
        get_guery = "SELECT * FROM `four_in_a_row` WHERE `player2` = %s;"
        cursor.execute(get_guery, (user_id,))
        data1 = cursor.fetchone()
        db_connection.commit()
        if (data or data1) is not None:
            return True
        else:
            return False

    def delete_4game(self, msg_id):
        delete_guery = "DELETE FROM `four_in_a_row` WHERE `msg_id` = %s;"
        cursor.execute(delete_guery, (msg_id,))
        db_connection.commit()

    def get_marriagestatus(self, user_id, guild_id):
        get_guery1 = "SELECT * FROM `marriage` WHERE `id1` =%s AND `guild_id` = %s;"
        cursor.execute(get_guery1, (user_id, guild_id,))
        data1 = cursor.fetchall()
        db_connection.commit()
        get_guery2 = "SELECT * FROM `marriage` WHERE `id2` =%s AND `guild_id` = %s;"
        cursor.execute(get_guery2, (user_id, guild_id,))
        data2 = cursor.fetchall()
        db_connection.commit()
        return data1 + data2

    def update_marriagestatus(self, id1, id2, status, m_time, msg_id, guild_id):
        update_guery = "INSERT INTO `marriage` (`id1`, `id2`, `status`, `time`, `msg_id`," \
                       " `time_end`, `guild_id`) VALUES (%s, %s, %s, %s, %s, %s, %s);"
        cursor.execute(update_guery, (id1, id2, status, m_time, msg_id, '0', guild_id,))
        db_connection.commit()

    def divorce_marriage(self, msg_id, time_end):
        update_guery = "UPDATE `marriage` SET `status` = %s, `time_end` = %s WHERE `msg_id` = %s;"
        cursor.execute(update_guery, ('divorced', time_end, msg_id,))
        db_connection.commit()

    def delete_requeste_marriage(self, id1, id2, guild_id):
        delete_query = "DELETE FROM `marriage` WHERE `id1` =%s AND `id2` = %s AND" \
                       " `status` = 'requested' AND `guild_id` =%s;"
        cursor.execute(delete_query, (id1, id2, guild_id,))
        db_connection.commit()

    def get_all_marriage(self, guild_id):
        get_guery = "SELECT * FROM `marriage` WHERE `guild_id` = %s;"
        cursor.execute(get_guery, (guild_id,))
        data = cursor.fetchall()
        return data

    def hangman_game_handler(self, msg_id, used_letters, user_id, players, word):
        update_guery = "INSERT INTO `hangman` (`msg_id`, `used_letters`, `user_id`, `players`, `word`)" \
                       " VALUES (%s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE `used_letters` =%s, `user_id` =%s," \
                       " `players` =%s, `word` =%s;"
        cursor.execute(update_guery,
                       (msg_id, used_letters, user_id, players, word, used_letters, user_id, players, word,))
        db_connection.commit()

    def get_hangman(self, msg_id):
        get_guery = "SELECT * FROM `hangman` WHERE `msg_id` =%s;"
        cursor.execute(get_guery, (msg_id,))
        data = cursor.fetchone()
        db_connection.commit()
        return data

    def delete_hangman(self, msg_id):
        delete_query = "DELETE FROM `hangman` WHERE `msg_id` = %s;"
        cursor.execute(delete_query, (msg_id,))
        db_connection.commit()

    def get_ship(self, id1, id2):
        get_guery = "SELECT * FROM `ship` WHERE `id1` = %s AND `id2` = %s;"
        cursor.execute(get_guery, (id1, id2,))
        data = cursor.fetchone()
        db_connection.commit()
        return data

    def update_ship(self, id1, id2, per, date):
        update_guery = "INSERT INTO `ship` (`id1`, `id2`, `per`, `date`) VALUES (%s, %s, %s, %s)" \
                       " ON DUPLICATE KEY UPDATE  `per` =%s, `date` =%s;"
        cursor.execute(update_guery, (id1, id2, per, date, per, date,))
        db_connection.commit()

    def update_counting(self, msg_id: int, author_id: int, count: int, c_time: str):
        update_guery = "INSERT INTO `counting` (`msg_id`, `author_id`, `count`, `time`) VALUES (%s, %s, %s, %s)" \
                       " ON DUPLICATE KEY UPDATE `msg_id` = %s, `author_id` = %s, `time` = %s;"
        cursor.execute(update_guery, (msg_id, author_id, count, c_time, msg_id, author_id, c_time,))
        db_connection.commit()

    def get_count_time(self, count):
        get_guery = "SELECT * FROM `counting`;"
        cursor.execute(get_guery, ())
        data = cursor.fetchall()
        db_connection.commit()
        for i in data:
            if i[2] == count:
                return i
        return None

    def update_music(self, guild_id, vc_id, channel_id, q, loop=0, q_place=None):
        if q_place is not None:
            update_guery = "INSERT INTO `music` (`guild_id`,  `vc_id`, `channel_id`, `q`, `q_place`,`loop`)" \
                           " VALUES (%s, %s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE `vc_id` =%s, `channel_id` =%s," \
                           " `q` =%s,`q_place`= %s ,`loop`= %s;"
            cursor.execute(update_guery, (guild_id, vc_id, channel_id, q, q_place, loop, vc_id, channel_id, q, q_place,
                                          loop,))
        else:
            update_guery = "INSERT INTO `music` (`guild_id`,  `vc_id`, `channel_id`, `q`, `loop`)" \
                           " VALUES (%s, %s, %s, %s,%s) ON DUPLICATE KEY UPDATE `vc_id` =%s, `channel_id` =%s," \
                           " `q` =%s,`loop`= %s;"
            cursor.execute(update_guery, (guild_id, vc_id, channel_id, q, loop, vc_id, channel_id, q, loop,))
        db_connection.commit()

    def get_music(self, guild_id):
        get_guery = "SELECT * FROM `music` WHERE `guild_id` = %s;"
        cursor.execute(get_guery, (guild_id,))
        data = cursor.fetchone()
        db_connection.commit()
        return data

    def del_music(self, guild_id):
        del_guery = "DELETE FROM `music` WHERE `guild_id` =%s;"
        cursor.execute(del_guery, (guild_id,))
        db_connection.commit()
