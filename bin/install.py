import argparse
import os
import pathlib
import sys
import time

if os.geteuid() != 0:
	print("\nPlease run as root\n")
	sys.exit(1)

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
is_dev_env = True if args.env == 'dev' else False
is_first_deployment = True if args.deploy == 'true' else False


def run_command(command, description):
	print("\n{}\n".format(description))
	if is_quiet:
		os.system("{} > /dev/null".format(command))
	else:
		os.system("{}".format(command))


os.system('clear')
run_command('apt-get update', 'Installing updates')


def deploy_on_production():
	run_command(
		'apt-get install asterisk asterisk-mp3 nginx apache2-utils curl python3-dev python3-pip redis-server -y',
		'Installing asterisk, asterisk-mp3, redis, nginx, apache2-utils, curl, python3-dev, python3-pip'
	)
	config = """server {{
	listen 80;

	server_name _;

	location / {{
			proxy_set_header Host $host;
			proxy_set_header X-Real-IP $remote_addr;
			proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
			proxy_set_header X-Forwarded-Proto $scheme;
			proxy_pass http://127.0.0.1:5000;
			proxy_read_timeout 90;
			proxy_http_version 1.1;
			proxy_request_buffering off;
	}}
}}
"""
	file = open('/etc/nginx/sites-available/default', 'w')
	file.write(config)
	file.close()
	os.system("nginx -t")
	os.system("systemctl reload nginx")
	os.system('sed -i "s/^bind.*/bind 0.0.0.0/g" /etc/redis/redis.conf')
	os.system('sed -i "s/^supervised.*/supervised systemd/g" /etc/redis/redis.conf')
	os.system('systemctl restart redis.service')
	os.system("cp {}/* {}".format(ASTERISK_PROJECT_DIR, ASTERISK_DIR))


def deploy_on_dev():
	run_command(
		'apt-get install asterisk asterisk-mp3 docker.io python3-dev python3-pip -y',
		'Installing asterisk, asterisk-mp3, docker.io, python3-dev, python3-pip'
	)
	run_command('systemctl enable docker', 'Enabling docker services')
	run_command(
		'docker run -d --name redis --restart always -p 6379:6379 redis:alpine',
		'Setting up redis caching services via docker services'
	)
	run_command(
		"docker run -d --name ivr-db --restart always -p 3306:3306 -e MYSQL_ROOT_PASSWORD=root -d mysql:5.7.30",
		"Setting up MySQL services via docker"
	)


def setup_cron_tabs():
	ivr_system_cron = os.path.join(CRON_DIR, "ivr-system-cron")
	os.system("rm -rf {}".format(ivr_system_cron))
	os.system("touch {}".format(ivr_system_cron))
	os.system("chown root:root {}".format(ivr_system_cron))
	os.system("chmod 600 {}".format(ivr_system_cron))

	# Set up call queuing cron to run every after 3 minutes
	os.system('echo "*/3 * * * * root cd {} && python3 call-request-queue.py" > {}'.format(bin_dir, ivr_system_cron))
	# Set up log sip peer monitoring cron-tab to run every 30 minutes
	os.system('echo "*/50 * * * * root cd {} && python3 sip-peer-monitor.py" >> {}'.format(bin_dir, ivr_system_cron))
	# Set up log rotation cron-tab to run every night at 23:59
	os.system('echo "59 23 * * * root cd {} && python3 log-rotation.py" >> {}'.format(bin_dir, ivr_system_cron))


def update_and_restart_services():
	print("\nUpdating IVR API Service\n")

	if os.path.exists(OLD_IVR_SERVICE):
		os.system("systemctl stop ivr-api.service")

	os.system("cp {} {}".format(NEW_IVR_SERVICE, OLD_IVR_SERVICE))

	os.system("systemctl daemon-reload")
	os.system("systemctl enable ivr-api.service")
	os.system("systemctl start ivr-api.service")

	print("\nUpdating IVR Asterisk Events Listener Service\n")
	if os.path.exists(OLD_LISTENER_SERVICE):
		os.system("systemctl stop asterisk-events-listener.service")

	os.system("cp {} {}".format(NEW_LISTENER_SERVICE, OLD_LISTENER_SERVICE))

	os.system("systemctl daemon-reload")
	os.system("systemctl enable asterisk-events-listener.service")
	os.system("systemctl start asterisk-events-listener.service")


if is_first_deployment and is_dev_env:
	deploy_on_dev()

if is_first_deployment and not is_dev_env:
	deploy_on_production()


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

if not is_dev_env:
	setup_cron_tabs()
	update_and_restart_services()

print("\nInstallation done in: {} seconds\n".format((time.time() - start_time)))

sys.exit(0)
