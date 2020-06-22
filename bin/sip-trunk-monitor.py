#!/usr/bin/env python3

import datetime
import math
import os
import pathlib
import subprocess
import sys

sys.path.append('..')
from core import config, logger, database
from src.Email import Email

base_dir = pathlib.Path(os.path.dirname(os.path.realpath(__file__))).parent
logs_dir = os.path.join(base_dir, 'logs')

if not os.path.exists(logs_dir):
    os.makedirs(logs_dir)

connection = database.get_conn()
cursor = database.get_cursor()

host = 'sip.simbanet.co.ug'
table_name = 'sip_trunk_monitor_records'

create_table = """CREATE TABLE IF NOT EXISTS `{}` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `date_created` datetime NOT NULL,
  `status` varchar(100) NOT NULL,
  `host` varchar(255) NOT NULL,
  `downtime` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1""".format(table_name)

cursor.execute(create_table)
connection.commit()

# Query used to select the last trunk status entry from the database
sql = "SELECT * FROM `{}` ORDER BY `id` DESC LIMIT 1".format(table_name)
cursor.execute(sql)
result = cursor.fetchone()


def sip_trunk_is_online():
    cmd = "sudo asterisk -rx 'sip show registry'"
    process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    output = process.stdout
    for line in output:
        string = line.decode('utf8')
        if "Registered" in string:
            return True
    return False


def send_mail(msg, subject):
    config.set_section('daily_reports_email')
    try:
        mail_send_to = config.get('to_recipients').split(',')
    except Exception as e:
        mail_send_to = None
        logger.log_error("SIP Trunk monitor email To: {}".format(str(e)))

    try:
        mail_send_cc = config.get('cc_recipients').split(',')
    except Exception as e:
        mail_send_cc = None
        logger.log_error("SIP Trunk monitor email Cc: {}".format(str(e)))

    email = Email(mail_send_to, subject, msg, mail_send_cc)
    email.send_email()


def log_server_online(downtime):
    try:
        date = datetime.datetime.now()
        data = {'date_created': date, 'status': 'online', 'host': host, 'downtime': downtime}
        database.insert(data, table_name)
    except Exception as e:
        logger.log_error("SIP Trunk Monitor: {}".format(str(e)))


def log_server_offline():
    try:
        date = datetime.datetime.now()
        data = {'date_created': date, 'status': 'offline', 'host': host}
        database.insert(data, table_name)
    except Exception as e:
        print(str(e))
        logger.log_error("SIP Trunk Monitor: {}".format(str(e)))


def send_alert_server_online_email(downtime):
    if downtime <= 60:
        formatted_downtime = "{} minute(s).".format(math.ceil(downtime))
    else:
        hours = int(downtime / 60)
        minutes = downtime % 60
        formatted_downtime = "{} hour(s) and {} minute(s).".format(hours, math.ceil(minutes))

    msg = """Hello,

SIP Trunk ({}) is back online. There was a downtime of {}.

Regards,
Academy IS Team
"""
    return send_mail(msg.format(host, formatted_downtime), 'SIP Trunk Status')


def send_alert_server_offline_email():
    msg = """Hello,

SIP Trunk ({}) has gone offline. Please check SIP registration.

Regards,
Academy IS Team
"""
    return send_mail(msg.format(host), 'Critical SIP Trunk Status')


if result is None:
    if sip_trunk_is_online():
        log_server_online(0)
    else:
        log_server_offline()

    cursor.execute(sql)
    new_results = cursor.fetchone()
    record_id = new_results['id']
    last_date = new_results['date_created']
    last_status = new_results['status']
else:
    record_id = result['id']
    last_date = result['date_created']
    last_status = result['status']


time_gap = (datetime.datetime.now() - last_date).total_seconds() / 60


if sip_trunk_is_online():
    if last_status == 'offline' and time_gap >= 5:
        log_server_online(time_gap)
        send_alert_server_online_email(time_gap)
else:
    if last_status == 'online' and time_gap >= 5:
        log_server_offline()
        send_alert_server_offline_email()

date_now = datetime.datetime.now().strftime('%b-%d-%Y %X')
update_cron_log = "echo {}: sip-trunk-monitor.py has ran successfully >> {}"
os.system(update_cron_log.format(date_now, os.path.join(logs_dir, 'cron_jobs.log')))

connection.close()
exit(0)
