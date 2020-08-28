#!/usr/bin/env bash

CONFIG_FILE=./config.ini

if [ ! -f "$CONFIG_FILE" ]; then
  cp ./config.ini.test ./config.ini
fi

python bin/asterisk.py
/etc/init.d/asterisk start
asterisk -rx 'core restart now'
sleep 10
python app.py
