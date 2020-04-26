#!/usr/bin/env python3

from flask import Flask, request, redirect
import requests
from asterisk.ami import AMIClient
from asterisk.ami import AMIClientAdapter
from configparser import ConfigParser
import os
import random
import string
import time
import datetime
import threading
from src.Logger import Logger

working_dir = os.path.dirname(os.path.realpath(__file__))

config = ConfigParser()
config.read(working_dir + '/config.ini')

# Initiate Logger
logger = Logger(working_dir)

# Grab the ami section from the config file
ami = config['ami']
motech_config = config['motech']

ami_host = ami['host']
ami_user = ami['user']
ami_pass = ami['pass']
ami_port = int(ami['port'])
ami_trunk = ami['trunk']
motech_hostname = motech_config['host']
state = ''

status_base_link = 'http://{}/motech-platform-server/module/callflows/status/'.format(motech_hostname)


app = Flask(__name__)
client = AMIClient(address=ami_host, port=ami_port)
client.login(username=ami_user, secret=ami_pass)


def callback_response(response):
    logger.log_info(response)


def random_alphanumeric_string(stringlength=32):
    char = string.ascii_lowercase + string.digits
    external_id = ''.join((random.choice(char) for i in range(stringlength)))
    return str(external_id)


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


def channel_reason(status):
    reasons = {'BUSY': 'busy', 'COMPLETED': 'application', 'FAILED': 'unreachable', 'NO_ANSWER': 'timeout'}
    for key in reasons:
        if status == key:
            return reasons[key]


def gen_motech_reply(call_id, channel, status, timer):
    """
    :param status:
    :param call_id: MOTECH generated caller ID
    :param timestamp: Generate timestamp
    :param reason: BUSY, COMPLETED, FAILED, NO_ANSWER
    :param channel: SIP Channel
    :param external_id: Random Alphanumeric String
    :param timer: Time to wait before sending link to change MOTECH call state from IN_PROGRESS to COMPLETED
    :return: Reply to MOTECH
    """

    initial_state = 'IN_PROGRESS'
    session_type = 'voxeoSessionId'

    logger.log_info('ActionID: {}, Channel: {}, Channel state: {}\n'.format(call_id, channel, status))
    if status == 'COMPLETED':
        link = gen_status_link(call_id,
                               current_timestamp(),
                               initial_state,
                               channel_reason(status),
                               externalID=random_alphanumeric_string(),
                               externalType=session_type
                               )
        completed_link = gen_status_link(call_id,
                                         current_timestamp(),
                                         status,
                                         channel_reason(status),
                                         externalID=random_alphanumeric_string(),
                                         externalType=session_type
                                         )
        threading.Timer(timer, lambda: requests.get(completed_link)).start()
        threading.Timer(timer, lambda: logger.log_info(
            'COMPLETED_State Update to MOTECH: {}'.format(completed_link))).start()
        logger.log_info('Reply to MOTECH(Call Answered): {}\n'.format(link))
        return link
    link = gen_status_link(call_id, current_timestamp(), status, channel_reason(status))
    logger.log_info('Reply to MOTECH: {}\n'.format(link))
    return link


def event_listener(event, **kwargs):
    global state
    if str(event.name) == 'OriginateResponse':
        try:
            channel_status_num = str(event.keys.get('Reason'))
            state = channel_statuses(channel_status_num)
        except Exception as e:
            logger.log_info('Event Listener Error : {}'.format(str(e)))


def current_timestamp():
    t1 = datetime.datetime.now()
    t1 = t1.timestamp()
    t1 = round(t1, 3)
    t1 = str(t1).replace('.', '')
    return t1


def gen_status_link(callid, timestamp, status, reason, **optional_params):
    """
    :param callid:
    :param timestamp:
    :param status: NO_ANSWER,COMPLETED,FAILED,BUSY
    :param reason: timeout,application,unreachable,busy
    :param optional_params: externalID, externalType >> Used is status == COMPLETED
    :return: status_link
    """
    status_link = str(status_base_link + callid + '.vxml?_dt=' + timestamp + '&status=' + status + '&reason=' + reason)

    if 'externalID' and 'externalType' in optional_params:
        status_link = str(status_link + '&externalId=' + optional_params['externalID'] + '&externalType=' +
                          optional_params['externalType'])
        return status_link
    return status_link


@app.route('/', methods=['GET', 'POST'])
def index():
    flow = request.args.get('jumpTo')
    phone = request.args.get('phone')
    call_id = request.args.get('callId')
    logger.log_info(request.url)

    adapter = AMIClientAdapter(client)

    channel = 'SIP/' + phone

    if ami_trunk is not None and len(ami_trunk) > 0:
        channel = 'SIP/{}/+{}'.format(ami_trunk, phone)

    adapter.Originate(
        Channel=channel,
        Exten='100',
        Priority=1,
        Context='ivr',
        CallerID='Call For Life Uganda',
        Variable='data={}&{}&{}&{},CDR(dialed_number)={}'.format(call_id, phone, flow, channel, phone),
        ActionID=call_id,
        Timeout=45000,
        Async=True,
        _callback=callback_response
    )

    client.add_event_listener(event_listener)
    complete_status_counter = int(360)

    global state
    if state != "":
        state = ""
        while state == "":
            time.sleep(0.5)
        link = gen_motech_reply(call_id, channel, state, complete_status_counter)
        return redirect(link)
    else:
        while state == "":
            time.sleep(0.5)
        link = gen_motech_reply(call_id, channel, state, complete_status_counter)
        return redirect(link)


if __name__ == '__main__':
    # Debug Info shown in log file
    logger.log_info('App.py Logger Started')
    app.run(host='0.0.0.0', debug=True)
