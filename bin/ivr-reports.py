import argparse
import os
import sys
import pandas as pd

sys.path.append('..')
from app.utilities.Hash import Hash
from app.core import database
from app.utilities.Email import Email

connection = database.get_conn()
cursor = database.get_cursor()

parser = argparse.ArgumentParser()

# Optional arguments
report_help = "Set the report id"
parser.add_argument("-r", "--report", help=report_help, type=int, default=0)

# Parse arguments
args = parser.parse_args()

report_id = int(args.report)


def report_data():
    sql = "SELECT * FROM `{}` WHERE `id` = {}".format('reports', report_id)
    cursor.execute(sql)
    results = cursor.fetchone()
    return results


def report_type_data(data):
    sql = "SELECT `sql` FROM `{}` WHERE `id` = {}".format('report_types', data['type_id'])
    cursor.execute(sql)
    results = cursor.fetchone()
    return results['sql']


report = report_data()
report_sql = report_type_data(report)

sql_query = pd.read_sql_query(report_sql, connection)
df = pd.DataFrame(sql_query)

data_file = "/tmp/{}.csv".format(Hash.hash(report['name']))
df.to_csv(data_file, index=False)

message = """
Hello there,

Please find attached {} IVR report ({}) for your reference.

Best Regards,
Academy IS Team.
"""

email = Email(
    subject="Academy IVR: {}".format(report['name']),
    body_message=message.format(report['recurrence'], report['name']),
    to_recipients=str(report['recipients_to']).split(','),
    cc_recipients=str(report['recipients_cc']).split(','),
    attachment_paths=[data_file]
)

email.send_email()
os.system("rm -rf {}".format(data_file))
exit(0)
