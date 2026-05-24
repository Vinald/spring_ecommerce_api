"""
Call Detail Record (CDR) manager.

Handles writing CDR data from the Redis cache into the database when a call
ends. Uses a two-phase approach: data is assembled in Redis during the call
and flushed to the DB on hangup.

CHANGED: Previously inserted CDRs via the raw PyMySQL Database.insert() method.
Now uses a SQLAlchemy session for all DB writes, eliminating the second
connection pool and making CDR inserts participate in the same ORM session
management as the rest of the application.
"""
import time
import json
from datetime import datetime
from sqlalchemy.orm import Session as SASession
from app.manager.CacheManager import CacheManager
from app.models.models import CDR
from app.utilities.Logger import Logger


class CDRManager:
    __TIME_FORMAT = '%H:%M:%S'

    def __init__(self, cache: CacheManager, session_factory, logger: Logger):
        # CHANGED: was __init__(self, cache, database: Database, logger)
        # Now receives a SQLAlchemy session_factory instead of the raw Database
        # wrapper, removing the remaining PyMySQL insert() dependency.
        self.__cache = cache
        self.__session_factory = session_factory
        self.__logger = logger

    def _get_session(self) -> SASession:
        """Open a new SQLAlchemy session for this operation."""
        return self.__session_factory()

    def update_call_start_time(self, unique_id: str):
        """
        Mark the call as ANSWERED and store the Unix start timestamp in Redis.
        The Unix timestamp is used by end_call_and_flush_cdr_to_db() to
        calculate duration correctly across midnight boundaries.
        """
        try:
            key = 'cdr-{}'.format(unique_id)
            cdr_data = self.__cache.get(key)
            if cdr_data is not None:
                data = json.loads(cdr_data)
                data['call_state'] = 'ANSWERED'
                # CHANGED: store Unix float for midnight-safe duration calculation.
                data['call_start_timestamp'] = time.time()
                data['call_start_time'] = time.strftime(self.__TIME_FORMAT)
                self.__cache.save(key, json.dumps(data), 3600)
        except Exception as e:
            self.__logger.log_critical("CDR update failure: {}".format(str(e)))

    def flush_cdr_to_db(self, unique_id: str, call_state: str):
        """Write a CDR for a call that did not complete (FAILED, BUSY, NO_ANSWER)."""
        try:
            key = 'cdr-{}'.format(unique_id)
            cdr_data = self.__cache.get(key)
            if cdr_data is not None:
                self.__cache.delete(key)
                data = json.loads(cdr_data)
                data['call_state'] = call_state
                # Strip internal timestamp — not a DB column.
                data.pop('call_start_timestamp', None)
                self._insert_cdr(data)
        except Exception as e:
            self.__logger.log_critical("CDR flush failure: {}".format(str(e)))

    def end_call_and_flush_cdr_to_db(self, unique_id: str):
        """Write a CDR for a completed (ANSWERED) call, computing duration."""
        try:
            key = 'cdr-{}'.format(unique_id)
            cdr_data = self.__cache.get(key)
            if cdr_data is not None:
                self.__cache.delete(key)
                data = json.loads(cdr_data)
                end_time = time.strftime(self.__TIME_FORMAT)
                data['call_end_time'] = end_time

                # CHANGED: use Unix timestamp for duration — correct across midnight.
                start_ts = data.pop('call_start_timestamp', None)
                if start_ts is not None:
                    data['duration'] = max(0, int(time.time() - start_ts))
                else:
                    # Fallback for CDRs written before this fix was deployed.
                    start_time = data.get('call_start_time')
                    if start_time:
                        delta = datetime.strptime(end_time, self.__TIME_FORMAT) - \
                                datetime.strptime(start_time, self.__TIME_FORMAT)
                        data['duration'] = max(0, delta.seconds)
                    else:
                        data['duration'] = 0

                self._insert_cdr(data)
        except Exception as e:
            self.__logger.log_critical("CDR flush failure: {}".format(str(e)))

    def get_number_of_processed_calls(self) -> int:
        """
        Return the count of answered calls.
        CHANGED: was a raw SQL cursor.execute() call. Now uses ORM count().
        """
        session = self._get_session()
        try:
            return session.query(CDR).filter(CDR.call_state == 'ANSWERED').count()
        except Exception as e:
            self.__logger.log_critical("CDR count failure: {}".format(str(e)))
            return 0
        finally:
            session.close()

    def _insert_cdr(self, data: dict):
        """
        Insert a CDR row using SQLAlchemy ORM.
        CHANGED: was Database.insert(data, 'cdr') via raw PyMySQL cursor.
        Now maps the data dict to a CDR model instance and uses session.add().
        Only known CDR columns are mapped — any extra keys are safely ignored.
        """
        session = self._get_session()
        try:
            cdr = CDR(
                app_name=data.get('app_name', ''),
                creation_date=data.get('creation_date'),
                call_start_time=data.get('call_start_time'),
                call_end_time=data.get('call_end_time'),
                duration=data.get('duration', 0),
                caller_id=data.get('caller_id', ''),
                dialed_number=data.get('dialed_number', ''),
                call_state=data.get('call_state'),
                peer=data.get('peer'),
                call_direction=data.get('call_direction', 'OUTGOING'),
                token=data.get('token'),
                call_id=data.get('call_id'),
                external_id=data.get('external_id'),
            )
            session.add(cdr)
            session.commit()
        except Exception as e:
            session.rollback()
            self.__logger.log_critical("CDR insert failure: {}".format(str(e)))
        finally:
            session.close()
