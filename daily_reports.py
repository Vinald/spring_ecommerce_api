#!/usr/bin/env python3

from datetime import date, timedelta, datetime
import pandas
from src.Email import Email
from src.Config import Config
import os
from textwrap import dedent
from src.Logger import Logger
import schedule
import time

reports_path = "/root/ivr/reports"
file_path = "/var/log/asterisk/cdr-custom/ivr_reports.csv"
call_cost_per_second = 3
working_dir = os.path.dirname(os.path.realpath(__file__))
logger = Logger(working_dir)
config = Config(working_dir, logger)
config.set_section('host_machine')
host_name = config.get('name')
config.set_section('daily_reports_email')

headers = ["Date", "App Name", "SIP Trunk Channel", "SIP Trunk Number", "Call Initiate Time", "Call Answer Time",
           "Call Ended", "Total Call Duration (s)", "Call Duration when Answered (s)", "Call State", "Dialed Number",
           "Call_ID", "Call_Direction"]

date_today = date.today()
date_yesterday = date_today + timedelta(days=-1)
date_today = date.today().strftime("%b-%d-%Y")
date_yesterday = date_yesterday.strftime("%b-%d-%Y")

to_recipients = config.get('to_recipients')
email_subject = '{}_IVR Call Detail Reports as of {}'.format(host_name, date_yesterday)
email_body = dedent("""\
Hello,

Please find attached the Call Detail Records for {} as of {} for your reference.

Best Regards,
Academy IS Team.
""").format(host_name, date_yesterday)


def create_reports_dir():
    os.system("cd {}".format(working_dir))
    os.system("mkdir -p reports")


def send_email_at(attachment: list):
    email = Email(to_recipients, email_subject, email_body, attachment_paths=[attachment])
    email.send_email()


def generate_csv(file: str, header_names: list, call_cost: int, report_path: str):
    csv_file = pandas.read_csv(file, names=header_names)
    csv_file["Call Initiate Time"] = csv_file["Call Initiate Time"].str.split(r" ").str.get(1)
    csv_file["Call Answer Time"] = csv_file["Call Answer Time"].str.split(r" ").str.get(1)
    csv_file["Call Ended"] = csv_file["Call Ended"].str.split(r" ").str.get(1)
    csv_file["Total Charge (UGX)"] = csv_file["Call Duration when Answered (s)"] * call_cost
    report_name = "{}_IVR_Report.{}.csv"
    dates_column = csv_file["Date"].to_dict()
    latest_date_key = max(dates_column.keys())
    latest_date_value = dates_column[latest_date_key]

    if report_path[-1] != "/":
        report_path = str(report_path + "/")
    new_formatted_csv = report_path + report_name.format(host_name, latest_date_value)
    csv_file.to_csv(new_formatted_csv, index=False)

    if latest_date_value != date_today:
        csv_file.to_csv(new_formatted_csv, index=False)
        email = Email(to_recipients, email_subject, email_body, attachment_paths=[new_formatted_csv])
        email.send_email()


create_reports_dir()
generate_csv(file_path, headers, call_cost_per_second, reports_path)





