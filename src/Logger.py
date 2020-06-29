import logging


class Logger:
    def __init__(self, log_dir, phone=None):
        self.__app = None
        self.__token = None
        self.__external_id = None
        self.__phone = phone
        self.__log_dir = log_dir
        self.__check_if_log_file_is_writable()
        logging.basicConfig(
            level=logging.INFO,
            format='[%(asctime)s] %(levelname)s: %(message)s',
            datefmt='%m/%d/%Y %H:%M:%S',
            filename=self.__log_dir + '/app.log',
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

    def set_token(self, token=None):
        self.__token = token

    def set_external_id(self, external_id=None):
        self.__external_id = external_id

    def __custom_logger(self, level: int, message: str):
        try:
            msg = "[Application: {}, Token: {}, Number: {}, External ID: {}] {}".format(
                self.__app,
                self.__token,
                self.__phone,
                self.__external_id,
                message
            )
            self.logger.log(level, msg)
        except Exception as e:
            print('Failed to start the logger: {}'.format(str(e)))
            exit(1)

    def __check_if_log_file_is_writable(self):
        try:
            with open(self.__log_dir + '/app.log', 'a+') as f:
                f.close()
                pass
        except Exception as e:
            print('Log file not writable or does not exist: {}'.format(str(e)))
            exit(1)
