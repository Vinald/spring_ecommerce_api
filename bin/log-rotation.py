import datetime
import os

project_dir = os.path.dirname(os.path.realpath(__file__))
current_date = datetime.datetime.now()

date_string = current_date.strftime("%Y-%m-%d")

logs_dir = os.path.join(project_dir, 'logs')
log_file = os.path.join(logs_dir, 'app.log')

os.system("mkdir -p {}".format(logs_dir))

if os.path.exists(log_file):
    log_backup_file = "{}.{}".format(log_file, date_string)
    os.system("cp {} {}".format(log_file, log_backup_file))
    os.system("echo > {}".format(log_file))
    os.system("chown -R asterisk {}".format(logs_dir))
    os.system("chmod -R 775 {}".format(logs_dir))

    # Update cron log file that the job ran
    update_cron_log = "echo {}: log-rotation.py has ran successfully >> {}"
    os.system(update_cron_log.format(current_date.strftime('%b-%d-%Y %X'), os.path.join(logs_dir, 'cron_jobs.log')))
