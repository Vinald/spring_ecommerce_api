import json
import requests
import datetime
from asterisk.ami import Event
from redis import Redis
from src.Hash import Hash
from src.Logger import Logger


class AppWebListener:
    BUSY = 'BUSY'
    FAILED = 'FAILED'
    COMPLETED = 'COMPLETED'

    def __init__(self, logger: Logger, cache: Redis):
        self.cache = cache
        self.logger = logger
        self.status_base_link = None

    def set_status_link(self, link: str):
        self.status_base_link = link

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

    def gen_status_link(self, call_id, status, reason, **optional_params):
        """
        :param call_id:
        :param status: NO_ANSWER,COMPLETED,FAILED,BUSY
        :param reason: timeout,application,unreachable,busy
        :param optional_params: externalID, externalType >> Used is status == COMPLETED
        :return: status_link
        """

        stamp = "_dt={}".format(self.__current_timestamp())
        status = "status={}".format(status)
        reason = "reason={}".format(reason)

        link = self.status_base_link + call_id
        status_link = "{}.vxml?{}&{}&{}".format(link, stamp, status, reason)

        if 'externalID' and 'externalType' in optional_params:
            external_id = optional_params['externalID']
            external_type = optional_params['externalType']

            params = '&externalId={}&externalType={}'.format(external_id, external_type)
            return str(status_link + params)

        return status_link

    def in_progress(self, call_id):
        status = 'IN_PROGRESS'
        reason = self.channel_reason(self.COMPLETED)
        self.update_call_status(call_id, status, reason)

    def update_call_status(self, call_id: str, status: str, reason: str):
        link = self.gen_status_link(call_id, status, reason)
        results = str(requests.get(link).content)
        log_msg = "Call status: {}, call_id: {}, external_app_results: {}"
        self.logger.log_info(log_msg.format(status, call_id, results))

    def process_originate_event(self, event: Event):
        status = str(event.keys.get('Reason'))
        call_id = str(event.keys.get('ActionID'))
        unique_id = str(event.keys.get('Uniqueid'))
        state = self.get_channel_status(status)

        call_details = self.cache.get(call_id)

        if call_details is not None:
            data = json.loads(call_details)
            phone = data['phone']
            initiated = True if data['initiated'] == 'yes' else False

            self.logger.set_phone(phone)

            if not initiated:
                data = '{"phone": "%s", "initiated": "yes"}' % phone
                self.cache.set(call_id, data, 1800)
                self.__process_call(state, call_id, unique_id, phone)

    def set_token(self, token):
        self.logger.set_token(token)

    def set_app(self, app):
        self.logger.set_app(app)

    def __process_call(self, state, call_id, unique_id, phone):
        if state == self.COMPLETED and unique_id != '<unknown>':
            key = Hash.hash(unique_id)
            reason = self.channel_reason(self.COMPLETED)
            hangup_link = self.gen_status_link(call_id, self.COMPLETED, reason)
            data = '{"link": "%s", "phone": "%s"}' % (hangup_link, phone)
            self.cache.set(key, data, 1800)
            self.in_progress(call_id)
        else:
            reason = self.channel_reason(state)
            self.update_call_status(call_id, state, reason)

    @staticmethod
    def __current_timestamp():
        timestamp = datetime.datetime.now()
        timestamp = timestamp.timestamp()
        timestamp = round(timestamp, 3)
        timestamp = str(timestamp).replace('.', '')
        return timestamp
