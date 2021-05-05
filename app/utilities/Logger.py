import logging
import os
import datetime
from app.models.models import User


class Logger:
    def __init__(self, project_dir, log_file='app.log', log_level='DEBUG'):
        self.__user_id = None
        self.__app = None
        self.__phone = None
        self.__log_dir = os.path.join(project_dir, 'logs')
        self.__log_file = os.path.join(self.__log_dir, log_file)
        self.__check_if_log_file_is_writable(self.__log_file)
        logging.basicConfig(
            level=log_level.upper(),
            format='[%(asctime)s] %(levelname)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
            filename=self.__log_file,
            filemode='a',
        )
        self.__logger = logging.getLogger()

    def initialize(self):
        self.set_app()
        self.set_phone()

    def get_log_dir(self):
        return self.__log_dir

    def log_info(self, message: str):
        self.__custom_logger(logging.INFO, message)

    def log_warning(self, message: str):
        self.__custom_logger(logging.WARNING, message)

    def log_error(self, message: str):
        self.__custom_logger(logging.ERROR, message)

    def log_critical(self, message: str):
        self.__custom_logger(logging.CRITICAL, message)

    def get_logger(self):
        return self.__logger

    def set_phone(self, phone=None):
        self.__phone = phone

    def set_app(self, app=None):
        self.__app = app

    def set_level(self, level: str):
        self.__logger.setLevel(level.upper())

    def log_user_action(self, user: User, action, component: dict):
        log_msg = f'ACTION: {action}, OPERATOR: {user.email}, COMPONENT: {component}'
        try:
            log_date = datetime.datetime.now().strftime("%Y-%m-%d")
            log_file = f'{self.__log_dir}/actions.{log_date}.log'
            log = self.__self_made_logger('user-actions', log_file)
            log.log(logging.INFO, log_msg)
        except Exception as e:
            self.log_error(f'Failed to log action [{log_msg}]: {str(e)}')

    def __custom_logger(self, level: int, message: str):
        try:
            msg = "[App: {}, Phone: {}] {}".format(
                self.__app,
                self.__phone,
                message
            )
            self.__logger.log(level, msg)
            self.__app_logger(level, msg)
        except Exception as e:
            print('Failed to start the logger: {}'.format(str(e)))
            exit(1)

    @staticmethod
    def __check_if_log_file_is_writable(log_file):
        try:
            with open(log_file, 'a+') as f:
                f.close()
        except Exception as e:
            print(f'Log file [{log_file}] not writable or does not exist: {str(e)}')
            exit(1)

    def set_user_id(self, user_id):
        self.__user_id = user_id

    def __app_logger(self, level, msg):
        if self.__user_id and self.__user_id > 0:
            try:
                log_dir = f'{self.__log_dir}/user-logs/{self.__user_id}'
                if not os.path.exists(log_dir):
                    os.system(f'mkdir -p {log_dir}')
                    os.system(f'chown -R asterisk {self.__log_dir}')
                log_date = datetime.datetime.now().strftime("%Y-%m-%d")
                log_file = f'{log_dir}/{log_date}.log'

                log = self.__self_made_logger('user-log', log_file)
                log.log(level, msg)
            except Exception as e:
                self.log_error(f'Error logging user based log: {str(e)}')

    @staticmethod
    def __self_made_logger(logger_name, log_file):
        file_handler = logging.FileHandler(log_file)
        formatter = logging.Formatter(
            fmt='[%(asctime)s] %(levelname)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        log = logging.getLogger(logger_name)  # root logger - Good to get it only once.
        for log_handler in log.handlers[:]:  # remove the existing file handlers
            if isinstance(log_handler, logging.FileHandler):
                log.removeHandler(log_handler)
        log.addHandler(file_handler)  # set the new handler
        log.setLevel(logging.INFO)
        return log
