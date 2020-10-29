import pymysql
from app.utilities.Config import Config


class Database:
    APPS_TABLE = 'apps'

    def __init__(self, config: Config):
        self.conn = None
        self.cursor = None
        self.__config = config
        self.__initialize()

    def insert(self, data: dict, table_name: str):
        self.reconnect()
        key_list = []
        value_list = []
        substitution_list = []

        for key, value in data.items():
            key_list.append("`{}`".format(key))
            value_list.append(value)
            substitution_list.append("%s")

        columns = ", ".join(key_list)
        tuple_values = tuple(value_list)
        column_values = ", ".join(substitution_list)

        sql = "INSERT INTO `{}` ({}) VALUES ({})".format(table_name, columns, column_values)
        self.cursor.execute(sql, tuple_values)
        self.conn.commit()

    def update(self, unique_id: int, data: dict, table_name: str):
        key_list = []
        value_list = []

        self.reconnect()

        for key, value in data.items():
            key_list.append("{}=%s".format(key))
            value_list.append(value)

        columns = ", ".join(key_list)
        tuple_values = tuple(value_list)

        sql = "UPDATE `{}` SET {} WHERE id={} LIMIT 1".format(table_name, columns, unique_id)
        self.cursor.execute(sql, tuple_values)
        self.conn.commit()

    def reconnect(self):
        try:
            self.conn.ping(reconnect=True)
        except Exception as e:
            print("Database reconnect error: {}".format(str(e)))

    def get_cursor(self):
        self.reconnect()
        return self.cursor

    def get_conn(self):
        self.reconnect()
        return self.conn

    def __initialize(self):
        self.__config.set_section('database')
        try:
            self.conn = pymysql.connect(
                host=self.__config.get('host'),
                user=self.__config.get('user'),
                charset='utf8mb4',
                password=self.__config.get('pass'),
                port=self.__config.get_int('port'),
                cursorclass=pymysql.cursors.DictCursor
            )
            self.cursor = self.conn.cursor()
            self.cursor.execute("CREATE DATABASE IF NOT EXISTS %s;" % self.__config.get('database'))
            self.conn.select_db(self.__config.get('database'))
        except Exception as e:
            print("Database error: {}".format(str(e)))
