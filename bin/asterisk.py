import os
import pathlib

if os.geteuid() != 0:
    exit("You need to have root privileges to run this script.\nPlease try again, this time using 'sudo'. Exiting...")

project_dir = pathlib.Path(os.path.dirname(os.path.realpath(__file__))).parent
asterisk_configs_dir = os.path.join(project_dir, 'asterisk')

os.system("cp /etc/asterisk/ari.conf /etc/asterisk/ari.conf.backup")
os.system("cp /etc/asterisk/http.conf /etc/asterisk/http.conf.backup")
os.system("cp /etc/asterisk/sip.conf /etc/asterisk/sip.conf.backup")
os.system("cp /etc/asterisk/extensions.conf /etc/asterisk/extensions.conf.backup")
os.system("cp /etc/asterisk/cdr.conf /etc/asterisk/cdr.conf.backup")
os.system("cp /etc/asterisk/cdr_custom.conf /etc/asterisk/cdr_custom.conf.backup")
os.system("cp /etc/asterisk/manager.conf /etc/asterisk/manager.conf.backup")
os.system("cp /etc/asterisk/logger.conf /etc/asterisk/logger.conf.backup")

print("\n\nCopying asterisk configs\n\n")
os.system("cp -r {}/* /etc/asterisk".format(asterisk_configs_dir))

print("\n\nFixing permissions\n\n")
os.system("chown -R asterisk:asterisk /root")

print("\n\nRestarting asterisk\n\n")
os.system("asterisk -rx 'core restart now'")

print("\n\nDone. Thanks.\n\n")
