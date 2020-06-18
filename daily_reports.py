#!/usr/bin/env python3

from datetime import date, timedelta, datetime
import pandas
from src.Email import Email
from src.Config import Config
import os
from textwrap import dedent
from src.Logger import Logger
import sys
from dateutil.parser import parse


reports_path = "/root/ivr/reports/CDRs/"
custom_reports_path = "/root/ivr/reports/CDRs/custom"
file_path = "/var/log/asterisk/cdr-custom/ivr_report.csv"
call_cost_per_second = 3

working_dir = os.path.dirname(os.path.realpath(__file__))
logger = Logger(working_dir)
config = Config(working_dir, logger)

config.set_section('host_machine')
host_name = config.get('name')
config.set_section('daily_reports_email')

headers = ["Date", "App Name", "SIP Trunk Channel", "SIP Trunk Number", "Call Initiate Time", "Call Answer Time",
           "Call Ended", "Total Call Duration (s)", "Call Duration when Answered (s)", "Call State", "Dialed Number",
           "Call_ID", "Call_Direction", "Token", "Application Name"]

date_today = date.today().strftime("%b-%d-%Y")
to_recipients = list(config.get('to_recipients').split(','))


def create_reports_dir():
    os.system("cd {}".format(working_dir))
    os.system("mkdir -p reports")


def create_custom_reports_dir():
    os.system("cd {}".format(working_dir))
    os.system("mkdir -p reports/custom")


def is_date(string, fuzzy=False):
    try:
        parse(string, fuzzy=fuzzy)
        return True
    except ValueError:
        return False


def check_date_format(date_to_check: str):
    try:
        datetime.strptime(date_to_check, '%b-%d-%Y')
        return True
    except ValueError:
        print("Incorrect data format, should be MMM-DD-YYYY")
        return False


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
    csv_file = csv_file[csv_file["SIP Trunk Channel"].notnull()]

    email_subject = '{}_IVR Call Detail Reports as of {}'.format(host_name, latest_date_value)
    email_body = dedent("""\
    Hello,

    Please find attached the Call Detail Records for {} as of {} for your reference.

    Best Regards,
    Academy IS Team.
    """).format(host_name, latest_date_value)

    if report_path[-1] != "/":
        report_path = str(report_path + "/")
    new_formatted_csv = report_path + report_name.format(host_name, latest_date_value)
    csv_file.to_csv(new_formatted_csv, index=False)
    os.system("")
    email = Email(to_recipients, email_subject, email_body, attachment_paths=[new_formatted_csv])
    email.send_email()


def generate_csv_for_particular_day(file: str, report_date: str, header_names: list, call_cost: int,
                                    custom_report_path: str):

    csv_file = pandas.read_csv(file, names=header_names)
    csv_file["Call Initiate Time"] = csv_file["Call Initiate Time"].str.split(r" ").str.get(1)
    csv_file["Call Answer Time"] = csv_file["Call Answer Time"].str.split(r" ").str.get(1)
    csv_file["Call Ended"] = csv_file["Call Ended"].str.split(r" ").str.get(1)
    csv_file["Total Charge (UGX)"] = csv_file["Call Duration when Answered (s)"] * call_cost
    current_time = datetime.now().strftime('%X')
    report_name = "{}_Daily_IVR_Report.{}.{}.csv"
    csv_file = csv_file.loc[csv_file["Date"] == report_date]

    email_subject = '{} Call Detail Reports for {} at {}'.format(host_name, report_date, current_time)
    email_body = dedent("""\
    Hello,

    Please find attached the {} Call Detail Records for {} taken at for your reference.

    Best Regards,
    Academy IS Team.
    """).format(host_name, report_date, current_time)

    if custom_report_path[-1] != "/":
        custom_report_path = str(custom_report_path + "/")
    new_formatted_csv = custom_report_path + report_name.format(host_name, report_date, current_time)
    csv_file.to_csv(new_formatted_csv, index=False)
    email = Email(to_recipients, email_subject, email_body, attachment_paths=[new_formatted_csv])
    email.send_email()


date_now = datetime.now().strftime('%b-%d-%Y %X')
update_cron_log = "echo {}: daily_reports.py has ran successfully >> /root/ivr/logs/cron_jobs.log".format(date_now)

if len(sys.argv) - 1 == 1:
    arg1 = sys.argv[1]
    if is_date(arg1) is False:
        print("Invalid Argument!! Only takes a date argument in the format [May-22-2020]")
        exit(1)
    if check_date_format(arg1) is False:
        exit(1)
    create_custom_reports_dir()
    generate_csv_for_particular_day(file_path, arg1, headers, call_cost_per_second, custom_reports_path)
    os.system(update_cron_log)

elif len(sys.argv) - 1 == 0:
    create_reports_dir()
    generate_csv(file_path, headers, call_cost_per_second, reports_path)
    os.system(update_cron_log)

else:
    print("Invalid Syntax")
    exit(1)
