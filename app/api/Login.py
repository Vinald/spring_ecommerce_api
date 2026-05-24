import bcrypt
from app.models.models import User
from app.schemas.schemas import LoginSchema
from app.utilities.Logger import Logger
from app.utilities.validation import validate_request


class Login:
    def __init__(self, logger: Logger):
        self.__logger = logger

    def verify(self, request, session):
        """
        Verify credentials and return user details, or False on any failure.

        Returns:
            {'user': User, 'details': {...}}  on success
            False                             on bad credentials OR bad input

        FIXED (Copilot review): previously returned a tuple ({'errors':...}, 400)
        on validation failure. That is truthy, so the blueprint would attempt
        user_details['user'] on a tuple and raise TypeError/KeyError.
        Now returns False consistently so callers only need one check.
        The blueprint logs the 400 detail separately so it isn't swallowed.
        """
        errors, data = validate_request(request.form, LoginSchema())
        if errors:
            # Log the validation error for debugging but return False so the
            # route layer returns a generic 401 (avoids leaking field names).
            self.__logger.log_warning('Login validation error: {}'.format(errors))
            return False

        username = data['username']
        password = data['password']

        user = session.query(User).filter(User.email == username).first()
        if user is None or not bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
            return False

        login_log_message = 'LOGIN from IP: {}'.format(request.remote_addr)
        self.__logger.log_user_action(user, login_log_message, user.to_dict())
        return {'details': {'email': user.email, 'role': user.role}, 'user': user}
