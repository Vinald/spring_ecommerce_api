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
        self.reconnect()
        key_list = []
        value_list = []

        for key, value in data.items():
            key_list.append("{}=%s".format(key))
            value_list.append(value)

        columns = ", ".join(key_list)
        tuple_values = tuple(value_list)

        # CHANGED: was WHERE id={} with string formatting — SQL injection risk.
        # Now uses a parameterised placeholder with the id appended to the tuple.
        sql = "UPDATE `{}` SET {} WHERE id=%s LIMIT 1".format(table_name, columns)
        self.cursor.execute(sql, tuple_values + (unique_id,))
        self.conn.commit()

    def reconnect(self):
        try:
            self.conn.ping(reconnect=True)
        except Exception as e:
            print("Database reconnect error: {}".format(str(e)))
            # CHANGED: previously a failed ping would leave the connection broken.
            # Now re-initialise fully so the next query has a working connection.
            self.__initialize()

    def get_cursor(self):
        self.reconnect()
        return self.cursor

    def get_conn(self):
        self.reconnect()
        return self.conn

    def __initialize(self):
        self.__config.set_section('database')
        try:
            db = self.__config.get('database')
            # Bootstrap connection: create the database schema if it does not exist.
            # Uses a context manager so the cursor is always closed cleanly.
            bootstrap = pymysql.connect(
                host=self.__config.get('host'),
                user=self.__config.get('user'),
                password=self.__config.get('pass'),
                port=self.__config.get_int('port')
            )
            with bootstrap.cursor() as cur:
                cur._defer_warnings = True
                cur.execute("CREATE DATABASE IF NOT EXISTS `%s`;" % db)
            bootstrap.close()

            self.conn = pymysql.connect(
                host=self.__config.get('host'),
                user=self.__config.get('user'),
                charset='utf8mb4',
                db=db,
                password=self.__config.get('pass'),
                port=self.__config.get_int('port'),
                cursorclass=pymysql.cursors.DictCursor,
                # CHANGED: explicit autocommit=False so transactions are always
                # controlled deliberately by calling conn.commit().
                autocommit=False,
            )
            self.cursor = self.conn.cursor()
        except Exception as e:
            print("Database error: {}".format(str(e)))
