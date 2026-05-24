from app.utilities.Database import Database
from app.utilities.Logger import Logger


class Apps:
    def __init__(self, database: Database, logger: Logger):
        self.__logger = logger
        self.__database = database
        self.__database.reconnect()

    def get_token_by_dialed_number(self, dialed_num: str):
        try:
            self.__database.reconnect()
            # CHANGED: was 'SELECT ... WHERE phone = "{}"'.format(dialed_num) —
            # direct string interpolation allows SQL injection. Now uses a
            # parameterised %s placeholder so the driver escapes the value safely.
            sql = 'SELECT token FROM apps WHERE phone = %s'
            self.__database.cursor.execute(sql, (dialed_num,))
            data = self.__database.cursor.fetchone()
            return data['token'] if data else None
        except Exception as e:
            self.__logger.log_info("Database fetch error: {}".format(str(e)))
            return None

    def get_voice_url(self, token):
        data = self.get_data(token)
        return str(data['voice_url'])

    def get_status_url(self, token):
        data = self.get_data(token)
        status = str(data['status_url'])
        if status[-1] == '/':
            return status
        return str(status + '/')

    def get_data(self, token):
        try:
            self.__database.reconnect()
            # CHANGED: was 'SELECT * FROM apps WHERE token = "{}"'.format(token) —
            # same SQL injection fix as above.
            sql = 'SELECT * FROM apps WHERE token = %s'
            self.__database.cursor.execute(sql, (token,))
            return self.__database.cursor.fetchone()
        except Exception as e:
            self.__logger.log_info("Database fetch error: {}".format(str(e)))
            return {}
