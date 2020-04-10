#!/usr/bin/env python3

from flask import Flask, request, jsonify
from asterisk.ami import AMIClient, SimpleAction
from asterisk.ami import AMIClientAdapter
from configparser import ConfigParser
import os
import logging
import re
import ast
import time


working_dir = os.path.dirname(os.path.realpath(__file__))

config = ConfigParser()
config.read(working_dir + '/config.ini')

# Initiate Logger
log_dir = os.path.dirname(os.path.realpath(__file__))

logging.basicConfig(
            level=logging.INFO,
            format='[%(asctime)s] %(levelname)s: %(message)s',
            filename=log_dir + '/app_py.log',
            filemode='a+',
        )

open(log_dir + '/app_py.log', 'w+')

logger = logging.getLogger()

# Grab the ami section from the config file
ami = config['ami']

ami_host = ami['host']
ami_user = ami['user']
ami_pass = ami['pass']
ami_port = int(ami['port'])
ami_trunk = ami['trunk']

app = Flask(__name__)


client = AMIClient(address=ami_host, port=ami_port)
client.login(username=ami_user, secret=ami_pass)


def callback_response(response):
    logger.info(response)
    print(response)



state = ''

def channel_statuses(status):
    codes = {'0': 'NO EXTENSION', '3': 'NO ANSWER', '4': 'ANSWERED', '5': 'BUSY', '8': 'CHANNEL NOT AVAILABLE'}
    for key in codes.keys():
        if status == key:
            code = codes[key]
            return code


def event_listener_originate(event, **kwargs):
    global state
    event_dict = re.split(r"\->", str(event))
    event_dict = event_dict[1]
    event_dict = event_dict[1:]
    event_dict = ast.literal_eval(event_dict)
    channelstatus_num = event_dict["Reason"]
    actionid = event_dict["ActionID"]
    channel = event_dict["Channel"]
    state = channel_statuses(channelstatus_num)
    logger.info('ActionID: {}, Channel: {}, Channel state: {}'.format(actionid, channel, state))



@app.route('/', methods=['GET', 'POST'])
def index():
    flow = request.args.get('jumpTo')
    phone = request.args.get('phone')
    call_id = request.args.get('callId')

    logger.info(request.args.get(''))

    adapter = AMIClientAdapter(client)

    channel = 'SIP/' + phone

    if ami_trunk is not None and len(ami_trunk) > 0:
        channel = 'SIP/{}/+{}'.format(ami_trunk, phone)

    future = adapter.Originate(
            Channel=channel,
            Exten='100',
            Priority=1,
            Context='ivr',
            CallerID='Call For Life Uganda',
            Variable='data={}&{}&{}&{}'.format(call_id, phone, flow, channel),
            ActionID=call_id,
            Timeout=30000,
            Async=True,
            _callback=callback_response

        )

    client.add_event_listener(event_listener_originate, white_list='OriginateResponse')

    global state
    if state != "":
        state = ""
        while state == "":
            time.sleep(0.5)
        return jsonify({'status': state})
    else:
        while state == "":
            time.sleep(0.5)
        return jsonify({'status': state})


if __name__ == '__main__':
    # Debug Info shown in log file
    logger.info('App.py Logger Started')
    app.run(host='0.0.0.0', debug=True)
