import bcrypt
from flask import jsonify
from app.models.models import User
from app.utilities.Logger import Logger
from app.utilities.utils import error_message, error, success, un_auth
import datetime


class Users:
    def __init__(self, logger: Logger):
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
            role = request.form['role']
            email = request.form['email']
            password = request.form['password']

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
            user = session.query(User).get(int(request.form['id']))

            role = request.form['role']
            email = request.form['email']
            password = request.form['password']

            user.role = role

            if user.email != email:
                if session.query(User).filter_by(email=email).first():
                    return error_message('Email already taken')
                else:
                    user.email = email

            if len(password) > 0:
                user.password = password

            user.modification_date = datetime.datetime.now()

            session.add(user)
            session.commit()
            self.__logger.log_user_action(current_user, 'UPDATE USER', user.to_dict())
            return jsonify(success('User updated successfully'))
        except Exception as e:
            return jsonify(error('Error updating user', e))

    def __delete(self, request, session, current_user):
        try:
            user_id = int(request.args.get('id'))
            user = session.query(User).get(user_id)
            session.delete(user)
            session.commit()
            self.__logger.log_user_action(current_user, 'DELETE USER', user.to_dict())
            return jsonify(success('User deleted successfully'))
        except Exception as e:
            return jsonify(error('Error deleting user', e))
