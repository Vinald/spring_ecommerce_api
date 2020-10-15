from datetime import datetime
import json
import time
from app.manager.CacheManager import CacheManager
from app.utilities.Database import Database
from app.utilities.Logger import Logger


class CDRManager:
    __CDR_TABLE = 'cdr'
    __TIME_FORMAT = '%H:%M:%S'

    def __init__(self, cache: CacheManager, database: Database, logger: Logger):
        self.__cache = cache
        self.__logger = logger
        self.__database = database

    def update_call_start_time(self, call_id):
        try:
            key = 'cdr-{}'.format(call_id)
            cdr_data = self.__cache.get(key)
            if cdr_data is not None:
                data = json.loads(cdr_data)
                data['call_state'] = 'ANSWERED'
                data['call_start_time'] = time.strftime('%H:%M:%S')
                self.__cache.save(key, json.dumps(data), 3600)
        except Exception as e:
            self.__logger.log_critical("CDR update failure: {}".format(str(e)))

    def flush_cdr_to_db(self, call_id, call_state):
        try:
            key = 'cdr-{}'.format(call_id)
            cdr_data = self.__cache.get(key)
            if cdr_data is not None:
                self.__cache.delete(key)
                data = json.loads(cdr_data)
                data['call_state'] = call_state
                self.__database.insert(data, self.__CDR_TABLE)
        except Exception as e:
            self.__logger.log_critical("CDR flush failure: {}".format(str(e)))

    def end_call_and_flush_cdr_to_db(self, call_id):
        try:
            key = 'cdr-{}'.format(call_id)
            cdr_data = self.__cache.get(key)
            if cdr_data is not None:
                self.__cache.delete(key)
                data = json.loads(cdr_data)
                end_time = time.strftime(self.__TIME_FORMAT)
                start_time = data['call_start_time']
                data['call_end_time'] = end_time
                time_delta = (
                    datetime.strptime(end_time, self.__TIME_FORMAT)
                    -
                    datetime.strptime(start_time, self.__TIME_FORMAT)
                )
                data['duration'] = time_delta.seconds
                self.__database.insert(data, self.__CDR_TABLE)
        except Exception as e:
            self.__logger.log_critical("CDR flush failure: {}".format(str(e)))
