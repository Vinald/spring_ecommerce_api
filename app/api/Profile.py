import datetime
import re

import bcrypt
from flask import jsonify

from app.models.models import User
from app.utilities.Logger import Logger
from app.utilities.utils import error_message, success


class Profile:
    def __init__(self, logger: Logger):
        self.__logger = logger

    def process(self, request, session, user):
        if request.method == 'POST':
            return self.__post(request, session, user)

    def __post(self, request, session, user):
        try:
            user = session.query(User).filter(User.email == user.email).first()
            password = request.form['password']
            old_password = request.form['oldPassword']

            if user is None or not bcrypt.checkpw(old_password.encode('utf-8'), user.password.encode('utf-8')):
                return jsonify(error_message('Wrong old password'))

            if re.search('^(?=.*\d)(?=.*[a-z])(?=.*[A-Z])(?=.*[a-zA-Z]).{8,}$', password) is None:
                msg = 'Password must be a minimum of 8 characters. Must contain a digit, upper and lower case letter'
                return jsonify(error_message(msg))

            user.password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            user.modification_date = datetime.datetime.now()

            session.add(user)
            session.commit()
            return jsonify(success('Password updated successfully'))
        except Exception as e:
            self.__logger.log_error(f'Error updating user password: {str(e)}')
            return jsonify(error_message('Error updating password'))

