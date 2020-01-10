#!/usr/bin/env bash

# Check if user is root and if not, exit script.
if [[ "$EUID" -ne 0 ]]
	then
	echo "Please run as root"
	exit
fi

# Define apache root directory
apache_web_root_dir='/var/www/html'

# Define path to the audio file
audio_zipped_file='./audio.zip'

# Check if the audio.zip file before continuing. If file does not exist, script will exit immediately
if [[ ! -f ${audio_zipped_file} ]]
	then
	echo "Please copy the audio.zip file to the current folder: $(pwd)"
	exit
fi

echo
echo "+-----------------------------------------------------------------+"
echo "|                   Processing. Please wait 1/2                   |"
echo "+-----------------------------------------------------------------+"
echo

# First update ubuntu repositories
apt-get update > /dev/null

# Install zip and apache2 software to help in streaming audio files
apt-get install zip apache2 -y > /dev/null

# Remove root directory
rm -rf ${apache_web_root_dir}

# Recreate root directory
mkdir -p ${apache_web_root_dir}

# Unzip the audio file to the linux temporary directory
unzip ${audio_zipped_file} -d '/tmp' > /dev/null

# Move audio files to the apache root directory
mv '/tmp/audio/*' ${apache_web_root_dir}

# Clean the tmp directory
rm -rf '/tmp/audio'

# Allow apache to listen to port 8001
echo 'Listen 8000' > /etc/apache2/ports.conf

# Edit apache2 default virtual host to listen to port 8001
sed -i 's/80/8000/g' '/etc/apache2/sites-available/000-default.conf'

# Confirm ownership of default apache2 directory to www-data (This is the default apache user)
chown -R www-data:www-data ${apache_web_root_dir}


echo
echo "+-----------------------------------------------------------------+"
echo "|                      Restarting Apache  2/2                     |"
echo "+-----------------------------------------------------------------+"
echo

# Restart asterisk after updating config files
systemctl restart apache2
