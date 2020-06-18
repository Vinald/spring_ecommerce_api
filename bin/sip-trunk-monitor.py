#!/usr/bin/env python3

import datetime
import math
import smtplib
import subprocess
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import sys
sys.path.append('..')
from core import config, logger, database

connection = database.get_conn()
cursor = database.get_cursor()

host = 'sip.simbanet.co.ug'
table_name = 'sip_trunk_monitor_records'

# Query used to select the last trunk status entry from the database
sql = "SELECT * FROM `{}` ORDER BY `id` DESC LIMIT 1".format(table_name)
cursor.execute(sql)
result = cursor.fetchone()


def sip_trunk_is_online():
    cmd = "asterisk -rx 'sip show registry'"
    process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    output = process.stdout
    for line in output:
        string = line.decode('utf8')
        if "Registered" in string:
            return True
    return False


def send_mail(msg, subject):
    config.set_section('email')
    mail_port = config.get('port')
    mail_host = config.get('host')
    mail_user = config.get('username')
    mail_pass = config.get('password')

    config.set_section('daily_reports_email')
    mail_send_to = config.get('to_recipients').split(',')
    mail_send_cc = config.get('cc_recipients').split(',')
    recipients = mail_send_to + mail_send_cc

    message = MIMEMultipart("alternative")
    message["Cc"] = ','.join(mail_send_cc)
    message["To"] = ','.join(mail_send_to)
    message["From"] = mail_user
    message["Subject"] = subject

    body = MIMEText(msg, "plain")
    server = smtplib.SMTP(mail_host, mail_port)
    message.attach(body)
    mail_sent = 0

    try:
        server.ehlo()
        server.starttls()
        server.login(mail_user, mail_pass)
        server.sendmail(mail_user, recipients, message.as_string())
        mail_sent = 1
    except Exception as e:
        logger.log_error("SIP Trunk Monitor: {}".format(str(e)))
        mail_sent = 0
    finally:
        server.quit()
        return mail_sent


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

    msg = "{} is back online. There was a downtime of {}"
    return send_mail(msg.format(host, formatted_downtime), 'SIP Trunk Status')


def send_alert_server_offline_email():
    msg = "{} has gone offline. Please check SIP registration."
    return send_mail(msg.format(host), 'Critical SIP Trunk Status')


if result is None:
    if sip_trunk_is_online():
        log_server_online()
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

exit(0)
