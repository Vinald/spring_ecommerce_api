from redis import Redis
from src.Config import Config
from src.Logger import Logger


class CacheManager:
    def __init__(self, config: Config, logger: Logger):
        self.config = config
        self.logger = logger
        self.__initialize()

    def get(self, key: str):
        try:
            return self.cache.get(key)
        except Exception as e:
            self.logger.log_critical("Redis -> failed to get cached data: {}".format(str(e)))
            return None

    def save(self, key: str, value, time_in_seconds: int):
        try:
            self.cache.set(key, value, time_in_seconds)
        except Exception as e:
            self.logger.log_critical("Redis -> failed to cache data: {}".format(str(e)))

    def delete(self, key: str):
        try:
            self.cache.delete(key)
        except Exception as e:
            self.logger.log_critical("Redis -> failed to delete data: {}".format(str(e)))

    def __initialize(self):
        try:
            self.config.set_section('redis')
            host = self.config.get('host')
            port = self.config.get('port')
            self.cache = Redis(host=host, port=port, socket_connect_timeout=2)
            self.cache.ping()
        except Exception as e:
            self.logger.log_critical("Redis -> connection failed: {}".format(str(e)))
            exit(1)
