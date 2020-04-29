#!/usr/bin/env python3

import string
import random
import requests
import datetime
import threading
from src.Logger import Logger


class AppWebListener:
    def __init__(self, working_dir, status_base_link):
        self.working_dir = working_dir
        self.status_base_link = status_base_link
        self.logger = Logger(self.working_dir)

    def random_alphanumeric_string(self, string_length=32):
        char = string.ascii_lowercase + string.digits
        external_id = ''.join((random.choice(char) for i in range(string_length)))
        return str(external_id)

    @staticmethod
    def channel_statuses(status):
        # Initial Originate Responses from Asterisk
        # codes = {'0': 'NO EXTENSION', '3': 'NO ANSWER', '4': 'ANSWERED', '5': 'BUSY', '8': 'CHANNEL NOT AVAILABLE'}
        codes = {
            '0': 'FAILED',
            '3': 'NO_ANSWER',
            '4': 'COMPLETED',
            '5': 'BUSY',
            '8': 'FAILED'}
        for key in codes:
            if status == key:
                return codes[key]

    def channel_reason(self, status):
        reasons = {'BUSY': 'busy', 'COMPLETED': 'application', 'FAILED': 'unreachable', 'NO_ANSWER': 'timeout'}
        for key in reasons:
            if status == key:
                return reasons[key]

    def current_timestamp(self):
        t1 = datetime.datetime.now()
        t1 = t1.timestamp()
        t1 = round(t1, 3)
        t1 = str(t1).replace('.', '')
        return t1

    def gen_status_link(self, call_id, timestamp, status, reason, **optional_params):
        """
        :param call_id:
        :param timestamp:
        :param status: NO_ANSWER,COMPLETED,FAILED,BUSY
        :param reason: timeout,application,unreachable,busy
        :param optional_params: externalID, externalType >> Used is status == COMPLETED
        :return: status_link
        """
        status_link = str(
            self.status_base_link + call_id + '.vxml?_dt=' + timestamp + '&status=' + status + '&reason=' + reason)

        if 'externalID' and 'externalType' in optional_params:
            status_link = str(status_link + '&externalId=' + optional_params['externalID'] + '&externalType=' +
                              optional_params['externalType'])
            return status_link
        return status_link

    def gen_motech_reply(self, call_id, channel, status, timer):
        """
        :param status: State of the call
        :param call_id: MOTECH generated caller ID
        :param channel: SIP Channel
        :param timer: Time to wait before sending link to change MOTECH call state from IN_PROGRESS to COMPLETED
        :return: Reply to MOTECH
        """

        initial_state = 'IN_PROGRESS'
        session_type = 'voxeoSessionId'

        self.logger.log_info('ActionID: {}, Channel: {}, Channel state: {}\n'.format(call_id, channel, status))
        if status == 'COMPLETED':
            link = self.gen_status_link(call_id,
                                        self.current_timestamp(),
                                        initial_state,
                                        self.channel_reason(status),
                                        externalID=self.random_alphanumeric_string(),
                                        externalType=session_type
                                        )
            completed_link = self.gen_status_link(call_id,
                                                  self.current_timestamp(),
                                                  status,
                                                  self.channel_reason(status),
                                                  externalID=self.random_alphanumeric_string(),
                                                  externalType=session_type
                                                  )
            threading.Timer(timer, lambda: requests.get(completed_link)).start()
            threading.Timer(timer, lambda: self.logger.log_info(
                'COMPLETED_State Update to MOTECH: {}'.format(completed_link))).start()
            self.logger.log_info('Reply to MOTECH(Call Answered): {}\n'.format(link))
            return link
        link = self.gen_status_link(call_id, self.current_timestamp(), status, self.channel_reason(status))
        self.logger.log_info('Reply to MOTECH: {}\n'.format(link))
        return link
