import os
from configparser import ConfigParser
from src.Logger import Logger


class Config:
    def __init__(self, working_dir: str, logger: Logger, section=None, config_file='config.ini'):
        self.logger = logger
        self.config = ConfigParser()
        self.section = section
        self.working_dir = working_dir
        self.config_file = config_file
        self.__parse_config_file()

    def get_audio_path(self):
        return self.get('audio_path')

    def get_starting_url(self):
        start_url = 'http://{}/motech-platform-server/module/callflows/in/voxeo/flows/MainFlow.vxml?phone='
        return start_url.format(self.get('host'))

    def get_status_base_url(self):
        status_url = 'http://{}/motech-platform-server/module/callflows/status/'
        return status_url.format(self.get('host'))

    def get_ami_host(self):
        return self.get('host')

    def get_ami_port(self):
        return self.get_int('port')

    def get_ami_user(self):
        return self.get('user')

    def get_ami_pass(self):
        return self.get('pass')

    def get_sip_trunk(self):
        return self.get('trunk')

    def get(self, key: str, default=None):
        try:
            return str(self.config[self.section][key])
        except Exception as e:
            self.logger.log_info('Config key error: {}'.format(str(e)))
            return default

    def get_int(self, key: str, default=0):
        try:
            return int(self.get(key, default))
        except Exception as e:
            self.logger.log_info('Conversion error: {}'.format(str(e)))
            return default

    def set_section(self, section: str):
        self.section = section

    def __parse_config_file(self):
        try:
            self.config.read(os.path.join(self.working_dir, self.config_file))
        except Exception as e:
            log_msg = 'Failed to read config file: {}'.format(str(e))
            self.logger.log_info(log_msg)
            exit()
