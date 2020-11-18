import argparse
import os
import pathlib
import sys
import time

start_time = time.time()

parser = argparse.ArgumentParser()

# Optional arguments
env_help = "Environment of deployment prod or dev. Default is dev"
quiet_help = "Set to true (--quiet true) if want to see script output. default is true"
deploy_help = "Set to true (--deploy true) if its the first time to deploy the application. default is false"
parser.add_argument("-e", "--env", help=env_help, type=str, default='dev')
parser.add_argument("-q", "--quiet", help=quiet_help, type=str, default='true')
parser.add_argument("-d", "--deploy", help=deploy_help, type=str, default='false')

# Parse arguments
args = parser.parse_args()

is_quiet = True if args.quiet == 'true' else False
is_dev_env = args.env == 'dev'
is_first_deployment = True if args.deploy == 'true' else False


def run_command(command, description):
	print("\n{}\n".format(description))
	if is_quiet:
		os.system("{} > /dev/null".format(command))
	else:
		os.system("{}".format(command))


if is_first_deployment:
	os.system('clear')
	# Install updates
	run_command('apt-get update', 'Installing updates')
	# Install dependencies
	run_command(
		'apt-get install asterisk asterisk-mp3 nginx apache2-utils curl docker.io python3-dev python3-pip -y',
		'Installing asterisk, asterisk-mp3, nginx, apache2-utils, curl, docker.io, python3-dev, python3-pip'
	)
	# Install docker services
	run_command('systemctl enable docker', 'Enabling docker services')
	run_command(
		'docker run -d --name redis --restart always -p 6379:6379 redis:alpine',
		'Setting up redis caching services via docker services'
	)
	run_command(
		"docker run -d --name ivr-db --restart always -p 3306:3306 -e MYSQL_ROOT_PASSWORD=root -d mysql:5.7.30",
		"Setting up MySQL services via docker"
	)


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

# Install asterisk config files.
if is_dev_env:
	os.system("cp {}/* {}".format(ASTERISK_PROJECT_DIR, ASTERISK_DIR))
else:
	os.system("cp {}/ari.conf {}/http.conf {}/cdr.conf {}/manager.conf {}".format(
		ASTERISK_PROJECT_DIR,
		ASTERISK_PROJECT_DIR,
		ASTERISK_PROJECT_DIR,
		ASTERISK_PROJECT_DIR,
		ASTERISK_DIR
	))


# Set up call queuing cron to run every after 3 minutes
call_request_queue_file = os.path.join(bin_dir, "call-request-queue.py")
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


# Install any updates available in ubuntu repositories
run_command('apt-get update', 'Installing updates')

# Install python3-dev, pip 3
run_command('apt-get install python3-dev python3-pip', 'Installing python3-dev, python3-pip')

# Install all dependencies listed in the requirements file
run_command(
	"pip3 install -r {}".format(REQUIREMENTS_FILE),
	"Installing python requirements in file: {}".format(REQUIREMENTS_FILE)
)

# Run database operations like upgrading database etc
run_command(
	"cd {} && /usr/local/bin/alembic upgrade head".format(ALEMBIC_DIR),
	"Doing database operations"
)

os.system("mkdir -p {}".format(LOG_DIR))

# Restart asterisk
run_command("asterisk -rx 'core restart now'", 'Restarting asterisk')

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
