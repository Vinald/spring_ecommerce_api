import pymysql
from src.Config import Config


class AppDatabase:
    APPS_TABLE = 'apps'

    def __init__(self, config: Config):
        self.config = config
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
        self.conn.ping(reconnect=True)

    def get_cursor(self):
        self.reconnect()
        return self.cursor

    def get_conn(self):
        self.reconnect()
        return self.conn

    def __initialize(self):
        self.config.set_section('database')
        self.conn = pymysql.connect(
            db=self.config.get('database'),
            host=self.config.get('hostname'),
            user=self.config.get('username'),
            charset='utf8mb4',
            password=self.config.get('password'),
            port=self.config.get_int('port'),
            cursorclass=pymysql.cursors.DictCursor
        )
        self.cursor = self.conn.cursor()
