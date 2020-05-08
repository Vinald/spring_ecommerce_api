#!/usr/bin/env bash

export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games:/usr/local/games:/snap/bin

# Check if user is root and if not, exit script.
if [[ "$EUID" -ne 0 ]]
	then
	echo "Please run as root"
	exit
fi

# Install any updates available in ubuntu repositories
apt-get update > /dev/null

# Install python 3 and pip 3
apt-get install python3 python3-pip -y > /dev/null

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
