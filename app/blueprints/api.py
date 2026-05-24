"""
API blueprint — authenticated REST routes (/api/*).

ADDED: These routes were previously in run.py mixed with telephony routes.
Moving them to a dedicated blueprint isolates the REST API concern and makes
each endpoint independently testable.

All routes here require a valid JWT (@jwt_required()) issued by /api/login.
The /api/login route itself is rate-limited to 10 req/min (set in create_app)
to prevent brute-force attacks.
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, create_access_token, current_user

from app.api.Charts import Charts
from app.api.Dashboard import Dashboard

# Shared dependencies injected once by init_api_blueprint() from create_app().
_deps = {}

api_bp = Blueprint('api', __name__, url_prefix='/api')


def init_api_blueprint(core, queue, asterisk_ari, cdr_manager, peer_manager, Session, logger):
    """Inject shared dependencies — called once from create_app() in run.py."""
    _deps.update({
        'core': core, 'queue': queue, 'ari': asterisk_ari,
        'cdr': cdr_manager, 'peers': peer_manager,
        'Session': Session, 'logger': logger,
    })


@api_bp.route('/login', methods=['POST'])
def login():
    """
    Authenticate and return a JWT.
    Rate limited to 10 req/min per IP in create_app() to block brute-force.
    Input is validated by LoginSchema inside login_api.verify().
    """
    core = _deps['core']
    user_details = core.login_api.verify(request, _deps['Session']())
    if not user_details:
        return jsonify({'status': 'error', 'message': 'Bad username or password'}), 401
    token = create_access_token(identity=user_details['user'])
    return jsonify(token=token, user=user_details['details'])


@api_bp.route('/dashboard-stats', methods=['GET'])
@jwt_required()
def dashboard_stats():
    """System metrics — CPU, memory, active channels, queue depth. Admin only."""
    d = _deps
    dashboard = Dashboard(d['ari'], d['queue'], d['logger'], d['cdr'], d['peers'])
    return jsonify(dashboard.get_stats(current_user))


@api_bp.route('/charts', methods=['GET'])
@jwt_required()
def charts():
    """CDR chart data for the last 15 days."""
    core = _deps['core']
    chart = Charts(core.database)
    return jsonify(chart.get_cdr_data(current_user, _deps['Session']()))


@api_bp.route('/apps', methods=['GET', 'POST', 'PUT', 'DELETE'])
@jwt_required()
def ivr_apps():
    """CRUD for IVR applications. Input validated by AppCreate/UpdateSchema."""
    core = _deps['core']
    return core.apps_api.process_request(request, _deps['Session'](), current_user)


@api_bp.route('/reports', methods=['GET', 'POST', 'PUT', 'DELETE'])
@jwt_required()
def report():
    """CRUD for scheduled reports. Input validated by ReportCreate/UpdateSchema."""
    core = _deps['core']
    return core.reports_api.process(request, _deps['Session'](), current_user)


@api_bp.route('/report-types', methods=['GET', 'POST', 'PUT', 'DELETE'])
@jwt_required()
def report_types():
    """CRUD for report SQL templates. SQL validated as SELECT-only in ReportTypes."""
    core = _deps['core']
    return core.report_types_api.process(request, _deps['Session'](), current_user)


@api_bp.route('/user', methods=['GET', 'POST', 'PUT', 'DELETE'])
@jwt_required()
def manage_user():
    """User management — admin only. Input validated by UserCreate/UpdateSchema."""
    core = _deps['core']
    return core.users_api.handle_request(request, _deps['Session'](), current_user)


@api_bp.route('/profile', methods=['POST'])
@jwt_required()
def user_profile():
    """Password change for the currently authenticated user."""
    core = _deps['core']
    return core.profile_api.process(request, _deps['Session'](), current_user)


@api_bp.route('/roles', methods=['GET'])
@jwt_required()
def roles():
    """Return available role definitions from config."""
    return jsonify(_deps['core'].roles)


@api_bp.route('/logs', methods=['GET'])
@jwt_required()
def logs():
    """Return log file list for the current user (admin sees all users)."""
    return _deps['core'].logs_api.process(request, current_user)
