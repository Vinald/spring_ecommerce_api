"""
App data access used by the AGI script (agi.py) to look up voice URLs and tokens.

CHANGED: Previously used raw PyMySQL queries via the Database utility class,
running alongside the SQLAlchemy ORM used everywhere else. This dual-layer
approach caused:
  - Two separate connection pools to the same database
  - Inconsistent transaction handling (PyMySQL autocommit vs SQLAlchemy explicit)
  - Connection leaks when the raw cursor was not properly closed

Now uses a SQLAlchemy session passed in from the caller, eliminating the raw
PyMySQL dependency entirely for this class.
"""
from sqlalchemy.orm import Session as SASession
from app.models.models import App
from app.utilities.Logger import Logger


class Apps:
    def __init__(self, session_factory, logger: Logger):
        # CHANGED: was __init__(self, database: Database, logger: Logger)
        # Now receives a SQLAlchemy session_factory (sessionmaker) instead of
        # the raw Database wrapper, removing the PyMySQL dependency.
        self.__session_factory = session_factory
        self.__logger = logger

    def _get_session(self) -> SASession:
        """Open a new SQLAlchemy session for this operation."""
        return self.__session_factory()

    def get_token_by_dialed_number(self, dialed_num: str):
        """
        Look up the app token for an incoming dialed number.
        CHANGED: was a raw SQL string query. Now uses ORM filter() —
        parameterisation is handled by SQLAlchemy automatically.
        """
        session = self._get_session()
        try:
            app = session.query(App).filter(App.phone == dialed_num).first()
            return app.token if app else None
        except Exception as e:
            self.__logger.log_info("ORM fetch error (get_token_by_dialed_number): {}".format(str(e)))
            return None
        finally:
            session.close()

    def get_voice_url(self, token: str) -> str:
        data = self.get_data(token)
        return str(data['voice_url']) if data else ''

    def get_status_url(self, token: str) -> str:
        data = self.get_data(token)
        if not data:
            return ''
        status = str(data['status_url'])
        return status if status.endswith('/') else status + '/'

    def get_data(self, token: str):
        """
        Fetch all app fields for a given token.
        CHANGED: was raw SQL 'SELECT * FROM apps WHERE token = %s'.
        Now uses ORM query and returns a plain dict for backward compatibility
        with callers that access fields by key (e.g. data['name']).
        """
        session = self._get_session()
        try:
            app = session.query(App).filter(App.token == token).first()
            if app is None:
                return {}
            # Return a plain dict to keep the existing call-site interface intact.
            return {
                'id': app.id,
                'name': app.name,
                'token': app.token,
                'phone': app.phone,
                'toll_free': app.toll_free,
                'caller_id': app.caller_id,
                'voice_url': app.voice_url,
                'status_url': app.status_url,
                'user_id': app.user_id,
            }
        except Exception as e:
            self.__logger.log_info("ORM fetch error (get_data): {}".format(str(e)))
            return {}
        finally:
            session.close()
