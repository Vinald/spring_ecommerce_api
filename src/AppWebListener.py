import json
import requests
import datetime
from redis import Redis
from src.Hash import Hash
from src.Logger import Logger


class AppWebListener:
    BUSY = 'BUSY'
    FAILED = 'FAILED'
    COMPLETED = 'COMPLETED'
    call_link_uganda = "Call Link Uganda"

    def __init__(self, logger: Logger, cache: Redis):
        self.cache = cache
        self.logger = logger

    @staticmethod
    def get_channel_status(status: str):
        codes = {
            '0': 'FAILED',
            '3': 'NO_ANSWER',
            '4': 'COMPLETED',
            '5': 'BUSY',
            '8': 'FAILED'
        }
        return codes[status] if status in codes.keys() else 'UNKNOWN'

    @staticmethod
    def channel_reason(status: str):
        reasons = {
            'BUSY': 'busy',
            'COMPLETED': 'application',
            'FAILED': 'unreachable',
            'NO_ANSWER': 'timeout'
        }
        return reasons[status] if status in reasons.keys() else 'unknown'

    def handle_hangup_event(self, unique_id, channel):
        key = Hash.hash(unique_id)
        cache_result = self.cache.get(key)

        if cache_result is not None:
            self.cache.delete(key)
            data = json.loads(cache_result)
            phone = data['phone']
            results = str(requests.get(data['link']).content)
            log_msg = "Call hangup detected for channel: {} results: {}"
            self.logger.set_app(data['app'])
            self.logger.set_phone(phone)
            self.logger.log_info(log_msg.format(channel, results))

    def gen_status_link(self, call_id, status, reason, status_url, **optional_params):
        """
        :param status_url:
        :param call_id:
        :param status: NO_ANSWER,COMPLETED,FAILED,BUSY
        :param reason: timeout,application,unreachable,busy
        :param optional_params: externalID, externalType >> Used is status == COMPLETED
        :return: status_link
        """

        stamp = "_dt={}".format(self.__current_timestamp())
        status = "status={}".format(status)
        reason = "reason={}".format(reason)

        link = "{}/{}".format(status_url, call_id)
        status_link = "{}.vxml?{}&{}&{}".format(link, stamp, status, reason)

        if 'externalID' and 'externalType' in optional_params:
            external_id = optional_params['externalID']
            external_type = optional_params['externalType']

            params = '&externalId={}&externalType={}'.format(external_id, external_type)
            return status_link + params

        return status_link

    def in_progress(self, call_id, status_url, phone, app_name):
        reason = self.channel_reason(self.COMPLETED)
        self.update_call_status(call_id, 'IN_PROGRESS', reason, status_url, phone, app_name)

    def update_call_status(self, call_id, status, reason, status_url, phone, app_name):
        link = self.gen_status_link(call_id, status, reason, status_url)
        results = str(requests.get(link).content)
        log_msg = "Call status: {}, call_id: {}, external_app_results: {}"
        self.logger.set_app(app_name)
        self.logger.set_phone(phone)
        self.logger.log_info(log_msg.format(status, call_id, results))

    def process_originate_event(self, status, call_id, unique_id):
        state = self.get_channel_status(status)
        call_details = self.cache.get(call_id)

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
                self.cache.set(call_id, data, 1800)
                self.__process_call(
                    state,
                    call_id,
                    unique_id,
                    phone,
                    external_id,
                    status_url,
                    app_name
                )

    def __process_call(self, state, call_id, asterisk_unique_id, phone, external_id, status_url, app_name):
        if state == self.COMPLETED and asterisk_unique_id != '<unknown>':
            key = Hash.hash(asterisk_unique_id)
            reason = self.channel_reason(self.COMPLETED)
            hangup_link = self.gen_status_link(
                call_id,
                self.COMPLETED,
                reason,
                status_url,
                externalID=str(external_id),
                externalType=self.call_link_uganda
            )
            data = json.dumps({'link': hangup_link, 'phone': phone, 'app': app_name})
            self.cache.set(key, data, 1800)
            self.in_progress(call_id, status_url, phone, app_name)
        else:
            reason = self.channel_reason(state)
            self.update_call_status(call_id, state, reason, status_url, phone, app_name)

    @staticmethod
    def __current_timestamp():
        timestamp = datetime.datetime.now()
        timestamp = timestamp.timestamp()
        timestamp = round(timestamp, 3)
        timestamp = str(timestamp).replace('.', '')
        return timestamp
