#!/usr/bin/env python3

from flask import Flask, request, redirect
import requests
from asterisk.ami import AMIClient
from asterisk.ami import AMIClientAdapter
from configparser import ConfigParser
import os
import random
import string
import ast
import re
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


def event_listener_originate(event, **kwargs):
    global state
    logger.log_info('{}\n'.format(event))
    event_dict = re.split(r"\->", str(event))
    event_dict = event_dict[1]
    event_dict = event_dict[1:]
    event_dict = ast.literal_eval(event_dict)
    channel_status_num = event_dict["Reason"]
    action_id = event_dict["ActionID"]
    channel = event_dict["Channel"]
    state = channel_statuses(channel_status_num)
    logger.log_info(
        'ActionID: {}, Channel: {}, Channel state: {}\n'.format(
            action_id, channel, state))


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
        logger.log_info('Reply to MOTECH(Call Answered): {}\n'.format(status_link))
        return status_link
    logger.log_info('Reply to MOTECH: {}\n'.format(status_link))
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

    client.add_event_listener(
        event_listener_originate,
        white_list='OriginateResponse')

    session_type = 'voxeoSessionId'
    complete_status_counter = int(360)
    initial_state = 'IN_PROGRESS'

    global state
    if state != "":
        state = ""
        while state == "":
            time.sleep(0.5)
        if state == 'COMPLETED':
            link = gen_status_link(call_id, current_timestamp(), initial_state, channel_reason(state),
                                   externalID=random_alphanumeric_string(), externalType=session_type)
            completed_link = gen_status_link(call_id, current_timestamp(), state, channel_reason(state),
                                   externalID=random_alphanumeric_string(), externalType=session_type)
            threading.Timer(complete_status_counter, lambda: requests.get(completed_link)).start()
            threading.Timer(complete_status_counter, lambda: logger.log_info('COMPLETED_State Update to MOTECH: {}'
                                                                             .format(completed_link))).start()
            return redirect(link, code=302)
        link = gen_status_link(call_id, current_timestamp(), state, channel_reason(state))
        return redirect(link, code=302)

    else:
        while state == "":
            time.sleep(0.5)
        if state == 'COMPLETED':
            link = gen_status_link(call_id, current_timestamp(), initial_state, channel_reason(state),
                                   externalID=random_alphanumeric_string(), externalType=session_type)
            completed_link = gen_status_link(call_id, current_timestamp(), state, channel_reason(state),
                                   externalID=random_alphanumeric_string(), externalType=session_type)
            threading.Timer(complete_status_counter, lambda: requests.get(completed_link)).start()
            threading.Timer(complete_status_counter, lambda: logger.log_info('COMPLETED_State Update to MOTECH: {}'
                                                                             .format(completed_link))).start()
            return redirect(link, code=302)
        link = gen_status_link(call_id, current_timestamp(), state, channel_reason(state))
        return redirect(link, code=302)


if __name__ == '__main__':
    # Debug Info shown in log file
    logger.log_info('App.py Logger Started')
    app.run(host='0.0.0.0', debug=True)
