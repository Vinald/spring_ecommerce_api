import logging
import os


class Logger:
    def __init__(self, project_dir):
        self.__app = None
        self.__phone = None
        self.__log_file = os.path.join(project_dir, 'app.log')
        self.__check_if_log_file_is_writable()
        logging.basicConfig(
            level=logging.INFO,
            format='[%(asctime)s] %(levelname)s: %(message)s',
            datefmt='%m/%d/%Y %H:%M:%S',
            filename=self.__log_file,
            filemode='a',
        )
        self.logger = logging.getLogger()

    def log_info(self, message: str):
        self.__custom_logger(logging.INFO, message)

    def log_warning(self, message: str):
        self.__custom_logger(logging.WARNING, message)

    def log_error(self, message: str):
        self.__custom_logger(logging.ERROR, message)

    def log_critical(self, message: str):
        self.__custom_logger(logging.CRITICAL, message)

    def get_logger(self):
        return self.logger

    def set_phone(self, phone=None):
        self.__phone = phone

    def set_app(self, app=None):
        self.__app = app

    def __custom_logger(self, level: int, message: str):
        try:
            msg = "[App: {}, Phone: {}] {}".format(
                self.__app,
                self.__phone,
                message
            )
            self.logger.log(level, msg)
        except Exception as e:
            print('Failed to start the logger: {}'.format(str(e)))
            exit(1)

    def __check_if_log_file_is_writable(self):
        try:
            with open(self.__log_file, 'a+') as f:
                f.close()
                pass
        except Exception as e:
            print('Log file not writable or does not exist: {}'.format(str(e)))
            exit(1)
