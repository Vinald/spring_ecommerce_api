#!/usr/bin/env python3

import threading
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
from app import core
from app.api.Charts import Charts
from app.api.Dashboard import Dashboard
from app.core import asterisk_ari, cdr_manager, peer_manager
from app.core import engine
from app.manager.QueueManager import QueueManager
from app.models.models import Base
from app.utilities.Hash import Hash

app = Flask(__name__)

Base.metadata.create_all(bind=engine)

CORS(app, resources={r'/*': {'origins': '*'}})

logger = core.logger
database = core.database
app_manager = core.app_manager

queue = QueueManager(core.cache)

app_web_listener = core.asterisk_events_handler


def is_valid_token(token: str):
    try:
        results = app_manager.get_data(token)
        return False if not results else True
    except Exception as e:
        logger.log_info("Database error: {}".format(str(e)))
        return False


@app.route('/', methods=['GET', 'POST'])
def index():
    flow = request.args.get('jumpTo')
    phone = request.args.get('phone')
    token = request.args.get('token')
    call_id = request.args.get('callId')

    core.initialize_log()

    logger.log_info("Call request from external app: {}".format(request.url))

    #  Database has tendency of disconnecting making it seem like every token is invalid.
    #  So we shall try to reconnect on every request only if the connection closed
    database.reconnect()

    if not is_valid_token(token):
        logger.log_info("Failed to route call: Reason: Invalid token")
        return {'status': 'FAILED TO ROUTE CALL'}

    app_data = app_manager.get_data(token)

    data = {
        'phone': phone,
        'token': token,
        'call_id': call_id,
        'flow': flow,
        'external_id': Hash.hash(str(datetime.now().timestamp())),
        'app-data': app_data
    }

    if not asterisk_ari.has_free_channels():
        queue.queue_call(data)
        return {'status': 'CALL_QUEUED'}

    core.initiate_call(data)
    return {'status': 'INITIATED'}


@app.route('/ivr/queue', methods=['GET'])
def process_queue():
    if request.remote_addr != '127.0.0.1':
        return {'status': 'error', 'message': 'Unauthorized Access'}

    core.initialize_log()

    empty_queue = queue.is_empty()
    has_free_channels = asterisk_ari.has_free_channels()

    if has_free_channels and not empty_queue:
        call_data = queue.get_next_call_in_queue()
        logger.log_info('Initiating queued call: {}'.format(str(call_data)))
        core.initiate_call(call_data)
        return {'status': 'INITIATED', 'data': call_data}

    return {'has_free_channels': has_free_channels, 'empty_queue': empty_queue}


@app.route('/ivr/events', methods=['GET'])
def asterisk_events_handler():
    if request.remote_addr != '127.0.0.1':
        return {'status': 'error', 'message': 'Unauthorized Access'}

    name = request.args.get('name')
    status = request.args.get('status')
    call_id = request.args.get('call-id')
    channel = request.args.get('channel')
    unique_id = request.args.get('unique-id')

    if name == 'OriginateResponse':
        originate_thread = threading.Thread(
            target=app_web_listener.handle_originate_event,
            args=(status, call_id, unique_id)
        )
        originate_thread.start()
        return '', 204
    if name == 'Hangup':
        hangup_thread = threading.Thread(
            target=app_web_listener.handle_hangup_event,
            args=(unique_id, channel)
        )
        hangup_thread.start()
        return '', 204
    return {'status': 'error', 'message': 'Unknown event'}


@app.route('/api/dashboard-stats', methods=['GET'])
def dashboard_stats():
    dashboard = Dashboard(asterisk_ari, queue, logger, cdr_manager, peer_manager)
    return jsonify(dashboard.get_stats())


@app.route('/api/charts')
def charts():
    chart = Charts(database)
    return jsonify(chart.get_cdr_data())


@app.route('/api/apps', methods=['GET', 'POST', 'PUT', 'DELETE'])
def ivr_apps():
    if request.method == 'GET':
        return jsonify({'apps': app_manager.get_all_apps()})
    if request.method == 'POST':
        app_name = request.form['name']
        app_phone = request.form['phone']
        voice_url = request.form['voice_url']
        status_url = request.form['status_url']
        caller_id = request.form['caller_id']
        toll_free = request.form['toll_free']
        response = app_manager.create_app(app_name, voice_url, status_url, app_phone, toll_free, caller_id)
        return jsonify(response)
    if request.method == 'DELETE':
        app_id = int(request.args.get('id'))
        return jsonify(app_manager.delete_app(app_id))
    if request.method == 'PUT':
        app_id = int(request.form['id'])
        app_name = request.form['name']
        app_phone = request.form['phone']
        voice_url = request.form['voice_url']
        status_url = request.form['status_url']
        caller_id = request.form['caller_id']
        toll_free = request.form['toll_free']
        response = app_manager.update_app(app_id, app_name, voice_url, status_url, app_phone, toll_free, caller_id)
        return jsonify(response)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
