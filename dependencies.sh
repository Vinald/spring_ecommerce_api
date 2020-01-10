#!/usr/bin/env bash

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
