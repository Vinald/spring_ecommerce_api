#!/bin/bash

if [[ "$EUID" -ne 0 ]]; then
  echo "Please run as root"
  exit
fi

# Get the current date
date=$(date '+%F')

# Define base directory to be the current working directory with pwd command
base_dir=$(pwd)

# Define a directory where to keep the logs
log_files_dir=$base_dir/logs

# Make log files directory if does not exist
mkdir -p "$log_files_dir"

# Check if log file exists
if [ -f "$base_dir/app.log" ]; then
  # Backup the log file to the log files directory and append a date to it.
  cp "$base_dir/app.log" "$log_files_dir/app.log.$date"
  # Empty the current log file for a new day
  echo > "$base_dir/app.log"
  chown -R asterisk "$log_files_dir"
  chmod -R 664 "$log_files_dir"
fi
