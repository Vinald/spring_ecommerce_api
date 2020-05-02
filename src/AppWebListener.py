import string
import random
import requests
import datetime
import threading
from src.Logger import Logger


class AppWebListener:
    def __init__(self, logger: Logger, status_base_link):
        self.logger = logger
        self.status_base_link = status_base_link

    @staticmethod
    def channel_statuses(status):
        """
        Initial Originate Responses from Asterisk
        codes = {
            '0': 'NO EXTENSION',
            '3': 'NO ANSWER',
            '4': 'ANSWERED',
            '5': 'BUSY',
            '8': 'CHANNEL NOT AVAILABLE'
        }
        """
        codes = {
            '0': 'FAILED',
            '3': 'NO_ANSWER',
            '4': 'COMPLETED',
            '5': 'BUSY',
            '8': 'FAILED'
        }

        for key in codes:
            if status == key:
                return codes[key]
        return 'UNKNOWN'

    @staticmethod
    def channel_reason(status):
        reasons = {
            'BUSY': 'busy',
            'COMPLETED': 'application',
            'FAILED': 'unreachable',
            'NO_ANSWER': 'timeout'
        }

        for key in reasons:
            if status == key:
                return reasons[key]
        return 'unknown'

    @staticmethod
    def current_timestamp():
        timestamp = datetime.datetime.now()
        timestamp = timestamp.timestamp()
        timestamp = round(timestamp, 3)
        timestamp = str(timestamp).replace('.', '')
        return timestamp

    def gen_status_link(self, call_id, timestamp, status, reason, **optional_params):
        """
        :param call_id:
        :param timestamp:
        :param status: NO_ANSWER,COMPLETED,FAILED,BUSY
        :param reason: timeout,application,unreachable,busy
        :param optional_params: externalID, externalType >> Used is status == COMPLETED
        :return: status_link
        """

        base_link = self.status_base_link + call_id
        status_link = '{}.vxml?_dt={}&status={}&reason={}'.format(base_link, timestamp, status, reason)

        if 'externalID' and 'externalType' in optional_params:
            external_id = optional_params['externalID']
            external_type = optional_params['externalType']

            params = '&externalId={}&externalType={}'.format(external_id, external_type)
            return str(status_link + params)

        return status_link

    def gen_motech_reply(self, call_id, channel, status, timer):
        """
        :param status: State of the call
        :param call_id: MOTECH generated caller ID
        :param channel: SIP Channel
        :param timer: Time to wait before sending link to change MOTECH call state from IN_PROGRESS to COMPLETED
        :return: Reply to MOTECH
        """

        session_type = 'voxeoSessionId'
        initial_state = 'IN_PROGRESS'

        log_msg = "ActionID: {}, Channel: {}, Channel state: {}\n"
        self.logger.log_info(log_msg.format(call_id, channel, status))

        if status == 'COMPLETED':
            link = self.gen_status_link(
                call_id,
                self.current_timestamp(),
                initial_state,
                self.channel_reason(status),
                externalID=self.random_alphanumeric_string(),
                externalType=session_type
            )

            completed_link = self.gen_status_link(
                call_id,
                self.current_timestamp(),
                status,
                self.channel_reason(status),
                externalID=self.random_alphanumeric_string(),
                externalType=session_type
            )

            log_msg = 'COMPLETED_State Update to MOTECH: {}'.format(completed_link)

            threading.Timer(timer, lambda: requests.get(completed_link)).start()
            threading.Timer(timer, lambda: self.logger.log_info(log_msg)).start()

            self.logger.log_info("Reply to MOTECH(Call Answered): {}\n".format(link))
            return link

        link = self.gen_status_link(
            call_id,
            self.current_timestamp(),
            status,
            self.channel_reason(status)
        )

        self.logger.log_info("Reply to MOTECH: {}\n".format(link))
        return link

    @staticmethod
    def random_alphanumeric_string(length=32):
        char = string.ascii_lowercase + string.digits
        generated_string = ''.join((random.choice(char) for i in range(length)))
        return str(generated_string)
