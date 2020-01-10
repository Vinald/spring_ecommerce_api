#!/usr/bin/env bash

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
