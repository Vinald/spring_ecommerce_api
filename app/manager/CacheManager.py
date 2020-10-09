from redis import Redis
from app.utilities.Config import Config
from app.utilities.Logger import Logger


class CacheManager:
    def __init__(self, config: Config, logger: Logger):
        self.__cache = None
        self.__config = config
        self.__logger = logger
        self.__initialize()
        self.__logger.initialize()

    def get(self, key: str):
        try:
            return self.__cache.get(key)
        except Exception as e:
            msg = "Redis -> failed to get cached data: {}".format(str(e))
            self.__logger.log_critical(msg)
            return None

    def save(self, key: str, value, time_in_seconds: int):
        try:
            self.__cache.set(key, value, time_in_seconds)
        except Exception as e:
            msg = "Redis -> failed to cache data: {}".format(str(e))
            self.__logger.log_critical(msg)

    def delete(self, key: str):
        try:
            self.__cache.delete(key)
        except Exception as e:
            msg = "Redis -> failed to delete data: {}".format(str(e))
            self.__logger.log_critical(msg)

    def __initialize(self):
        try:
            self.__config.set_section('redis')
            host = self.__config.get('host')
            port = self.__config.get('port')
            self.__cache = Redis(host=host, port=port, socket_connect_timeout=2)
            self.__cache.ping()
        except Exception as e:
            msg = "Redis -> connection failed: {}".format(str(e))
            self.__logger.log_critical(msg)
            exit(1)
