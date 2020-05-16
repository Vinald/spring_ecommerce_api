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

    def __init__(self, logger: Logger, link: str, cache: Redis):
        self.cache = cache
        self.logger = logger
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
        self.logger.log_info("Channel answered: Call in progress")
        self.update_call_status(call_id, status, reason)

    def update_call_status(self, call_id: str, status: str, reason: str):
        link = self.gen_status_link(call_id, status, reason)
        results = str(requests.get(link).content)
        self.logger.log_info("CALL STATUS UPDATE RESULTS: {}".format(results))

    def process_originate_event(self, event: Event):
        status = str(event.keys.get('Reason'))
        call_id = str(event.keys.get('ActionID'))
        unique_id = str(event.keys.get('Uniqueid'))
        state = self.get_channel_status(status)

        if state == self.COMPLETED and unique_id != '<unknown>':
            key = Hash.hash(unique_id)
            reason = self.channel_reason(self.COMPLETED)
            hangup_link = self.gen_status_link(call_id, self.COMPLETED, reason)
            self.cache.set(key, hangup_link, 1800)
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
