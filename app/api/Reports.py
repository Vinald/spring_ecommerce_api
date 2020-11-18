import os
from flask import jsonify, make_response
from app.models.models import ReportType, Report
import pandas as pd


class Reports:
    def __init__(self, bin_dir, cron_dir, raw_db_connection):
        self.__bin_dir = bin_dir
        self.__cron_dir = cron_dir
        self.__raw_db_connection = raw_db_connection

    def process(self, request, session):
        if request.method == 'GET':
            return self.__get(request, session)
        if request.method == 'POST':
            return self.__post(request, session)
        if request.method == 'DELETE':
            return self.__delete(request, session)
        if request.method == 'PUT':
            return self.__put(request, session)

    def __post(self, request, session):
        try:
            time = request.form['time']
            recurrence = request.form['recurrence']
            scheduled = 1 if request.form['scheduled'] == 'true' else 0
            cron_expression = None
            report_type = session.query(ReportType).get(int(request.form['type']))
            report_name = request.form['name']
            recipients_to = str(request.form['to'])
            recipients_cc = str(request.form['cc'])
            day_of_week = request.form['day']

            if scheduled == 1:
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
                report_type=report_type,
                scheduled=scheduled,
                cron_expression=cron_expression,
                recipients_to=recipients_to,
                recipients_cc=recipients_cc,
                time=time,
                day=day_of_week,
                recurrence=recurrence
            )

            session.add(report)
            session.commit()
            self.__reload_reports_cron_tab(session)
            return jsonify({'status': 'success', 'message': 'Report created successfully'})
        except Exception as e:
            return jsonify({'status': 'error', 'message': 'Error creating report: {}'.format(str(e))})

    def __get(self, request, session):
        action = request.args.get('action')
        report_id = request.args.get('report-id')

        if action == 'download':
            try:
                download_report: Report = session.query(Report).get(int(report_id))
                sql_query = pd.read_sql_query(download_report.report_type.sql, self.__raw_db_connection)
                df = pd.DataFrame(sql_query)
                resp = make_response(df.to_csv(index=False))
                resp.headers["Content-Disposition"] = "attachment; filename=report.csv"
                resp.headers["Content-Type"] = "text/csv"
                return resp
            except Exception as e:
                message = 'Error downloading report: {}'.format(str(e))
                return jsonify({'status': 'error', 'message': message})

        reports = []
        reports_from_db = session.query(Report).all()

        if reports_from_db:
            for report in reports_from_db:
                reports.append({
                    'id': report.id,
                    'name': report.name,
                    'type': report.report_type.id,
                    'time': report.time,
                    'day': report.day,
                    'recurrence': report.recurrence,
                    'to': report.recipients_to,
                    'cc': report.recipients_cc,
                    'scheduled': True if report.scheduled == 1 else False,
                    'date_created': report.creation_date,
                })
        return jsonify(reports)

    def __put(self, request, session):
        try:
            report = session.query(Report).get(int(request.form['id']))
            time = request.form['time']
            recurrence = request.form['recurrence']
            scheduled = 1 if request.form['scheduled'] == 'true' else 0
            cron_expression = None
            report_type = session.query(ReportType).get(int(request.form['type']))
            report_name = request.form['name']
            recipients_to = str(request.form['to'])
            recipients_cc = str(request.form['cc'])
            day_of_week = request.form['day']

            if scheduled == 1:
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
            report.report_type = report_type
            report.scheduled = scheduled
            report.cron_expression = cron_expression
            report.recipients_to = recipients_to
            report.recipients_cc = recipients_cc
            report.time = time
            report.day = day_of_week
            report.recurrence = recurrence

            session.add(report)
            session.commit()
            self.__reload_reports_cron_tab(session)
            return jsonify({'status': 'success', 'message': 'Report updated successfully'})
        except Exception as e:
            return jsonify({'status': 'error', 'message': 'Error updating report: {}'.format(str(e))})

    def __delete(self, request, session):
        try:
            report_ids = str(request.args.get('reports')).split(',')
            for report_id in report_ids:
                report = session.query(Report).get(int(report_id))
                session.delete(report)
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
            if report.scheduled == 1:
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
