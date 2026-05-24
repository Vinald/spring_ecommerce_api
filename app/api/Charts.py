import datetime
from sqlalchemy import func
from app.models.models import User, CDR


class Charts:
    def __init__(self):
        pass

    @staticmethod
    def __date_range(date1, date2):
        for n in range(int((date2 - date1).days) + 1):
            yield date1 + datetime.timedelta(n)

    def __chart_data(self, state, session, user: User):
        start_date = datetime.date.today() - datetime.timedelta(15)
        end_date = datetime.date.today()
        x = {}
        tokens = self.__get_user_apps_tokens(user)

        for dt in self.__date_range(start_date, end_date):
            if user.is_admin():
                data_count = session.query(CDR).filter(
                    CDR.call_state == state,
                    func.date(CDR.creation_date) == dt.strftime("%Y-%m-%d")
                ).count()
                x[dt.__str__()] = data_count
            else:
                if not tokens:
                    return []
                data_count = session.query(CDR).filter(
                    CDR.token.in_(tokens),
                    CDR.call_state == state,
                    func.date(CDR.creation_date) == dt.strftime("%Y-%m-%d")
                ).count()
                x[dt.__str__()] = data_count
        return x

    def get_cdr_data(self, user: User, session):
        all_data = []
        busy_data = {'name': 'BUSY', 'data': self.__chart_data('BUSY', session, user)}
        # CHANGED: was querying 'ANSWERED' but labelling the series 'COMPLETED'.
        # CDRManager writes 'ANSWERED' as the call_state so the query and label
        # must match. Using 'ANSWERED' consistently across both.
        answered_data = {'name': 'ANSWERED', 'data': self.__chart_data('ANSWERED', session, user)}
        failed_data = {'name': 'FAILED', 'data': self.__chart_data('FAILED', session, user)}
        no_answer_data = {'name': 'NO_ANSWER', 'data': self.__chart_data('NO_ANSWER', session, user)}
        all_data.append(no_answer_data)
        all_data.append(failed_data)
        all_data.append(busy_data)
        all_data.append(answered_data)
        return all_data

    @staticmethod
    def __get_user_apps_tokens(user: User):
        apps = user.apps
        tokens = []
        if apps:
            for app in apps:
                tokens.append(app.token)
            return tokens
        return None
