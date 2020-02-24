import logging


class Logger:
    def __init__(self, logger_dir, phone):
        self.logger_dir = logger_dir
        self.phone = phone

    def log_config(self):
        logging.basicConfig(
            level=logging.INFO,
            format='[%(asctime)s] %(levelname)s: %(message)s',
            filename=self.logger_dir + '/app.log',
            filemode='w',
        )

    def log_info(self, message):
        self.log_config()
        logging.info('[Number: {}]: {}'.format(self.phone, str(message)))