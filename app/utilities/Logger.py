import logging
import os


class Logger:
    def __init__(self, project_dir, log_level='DEBUG'):
        self.__app = None
        self.__phone = None
        self.__log_dir = os.path.join(project_dir, 'logs')
        self.__log_file = os.path.join(self.__log_dir, 'app.log')
        self.__check_if_log_file_is_writable()
        logging.basicConfig(
            level=log_level.upper(),
            format='[%(asctime)s] %(levelname)s: %(message)s',
            datefmt='%m/%d/%Y %H:%M:%S',
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

    def __custom_logger(self, level: int, message: str):
        try:
            msg = "[App: {}, Phone: {}] {}".format(
                self.__app,
                self.__phone,
                message
            )
            self.__logger.log(level, msg)
        except Exception as e:
            print('Failed to start the logger: {}'.format(str(e)))
            exit(1)

    def __check_if_log_file_is_writable(self):
        try:
            with open(self.__log_file, 'a+') as f:
                f.close()
        except Exception as e:
            print('Log file not writable or does not exist: {}'.format(str(e)))
            exit(1)
