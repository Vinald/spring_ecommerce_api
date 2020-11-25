import datetime
from app.utilities.Database import Database


class Charts:
    def __init__(self, database: Database):
        self.__database = database

    @staticmethod
    def __date_range(date1, date2):
        for n in range(int((date2 - date1).days) + 1):
            yield date1 + datetime.timedelta(n)

    def __chart_data(self, sql, state):
        start_date = datetime.date.today() - datetime.timedelta(7)
        end_date = datetime.date.today()
        x = {}
        cursor = self.__database.get_cursor()
        for dt in self.__date_range(start_date, end_date):
            cursor.execute(sql.format(state, dt))
            db_data = cursor.fetchone()
            x[dt.__str__()] = db_data['count']
        return x

    def get_cdr_data(self):
        busy = "SELECT count(id) count from cdr where call_state = '{}' and DATE(creation_date) = '{}'"
        failed = "SELECT count(id) count from cdr where call_state = '{}' and DATE(creation_date) = '{}'"
        answered = "SELECT count(id) count from cdr where call_state = '{}' and DATE(creation_date) = '{}'"
        no_answer = "SELECT count(id) count from cdr where call_state = '{}' and DATE(creation_date) = '{}'"
        all_data = []
        busy_data = {'name': 'BUSY', 'data': self.__chart_data(busy, 'BUSY')}
        answered_data = {'name': 'COMPLETED', 'data': self.__chart_data(answered, 'ANSWERED')}
        failed_data = {'name': 'FAILED', 'data': self.__chart_data(failed, 'FAILED')}
        no_answer_data = {'name': 'NO_ANSWER', 'data': self.__chart_data(no_answer, 'NO_ANSWER')}
        all_data.append(no_answer_data)
        all_data.append(failed_data)
        all_data.append(busy_data)
        all_data.append(answered_data)
        return all_data
