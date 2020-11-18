from datetime import datetime
from flask import jsonify
from app.models.models import ReportType


class ReportTypes:
    def process(self, request, session):
        if request.method == 'GET':
            return self.__get(session)
        if request.method == 'POST':
            return self.__post(request, session)
        if request.method == 'DELETE':
            return self.__delete(request, session)
        if request.method == 'PUT':
            return self.__put(request, session)

    @staticmethod
    def __post(request, session):
        try:
            report_type = ReportType(sql=request.form['sql'], name=request.form['name'])
            session.add(report_type)
            session.commit()
            return jsonify({'status': 'success', 'message': 'Report type created successfully'})
        except Exception as e:
            return jsonify({'status': 'error', 'message': 'Error creating report type: {}'.format(str(e))})

    @staticmethod
    def __get(session):
        types = []
        report_types = session.query(ReportType).all()
        if report_types:
            for report_type in report_types:
                types.append({'id': report_type.id, 'sql': report_type.sql, 'name': report_type.name})
        return jsonify(types)

    @staticmethod
    def __put(request, session):
        report_type_id = int(request.form['id'])
        sql = request.form['sql']
        name = request.form['name']
        try:
            report_type = session.query(ReportType).get(report_type_id)
            report_type.sql = sql
            report_type.name = name
            report_type.modification_date = datetime.now()
            session.add(report_type)
            session.commit()
            return jsonify({'status': 'success', 'message': 'Report type updated successfully'})
        except Exception as e:
            return jsonify({'status': 'error', 'message': 'Report type update failure: {}'.format(str(e))})

    @staticmethod
    def __delete(request, session):
        report_type_id = int(request.args.get('id'))
        try:
            report_type = session.query(ReportType).get(report_type_id)
            session.delete(report_type)
            session.commit()
            return jsonify({'status': 'success', 'message': 'Report type deleted successfully'})
        except Exception as e:
            return jsonify({'status': 'error', 'message': 'Failed to delete report type: {}'.format(str(e))})
