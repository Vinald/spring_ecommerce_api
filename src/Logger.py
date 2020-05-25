import logging


class Logger:
    def __init__(self, log_dir, phone=None):
        self.phone = phone
        self.log_dir = log_dir
        self.check_if_log_file_is_writable()
        logging.basicConfig(
            level=logging.INFO,
            format='[%(asctime)s] %(levelname)s: %(message)s',
            datefmt='%m/%d/%Y %H:%M:%S',
            filename=self.log_dir + '/app.log',
            filemode='a',
        )
        self.logger = logging.getLogger()

    def get_logger(self):
        return self.logger

    def set_phone(self, phone):
        self.phone = phone

    def log_info(self, message):
        try:
            if self.phone:
                self.logger.info('[Number: {}]: {}'.format(self.phone, str(message)))
            else:
                self.logger.info('{}'.format(str(message)))
        except Exception as e:
            print('Failed to start the logger: {}'.format(str(e)))
            exit()

    def check_if_log_file_is_writable(self):
        try:
            with open(self.log_dir + '/app.log', 'a+') as f:
                f.close()
                pass
        except Exception as e:
            print('Log file not writable or does not exist: {}'.format(str(e)))
            exit()
