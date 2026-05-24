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
            # ADDED: validate all required fields before creating the user.
            # UserCreateSchema enforces email format, min password length,
            # and role allowlist. Previously a missing field → KeyError → 500.
            errors, data = validate_request(request.form, UserCreateSchema())
            if errors:
                return jsonify(error_message(errors)), 400

            if session.query(User).filter_by(email=data['email']).first():
                return error_message('Email already taken')

            user = User(
                role=data['role'],
                email=data['email'],
                password=bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt())
            )
            session.add(user)
            session.commit()
            self.__logger.log_user_action(current_user, 'CREATE USER', user.to_dict())

            # CHANGED: previously emailed the plaintext password — serious security
            # risk (visible in email logs and inboxes). Now tells the user to contact
            # the admin for their temporary password.
            self.__mailer.set_to([user.email])
            self.__mailer.set_subject('Academy IVR Account')
            self.__mailer.set_message(
                "Hello,\n\nYour IVR account has been created successfully.\n"
                "Username: {}\n\nContact your administrator for your temporary "
                "password and change it on first login.\n\nHave a good day.\n".format(user.email)
            )
            self.__mailer.send_email()
            return jsonify(success('User created successfully'))
        except Exception as e:
            return jsonify(error('Failed to create user', e))

    @staticmethod
    def __get(session):
        try:
            users = [u.to_dict() for u in session.query(User).all()]
            return jsonify(users=users)
        except Exception as e:
            return jsonify(error('Error fetching users', e))

    def __put(self, request, session, current_user):
        try:
            # ADDED: validate update fields including role allowlist and email format.
            errors, data = validate_request(request.form, UserUpdateSchema())
            if errors:
                return jsonify(error_message(errors)), 400

            user = session.query(User).get(data['id'])
            user.role = data['role']

            if user.email != data['email']:
                if session.query(User).filter_by(email=data['email']).first():
                    return error_message('Email already taken')
                user.email = data['email']

            if len(data['password']) > 0:
                user.password = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt())

            user.modification_date = datetime.datetime.now()
            session.add(user)
            session.commit()
            self.__logger.log_user_action(current_user, 'UPDATE USER', user.to_dict())
            return jsonify(success('User updated successfully'))
        except Exception as e:
            return jsonify(error('Error updating user', e))

    def __delete(self, request, session, current_user):
        try:
            # ADDED: validate the id query param — was previously int(request.args.get('id'))
            # which raised ValueError if the param was missing or non-numeric → 500.
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
