import datetime
import uuid
from src.AppDatabase import AppDatabase
from src.Hash import Hash
from src.Logger import Logger


class AppManager:
    def __init__(self, database: AppDatabase, logger: Logger):
        self.logger = logger
        self.database = database
        self.database.reconnect()

    def get_token_by_dialed_number(self, dialed_num: str):
        try:
            self.database.reconnect()
            sql = 'SELECT token FROM apps WHERE phone = "{}"'.format(dialed_num)
            self.database.cursor.execute(sql)
            data = self.database.cursor.fetchone()
            return data['token']
        except Exception as e:
            self.logger.log_info("Database fetch error: {}".format(str(e)))
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
            self.database.reconnect()
            sql = 'SELECT * FROM apps WHERE token = "{}"'.format(token)
            self.database.cursor.execute(sql)
            return self.database.cursor.fetchone()
        except Exception as e:
            self.logger.log_info("Database fetch error: {}".format(str(e)))
            return {}

    def get_all_apps(self):
        try:
            self.database.reconnect()
            sql = 'SELECT * FROM apps'
            self.database.cursor.execute(sql)
            return self.database.cursor.fetchall()
        except Exception as e:
            self.logger.log_info("Database fetch error: {}".format(str(e)))
            return []

    def create_app(self, app_name, app_voice_url, app_status_url, phone):
        token = self.token_generator()

        data = {
            'name': app_name,
            'phone': phone,
            'token': token,
            'voice_url': app_voice_url,
            'status_url': app_status_url,
            'date_created': datetime.datetime.now()
        }

        try:
            self.database.reconnect()
            cursor = self.database.get_cursor()
            cursor.execute('SELECT name FROM apps WHERE name="{}"'.format(app_name))
            if int(cursor.rowcount) > 0:
                return {'status': 'error', 'message': 'Application already exists'}
            self.database.insert(data, AppDatabase.APPS_TABLE)
            return {'status': 'success', 'message': 'Application added successfully'}
        except Exception as e:
            message = "An error occurred while adding application: {}".format(str(e))
            return {'status': 'error', 'message': message}

    def update_app(self, app_id: int, app_name, app_voice_url, app_status_url, phone):
        data = {
            'name': app_name,
            'phone': phone,
            'voice_url': app_voice_url,
            'status_url': app_status_url,
            'date_modified': datetime.datetime.now()
        }

        try:

            self.database.update(app_id, data, 'apps')
            return {'status': 'success', 'message': 'Application updated successfully'}
        except Exception as e:
            message = "An error occurred while updating application: {}".format(str(e))
            return {'status': 'error', 'message': message}

    def delete_app(self, app_id: int):
        try:
            conn = self.database.get_conn()
            cursor = self.database.get_cursor()
            cursor.execute('DELETE FROM apps WHERE id={} LIMIT 1'.format(app_id))
            conn.commit()
            return {'status': 'success', 'message': 'Application deleted successfully'}
        except Exception as e:
            message = "An error occurred while deleting app: {}".format(str(e))
            return {'status': 'error', 'message': message}

    @staticmethod
    def token_generator():
        unique_id = str(uuid.uuid1())
        return Hash.hash(unique_id)
