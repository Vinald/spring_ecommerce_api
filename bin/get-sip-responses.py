import os
import ast
import csv
from datetime import datetime
import time
from dateutil.parser import parse
import sys
sys.path.append('../')
from src.Email import Email
from src.Config import Config
from src.Logger import Logger


asterisk_log_file = "/var/log/asterisk/ivr_verbose_log"
general_sip_responses_csv = "/root/ivr/logs/sip_responses_logs/"
custom_sip_responses_csv = "/root/ivr/logs/sip_responses_logs/custom/"
output_dict = {}

working_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
logger = Logger(working_dir)
config = Config(working_dir, logger)
config.set_section('host_machine')
host_name = config.get('name')
config.set_section('daily_reports_email')


# Email information
to_recipients = list(config.get('to_recipients').split(','))

general_sip_response_subject = "Asterisk IVR SIP Responses as of {}"

general_sip_responses_body = """
Hello,

Please find attached the {} Asterisk IVR SIP Responses as of {} for your reference.

Best Regards,
Academy IS Team.
"""

custom_sip_response_subject = "Asterisk IVR SIP Responses - {} {}"

custom_sip_responses_body = """
Hello,

Please find attached the {} Asterisk IVR SIP Responses for {} taken at {} for your reference.

Best Regards,
Academy IS Team.
"""


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


def format_asterisk_log(asterisk_log_path: str):
    if not os.path.exists(asterisk_log_path):
        print("Asterisk Log File doesnt exist")
        exit(1)

    output_list = []
    file = open(asterisk_log_path, "r")
    file_content = file.readlines()

    for i in range(len(file_content)):
        if file_content[i] is not "":
            if file_content[i][0] == "{":
                box = ast.literal_eval(file_content[i])
                output_list.append(box)

    statuses = ["busy", "congested"]
    for i in range(len(output_list)):
        if "Called" in output_list[i]["logmsg"]["message"]:
            id_number = output_list[i]["identifiers"]["lwp"]
            time_stamp = output_list[i]["timestamp"]
            current_year = time.strftime('%Y')
            date = datetime.strptime(time_stamp, '%b  %d %X').strftime('%b-%d-{}'.format(current_year))
            call_time = datetime.strptime(time_stamp, '%b  %d %X').strftime('%X')
            dialed_number = output_list[i]["logmsg"]["message"].rstrip("\n").split("/+")[1]
            output_dict.update({str(id_number): '"{}","{}","{}"'.format(date, call_time, dialed_number)})

        result = [ele for ele in statuses if(ele in output_list[i]["logmsg"]["message"])]
        if bool(result) is True:
            call_status = output_list[i]["logmsg"]["message"].rstrip("\n").split("is ")[1].upper()
            sip_response = output_list[i-1]["logmsg"]["message"].split('"')[1]
            id_number = output_list[i]["identifiers"]["lwp"]
            if str(id_number) in output_dict.keys():
                new_record = output_dict[str(id_number)] + ',"{}","{}"'.format(call_status, sip_response)
                output_dict[str(id_number)] = new_record

        if "answered" in output_list[i]["logmsg"]["message"] and \
                str(output_list[i]["identifiers"]["lwp"]) in output_dict.keys():
            id_number = str(output_list[i]["identifiers"]["lwp"])
            answered_status = output_list[i]["logmsg"]["message"].rstrip("\n").split(" ")[1].upper()
            new_record = output_dict[id_number] + ',"{}"'.format(answered_status)
            output_dict[id_number] = new_record


def gen_sip_responses_csv(path_to_new_csv: str):
    if not os.path.exists(path_to_new_csv):
        print("Path provided to save sip_responses.csv doesnt exist")
    csv_headers = ["Date", "Call Initiate Time", "Dialed Number", "Call Status", "SIP Response"]
    current_date = datetime.now().strftime('%b-%d-%Y')
    file_name = "{}-SIP-Responses.{}.csv"
    path_to_new_csv = path_to_new_csv + file_name.format(host_name, current_date)
    try:
        with open(path_to_new_csv, "w") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=csv_headers)
            writer.writeheader()
            for values in output_dict.values():
                csv_file.write('{}\n'.format(values))
        email = Email(to_recipients, general_sip_response_subject.format(current_date),
                      general_sip_responses_body.format(host_name, current_date), attachment_paths=[path_to_new_csv])
        email.send_email()
    except Exception as e:
        print("Error: {}".format(e))
        logger.log_info(str(e))
    return path_to_new_csv


def gen_sip_responses_by_date(custom_path_to_new_csv: str, custom_date: str):
    if not os.path.exists(custom_path_to_new_csv):
        print("Path provided to save sip_responses.csv doesnt exist")

    csv_headers = ["Date", "Call Initiate Time", "Dialed Number", "Call State", "SIP Response"]
    file_name = "{}-SIP-Responses.{}.{}.csv"
    current_time = datetime.now().strftime('%X')
    path_to_new_csv = custom_sip_responses_csv + file_name.format(host_name, custom_date, current_time)
    try:
        with open(path_to_new_csv, "w") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=csv_headers)
            writer.writeheader()
            custom_date = '"' + custom_date + '"'
            for values in output_dict.values():
                if custom_date == values.split(",")[0]:
                    csv_file.write('{}\n'.format(values))
        email = Email(to_recipients, custom_sip_response_subject.format(custom_date, current_time),
                      custom_sip_responses_body.format(host_name, custom_date, current_time),
                      attachment_paths=[path_to_new_csv])
        email.send_email()
    except Exception as e:
        print("Error: {}".format(e))
        logger.log_info(str(e))
    return path_to_new_csv


date_now = datetime.now().strftime('%b-%d-%Y %X')
update_cron_log = "echo {}: get-sip-responses.py has ran successfully >> /root/ivr/logs/cron_jobs.log".format(date_now)

# Generate all SIP Response till current date
if len(sys.argv) - 1 == 1:
    arg1 = sys.argv[1]
    if is_date(arg1) is False:
        print("Invalid Argument!! Only takes a date argument in the format [May-22-2020]")
        exit(1)
    if check_date_format(arg1) is False:
        exit(1)
    os.system("mkdir -p {}".format(custom_sip_responses_csv))
    format_asterisk_log(asterisk_log_file)
    gen_sip_responses_by_date(custom_sip_responses_csv, arg1)
    os.system(update_cron_log)

# Generate custom SIP Response per date
elif len(sys.argv) - 1 == 0:
    format_asterisk_log(asterisk_log_file)
    os.system("mkdir -p {}".format(general_sip_responses_csv))
    gen_sip_responses_csv(general_sip_responses_csv)
    os.system(update_cron_log)

else:
    print("Invalid Syntax")
    exit(1)
