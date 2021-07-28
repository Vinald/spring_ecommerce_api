import datetime
import os
from flask import jsonify, make_response
from app.models.models import Report, User, App
import pandas as pd

from app.utilities.Logger import Logger
from app.utilities.utils import un_auth, error_message


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
            app_id = int(request.form['app'])
            time = request.form['time']
            recurrence = request.form['recurrence']
            cron_expression = None
            report_name = request.form['name']
            recipients_to = str(request.form['to'])
            recipients_cc = str(request.form['cc'])
            day_of_week = request.form['day']

            if session.query(Report).filter_by(name=report_name).first():
                return error_message('Name already taken')

            if recurrence == 'monthly':
                time = "00:00"
            time_split = str(time).split(':')
            hours = time_split[0]
            minutes = time_split[1]
            if recurrence == 'monthly':
                cron_expression = '0 0 1 * *'
            if recurrence == 'weekly':
                cron_expression = '{} {} * * {}'.format(minutes, hours, day_of_week)
            if recurrence == 'daily':
                cron_expression = '{} {} * * *'.format(minutes, hours)

            report = Report(
                name=report_name,
                cron_expression=cron_expression,
                recipients_to=recipients_to,
                recipients_cc=recipients_cc,
                time=time,
                day=day_of_week,
                recurrence=recurrence,
                user_id=user.id,
                app=app_id,
                sql=self.__get_report_sql(user, request, session, True)
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

        if action == 'download':
            try:
                sql = self.__get_report_sql(user, request, session)
                if sql is None:
                    return un_auth()
                sql_query = pd.read_sql_query(sql, self.__raw_db_connection)
                df = pd.DataFrame(sql_query)
                resp = make_response(df.to_csv(index=False))
                resp.headers["Content-Disposition"] = "attachment; filename=report.csv"
                resp.headers["Content-Type"] = "text/csv"
                return resp
            except Exception as e:
                message = 'Error downloading report: {}'.format(str(e))
                return jsonify({'status': 'error', 'message': message})

        apps = []
        reports = []

        if user.role == 'admin':
            apps.append({'value': 0, 'text': 'All'})
            apps_from_db = session.query(App).all()
            reports_from_db = session.query(Report).all()
        else:
            apps_from_db = user.apps
            reports_from_db = user.reports

        if apps_from_db:
            for app in apps_from_db:
                apps.append({'value': app.id, 'text': app.name})

        if reports_from_db:
            for report in reports_from_db:
                owner = 'admin'
                if report.user is not None:
                    owner = report.user.email
                reports.append({
                    'id': report.id,
                    'name': report.name,
                    'time': report.time,
                    'day': report.day,
                    'recurrence': report.recurrence,
                    'to': report.recipients_to,
                    'cc': report.recipients_cc,
                    'date_created': report.creation_date,
                    'owner': owner,
                    'app': report.app,
                })
        return jsonify({'reports': reports, 'apps': apps})

    def __put(self, request, session, user: User):
        try:
            report = session.query(Report).get(int(request.form['id']))

            if user.role != 'admin' and report.user_id != user.id:
                return un_auth()

            time = request.form['time']
            recurrence = request.form['recurrence']
            cron_expression = None
            app = int(request.form['app'])
            report_name = request.form['name']
            recipients_to = str(request.form['to'])
            recipients_cc = str(request.form['cc'])
            day_of_week = request.form['day']

            if report_name != report.name and session.query(Report).filter_by(name=report_name).first():
                return error_message('Report name in use')

            if recurrence == 'monthly':
                time = "00:00"
            time_split = str(time).split(':')
            hours = time_split[0]
            minutes = time_split[1]
            if recurrence == 'monthly':
                cron_expression = '0 0 1 * *'
            if recurrence == 'weekly':
                cron_expression = '{} {} * * {}'.format(minutes, hours, day_of_week)
            if recurrence == 'daily':
                cron_expression = '{} {} * * *'.format(minutes, hours)

            report.name = report_name
            report.app = app
            report.cron_expression = cron_expression
            report.recipients_to = recipients_to
            report.recipients_cc = recipients_cc
            report.time = time
            report.day = day_of_week
            report.recurrence = recurrence
            report.modification_date = datetime.datetime.now()
            report.sql = self.__get_report_sql(user, request, session, True)

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

    def __reload_reports_cron_tab(self, session):
        reports_cron_file = os.path.join(self.__cron_dir, "ivr-reports")
        reports = session.query(Report).all()
        os.system("rm -rf {}".format(reports_cron_file))
        for report in reports:
            report_id = report.id
            cron_expression = report.cron_expression
            os.system('echo "{} root cd {} && python3 ivr-reports.py --report {}" >> {}'.format(
                cron_expression,
                self.__bin_dir,
                report_id,
                reports_cron_file
            ))
        os.system("chown root:root {}".format(reports_cron_file))
        os.system("chmod 600 {}".format(reports_cron_file))

    @staticmethod
    def __get_report_sql(user: User, request, session, monthly=False):
        end = request.args.get('endDate')
        start = request.args.get('startDate')
        app_id = request.args.get('app') if request.args.get('app') is not None else request.form['app']
        app = session.query(App).get(int(app_id))
        if (app is None and user.role != 'admin') or (user.role != 'admin' and app.user_id != user.id):
            return None
        if monthly and app is None:
            return "SELECT `creation_date` as `Date Created`, `app_name` as `App Name`, `caller_id` as `Caller ID`, `dialed_number` as `Dialed Number`, `call_start_time` as `Call Start Time`, `call_end_time` as `Call End Time`, `duration` as `Duration`, `call_state` as `Call State`, `peer` as `Service Provider`, `call_direction` as `Direction` FROM `cdr` WHERE DATE(`creation_date`) BETWEEN DATE_ADD(LAST_DAY(DATE_SUB(current_date, INTERVAL 2 MONTH)), INTERVAL 1 DAY) AND LAST_DAY(DATE_SUB(current_date, INTERVAL 1 MONTH))"
        if monthly and app is not None:
            return f"SELECT `creation_date` as `Date Created`, `app_name` as `App Name`, `caller_id` as `Caller ID`, `dialed_number` as `Dialed Number`, `call_start_time` as `Call Start Time`, `call_end_time` as `Call End Time`, `duration` as `Duration`, `call_state` as `Call State`, `peer` as `Service Provider`, `call_direction` as `Direction` FROM `cdr` WHERE `token`='{app.token}' AND DATE(`creation_date`) BETWEEN DATE_ADD(LAST_DAY(DATE_SUB(current_date, INTERVAL 2 MONTH)), INTERVAL 1 DAY) AND LAST_DAY(DATE_SUB(current_date, INTERVAL 1 MONTH))"
        if app is None:
            return f"SELECT `creation_date` as `Date Created`, `app_name` as `App Name`, `caller_id` as `Caller ID`, `dialed_number` as `Dialed Number`, `call_start_time` as `Call Start Time`, `call_end_time` as `Call End Time`, `duration` as `Duration`, `call_state` as `Call State`, `peer` as `Service Provider`, `call_direction` as `Direction` FROM `cdr` WHERE DATE(`creation_date`) BETWEEN DATE('{start}') AND DATE('{end}')"
        if app is not None:
            return f"SELECT `creation_date` as `Date Created`, `app_name` as `App Name`, `caller_id` as `Caller ID`, `dialed_number` as `Dialed Number`, `call_start_time` as `Call Start Time`, `call_end_time` as `Call End Time`, `duration` as `Duration`, `call_state` as `Call State`, `peer` as `Service Provider`, `call_direction` as `Direction` FROM `cdr` WHERE `token`='{app.token}' AND DATE(`creation_date`) BETWEEN DATE('{start}') AND DATE('{start}')"
        return None
