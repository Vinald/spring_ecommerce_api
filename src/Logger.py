import logging


class Logger:
    def __init__(self, log_dir, phone):
        self.phone = phone
        self.logger = logging.basicConfig(
            level=logging.INFO,
            format='[%(asctime)s] %(levelname)s: %(message)s',
            filename=log_dir + '/app.log',
            filemode='w',
        )

    def get_logger(self):
        return self.logger

    def log_info(self, message):
        self.logger.info('[Number: {}]: {}'.format(self.phone, str(message)))
