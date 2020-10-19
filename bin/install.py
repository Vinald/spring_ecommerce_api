import os
import pathlib
import sys
import time

start_time = time.time()

# Main directory vars
project_dir = pathlib.Path(os.path.dirname(os.path.realpath(__file__))).parent
bin_dir = os.path.join(project_dir, "bin")

# Cron vars
CRON_DIR = "/etc/cron.d"

# Asterisk vars
ASTERISK_DIR = "/etc/asterisk"
SYSTEM_D_DIR = "/etc/systemd/system"
ASTERISK_PROJECT_DIR = os.path.join(project_dir, 'asterisk')

# Requirements vars
REQUIREMENTS_FILE = os.path.join(project_dir, "requirements.txt")

# Logs vars
LOG_DIR = os.path.join(project_dir, "logs")

# IVR service vars
OLD_IVR_SERVICE = os.path.join(SYSTEM_D_DIR, "ivr-api.service")
NEW_IVR_SERVICE = os.path.join(project_dir, 'bin', "ivr-api.service")

OLD_LISTENER_SERVICE = os.path.join(SYSTEM_D_DIR, "asterisk-events-listener.service")
NEW_LISTENER_SERVICE = os.path.join(project_dir, 'bin', "asterisk-events-listener.service")

ALEMBIC_DIR = os.path.join(project_dir, 'alembic')

os.system("clear")

if os.geteuid() != 0:
	print("\nPlease run as root\n")
	sys.exit(1)

# Set timezone
os.system("timedatectl set-timezone Africa/Kampala")

# Install vital asterisk config files.
os.system("cp {}/ari.conf {}/http.conf {}/logger.conf {}/cdr_custom.conf {}".format(
	ASTERISK_PROJECT_DIR,
	ASTERISK_PROJECT_DIR,
	ASTERISK_PROJECT_DIR,
	ASTERISK_PROJECT_DIR,
	ASTERISK_DIR
))


# Set up call queuing cron to run every after 3 minutes
call_request_queue_file = os.path.join(project_dir, "call-request-queue.py")
call_request_queue_cron_file = os.path.join(CRON_DIR, "call-request-queue")
os.system("chmod +x {}".format(call_request_queue_file))
os.system('echo "*/3 * * * * root cd {} && python3 call-request-queue.py" > {}'.format(
	bin_dir,
	call_request_queue_cron_file
))
os.system("chown root:root {}".format(call_request_queue_cron_file))
os.system("chmod 600 {}".format(call_request_queue_cron_file))


# Set up log sip peer monitoring cron-tab to run every 30 minutes
sip_monitor_cron_file = os.path.join(CRON_DIR, "sip-peer-monitor")
os.system('echo "*/30 * * * * root cd {} && python3 sip-peer-monitor.py" > {}'.format(bin_dir, sip_monitor_cron_file))
os.system("chown root:root {}".format(sip_monitor_cron_file))
os.system("chmod 600 {}".format(sip_monitor_cron_file))


# Set up log rotation cron-tab to run every night at 23:59
log_rotation_cron_file = os.path.join(CRON_DIR, "ivr-log-rotation")
os.system('echo "59 23 * * * root cd {} && python3 log-rotation.py" > {}'.format(bin_dir, log_rotation_cron_file))
os.system("chown root:root {}".format(log_rotation_cron_file))
os.system("chmod 600 {}".format(log_rotation_cron_file))


# Install cron-tab for daily_reports to run every day at mid-night (00:00) hrs
daily_reports_cron_file = os.path.join(CRON_DIR, "ivr-daily-reports")
os.system('echo "0 0 * * * root cd {} && python3 daily-reports.py" > {}'.format(bin_dir, daily_reports_cron_file))
os.system("chown root:root {}".format(daily_reports_cron_file))
os.system("chmod 600 {}".format(daily_reports_cron_file))


# Setup asterisk logging
os.system('asterisk -rx "core set verbose 3"')
os.system('asterisk -rx "logger reload"')


# Install any updates available in ubuntu repositories
print("\nInstalling updates\n")
os.system("apt-get update > /dev/null")


# Install python3-dev, pip 3
print("\nInstalling python3-dev, python3-pip\n")
os.system("apt-get install python3-dev python3-pip -y > /dev/null")


# Install all dependencies listed in the requirements file
print("\nInstalling python requirements in file: {}\n".format(REQUIREMENTS_FILE))
os.system("pip3 install -r {}".format(REQUIREMENTS_FILE))

os.system("cd {} && /usr/local/bin/alembic upgrade head".format(ALEMBIC_DIR))

os.system("mkdir -p {}".format(LOG_DIR))

# Restart asterisk
print("\nRestarting asterisk\n")
os.system("asterisk -rx 'core restart now'")


print("\nUpdating IVR Service\n")

if os.path.exists(OLD_IVR_SERVICE):
	os.system("systemctl stop ivr-api.service")

os.system("cp {} {}".format(NEW_IVR_SERVICE, OLD_IVR_SERVICE))

os.system("systemctl daemon-reload")
os.system("systemctl enable ivr-api.service")
os.system("systemctl start ivr-api.service")


print("\nUpdating IVR Listener Service\n")
if os.path.exists(OLD_LISTENER_SERVICE):
	os.system("systemctl stop asterisk-events-listener.service")

os.system("cp {} {}".format(NEW_LISTENER_SERVICE, OLD_LISTENER_SERVICE))

os.system("systemctl daemon-reload")
os.system("systemctl enable asterisk-events-listener.service")
os.system("systemctl start asterisk-events-listener.service")

print("\nInstallation done in: {} seconds\n".format((time.time() - start_time)))

sys.exit(0)
