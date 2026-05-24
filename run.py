#!/usr/bin/env python3

import threading
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime, timedelta

from flask_jwt_extended import JWTManager
from flask_jwt_extended import jwt_required
from flask_jwt_extended import create_access_token
from flask_jwt_extended import current_user
from sqlalchemy.orm import scoped_session

from app import core
from app.api.Charts import Charts
from app.api.Dashboard import Dashboard
from app.core import asterisk_ari, cdr_manager, peer_manager, Session
from app.manager.QueueManager import QueueManager
from app.models.models import User
from app.utilities.Hash import Hash
from app.utilities.utils import un_auth


app = Flask(__name__)

# Require a non-empty secret key — fail fast at startup rather than running insecurely
_secret_key = core.secret_key
if not _secret_key:
    raise RuntimeError(
        "JWT secret-key is empty. Set a strong value in config.json under [core] secret-key."
    )
app.config["JWT_SECRET_KEY"] = _secret_key
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=3)

jwt = JWTManager(app)

database = core.database
database.reconnect()

# Restrict CORS to the frontend origin — override via FRONTEND_ORIGIN env var if needed
import os
_frontend_origin = os.environ.get("FRONTEND_ORIGIN", "http://localhost:8080")
CORS(app, origins=[_frontend_origin])

logger = core.logger

app_manager = core.app_manager

queue = QueueManager(core.cache)

app_web_listener = core.asterisk_events_handler


@jwt.user_identity_loader
def user_identity_lookup(user):
    return user.id


@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):
    identity = jwt_data["sub"]

    s_session = scoped_session(Session)
    db_session = s_session()

    try:
        user = db_session.query(User).filter_by(id=identity).one_or_none()
        return user
    except Exception as e:
        core.logger.log_info(f"JWT user lookup DB error: {str(e)}")
        db_session.rollback()
        return None


def is_valid_token(token: str):
    try:
        results = app_manager.get_data(token)
        return False if not results else True
    except Exception as e:
        logger.log_info("Database error: {}".format(str(e)))
        return False


@app.route('/health', methods=['GET'])
def health():
    """Liveness probe for Docker / load balancers."""
    return jsonify({'status': 'ok'}), 200


@app.route('/call.initiate', methods=['GET'])
def index():
    flow = request.args.get('jumpTo')
    phone = request.args.get('phone')
    token = request.args.get('token')
    call_id = request.args.get('callId')

    core.initialize_log()

    logger.log_info("Call request from external app: {}".format(request.url))

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
        return un_auth()

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
        return un_auth()

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
@jwt_required()
def dashboard_stats():
    dashboard = Dashboard(asterisk_ari, queue, logger, cdr_manager, peer_manager)
    return jsonify(dashboard.get_stats(current_user))


@app.route('/api/charts', methods=['GET'])
@jwt_required()
def charts():
    chart = Charts(database)
    chart_data = chart.get_cdr_data(current_user, Session())
    return jsonify(chart_data)


@app.route('/api/apps', methods=['GET', 'POST', 'PUT', 'DELETE'])
@jwt_required()
def ivr_apps():
    return core.apps_api.process_request(request, Session(), current_user)


@app.route('/api/reports', methods=['GET', 'POST', 'PUT', 'DELETE'])
@jwt_required()
def report():
    return core.reports_api.process(request, Session(), current_user)


@app.route('/api/report-types', methods=['GET', 'POST', 'PUT', 'DELETE'])
@jwt_required()
def report_types():
    return core.report_types_api.process(request, Session(), current_user)


@app.route('/api/login', methods=['POST'])
def login():
    user_details = core.login_api.verify(request, Session())
    if not user_details:
        return jsonify({'status': 'error', 'message': 'Bad username or password'}), 401
    user: User = user_details['user']
    token = create_access_token(identity=user)
    return jsonify(token=token, user=user_details['details'])


@app.route('/api/user', methods=['GET', 'POST', 'PUT', 'DELETE'])
@jwt_required()
def register_user():
    return core.users_api.handle_request(request, Session(), current_user)


@app.route('/api/profile', methods=['POST'])
@jwt_required()
def user_profile():
    return core.profile_api.process(request, Session(), current_user)


@app.route('/api/roles', methods=['GET'])
@jwt_required()
def roles():
    return jsonify(core.roles)


@app.route('/api/logs', methods=['GET'])
@jwt_required()
def logs():
    return core.logs_api.process(request, current_user)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
