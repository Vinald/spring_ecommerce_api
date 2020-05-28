import os


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




def prerequisites():
    print("""    
    -----------------------------------------    
          Is this IVR Repo good to go?!!
    -----------------------------------------
    This script shall check the following services in the order below:
            1. Asterisk
            2. Redis Server
            3. ivr-api
            4. MOTECH
    -----------------------------------------
    """)


prerequisites()
check_services("asterisk")
check_services_with_listening_ports("redis-server")
check_service_is_running("ivr-api")

