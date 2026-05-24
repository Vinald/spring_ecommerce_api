import re
from datetime import datetime
from flask import jsonify
from app.models.models import ReportType, User
from app.schemas.schemas import ReportTypeCreateSchema, ReportTypeUpdateSchema, ReportTypeDeleteSchema
from app.utilities.Logger import Logger
from app.utilities.validation import validate_request

# CHANGED: report type SQL was previously stored and executed with no restrictions.
# An admin could run DROP TABLE, DELETE, or any destructive query. This allowlist
# enforces that only read-only SELECT statements are accepted.
_FORBIDDEN_SQL_KEYWORDS = [
    'drop', 'delete', 'truncate', 'insert', 'update', 'alter',
    'create', 'replace', 'grant', 'revoke', 'exec', 'execute',
    'xp_', 'sp_', '--', '/*', '*/'
]


def _validate_report_sql(sql: str):
    """
    Ensure report SQL is a read-only SELECT statement.
    Uses word boundaries to avoid false positives on column/table names.
    Returns (True, None) if valid, (False, reason_string) if not.
    """
    stripped = sql.strip().lower()
    if not stripped.startswith('select'):
        return False, "Report SQL must be a SELECT statement"

    for keyword in _FORBIDDEN_SQL_KEYWORDS:
        if keyword in ('--', '/*', '*/'):
            if keyword in stripped:
                return False, "Report SQL contains forbidden sequence: '{}'".format(keyword)
        elif keyword.startswith(('xp_', 'sp_')):
            if keyword in stripped:
                return False, "Report SQL contains forbidden keyword: '{}'".format(keyword)
        else:
            if re.search(r'\b' + re.escape(keyword) + r'\b', stripped):
                return False, "Report SQL contains forbidden keyword: '{}'".format(keyword)
    return True, None


class ReportTypes:
    def __init__(self, logger: Logger):
        self.__logger = logger

    def process(self, request, session, user: User):
        if user.role != 'admin' and request.method != 'GET':
            return {'msg': 'Unauthorised'}, 401
        if request.method == 'GET':
            return self.__get(session)
        if request.method == 'POST':
            return self.__post(request, session, user)
        if request.method == 'DELETE':
            return self.__delete(request, session, user)
        if request.method == 'PUT':
            return self.__put(request, session, user)

    def __post(self, request, session, current_user):
        try:
            # FIXED (Copilot review): was reading request.form['sql'/'name'] directly.
            # Missing fields raised KeyError → HTTP 500. Now validates via schema first.
            errors, data = validate_request(request.form, ReportTypeCreateSchema())
            if errors:
                return jsonify({'status': 'error', 'message': errors}), 400

            sql = data['sql']
            name = data['name']

            valid, reason = _validate_report_sql(sql)
            if not valid:
                return jsonify({'status': 'error', 'message': reason}), 400

            report_type = ReportType(sql=sql, name=name)
            session.add(report_type)
            session.commit()
            self.__logger.log_user_action(current_user, 'CREATE REPORT TYPE', report_type.to_dict())
            return jsonify({'status': 'success', 'message': 'Report type created successfully'})
        except Exception as e:
            return jsonify({'status': 'error', 'message': 'Error creating report type: {}'.format(str(e))})

    @staticmethod
    def __get(session):
        types = []
        report_types = session.query(ReportType).all()
        if report_types:
            for rt in report_types:
                types.append(rt.to_dict())
        return jsonify(types)

    def __put(self, request, session, current_user):
        try:
            # FIXED (Copilot review): was int(request.form['id']) and bare form access.
            # Missing/non-numeric id raised ValueError → HTTP 500. Now validated first.
            errors, data = validate_request(request.form, ReportTypeUpdateSchema())
            if errors:
                return jsonify({'status': 'error', 'message': errors}), 400

            sql = data['sql']
            name = data['name']

            valid, reason = _validate_report_sql(sql)
            if not valid:
                return jsonify({'status': 'error', 'message': reason}), 400

            report_type = session.query(ReportType).get(data['id'])
            if report_type is None:
                return jsonify({'status': 'error', 'message': 'Report type not found'}), 404

            report_type.sql = sql
            report_type.name = name
            report_type.modification_date = datetime.now()
            session.add(report_type)
            session.commit()
            self.__logger.log_user_action(current_user, 'UPDATE REPORT TYPE', report_type.to_dict())
            return jsonify({'status': 'success', 'message': 'Report type updated successfully'})
        except Exception as e:
            return jsonify({'status': 'error', 'message': 'Report type update failure: {}'.format(str(e))})

    def __delete(self, request, session, current_user):
        try:
            # FIXED (Copilot review): was int(request.args.get('id')) — raises on
            # missing or non-numeric param. Now validated via schema.
            errors, data = validate_request(request.args, ReportTypeDeleteSchema())
            if errors:
                return jsonify({'status': 'error', 'message': errors}), 400

            report_type = session.query(ReportType).get(data['id'])
            if report_type is None:
                return jsonify({'status': 'error', 'message': 'Report type not found'}), 404

            session.delete(report_type)
            session.commit()
            self.__logger.log_user_action(current_user, 'DELETE REPORT TYPE', report_type.to_dict())
            return jsonify({'status': 'success', 'message': 'Report type deleted successfully'})
        except Exception as e:
            return jsonify({'status': 'error', 'message': 'Failed to delete report type: {}'.format(str(e))})
