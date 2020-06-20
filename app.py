#!/usr/bin/env python3

from flask import Flask, request, jsonify
from flask_cors import CORS
import core
from src.AsteriskARI import AsteriskARI
from src.Dashboard import Dashboard
from src.manager.QueueManager import QueueManager

app = Flask(__name__)

CORS(app, resources={r'/*': {'origins': '*'}})

logger = core.logger
config = core.config

database = core.database
app_manager = core.app_manager

queue = QueueManager(core.cache)
asterisk_ari = AsteriskARI(config, logger)

app_web_listener = core.app_web_listener


def is_valid_token(token: str):
    try:
        results = app_manager.get_data(token)
        if not results:
            return False
        link = app_manager.get_status_url(token)
        app_web_listener.set_status_link(link)
        app_web_listener.set_app(results['name'])
        app_web_listener.set_token(results['token'])
        return True
    except Exception as e:
        logger.log_info("Database error: {}".format(str(e)))
        return False


def event_listener(event, **kwargs):
    if str(event.name) == 'OriginateResponse':
        app_web_listener.process_originate_event(event)


def queue_event_listener(event, **kwargs):
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

    #  Database has tendency of disconnecting making it seem like every token is invalid.
    #  So we shall try to reconnect on every request only if the connection closed
    database.reconnect()

    if not is_valid_token(token):
        logger.log_info("Failed to route call: Reason: Invalid token")
        return {'status': 'FAILED TO ROUTE CALL'}

    if not asterisk_ari.has_free_channels():
        data = {'phone': phone, 'token': token, 'call_id': call_id, 'flow': flow}
        queue.queue_call(data)
        return {'status': 'CALL_QUEUED'}

    core.initiate_call(phone, token, call_id, flow)
    core.client.add_event_listener(event_listener)
    return {'status': 'CALL_INITIATED'}


@app.route('/queue', methods=['GET'])
def process_queue():
    if request.remote_addr != '127.0.0.1':
        return {'status': 'error', 'message': 'Unauthorized Access'}

    empty_queue = queue.is_empty()
    has_free_channels = asterisk_ari.has_free_channels()

    if has_free_channels and not empty_queue:
        call_data = queue.get_next_call_in_queue()
        logger.log_info('Initiating queued call: {}'.format(str(call_data)))
        core.initiate_call(
            call_data['phone'],
            call_data['token'],
            call_data['call_id'],
            call_data['flow']
        )
        core.client.add_event_listener(queue_event_listener)
        return {'status': 'CALL_INITIATED', 'data': call_data}

    return {'has_free_channels': has_free_channels, 'empty_queue': empty_queue}


@app.route('/api/dashboard-stats', methods=['GET'])
def dashboard_stats():
    dashboard = Dashboard(asterisk_ari, queue, logger)
    return jsonify(dashboard.get_stats())


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
