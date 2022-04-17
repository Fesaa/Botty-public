from mysql.connector import connect
from typing import Union


class Database:

    def __init__(self, host, database, user, password):
        self.db_connection = connect(host=host, database=database, user=user, password=password, buffered=True,
                                     auth_plugin='mysql_native_password')
        self.cursor = self.db_connection.cursor()

    def reconnect(self):
        self.db_connection.reconnect()

    def connect_ign(self, discord_id: int, uuid: str):
        insert_query = "INSERT INTO `ign` (`id`, `uuid`) VALUES (%s, %s) ON DUPLICATE KEY UPDATE `uuid` = %s;"
        self.cursor.execute(insert_query, (discord_id, uuid, uuid))
        self.db_connection.commit()

    def check_in_system(self, check: Union[str, int]) -> bool:
        if type(check) is int:
            return self.get_uuid(check) is not None
        elif type(check) is str:
            check_query = "SELECT * FROM `ign` WHERE `uuid` = %s;"
            self.cursor.execute(check_query, (check,))
            data = self.cursor.fetchone()
            return data is not None

    def get_uuid(self, discord_id) -> Union[list, None]:
        get_guery = "SELECT * FROM `ign` WHERE `id` = %s;"
        self.cursor.execute(get_guery, (discord_id,))
        data = self.cursor.fetchone()
        if data:
            return data[1]
        else:
            return None

    def get_dc_id(self, uuid: str) -> Union[list, None]:
        get_guery = "SELECT * FROM `ign` WHERE `uuid` = %s;"
        self.cursor.execute(get_guery, (uuid,))
        data = self.cursor.fetchone()
        if data:
            return data[0]
        else:
            return None

    def add_global_loot(self, loot_type: str, name: str, rarity: str, cubelet: str):
        insert_guery = "INSERT INTO `global` (`type`, `name`, `rarity`, `cubelet`) VALUES (%s, %s, %s, %s)" \
                       " ON DUPLICATE KEY UPDATE `rarity` = %s, `cubelet` = %s;"
        self.cursor.execute(insert_guery, (loot_type, name.replace("'", "''"), rarity, cubelet, rarity, cubelet))
        self.db_connection.commit()

    def import_global_loot(self, loot_list: list):
        insert_guery = "REPLACE INTO `global` (`type`, `name`, `rarity`, `cubelet`) VALUES "

        for loot_item in loot_list:
            insert_guery += f"""('{loot_item['type']}', '{loot_item['name'].replace("'", "''")}',""" \
                            f" '{loot_item['rarity']}', '{loot_item['cubelet']}'),"

        self.cursor.execute(insert_guery[:-1] + ";")
        self.db_connection.commit()

    def add_player_loot(self, loot_type: str, name: str, rarity: str, uuid: str, cubelet: str):
        insert_guery = "INSERT INTO `player` (`uuid`, `type`, `name`, `rarity`, `cubelet`) VALUES (%s, %s, %s, %s, %s)"\
                       " ON DUPLICATE KEY UPDATE `rarity` = %s;"
        self.cursor.execute(insert_guery, (uuid, loot_type, name.replace("'", "''"), rarity, cubelet, rarity))
        self.db_connection.commit()

    def import_player_loot(self, loot_list: list, uuid: str):
        insert_guery = "REPLACE INTO `player` (`uuid`,`type`, `name`, `rarity`, `cubelet`) VALUES "

        for loot_item in loot_list:
            insert_guery += f"""('{uuid}','{loot_item['type']}', '{loot_item['name'].replace("'", "''")}',""" \
                            f" '{loot_item['rarity']}', '{loot_item['cubelet']}'),"

        self.cursor.execute(insert_guery[:-1] + ";")
        self.db_connection.commit()

    def global_checker(self, loot_type: str, name: str) -> tuple:
        get_guery = "SELECT * FROM `global` WHERE `type` = %s AND `name` = %s;"
        self.cursor.execute(get_guery, (loot_type, name.replace("'", "''")))
        return self.cursor.fetchone()

    def get_player_loot(self, uuid: str) -> list:
        get_guery = "SELECT * FROM `player` WHERE `uuid` = %s ORDER BY `type` DESC;"
        self.cursor.execute(get_guery, (uuid,))
        return self.cursor.fetchall()

    def missing_player_loot(self, uuid: str, unobtainable: bool, pack_bundle: bool) -> list:
        player_loot = [i[1:][:-2] for i in self.get_player_loot(uuid)]
        missing_loot = []

        get_guery = "SELECT * FROM `global` ORDER BY `type` DESC;"
        self.cursor.execute(get_guery)

        all_loot = self.cursor.fetchall()

        for loot in all_loot:
            if loot[:-2] not in player_loot:

                if not unobtainable and pack_bundle:
                    if loot[3] != "unobtainable":
                        missing_loot.append(loot)

                elif not unobtainable and not pack_bundle:
                    if not loot[3] in ["pack_bundle", "unobtainable"]:
                        missing_loot.append(loot)

                elif unobtainable and not pack_bundle:
                    if loot[3] != "pack_bundle":
                        missing_loot.append(loot)

                else:
                    missing_loot.append(loot)

        return missing_loot

    def report(self, order: str, where: str, uuid: str = None):
        if uuid:
            count_guery = f"SELECT `{order}`, COUNT(*) FROM `{where}` WHERE `type` = %s AND" \
                          f" `uuid` = '{uuid}' GROUP BY `{order}`;"
        else:
            count_guery = f"SELECT `{order}`, COUNT(*) FROM `{where}` WHERE `type` = %s GROUP BY `{order}`;"

        raw_count_dict = {}
        output = {}

        for loot_type in ["hat", "banner", "wardrobe", "win_effect", "egg_break", "cage", "shield", "miniature",
                          "balloon", "arrow_trail", "trail", "gadget"]:
            self.cursor.execute(count_guery, (loot_type, ))
            raw_count_dict[loot_type] = {i[0]: i[1] for i in self.cursor.fetchall()}

            for raw_loot_type, raw_count in raw_count_dict.items():
                count_dict = {}

                if order == "rarity":
                    for rarity, display_rarity in zip(['mythical', 'legendary', 'rare', 'uncommon', 'common',
                                                       'no_rarity'],
                                                      ['Mythical', 'Legendary', 'Rare', 'Uncommon', 'Common',
                                                       'No rarity']):
                        try:
                            count_dict[display_rarity] = raw_count[rarity]
                        except KeyError:
                            count_dict[display_rarity] = 0
                elif order == 'cubelet':
                    for cubelet, display_cubelet in zip(['normal', 'halloween', 'winter', 'spring', 'summer',
                                                         'unobtainable', 'pack_bundle'],
                                                        ['Normal, super or uber', 'Halloween', 'Winter', 'Spring',
                                                         'Summer', 'No longer obtainable',
                                                         'Unlocked with a pack, bundle or rank']):
                        try:
                            count_dict[display_cubelet] = raw_count[cubelet]
                        except KeyError:
                            count_dict[display_cubelet] = 0
                else:
                    count_dict = ""

                output[raw_loot_type] = count_dict

        return output
