import json
import requests
import datetime
from redis import Redis
from app.manager.CDRManager import CDRManager
from app.utilities.Hash import Hash
from app.utilities.Logger import Logger

# Timeout (seconds) for outbound status-URL callbacks
_HTTP_TIMEOUT = 10


class AsteriskEventsHandler:
    __COMPLETED = 'COMPLETED'
    __CALL_LINK = "Academy IVR"

    __STATUS_CODES = {
        '0': 'FAILED',
        '3': 'NO_ANSWER',
        '4': 'COMPLETED',
        '5': 'BUSY',
        '8': 'FAILED'
    }

    __CHANNEL_REASONS = {
        'BUSY': 'busy',
        'COMPLETED': 'application',
        'FAILED': 'unreachable',
        'NO_ANSWER': 'timeout'
    }

    def __init__(self, logger: Logger, cache: Redis, cdr: CDRManager):
        self.__cdr = cdr
        self.__cache = cache
        self.__logger = logger
        self.__session = None

    def handle_originate_event(self, status, call_id, unique_id):
        state = self.__get_channel_status(status)
        call_details = self.__cache.get(call_id)

        if call_details is not None:
            call_data = json.loads(call_details)
            phone = call_data['phone']
            app_data = call_data['app-data']
            external_id = call_data['external_id']
            initiated = True if call_data['initiated'] == 'yes' else False

            app_name = app_data['name']
            status_url = app_data['status_url']

            if not initiated:
                call_data['initiated'] = 'yes'
                data = json.dumps(call_data)
                self.__cache.set(call_id, data, 1800)
                self.__process_call(
                    state,
                    call_id,
                    unique_id,
                    phone,
                    external_id,
                    status_url,
                    app_name
                )

    def handle_hangup_event(self, unique_id, channel):
        key = Hash.hash(unique_id)
        cache_result = self.__cache.get(key)

        if cache_result is not None:
            self.__cache.delete(key)
            data = json.loads(cache_result)
            phone = data['phone']
            if 'is_incoming' not in data.keys():
                call_id = data['call_id']
                self.__cdr.end_call_and_flush_cdr_to_db(call_id)
                results = self.__get_content(data['link'])
                log_msg = "Call hangup detected for channel: {} results: {}"
                self.__logger.set_app(data['app'])
                self.__logger.set_phone(phone)
                self.__logger.log_info(log_msg.format(channel, results))
            else:
                self.__cdr.end_call_and_flush_cdr_to_db(key)
                self.__logger.set_app()
                self.__logger.set_phone(phone)
                self.__logger.log_info("Incoming call hangup detected: {}".format(phone))

    def __get_channel_status(self, status: str):
        return self.__STATUS_CODES.get(status, 'UNKNOWN')

    def __channel_reason(self, status: str):
        return self.__CHANNEL_REASONS.get(status, 'unknown')

    def __gen_status_link(self, call_id, status, reason, status_url, **optional_params):
        stamp = "_dt={}".format(self.__current_timestamp())
        status_param = "status={}".format(status)
        reason_param = "reason={}".format(reason)

        link = "{}/{}".format(status_url, call_id)
        status_link = "{}.vxml?{}&{}&{}".format(link, stamp, status_param, reason_param)

        if 'externalID' in optional_params and 'externalType' in optional_params:
            external_id = optional_params['externalID']
            external_type = optional_params['externalType']
            params = '&externalId={}&externalType={}'.format(external_id, external_type)
            return status_link + params

        return status_link

    def __in_progress(self, call_id, status_url, phone, app_name):
        reason = self.__channel_reason(self.__COMPLETED)
        self.__update_call_status(call_id, 'IN_PROGRESS', reason, status_url, phone, app_name)

    def __update_call_status(self, call_id, status, reason, status_url, phone, app_name):
        link = self.__gen_status_link(call_id, status, reason, status_url)
        results = self.__get_content(link)
        log_msg = "Call status: {}, call_id: {}, external_app_results: {}"
        self.__logger.set_app(app_name)
        self.__logger.set_phone(phone)
        self.__logger.log_info(log_msg.format(status, call_id, results))

    def __process_call(self, state, call_id, asterisk_unique_id, phone, external_id, status_url, app_name):
        if state == self.__COMPLETED and asterisk_unique_id != '<unknown>':
            self.__cdr.update_call_start_time(call_id)
            key = Hash.hash(asterisk_unique_id)
            reason = self.__channel_reason(self.__COMPLETED)
            hangup_link = self.__gen_status_link(
                call_id,
                self.__COMPLETED,
                reason,
                status_url,
                externalID=str(external_id),
                externalType=self.__CALL_LINK
            )
            data = json.dumps({'link': hangup_link, 'phone': phone, 'app': app_name, 'call_id': call_id})
            self.__cache.set(key, data, 1800)
            self.__in_progress(call_id, status_url, phone, app_name)
        else:
            self.__cdr.flush_cdr_to_db(call_id, state)
            reason = self.__channel_reason(state)
            self.__update_call_status(call_id, state, reason, status_url, phone, app_name)

    @staticmethod
    def __current_timestamp():
        timestamp = datetime.datetime.now()
        timestamp = timestamp.timestamp()
        timestamp = round(timestamp, 3)
        timestamp = str(timestamp).replace('.', '')
        return timestamp

    def __get_content(self, link):
        if not self.__session:
            self.__session = requests.Session()
        try:
            return self.__session.get(link, timeout=_HTTP_TIMEOUT).text
        except requests.exceptions.RequestException as e:
            self.__logger.log_error("Failed to reach status URL [{}]: {}".format(link, str(e)))
            return ''
