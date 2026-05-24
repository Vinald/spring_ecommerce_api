"""
IVR blueprint — telephony-facing routes.

ADDED: These routes were previously in run.py mixed with API routes.
Moving them to a dedicated blueprint makes the telephony concerns
independently readable and testable.

Routes here do NOT require JWT authentication because they are called by
Asterisk or external app servers, not the Vue frontend. Internal-only
routes (/ivr/queue, /ivr/events) are restricted to 127.0.0.1 so they
cannot be reached from outside the server.
"""
import threading
from datetime import datetime
from flask import Blueprint, request, jsonify

from app.utilities.utils import un_auth
from app.utilities.Hash import Hash

# Shared dependencies injected once by init_ivr_blueprint() from create_app().
# Using a module-level dict avoids circular imports while keeping blueprints
# free of direct references to the core module.
_deps = {}

ivr_bp = Blueprint('ivr', __name__)


def init_ivr_blueprint(core, queue, asterisk_ari, app_web_listener, database, logger):
    """Inject shared dependencies — called once from create_app() in run.py."""
    _deps.update({
        'core': core,
        'queue': queue,
        'ari': asterisk_ari,
        'listener': app_web_listener,
        'database': database,
        'logger': logger,
    })


@ivr_bp.route('/health', methods=['GET'])
def health():
    """
    Liveness probe for Docker and load balancers.
    ADDED: was missing — Docker healthchecks and monitoring tools need this.
    No authentication required; exempt from rate limiting.
    """
    return jsonify({'status': 'ok'}), 200


@ivr_bp.route('/call.initiate', methods=['GET'])
def initiate_call():
    """
    Entry point for external apps to trigger an outbound IVR call.
    Rate limited to 30 req/min per IP (set in create_app).
    """
    core = _deps['core']
    queue = _deps['queue']
    ari = _deps['ari']
    database = _deps['database']
    logger = _deps['logger']

    flow = request.args.get('jumpTo')
    phone = request.args.get('phone')
    token = request.args.get('token')
    call_id = request.args.get('callId')

    core.initialize_log()
    logger.log_info("Call request from external app: {}".format(request.url))
    database.reconnect()

    try:
        results = core.app_manager.get_data(token)
        if not results:
            logger.log_info("Failed to route call: Reason: Invalid token")
            return jsonify({'status': 'FAILED TO ROUTE CALL'}), 401
    except Exception as e:
        logger.log_info("Database error: {}".format(str(e)))
        return jsonify({'status': 'FAILED TO ROUTE CALL'}), 401

    data = {
        'phone': phone, 'token': token, 'call_id': call_id, 'flow': flow,
        'external_id': Hash.hash(str(datetime.now().timestamp())),
        'app-data': results
    }

    if not ari.has_free_channels():
        queue.queue_call(data)
        return jsonify({'status': 'CALL_QUEUED'})

    core.initiate_call(data)
    return jsonify({'status': 'INITIATED'})


@ivr_bp.route('/ivr/queue', methods=['GET'])
def process_queue():
    """
    Internal endpoint — drain one call from the Redis queue.
    Restricted to 127.0.0.1 only; called by the cron queue processor.
    """
    if request.remote_addr != '127.0.0.1':
        return un_auth()

    core = _deps['core']
    queue = _deps['queue']
    ari = _deps['ari']
    logger = _deps['logger']

    core.initialize_log()
    empty_queue = queue.is_empty()
    has_free_channels = ari.has_free_channels()

    if has_free_channels and not empty_queue:
        call_data = queue.get_next_call_in_queue()
        logger.log_info('Initiating queued call: {}'.format(str(call_data)))
        core.initiate_call(call_data)
        return jsonify({'status': 'INITIATED', 'data': call_data})

    return jsonify({'has_free_channels': has_free_channels, 'empty_queue': empty_queue})


@ivr_bp.route('/ivr/events', methods=['GET'])
def asterisk_events():
    """
    Internal endpoint — receives Asterisk AMI event callbacks.
    Restricted to 127.0.0.1; handled in background threads so the
    response is returned to Asterisk immediately.
    """
    if request.remote_addr != '127.0.0.1':
        return un_auth()

    listener = _deps['listener']
    name = request.args.get('name')
    status = request.args.get('status')
    call_id = request.args.get('call-id')
    channel = request.args.get('channel')
    unique_id = request.args.get('unique-id')

    if name == 'OriginateResponse':
        threading.Thread(
            target=listener.handle_originate_event,
            args=(status, call_id, unique_id)
        ).start()
        return '', 204
    if name == 'Hangup':
        threading.Thread(
            target=listener.handle_hangup_event,
            args=(unique_id, channel)
        ).start()
        return '', 204

    return jsonify({'status': 'error', 'message': 'Unknown event'})
