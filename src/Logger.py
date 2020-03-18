import logging


class Logger:
    def __init__(self, log_dir, phone):
        self.phone = phone
        self.log_dir = log_dir
        self.check_if_log_file_is_writable()
        logging.basicConfig(
            level=logging.INFO,
            format='[%(asctime)s] %(levelname)s: %(message)s',
            filename=self.log_dir + '/app.log',
            filemode='w+',
        )
        self.logger = logging.getLogger()

    def get_logger(self):
        return self.logger

    def log_info(self, message):
        try:
            self.logger.info('[Number: {}]: {}'.format(self.phone, str(message)))
        except Exception as e:
            print('Failed to start the logger: {}'.format(str(e)))
            exit()

    def check_if_log_file_is_writable(self):
        try:
            with open(self.log_dir + '/app.log', 'w+') as f:
                pass
        except Exception as e:
            print('Log file not writable or does not exist: {}'.format(str(e)))
            exit()
