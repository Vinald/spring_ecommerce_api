#!/usr/bin/env bash

export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games:/usr/local/games:/snap/bin

# Check if user is root and if not, exit script.
if [[ "$EUID" -ne 0 ]]
	then
	echo "Please run as root"
	exit
fi

# Set timezone
timedatectl set-timezone Africa/Kampala

# Add execution permission for log rotation script
chmod +x "/root/ivr/log-rotation.sh"

# Define the cron file path
cron_file="/etc/cron.d/ivr-log-rotation.cron"

# Install cron-tab for log rotation to run every night at 23:59
echo "59 23 * * * root /root/ivr/log-rotation.sh" > $cron_file
chown root:root $cron_file
chmod 600 $cron_file

reports_cron_file="/etc/cron.d/ivr-daily-reports.cron"
# Install cron-tab for daily_reports to run every night at 00:00
echo "0 0 * * * root /root/ivr/daily_reports.py" > $reports_cron_file
chown root:root $reports_cron_file
chmod 600 $reports_cron_file

# Install any updates available in ubuntu repositories
apt-get update > /dev/null

# Install python 3, pip 3, and redis server for in-memory (RAM) caching
apt-get install python3 python3-pip redis-server -y > /dev/null

# Install all dependencies listed in the requirements file
pip3 install -r requirements.txt

systemctl stop ivr-api.service

old_service='/etc/systemd/system/ivr-api.service'
new_service='./ivr-api.service'

cp ${new_service} ${old_service}

systemctl daemon-reload
systemctl enable ivr-api.service
sleep 5
systemctl start ivr-api.service
