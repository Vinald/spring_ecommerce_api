#!/usr/bin/env bash

# Check if user is root and if not, exit script.
if [[ "$EUID" -ne 0 ]]
	then
	echo "Please run as root"
	exit
fi

# Change working directory to asterisk
cd ./asterisk

echo
echo "+------------------------------------------------------------+"
echo "|            Updating Asterisk Config Files 1/2              |"
echo "+------------------------------------------------------------+"
echo

# Copy new config file to asterisk directory
cp -r * /etc/asterisk


echo
echo "+------------------------------------------------------------+"
echo "|                 Restarting Asterisk  2/2                   |"
echo "+------------------------------------------------------------+"
echo

# Restart asterisk after updating config files
systemctl restart asterisk
