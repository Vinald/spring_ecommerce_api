#!/usr/bin/env python3

from flask import Flask, request
from asterisk.ami import AMIClient
from asterisk.ami import AMIClientAdapter
import os
from redis import Redis
from src.AppManager import AppManager
from src.AppDatabase import AppDatabase
from src.Config import Config
from src.Logger import Logger
from src.AppWebListener import AppWebListener

working_dir = os.path.dirname(os.path.realpath(__file__))

# Initiate Logger
logger = Logger(working_dir)

config = Config(working_dir, logger)

config.set_section('ami')
ami_host = config.get_ami_host()
ami_user = config.get_ami_user()
ami_pass = config.get_ami_pass()
ami_port = config.get_ami_port()
ami_trunk = config.get_sip_trunk()

config.set_section('app')
redis_host = str(config.get('redis_host'))
redis_port = config.get_int('redis_port')

# connect to redis
cache = Redis(host=redis_host, port=redis_port)

app = Flask(__name__)

client = AMIClient(address=ami_host, port=ami_port)
client.login(username=ami_user, secret=ami_pass)

# Initiate Web_Listener class
app_web_listener = AppWebListener(logger, cache)

# Initialize database
database = AppDatabase(config)

app_manager = AppManager(database, logger)


def is_valid_token(token: str):
    try:
        results = app_manager.get_data(token)
        if not results:
            return False
        link = app_manager.get_status_url(token)
        app_web_listener.set_status_link(link)
        return True
    except Exception as e:
        logger.log_info("Database error: {}".format(str(e)))
        return False


def event_listener(event, **kwargs):
    if str(event.name) == 'OriginateResponse':
        app_web_listener.process_originate_event(event)


@app.route('/', methods=['GET', 'POST'])
def index():
    flow = request.args.get('jumpTo')
    phone = request.args.get('phone')
    token = str(request.args.get('token'))
    call_id = request.args.get('callId')

    logger.set_phone(phone)
    logger.log_info("Call request from external app: {}".format(request.url))

    if not is_valid_token(token):
        logger.log_info("Failed to route call: Reason: Invalid token")
        return {'status': 'FAILED TO ROUTE CALL'}

    adapter = AMIClientAdapter(client)

    channel = 'SIP/' + phone

    if ami_trunk is not None and len(ami_trunk) > 0:
        channel = 'SIP/{}/+{}'.format(ami_trunk, phone)

    data = 'data={}&{}&{}&{},CDR(dialed_number)={}'

    adapter.Originate(
        Channel=channel,
        Exten='100',
        Priority=1,
        Context='ivr',
        CallerID='Call For Life Uganda',
        Variable=data.format(call_id, phone, flow, token, phone),
        ActionID=call_id,
        Timeout=45000,
        Async=True
    )

    data = '{"phone": "%s", "initiated": "no"}' % phone
    cache.set(call_id, data, 1800)

    client.add_event_listener(event_listener)
    return {'status': 'CALL_INITIATED'}


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
