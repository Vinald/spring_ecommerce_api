import sys
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
            self.__logger.log_critical("Redis -> failed to get cached data: {}".format(str(e)))
            return None

    def save(self, key: str, value, time_in_seconds: int):
        try:
            self.__cache.set(key, value, time_in_seconds)
        except Exception as e:
            self.__logger.log_critical("Redis -> failed to cache data: {}".format(str(e)))

    def delete(self, key: str):
        try:
            self.__cache.delete(key)
        except Exception as e:
            self.__logger.log_critical("Redis -> failed to delete data: {}".format(str(e)))

    def cache_exists(self, key):
        return self.get(key) is not None

    def __initialize(self):
        try:
            self.__config.set_section('redis')
            host = self.__config.get('host')
            port = self.__config.get_int('port')
            self.__cache = Redis(host=host, port=port, socket_connect_timeout=2)
            self.__cache.ping()
        except Exception as e:
            # CHANGED: was exit(1) which killed the entire Flask process including
            # any active Asterisk calls. Now prints to stderr and raises RuntimeError
            # so the caller can decide how to handle Redis being unavailable.
            msg = "Redis -> connection failed: {}".format(str(e))
            print(msg, file=sys.stderr)
            try:
                self.__logger.log_critical(msg)
            except Exception:
                pass
            raise RuntimeError(msg) from e
