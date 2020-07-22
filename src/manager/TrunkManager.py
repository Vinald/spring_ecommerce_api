import subprocess


class TrunkManager:
    def __init__(self, trunks: str = None):
        self.__trunks = trunks

    def get_available_peer(self):
        trunk_list = self.__trunks.split(',')
        for trunk in trunk_list:
            trunk_details = trunk.split(':')
            peer = trunk_details[0]
            host = trunk_details[1]
            if self.__sip_trunk_is_online(host):
                return peer

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
