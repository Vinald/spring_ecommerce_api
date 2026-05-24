import bcrypt
import datetime
from flask import jsonify
from app.models.models import User
from app.schemas.schemas import UserCreateSchema, UserUpdateSchema, UserDeleteSchema
from app.utilities.Logger import Logger
from app.utilities.Mailer import Mailer
from app.utilities.utils import error_message, error, success, un_auth
from app.utilities.validation import validate_request


class Users:
    def __init__(self, logger: Logger, mailer: Mailer):
        self.__mailer = mailer
        self.__logger = logger

    def handle_request(self, request, session, user: User):
        if user.role != 'admin':
            return un_auth()
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
            # ADDED: validate all required fields up-front.
            errors, data = validate_request(request.form, UserCreateSchema())
            if errors:
                return jsonify(error_message(errors)), 400

            email = data['email']
            password = data['password']
            role = data['role']

            if session.query(User).filter_by(email=email).first():
                return error_message('Email already taken')

            user = User(
                role=role,
                email=email,
                password=bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            )
            session.add(user)
            session.commit()
            self.__logger.log_user_action(current_user, 'CREATE USER', user.to_dict())

            self.__mailer.set_to([user.email])
            self.__mailer.set_subject('Academy IVR Account')
            self.__mailer.set_message(
                "Hello,\n\n"
                "Your IVR account has been created successfully.\n"
                "Use the details below to login:\n\n"
                "Username: {}\n\n"
                "Please contact your administrator for your temporary password "
                "and change it immediately after your first login.\n\n"
                "Have a good day.\n".format(user.email)
            )
            self.__mailer.send_email()
            return jsonify(success('User created successfully'))
        except Exception as e:
            return jsonify(error('Failed to create user', e))

    @staticmethod
    def __get(session):
        try:
            users = []
            users_from_db = session.query(User).all()
            if users_from_db:
                for user in users_from_db:
                    users.append(user.to_dict())
            return jsonify(users=users)
        except Exception as e:
            return jsonify(error('Error fetching users', e))

    def __put(self, request, session, current_user):
        try:
            # ADDED: validate update fields.
            errors, data = validate_request(request.form, UserUpdateSchema())
            if errors:
                return jsonify(error_message(errors)), 400

            user = session.query(User).get(data['id'])
            role = data['role']
            email = data['email']
            password = data['password']

            user.role = role
            if user.email != email:
                if session.query(User).filter_by(email=email).first():
                    return error_message('Email already taken')
                else:
                    user.email = email

            if len(password) > 0:
                user.password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

            user.modification_date = datetime.datetime.now()
            session.add(user)
            session.commit()
            self.__logger.log_user_action(current_user, 'UPDATE USER', user.to_dict())
            return jsonify(success('User updated successfully'))
        except Exception as e:
            return jsonify(error('Error updating user', e))

    def __delete(self, request, session, current_user):
        try:
            # ADDED: validate the id query param.
            errors, data = validate_request(request.args, UserDeleteSchema())
            if errors:
                return jsonify(error_message(errors)), 400

            user = session.query(User).get(data['id'])
            session.delete(user)
            session.commit()
            self.__logger.log_user_action(current_user, 'DELETE USER', user.to_dict())
            return jsonify(success('User deleted successfully'))
        except Exception as e:
            return jsonify(error('Error deleting user', e))
