import ast
import json
import typing

import mysql.connector as mysql
from mysql.connector.cursor import MySQLCursor

class DataBase:

    def __init__(self, host, database, user, password) -> None:
        self.host = host
        self.database = database
        self.user = user
        self.password = password
    
    def connect(self) -> None:
        self.db_connection: mysql.MySQLConnection = mysql.connect(host=self.host,
                                       database=self.database,
                                       user=self.user,
                                       password=self.password,
                                       buffered=True,
                                       auth_plugin='mysql_native_password')
        self.cursor: MySQLCursor = self.db_connection.cursor()
    
    def disconnect(self) -> None:
        self.db_connection.close()
        self.cursor.close()
    
    def reconnect(self) -> None:
        self.db_connection.reconnect()
    
    # ============================================
    # Config 

    def innit_guild(self, guild_id: int, command_prefix: str, max_lb_size: int, HL_max_reply: int, WS_wrong_guesses: int, HL_max_number: int) -> None:
        self.connect()

        self.update_prefix(guild_id=guild_id, command_prefix=command_prefix)
        insert_query = "INSERT INTO `game_settings` (`guild_id`, `max_lb_size`, `HL_max_reply`, `WS_wrong_guesses`, `HL_max_number`) VALUES (%s, %s, %s, %s, %s)"
        self.cursor.execute(insert_query, (guild_id, max_lb_size, HL_max_reply, WS_wrong_guesses, HL_max_number))
        self.db_connection.commit()
        insert_query = "INSERT INTO `channel_ids` (`guild_id`) VALUES (%s)"
        self.cursor.execute(insert_query, (guild_id,))
        self.db_connection.commit()
    
        self.disconnect()
    
    # ============================================
    # Prefix

    def get_prefix(self, guild_id: int) -> typing.Union[str, None]:
        self.connect()

        get_query = 'SELECT * FROM `command_prefix` WHERE `guild_id` = %s;'
        self.cursor.execute(get_query, (guild_id,))
        prefix = self.cursor.fetchone()

        self.disconnect()

        if prefix is not None:
            return prefix[1]
        else:
            return None 
    
    def update_prefix(self, guild_id: int, command_prefix: str) -> None:
        self.connect()

        insert_query = 'INSERT INTO `command_prefix` (`guild_id`, `prefix`) VALUES (%s, %s) ON DUPLICATE KEY UPDATE  `prefix` = %s;'
        self.cursor.execute(insert_query, (guild_id, command_prefix, command_prefix))
        self.db_connection.commit()

        self.disconnect()
    

    # ============================================
    # Channels
    
    def get_channel(self, guild_id: int, channel_type: str) -> list:
        self.connect()

        get_query = 'SELECT `' + channel_type + '` FROM `channel_ids` WHERE `guild_id` = %s;'
        self.cursor.execute(get_query, (guild_id,))
        data = self.cursor.fetchone()

        self.disconnect()

        if data:
            if data[0] is not None:
                return [int(i) for i in data[0].split(',')]
            else:
                return []
        else:
            return []
    
    def update_channel(self, guild_id: int, channel_type: str, channel_ids: str) -> None:
        self.connect()

        update_query = 'UPDATE `channel_ids` SET `' + channel_type + '` = %s WHERE `guild_id` = %s;'
        self.cursor.execute(update_query, (channel_ids, guild_id))
        self.db_connection.commit()

        self.disconnect()
    
    # ============================================
    # Settings
    
    def get_game_setting(self, guild_id: int, game_setting: str) -> typing.Union[int, None]:
        self.connect()

        get_query = 'SELECT `' + game_setting + '` FROM `game_settings` WHERE `guild_id` = %s;'
        self.cursor.execute(get_query, (guild_id,))
        data = self.cursor.fetchone()

        self.disconnect()

        if data is not None:
            return data[0]
        else:
            return None
    
    def update_game_setting(self, guild_id: int, game_setting: str, new_setting: int) -> None:
        self.connect()
        
        update_query = 'UPDATE `game_settings` SET `' + game_setting + '` = %s WHERE `guild_id` = %s;'
        self.cursor.execute(update_query, (new_setting, guild_id))
        self.db_connection.commit()

        self.disconnect()
    
    # ========================================================================================
    # Used Words

    def add_word(self, game: str, channel_id: int, word: str) -> None:
        self.connect()
        
        insert_query = 'INSERT INTO `usedwords` (`game`, `channel_id`, `word`) VALUES (%s, %s, %s);'
        self.cursor.execute(insert_query, (game, channel_id, word))
        self.db_connection.commit()

        self.disconnect()
    
    def clear_words(self, game: str, channel_id: int) -> None:
        self.connect()
        
        delete_query = 'DELETE FROM `usedwords` WHERE `game` = %s AND `channel_id` = %s;'
        self.cursor.execute(delete_query, (game, channel_id))
        self.db_connection.commit()

        self.disconnect()

    def check_used_word(self, game: str, channel_id: int, word: str) -> None:
        self.connect()
        
        check_query = "SELECT `word` FROM `usedwords` WHERE `game` = %s AND `word` = %s AND `channel_id` = %s;"
        self.cursor.execute(check_query, (game, word, channel_id))
        data = self.cursor.fetchone()

        self.disconnect()

        return not data is None
    
    # ========================================================================================
    # User Leaderboards

    def update_lb(self, game: str, channel_id: int, user_id: int) -> None:
        self.connect()
        
        update_query = 'INSERT INTO `leaderboards` (`game`, `user_id`, `score`, `channel_id`) VALUES (%s, %s, %s, %s) ON DUPLICATE KEY UPDATE `score` = `score` + 1;'
        self.cursor.execute(update_query, (game, user_id, 0, channel_id))
        self.db_connection.commit()

        self.disconnect()
    
    def get_lb(self, channel_id: int, lb_size: int, game: str = None) -> list:
        self.connect()
        
        if game:
            get_query = "SELECT * FROM `leaderboards` WHERE `channel_id` = %s AND `game` = %s  ORDER BY `score` DESC LIMIT %s;"
            self.cursor.execute(get_query, (channel_id, game, lb_size))
            data = self.cursor.fetchall()
        else:
            get_query = "SELECT * FROM `leaderboards` WHERE `channel_id` = %s ORDER BY `score` DESC LIMIT %s;"
            self.cursor.execute(get_query, (channel_id, lb_size))
            data = self.cursor.fetchall()

        self.disconnect()

        return data
    
    def get_score(self, game: str, channel_id: int, user_id: int) -> int:
        self.connect()
        
        get_query = "SELECT * FROM `leaderboards` WHERE `channel_id` = %s AND `game` = %s AND `user_id` = %s;"
        self.cursor.execute(get_query, (channel_id, game, user_id))
        data = self.cursor.fetchone()

        self.disconnect()

        return data


    # ========================================================================================
    # WordSnake

    def get_WordSnake_data(self, channel_id: int) -> typing.Union[dict, None]:
        self.connect()

        get_query = 'SELECT * FROM `WordSnake_game_data` WHERE `channel_id` = %s;'
        self.cursor.execute(get_query, (channel_id,))
        data = self.cursor.fetchone()

        self.disconnect()

        if data is not None:
            return {
                'channel_id': data[0],
                'last_user_id': data[1],
                'last_word': data[2],
                'count': data[3],
                'allowed_mistakes': data[4],
                'msg_id': data[5]
            }
        else:
            return None
    
    def update_WordSnake_data(self, channel_id: int, last_user_id: int, last_word: str, msg_id: int, count: int) -> None:
        self.connect()

        update_query = 'UPDATE `WordSnake_game_data` SET `last_user_id` = %s, `last_word` = %s, `msg_id` = %s, `count` =  %s WHERE `channel_id` = %s;'
        self.cursor.execute(update_query, (last_user_id, last_word, msg_id, count, channel_id))
        self.db_connection.commit()

        self.disconnect()
    
    def WordSnake_game_switch(self, chanel_id: int, game: bool) -> None:
        self.connect()

        if game:
            query = 'INSERT INTO `WordSnake_game_data` (`channel_id`) VALUES (%s);'
        else:
            query = 'DELETE FROM `WordSnake_game_data` WHERE `channel_id` = %s;'
        self.cursor.execute(query, (chanel_id,))
        self.db_connection.commit()

        self.disconnect()
    
    def allowed_mistakes(self, channel_id: int, allowed_mistake: int) -> None:
        self.connect()

        update_query = 'UPDATE `WordSnake_game_data` SET `allowed_mistakes` = %s WHERE `channel_id` = %s;'
        self.cursor.execute(update_query, (allowed_mistake, channel_id))
        self.db_connection.commit()

        self.disconnect()
    
    # ========================================================================================
    # NTBPL 

    def get_NTBPL_data(self, channel_id: int) -> typing.Union[dict, None]:
        self.connect()

        get_query = "SELECT * FROM `NTBPL_game_data` WHERE `channel_id` = %s;"
        self.cursor.execute(get_query, (channel_id,))
        data = self.cursor.fetchone()

        self.disconnect()

        if data is not None:
            return {
                'channel_id': data[0],
                'count': data[1],
                'letters': data[2],
                'last_user_id': data[3]
            }
        else:
            return None
    
    def update_NTBPL_data(self, channel_id: int, count: int, letters: str, last_user_id: int) -> None:
        self.connect()

        update_query = "UPDATE `NTBPL_game_data` SET `count` = %s, `letters` = %s, `last_user_id` = %s WHERE `channel_id` = %s;"
        self.cursor.execute(update_query, (count, letters, last_user_id, channel_id))
        self.db_connection.commit()

        self.disconnect()
    
    def NTBPL_game_switch(self, chanel_id: int, game: bool) -> None:
        self.connect()

        if game:
            query = 'INSERT INTO `NTBPL_game_data` (`channel_id`) VALUES (%s);'
        else:
            query = 'DELETE FROM `NTBPL_game_data` WHERE `channel_id` = %s;'
        self.cursor.execute(query, (chanel_id,))
        self.db_connection.commit()
        
        self.disconnect()
    
    # ========================================================================================
    # HigherLower 

    def get_HigherLower_data(self, channel_id: int):
        self.connect()

        get_query = "SELECT * FROM `HigherLower_game_data` WHERE `channel_id` = %s;"
        self.cursor.execute(get_query, (channel_id,))
        data = self.cursor.fetchone()

        self.disconnect()

        if data is not None:
            return {
                'channel_id': data[0],
                'number': data[1],
                'last_user_id': data[2],
                'count': data[3]
            }
        else:
            return None
    
    def update_HigherLower_data(self, channel_id: int, count: int, number: str, last_user_id: int) -> None:
        self.connect()

        update_query = "UPDATE `HigherLower_game_data` SET `number` = %s, `last_user_id` = %s, `count` = %s WHERE `channel_id` = %s;"
        self.cursor.execute(update_query, (number, last_user_id, count, channel_id))
        self.db_connection.commit()

        self.disconnect()
    
    def HigherLower_game_switch(self, chanel_id: int, game: bool) -> None:
        self.connect()

        if game:
            query = 'INSERT INTO `HigherLower_game_data` (`channel_id`) VALUES (%s);'
        else:
            query = 'DELETE FROM `HigherLower_game_data` WHERE `channel_id` = %s;'
        self.cursor.execute(query, (chanel_id,))
        self.db_connection.commit()

        self.disconnect()
    
    # ========================================================================================
    # HangMan 

    def get_HangMan_data(self, msg_id: int):
        self.connect()

        get_query = "SELECT * FROM `HangMan_game_data` WHERE `msg_id` = %s;"
        self.cursor.execute(get_query, (msg_id,))
        data = self.cursor.fetchone()

        self.disconnect()

        if data is not None:
            return {
                'msg_id': data[0],
                'word': data[1],
                'used_letters': data[2],
                'user_id': data[3],
                'players': data[4]
            }
        else:
            return None
    
    def update_HangMan_data(self, msg_id: int, word: str, used_letters: str, user_id: int, players: str) -> None:
        self.connect()

        update_query = "UPDATE `HangMan_game_data` SET `word` = %s, `used_letters` = %s, `user_id` = %s , `players` = %s  WHERE `msg_id` = %s;"
        self.cursor.execute(update_query, (word, used_letters, user_id, players, msg_id))
        self.db_connection.commit()

        self.disconnect()
    
    def HangMan_game_switch(self, msg_id: int, game: bool) -> None:
        self.connect()

        if game:
            query = 'INSERT INTO `HangMan_game_data` (`msg_id`) VALUES (%s);'
        else:
            query = 'DELETE FROM `HangMan_game_data` WHERE `msg_id` = %s;'
        self.cursor.execute(query, (msg_id,))
        self.db_connection.commit()
        
        self.disconnect()
    
    # ========================================================================================
    # ConnectFour 

    def get_ConnectFour_data(self, msg_id: int):
        self.connect()

        get_query = "SELECT * FROM `ConnectFour_game_data` WHERE `msg_id` = %s;"
        self.cursor.execute(get_query, (msg_id,))
        data = self.cursor.fetchone()

        self.disconnect()

        if data is not None:
            return {
                'player1': data[0],
                'player2': data[1],
                'config': data[2],
                'msg_id': data[3]
            }
        else:
            return None

    
    def update_ConnectFour_data(self, msg_id: int, player1: int, player2: int, config: str) -> None:
        self.connect()

        update_query = "UPDATE `ConnectFour_game_data` SET `player1` = %s, `player2` = %s, `game_config` = %s WHERE `msg_id` = %s;"
        self.cursor.execute(update_query, (player1, player2, config, msg_id))
        self.db_connection.commit()

        self.disconnect()
    
    def ConnectFour_game_switch(self, msg_id: int, game: bool) -> None:
        self.connect()

        if game:
            query = 'INSERT INTO `ConnectFour_game_data` (`msg_id`) VALUES (%s);'
        else:
            query = 'DELETE FROM `ConnectFour_game_data` WHERE `msg_id` = %s;'
        self.cursor.execute(query, (msg_id,))
        self.db_connection.commit()

        self.disconnect()
    
    # ========================================================================================
    # Tag 

    def add_tag(self, guild_id: int, tag: str, desc: str) -> None:
        self.connect()

        insert_query = "INSERT INTO `tag` (`guild_id`, `tag`, `desc`) VALUES (%s, %s, %s);"
        self.cursor.execute(insert_query, (guild_id, tag, desc))
        self.db_connection.commit()

        self.disconnect()
    
    def update_tag(self, guild_id: int, tag: str, desc: str) -> None:
        self.connect()

        insert_query = "UPDATE `tag` SET `desc` = %s WHERE (`guild_id`= %s OR `guild_id` = %s) AND `tag`= %s;"
        self.cursor.execute(insert_query, (desc, guild_id, 000000000000000000, tag))
        self.db_connection.commit()

        self.disconnect()
    
    def delete_tag(self, guild_id: int, tag: str) -> None:
        self.connect()

        delete_query = "DELETE FROM `tag` WHERE `guild_id`= %s  AND `tag`= %s;"
        self.cursor.execute(delete_query, (guild_id, tag))
        self.db_connection.commit()

        self.disconnect()

    def get_tag(self, guild_id: int, tag: str, search_global: bool=True) -> typing.Union[str, None]:
        self.connect()

        fetch_query = "SELECT * FROM `tag` WHERE "
        if search_global:
            fetch_query += "(`guild_id`= %s OR `guild_id` = '000000000000000000') "
        else:
            fetch_query += "`guild_id`= %s "
        
        fetch_query += "AND `tag`= %s;"
        self.cursor.execute(fetch_query, (guild_id, tag))

        if search_global:
            data = self.cursor.fetchall()
            if len(data) > 1:
                data = [i for i in data if i[0] != 0][0]
            elif data:
                data = data[0]
        else:
            data = self.cursor.fetchone()


        self.disconnect()

        if data:
            return {'tag': data[1],
                    'desc': data[2]}
        else:
            return None
    
    # ========================================================================================
    # Stats

    def stats_get_guild_info(self, guild_id: int) -> typing.Union[dict, None]:
        self.connect()

        fetch_query = "SELECT * FROM `stats` WHERE `guild_id` = %s;"
        self.cursor.execute(fetch_query, (guild_id,))
        data = self.cursor.fetchall()

        self.disconnect()

        if data:
            d_user = {}
            d_global = {}
            for entry in data:
                user_id, uses, command_name = entry[3], entry[2], entry[1]
                if command_name in d_global:
                    d_global[command_name] += uses
                else:
                    d_global[command_name] = uses
                
                if user_id not in d_user:
                    d_user[user_id] = {}
                
                if command_name in d_user[user_id]:
                    d_user[user_id][command_name] += uses
                else:
                    d_user[user_id][command_name] = uses
            
            return {'global': d_global,
                    'users': d_user}
        else:
            return {'global': {},
                    'users': {}}
    
    def stats_update_guild_info(self, guild_id: int, data: dict) -> None:

        if data:
            self.connect()

            update_query = "REPLACE INTO `stats` (`guild_id`, `user_id`, `uses`, `command`) VALUES "

            for user_id, command_data in data.items():
                for command, uses in command_data.items():
                    update_query += f"""('{guild_id}', '{user_id}', '{uses}', '{command}'),"""
            
            self.cursor.execute(update_query[:-1] + ";")
            self.db_connection.commit()
            self.disconnect()




