import subprocess


class TrunkManager:
    def __init__(self, trunks: str = None, routed_numbers: str = None):
        self.__trunks = trunks
        self.__routed_numbers = routed_numbers

    def get_available_peer(self):
        trunk_list = self.__trunks.split(',')
        for trunk in trunk_list:
            trunk_details = trunk.split(':')
            peer = trunk_details[0]
            host = trunk_details[1]
            if self.__sip_trunk_is_online(host):
                return peer

    def routed_number(self, phone: str):
        if self.__routed_numbers is None or len(self.__routed_numbers) <= 0:
            return False
        route_list = self.__routed_numbers.split(',')
        for route in route_list:
            route_details = route.split(':')
            peer = route_details[1]
            number_format = route_details[0]
            if phone.startswith(number_format):
                return peer
        return False

    @staticmethod
    def __sip_trunk_is_online(trunk: str):
        cmd = "sudo asterisk -rx 'sip show registry'"
        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
        output = process.stdout
        for line in output:
            string = line.decode('utf8')
            if trunk in string and "Registered" in string:
                return True
        return False
