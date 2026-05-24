"""
API blueprint — authenticated REST routes.

All routes here require a valid JWT (via @jwt_required()).
Route handlers delegate directly to the API handler classes in app/api/.
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, create_access_token, current_user

from app.api.Charts import Charts
from app.api.Dashboard import Dashboard

_deps = {}

api_bp = Blueprint('api', __name__, url_prefix='/api')


def init_api_blueprint(core, queue, asterisk_ari, cdr_manager, peer_manager, Session, logger):
    """Inject shared dependencies — called once from create_app()."""
    _deps.update({
        'core': core,
        'queue': queue,
        'ari': asterisk_ari,
        'cdr': cdr_manager,
        'peers': peer_manager,
        'Session': Session,
        'logger': logger,
    })


@api_bp.route('/login', methods=['POST'])
def login():
    core = _deps['core']
    Session = _deps['Session']
    user_details = core.login_api.verify(request, Session())
    if not user_details:
        return jsonify({'status': 'error', 'message': 'Bad username or password'}), 401
    user = user_details['user']
    token = create_access_token(identity=user)
    return jsonify(token=token, user=user_details['details'])


@api_bp.route('/dashboard-stats', methods=['GET'])
@jwt_required()
def dashboard_stats():
    d = _deps
    dashboard = Dashboard(d['ari'], d['queue'], d['logger'], d['cdr'], d['peers'])
    return jsonify(dashboard.get_stats(current_user))


@api_bp.route('/charts', methods=['GET'])
@jwt_required()
def charts():
    core = _deps['core']
    Session = _deps['Session']
    chart = Charts(core.database)
    return jsonify(chart.get_cdr_data(current_user, Session()))


@api_bp.route('/apps', methods=['GET', 'POST', 'PUT', 'DELETE'])
@jwt_required()
def ivr_apps():
    core = _deps['core']
    Session = _deps['Session']
    return core.apps_api.process_request(request, Session(), current_user)


@api_bp.route('/reports', methods=['GET', 'POST', 'PUT', 'DELETE'])
@jwt_required()
def report():
    core = _deps['core']
    Session = _deps['Session']
    return core.reports_api.process(request, Session(), current_user)


@api_bp.route('/report-types', methods=['GET', 'POST', 'PUT', 'DELETE'])
@jwt_required()
def report_types():
    core = _deps['core']
    Session = _deps['Session']
    return core.report_types_api.process(request, Session(), current_user)


@api_bp.route('/user', methods=['GET', 'POST', 'PUT', 'DELETE'])
@jwt_required()
def manage_user():
    core = _deps['core']
    Session = _deps['Session']
    return core.users_api.handle_request(request, Session(), current_user)


@api_bp.route('/profile', methods=['POST'])
@jwt_required()
def user_profile():
    core = _deps['core']
    Session = _deps['Session']
    return core.profile_api.process(request, Session(), current_user)


@api_bp.route('/roles', methods=['GET'])
@jwt_required()
def roles():
    core = _deps['core']
    return jsonify(core.roles)


@api_bp.route('/logs', methods=['GET'])
@jwt_required()
def logs():
    core = _deps['core']
    return core.logs_api.process(request, current_user)
