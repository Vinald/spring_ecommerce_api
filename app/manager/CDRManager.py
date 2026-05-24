import time
import json
from datetime import datetime
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

    def update_call_start_time(self, unique_id):
        try:
            key = 'cdr-{}'.format(unique_id)
            cdr_data = self.__cache.get(key)
            if cdr_data is not None:
                data = json.loads(cdr_data)
                data['call_state'] = 'ANSWERED'
                # CHANGED: store a Unix float timestamp alongside the formatted time.
                # This is used in end_call_and_flush_cdr_to_db() for duration
                # calculation to avoid the midnight boundary bug (see below).
                data['call_start_timestamp'] = time.time()
                data['call_start_time'] = time.strftime(self.__TIME_FORMAT)
                self.__cache.save(key, json.dumps(data), 3600)
        except Exception as e:
            self.__logger.log_critical("CDR update failure: {}".format(str(e)))

    def flush_cdr_to_db(self, unique_id, call_state):
        try:
            key = 'cdr-{}'.format(unique_id)
            cdr_data = self.__cache.get(key)
            if cdr_data is not None:
                self.__cache.delete(key)
                data = json.loads(cdr_data)
                data['call_state'] = call_state
                # Remove the internal Unix timestamp — it is not a DB column.
                data.pop('call_start_timestamp', None)
                self.__database.insert(data, self.__CDR_TABLE)
        except Exception as e:
            self.__logger.log_critical("CDR flush failure: {}".format(str(e)))

    def end_call_and_flush_cdr_to_db(self, unique_id):
        try:
            key = 'cdr-{}'.format(unique_id)
            cdr_data = self.__cache.get(key)
            if cdr_data is not None:
                self.__cache.delete(key)
                data = json.loads(cdr_data)
                end_time = time.strftime(self.__TIME_FORMAT)
                data['call_end_time'] = end_time

                # CHANGED: the original code subtracted two HH:MM:SS strings using
                # datetime.strptime(). This produced a negative duration for calls
                # that span midnight (e.g. start 23:58, end 00:02 → -86 seconds).
                # Fix: use the stored Unix float timestamp so the subtraction is
                # always correct regardless of clock rollover.
                start_ts = data.pop('call_start_timestamp', None)
                if start_ts is not None:
                    data['duration'] = max(0, int(time.time() - start_ts))
                else:
                    # Fallback for CDRs written before this fix was deployed.
                    start_time = data.get('call_start_time')
                    if start_time:
                        start_dt = datetime.strptime(start_time, self.__TIME_FORMAT)
                        end_dt = datetime.strptime(end_time, self.__TIME_FORMAT)
                        delta = end_dt - start_dt
                        data['duration'] = max(0, delta.seconds)
                    else:
                        data['duration'] = 0

                self.__database.insert(data, self.__CDR_TABLE)
        except Exception as e:
            self.__logger.log_critical("CDR flush failure: {}".format(str(e)))

    def get_number_of_processed_calls(self):
        sql = "SELECT count(id) count FROM cdr WHERE call_state = 'ANSWERED'"
        self.__database.reconnect()
        self.__database.cursor.execute(sql)
        db_data = self.__database.cursor.fetchone()
        return int(db_data['count'])
