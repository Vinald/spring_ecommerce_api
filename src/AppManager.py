from src.AppDatabase import AppDatabase
from src.Logger import Logger


class AppManager:
    def __init__(self, database: AppDatabase, logger: Logger):
        self.logger = logger
        self.database = database

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
            sql = 'SELECT * FROM apps WHERE token = "{}"'.format(token)
            self.database.cursor.execute(sql)
            return self.database.cursor.fetchone()
        except Exception as e:
            self.logger.log_info("Database fetch error: {}".format(str(e)))
            return {}
