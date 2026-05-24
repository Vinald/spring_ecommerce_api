import bcrypt
from flask import jsonify
from app.models.models import User
from app.schemas.schemas import LoginSchema
from app.utilities.Logger import Logger
from app.utilities.validation import validate_request


class Login:
    def __init__(self, logger: Logger):
        self.__logger = logger

    def verify(self, request, session):
        # ADDED: validate required fields before touching the DB.
        # Previously a missing 'username' or 'password' field would raise
        # KeyError which Flask returned as an unhandled HTTP 500.
        errors, data = validate_request(request.form, LoginSchema())
        if errors:
            return False

        username = data['username']
        password = data['password']

        user = session.query(User).filter(User.email == username).first()
        if user is None or not bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
            return False
        login_log_message = f'LOGIN from IP: {request.remote_addr}'
        self.__logger.log_user_action(user, login_log_message, user.to_dict())
        return {'details': {'email': user.email, 'role': user.role}, 'user': user}
