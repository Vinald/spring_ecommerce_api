import datetime
import uuid
from flask import jsonify
from app.models.models import App
from app.schemas.schemas import AppCreateSchema, AppUpdateSchema, AppDeleteSchema
from app.utilities.Hash import Hash
from app.utilities.Logger import Logger
from app.utilities.utils import error, success, un_auth, error_message
from app.utilities.validation import validate_request


class Applications:
    def __init__(self, logger: Logger):
        self.__logger = logger

    def process_request(self, request, session, user):
        if request.method == 'GET':
            return self.__get(session, user)
        if request.method == 'POST':
            return self.__post(request, session, user)
        if request.method == 'DELETE':
            return self.__delete(request, session, user)
        if request.method == 'PUT':
            return self.__put(request, session, user)

    @staticmethod
    def __get(session, user):
        try:
            apps = []
            if user.role == 'admin':
                apps_from_db = session.query(App).all()
            else:
                apps_from_db = user.apps

            if apps_from_db:
                for app in apps_from_db:
                    owner = 'admin'
                    if app.user is not None:
                        owner = app.user.email
                    app_data = app.to_dict()
                    app_data['owner'] = owner
                    apps.append(app_data)
            return jsonify(apps=apps)
        except Exception as e:
            return jsonify(error('Error fetching apps', e))

    def __post(self, request, session, user):
        try:
            # ADDED: validate all required fields before saving.
            errors, data = validate_request(request.form, AppCreateSchema())
            if errors:
                return jsonify(error_message(errors)), 400

            name = data['name']
            if session.query(App).filter_by(name=name).first():
                return error_message('Name already taken')

            app = App(
                name=name,
                token=self.__token_generator(),
                voice_url=data['voice_url'],
                status_url=data['status_url'],
                user_id=user.id,
            )
            if user.is_admin():
                app.phone = data['phone']
                app.toll_free = data['toll_free']
                app.caller_id = data['caller_id']

            session.add(app)
            session.commit()
            self.__logger.log_user_action(user, 'CREATE APP', app.to_dict())
            return jsonify(success('Application created successfully'))
        except Exception as e:
            return jsonify(error('Error creating app', e))

    def __put(self, request, session, user):
        try:
            # ADDED: validate update fields.
            errors, data = validate_request(request.form, AppUpdateSchema())
            if errors:
                return jsonify(error_message(errors)), 400

            app = session.query(App).get(data['id'])
            if user.role != 'admin' and app.user_id != user.id:
                return un_auth()

            app.name = data['name']
            app.voice_url = data['voice_url']
            app.status_url = data['status_url']
            app.date_modified = datetime.datetime.now()

            if user.is_admin():
                app.phone = data['phone']
                app.toll_free = data['toll_free']
                app.caller_id = data['caller_id']

            session.add(app)
            session.commit()
            self.__logger.log_user_action(user, 'UPDATE APP', app.to_dict())
            return jsonify(success('App updated successfully'))
        except Exception as e:
            return jsonify(error('Error updating app', e))

    def __delete(self, request, session, user):
        try:
            # ADDED: validate the id query param.
            errors, data = validate_request(request.args, AppDeleteSchema())
            if errors:
                return jsonify(error_message(errors)), 400

            app = session.query(App).get(data['id'])
            if user.role != 'admin' and app.user_id != user.id:
                return un_auth()
            session.delete(app)
            session.commit()
            self.__logger.log_user_action(user, 'DELETE APP', app.to_dict())
            return jsonify(success('App deleted successfully'))
        except Exception as e:
            return jsonify(error('Error deleting app', e))

    @staticmethod
    def __token_generator():
        unique_id = str(uuid.uuid1())
        return Hash.hash(unique_id)
