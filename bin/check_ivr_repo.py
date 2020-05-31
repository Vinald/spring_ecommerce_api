import os
from os import stat
from pwd import getpwuid
from prettytable import PrettyTable

working_dir = os.path.dirname(os.path.realpath(__file__))


def find_owner(filename):
    return getpwuid(stat(filename).st_uid).pw_name


def find_owner_for_multiple_files(ivr_repo: str = None):
    print("""
    ***** Checking IVR Repository file ownership *****
    --------------------------------------------------
    """)
    count = 0
    if ivr_repo is None:
        ivr_repo = '/root/ivr'
    print("Scanning your IVR Repo at path: {}\n".format(ivr_repo))
    for entry in os.scandir(r'{}'.format(ivr_repo)):
        if find_owner(entry.path) != "asterisk":
            print("{} is owned by {}".format(entry.path, find_owner(entry.path) ))
            count = count + 1
    if count > 0:
        print("\n{} files not owned by asterisk user. "
              "Run 'chown -R asterisk:asterisk {}' to resolve".format(count, ivr_repo))
        return False
    print("All files are owned by asterisk User.")
    return True


def print_header(service):
    message = """

        -----------------------------------------    
                    Checking {}
        -----------------------------------------
             """.format(service)
    print(message)


def check_if_package_installed(package: str):
    print("""    
    ****** Checking if {} is installed *****
    """.format(package))
    result = os.popen("apt -qq list {} 2>/dev/null".format(package)).read()
    if result == "" or None:
        print("Package: {} is not Installed".format(package))
        return False
    else:
        print(result)
        return True


def check_service_is_listening(service):
    print("""    
        ****** Checking if {} is listening *****
        """.format(service))
    result = os.popen("netstat -lntp | grep {}".format(service)).read()
    if result == "" or None:
        print("Package: {} is not listening. Service either not installed or started".format(service))
        return False
    else:
        print(result)
        return True


def check_service_is_running(service):
    print("""    
        ****** Checking {} status *****
        -------------------------------
        """.format(service))
    result = os.popen("service {} status".format(service)).read()
    for line in result.split('\n'):
        if "inactive (dead)" in line:
            print("The {} service is not active. Start the service".format(service))
            return False
        if "active (exited)" in line:
            print("There appears to be an issue with the {} service. Please check".format(service))
            return False
    if "could not be found" in result:
        print(result)
        return False
    else:
        print(result)
        return True


def check_services_with_listening_ports(service_to_check):
    if check_if_package_installed(service_to_check) is False:
        return None
    if check_service_is_running(service_to_check) is False:
        return None
    if check_service_is_listening(service_to_check) is False:
        return None


def check_services(service):
    if check_if_package_installed(service) is False:
        return None
    if check_service_is_running(service) is False:
        return None


def check_asterisk_sip_trunk():
    print("""
    ****** Checking SIP Trunk Status *****
    --------------------------------------
    """)
    result = os.popen('asterisk -rx "sip show registry"').read()
    print(result)
    if "Registered" not in result:
        print("Your asterisk instance may not be connected to a sip trunk")
        return False
    return True


def check_config_ini():
    print("""
    ***** Checking config.ini settings *****
    -----------------------------------------
    """)
    if os.path.exists('config.ini'):
        sample_config = """
    [motech]
host = 127.0.0.1
audio_path = /home/user/audio

[ami]
user=ivr
pass=1234
host=127.0.0.1
port=5038
trunk=staging-trunk
sip_trunk_number = 256206300462

[host_machine]
name=Conrad_IVR_Container

[email]
username=academysupport@idi.co.ug
password=1234Uganda*
port=587
host=smtp.office365.com

[daily_reports_email]
to_recipients = ekisac10@gmail.com

[app]
audio_path = /home/user/audio/
redis_host = 127.0.0.1
redis_port = 6379

[database]
port = 3306
hostname = 127.0.0.1
username = ivruser
password = ivruser
database = ivr
    """
        table = PrettyTable()
        table.field_names = ['Your Current config.ini', 'A Sample config.ini File']
        current_configs = os.popen('cat config.ini').read()
        table.add_row([current_configs, sample_config])
        print("Below is a side by side comparision of your config.ini and a sample config.ini\n")
        print(table)
        return True
    else:
        print('Your repo contains no config.ini. You must configure one. Refer to config.ini.test for a sample.')
        return False


def check_motech_running():
    print("""
    ****** Checking MOTECH status *****'
    ------------------------------------
    """)
    if check_service_is_listening('java'):
        print("""
        MOTECH appears to be running. If the landing page however is displaying errors,
        consider doing the following:
        * Check that the host machine RAM utilisation with 'htop'. If your RAM is almost maxed out,
          MOTECH may not run.
        * If the problem persists, simply restart the host machine and restart MOTECH with /opt/cfl/cfl.sh start          
        """)
        return True
    else:
        print('MOTECH isnt running, Start MOTECH with /opt/cfl/cfl.sh start')
        return False


def prerequisites():
    print("""    
    -----------------------------------------    
          Is this IVR Repo good to go?!!
    -----------------------------------------
    1. This script shall run install.sh
    2. This script shall check the following services in the order below:
            i)   Asterisk
            ii)  Redis Server
            iii) ivr-api
            iv)  MOTECH
    
    3. This script shall check that your SIP Trunk is running
    4. This script shall check that files in IVR repo are owned by asterisk user 
    5. This script shall cross check your config.ini
    -----------------------------------------
    """)


def run_checks():
    prerequisites()
    # os.system('./install.sh')
    check_services("asterisk")
    check_services_with_listening_ports("redis-server")
    check_service_is_running("ivr-api")
    check_motech_running()
    check_asterisk_sip_trunk()
    find_owner_for_multiple_files()
    check_config_ini()
    print("""
    Closing Notes:
    ----------------
    1) Remember to check you Asterisk configs
    2) Remember to check that you have run app-toke.py and have configured a token to handle calls
       on your machine.
    """)


run_checks()


