#!/usr/bin/env bash

# Check if user is root and if not, exit script.
if [[ "$EUID" -ne 0 ]]
	then
	echo "Please run as root"
	exit
fi

cp /etc/asterisk/ari.conf /etc/asterisk/ari.conf.backup
cp /etc/asterisk/http.conf /etc/asterisk/http.conf.backup
cp /etc/asterisk/sip.conf /etc/asterisk/sip.conf.backup
cp /etc/asterisk/extensions.conf /etc/asterisk/extensions.conf.backup
cp /etc/asterisk/cdr.conf /etc/asterisk/cdr.conf.backup
cp /etc/asterisk/cdr_custom.conf /etc/asterisk/cdr_custom.conf.backup
cp /etc/asterisk/manager.conf /etc/asterisk/manager.conf.backup 


# Change working directory to asterisk
cd ./asterisk || exit

echo
echo "+------------------------------------------------------------+"
echo "|            Updating Asterisk Config Files 1/2              |"
echo "+------------------------------------------------------------+"
echo

# Copy new config file to asterisk directory
cp -r ./* /etc/asterisk
chown -R asterisk:asterisk /root


echo
echo "+------------------------------------------------------------+"
echo "|                 Restarting Asterisk  2/2                   |"
echo "+------------------------------------------------------------+"
echo

# Restart asterisk after updating config files
systemctl restart asterisk
