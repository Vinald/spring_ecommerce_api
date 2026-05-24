import datetime
import bcrypt
from flask import jsonify
from app.models.models import User
from app.schemas.schemas import ProfileUpdateSchema
from app.utilities.Logger import Logger
from app.utilities.utils import error_message, success
from app.utilities.validation import validate_request


class Profile:
    def __init__(self, logger: Logger):
        self.__logger = logger

    def process(self, request, session, user):
        if request.method == 'POST':
            return self.__post(request, session, user)

    def __post(self, request, session, user):
        try:
            # ADDED: validate fields before processing. Previously a missing
            # 'password' or 'oldPassword' key would crash with KeyError → 500.
            errors, data = validate_request(request.form, ProfileUpdateSchema())
            if errors:
                return jsonify(error_message(errors)), 400

            user = session.query(User).filter(User.email == user.email).first()
            old_password = data['oldPassword']
            password = data['password']

            if user is None or not bcrypt.checkpw(old_password.encode('utf-8'), user.password.encode('utf-8')):
                return jsonify(error_message('Wrong old password'))

            user.password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            user.modification_date = datetime.datetime.now()
            session.add(user)
            session.commit()
            return jsonify(success('Password updated successfully'))
        except Exception as e:
            self.__logger.log_error(f'Error updating user password: {str(e)}')
            return jsonify(error_message('Error updating password'))
