import subprocess


class TrunkManager:
    def __init__(self, trunks: list = None, routed_numbers: list = None):
        self.__trunks = trunks
        self.__routed_numbers = routed_numbers

    def get_available_peer(self):
        for trunk in self.__trunks:
            peer = trunk['peer']
            host = trunk['host']
            if self.__sip_trunk_is_online(host):
                return peer

    def routed_number(self, phone: str):
        if self.__routed_numbers is None or len(self.__routed_numbers) <= 0:
            return False
        for route in self.__routed_numbers:
            peer = route['peer']
            number_format = route['format']
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
