import datetime
import os
import subprocess
from flask import jsonify, make_response
from app.models.models import ReportType, Report, User
from app.schemas.schemas import ReportCreateSchema, ReportUpdateSchema
from app.utilities.Logger import Logger
from app.utilities.utils import un_auth, error_message
from app.utilities.validation import validate_request
import pandas as pd


class Reports:
    def __init__(self, bin_dir, cron_dir, raw_db_connection, logger: Logger):
        self.__logger = logger
        self.__bin_dir = bin_dir
        self.__cron_dir = cron_dir
        self.__raw_db_connection = raw_db_connection

    def process(self, request, session, user: User):
        if request.method == 'GET':
            return self.__get(request, session, user)
        if request.method == 'POST':
            return self.__post(request, session, user)
        if request.method == 'DELETE':
            return self.__delete(request, session, user)
        if request.method == 'PUT':
            return self.__put(request, session, user)

    def __post(self, request, session, user):
        try:
            # ADDED: validate required fields before saving.
            # ReportCreateSchema enforces recurrence values and day-of-week range.
            errors, data = validate_request(request.form, ReportCreateSchema())
            if errors:
                return jsonify({'status': 'error', 'message': errors}), 400

            if session.query(Report).filter_by(name=data['name']).first():
                return error_message('Name already taken')

            time_val = data['time']
            recurrence = data['recurrence']
            scheduled = 1 if data['scheduled'] == 'true' else 0

            # CHANGED: cron expression building was duplicated verbatim in __post
            # and __put. Extracted to _build_cron_expression() to avoid drift.
            cron_expression = self._build_cron_expression(scheduled, recurrence, time_val, data['day'])
            if scheduled == 1 and recurrence == 'monthly':
                time_val = "00:00"

            report = Report(
                name=data['name'],
                report_type=session.query(ReportType).get(data['type']),
                scheduled=scheduled,
                cron_expression=cron_expression,
                recipients_to=data['to'],
                recipients_cc=data['cc'],
                time=time_val,
                day=data['day'],
                recurrence=recurrence,
                user_id=user.id
            )
            session.add(report)
            session.commit()
            self.__reload_reports_cron_tab(session)
            self.__logger.log_user_action(user, 'CREATE REPORT', report.to_dict())
            return jsonify({'status': 'success', 'message': 'Report created successfully'})
        except Exception as e:
            return jsonify({'status': 'error', 'message': 'Error creating report: {}'.format(str(e))})

    def __get(self, request, session, user: User):
        action = request.args.get('action')
        report_id = request.args.get('report-id')

        if action == 'download':
            try:
                download_report: Report = session.query(Report).get(int(report_id))
                if user.role != 'admin' and download_report.user_id != user.id:
                    return un_auth()
                sql_query = pd.read_sql_query(download_report.report_type.sql, self.__raw_db_connection)
                df = pd.DataFrame(sql_query)
                resp = make_response(df.to_csv(index=False))
                resp.headers["Content-Disposition"] = "attachment; filename=report.csv"
                resp.headers["Content-Type"] = "text/csv"
                return resp
            except Exception as e:
                return jsonify({'status': 'error', 'message': 'Error downloading report: {}'.format(str(e))})

        reports_from_db = session.query(Report).all() if user.role == 'admin' else user.reports
        reports = []
        if reports_from_db:
            for report in reports_from_db:
                owner = report.user.email if report.user else 'admin'
                reports.append({
                    'id': report.id, 'name': report.name,
                    'type': report.report_type.id, 'time': report.time,
                    'day': report.day, 'recurrence': report.recurrence,
                    'to': report.recipients_to, 'cc': report.recipients_cc,
                    'scheduled': True if report.scheduled == 1 else False,
                    'date_created': report.creation_date, 'owner': owner,
                })
        return jsonify(reports)

    def __put(self, request, session, user: User):
        try:
            # ADDED: validate update fields.
            errors, data = validate_request(request.form, ReportUpdateSchema())
            if errors:
                return jsonify({'status': 'error', 'message': errors}), 400

            report = session.query(Report).get(data['id'])
            if user.role != 'admin' and report.user_id != user.id:
                return un_auth()

            existing = session.query(Report).filter_by(name=data['name']).first()
            if existing and existing.id != report.id:
                return error_message('Name already taken')

            time_val = data['time']
            recurrence = data['recurrence']
            scheduled = 1 if data['scheduled'] == 'true' else 0
            cron_expression = self._build_cron_expression(scheduled, recurrence, time_val, data['day'])
            if scheduled == 1 and recurrence == 'monthly':
                time_val = "00:00"

            report.name = data['name']
            report.report_type = session.query(ReportType).get(data['type'])
            report.scheduled = scheduled
            report.cron_expression = cron_expression
            report.recipients_to = data['to']
            report.recipients_cc = data['cc']
            report.time = time_val
            report.day = data['day']
            report.recurrence = recurrence
            report.modification_date = datetime.datetime.now()

            session.add(report)
            session.commit()
            self.__reload_reports_cron_tab(session)
            self.__logger.log_user_action(user, 'UPDATE REPORT', report.to_dict())
            return jsonify({'status': 'success', 'message': 'Report updated successfully'})
        except Exception as e:
            return jsonify({'status': 'error', 'message': 'Error updating report: {}'.format(str(e))})

    def __delete(self, request, session, user):
        try:
            report_ids = str(request.args.get('reports')).split(',')
            for report_id in report_ids:
                report = session.query(Report).get(int(report_id))
                if user.role == 'admin' or report.user_id == user.id:
                    session.delete(report)
                    self.__logger.log_user_action(user, 'DELETE REPORT', report.to_dict())
            session.commit()
            self.__reload_reports_cron_tab(session)
            return jsonify({'status': 'success', 'message': 'Report(s) deleted successfully'})
        except Exception as e:
            return jsonify({'status': 'error', 'message': 'Error deleting report(s): {}'.format(str(e))})

    @staticmethod
    def _build_cron_expression(scheduled, recurrence, time_str, day_of_week):
        """
        Build a cron expression from report scheduling parameters.
        CHANGED: was duplicated verbatim in __post and __put. Extracting
        to a single method eliminates the risk of the two copies drifting.
        """
        if scheduled != 1:
            return None
        if recurrence == 'monthly':
            return '0 0 1 * *'
        parts = str(time_str).split(':')
        hours = parts[0]
        minutes = parts[1] if len(parts) > 1 else '0'
        if recurrence == 'weekly':
            return '{} {} * * {}'.format(minutes, hours, day_of_week)
        if recurrence == 'daily':
            return '{} {} * * *'.format(minutes, hours)
        return None

    def __reload_reports_cron_tab(self, session):
        """
        Rewrite the cron file using Python file I/O.
        CHANGED: was os.system('echo "..." >> file') which allowed shell injection.
        See Reports.py comments from PR #30 for the full explanation.
        """
        reports_cron_file = os.path.join(self.__cron_dir, "ivr-reports")
        try:
            if os.path.exists(reports_cron_file):
                os.remove(reports_cron_file)
        except OSError as e:
            self.__logger.log_error('Failed to remove cron file: {}'.format(str(e)))
            return

        lines = []
        for report in session.query(Report).all():
            if report.scheduled == 1 and report.cron_expression:
                expr = report.cron_expression
                # Allowlist: cron expressions only contain digits, spaces, * and /
                if not all(c in '0123456789* /' for c in expr):
                    self.__logger.log_warning(
                        'Skipping report {} — invalid cron expression: {}'.format(report.id, expr)
                    )
                    continue
                lines.append('{} root cd {} && python3 ivr-reports.py --report {}\n'.format(
                    expr, self.__bin_dir, int(report.id)
                ))
        try:
            with open(reports_cron_file, 'w') as f:
                f.writelines(lines)
            os.chmod(reports_cron_file, 0o600)
            subprocess.run(['chown', 'root:root', reports_cron_file], check=False)
        except OSError as e:
            self.__logger.log_error('Failed to write cron file: {}'.format(str(e)))
