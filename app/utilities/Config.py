import json
import os
from app.utilities.Logger import Logger


class Config:
    def __init__(
        self,
        project_dir,
        logger: Logger,
        section=None,
        config_file='config.json',
        config_dev_file='config.dev.json'
    ):
        self.__config = None
        self.__logger = logger
        self.__section = section
        self.__project_dir = project_dir
        self.__config_file = os.path.join(project_dir, config_file)
        self.__config_dev_file = os.path.join(project_dir, config_dev_file)
        self.__parse_config_file()

    def get(self, key: str, default=None):
        try:
            return str(self.__config[self.__section][key])
        except Exception as e:
            self.__logger.log_warning('Config key not found: {}'.format(str(e)))
            return default

    def get_int(self, key: str, default=0):
        try:
            return int(self.get(key, default))
        except Exception as e:
            self.__logger.log_warning('Conversion to int failed: {}'.format(str(e)))
            return default

    def get_bool(self, key: str, default=False):
        try:
            return True if self.get(key, default) == 'true' else False
        except Exception as e:
            self.__logger.log_warning('Conversion to bool failed: {}'.format(str(e)))
            return default

    def set_section(self, section: str):
        self.__section = section
        return self

    def get_section_content(self, section, default=None):
        try:
            return self.__config[section]
        except Exception as e:
            self.__logger.log_warning('Config section not found: {}'.format(str(e)))
            return default

    def __parse_config_file(self):
        try:
            if not os.path.exists(self.__config_file):
                os.system("cp {} {}".format(self.__config_dev_file, self.__config_file))
                os.system("chmod 775 {}".format(self.__config_file))
            file = open(self.__config_file)
            self.__config = json.load(file)
            file.close()
        except Exception as e:
            log_msg = 'Failed to read config file: {}'.format(str(e))
            self.__logger.log_critical(log_msg)
            exit(1)
