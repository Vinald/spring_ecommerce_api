import bcrypt
from app.models.models import User
from app.utilities.Logger import Logger


class Login:
    def __init__(self, logger: Logger):
        self.__logger = logger

    def verify(self, request, session):
        username = request.form['username']
        password = request.form['password']

        user = session.query(User).filter(User.email == username).first()
        if user is None or not bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
            return False
        login_log_message = f'LOGIN from IP: {request.remote_addr}'
        self.__logger.log_user_action(user, login_log_message, user.to_dict())
        return {'details': {'email': user.email, 'role': user.role}, 'user': user}
