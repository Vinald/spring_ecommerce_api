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

# Define the log-rotation.sh cron file path
log_rotation_cron_file="/etc/cron.d/ivr-log-rotation"
log_rotate_job="echo \$(date '+%F %T'): log-rotation.sh cron job has ran successfully >> /root/ivr/logs/cron_jobs.log"

# Install cron-tab for log rotation to run every night at 23:59
echo "59 23 * * * root cd /root/ivr && ./log-rotation.sh && ${log_rotate_job}" > $log_rotation_cron_file
chown root:root $log_rotation_cron_file
chmod 600 $log_rotation_cron_file

# Define the daily_reports.py cron file path
daily_reports_cron_file="/etc/cron.d/ivr-daily-reports"
reports_job="echo \$(date '+%F %T'): daily_reports.py cron job has ran successfully >> /root/ivr/logs/cron_jobs.log"

# Install cron-tab for daily_reports to run every night at 00:00
echo "0 0 * * * root python3 /root/ivr/daily_reports.py && ${reports_job}" > $daily_reports_cron_file
chown root:root $daily_reports_cron_file
chmod 600 $daily_reports_cron_file

# Define the get-sip-responses cron file path
get_sip_responses_cron_file="/etc/cron.d/get-sip-responses"
get_sip_responses_job="echo \$(date '+%F %T'): get_sip_responses.py cron job has ran successfully >> /root/ivr/logs/cron_jobs.log"

# Install cron-tab for get-sip-responses to run every night at 23:59
echo "59 23 * * * root python3 /root/ivr/bin/get-sip-responses.py && ${get_sip_responses_job}" > $get_sip_responses_cron_file
chown root:root $get_sip_responses_cron_file
chmod 600 $get_sip_responses_cron_file

# Setup asterisk logging
cp asterisk/logger.conf /etc/asterisk/logger.conf
asterisk -rx "core set verbose 3"
asterisk -rx "logger reload"

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
