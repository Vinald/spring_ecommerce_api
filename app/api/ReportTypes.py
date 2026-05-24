from datetime import datetime
from flask import jsonify
from app.models.models import ReportType, User
from app.utilities.Logger import Logger

# Basic SQL keyword allowlist — report type SQLs must be read-only SELECT statements
_FORBIDDEN_SQL_KEYWORDS = [
    'drop', 'delete', 'truncate', 'insert', 'update', 'alter',
    'create', 'replace', 'grant', 'revoke', 'exec', 'execute',
    'xp_', 'sp_', '--', '/*', '*/'
]


def _validate_report_sql(sql: str):
    """
    Ensure report SQL is a read-only SELECT statement.
    Returns (True, None) if valid, (False, reason) if not.
    """
    stripped = sql.strip().lower()
    if not stripped.startswith('select'):
        return False, "Report SQL must be a SELECT statement"
    for keyword in _FORBIDDEN_SQL_KEYWORDS:
        if keyword in stripped:
            return False, "Report SQL contains forbidden keyword: '{}'".format(keyword)
    return True, None


class ReportTypes:
    def __init__(self, logger: Logger):
        self.__logger = logger

    def process(self, request, session, user: User):
        if user.role != 'admin' and request.method != 'GET':
            return {'msg': 'This operation will be reported'}, 401
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
            sql = request.form['sql']
            name = request.form['name']

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
            for report_type in report_types:
                types.append(report_type.to_dict())
        return jsonify(types)

    def __put(self, request, session, current_user):
        report_type_id = int(request.form['id'])
        sql = request.form['sql']
        name = request.form['name']

        valid, reason = _validate_report_sql(sql)
        if not valid:
            return jsonify({'status': 'error', 'message': reason}), 400

        try:
            report_type = session.query(ReportType).get(report_type_id)
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
        report_type_id = int(request.args.get('id'))
        try:
            report_type = session.query(ReportType).get(report_type_id)
            session.delete(report_type)
            session.commit()
            self.__logger.log_user_action(current_user, 'DELETE REPORT TYPE', report_type.to_dict())
            return jsonify({'status': 'success', 'message': 'Report type deleted successfully'})
        except Exception as e:
            return jsonify({'status': 'error', 'message': 'Failed to delete report type: {}'.format(str(e))})
