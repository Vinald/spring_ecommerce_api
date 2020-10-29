from app.asterisk.AsteriskARI import AsteriskARI
from app.manager.CacheManager import CacheManager


class TrunkManager:
    __FAIL_TRUNK_CACHE = 'failing-trunk'

    def __init__(
        self,
        ari: AsteriskARI,
        cache: CacheManager,
        trunks: list = None,
        routed_numbers: list = None
    ):
        self.__ari = ari
        self.__cache = cache
        self.__peers = trunks
        self.__routed_numbers = routed_numbers

    def get_all_peers(self):
        peers = []
        for peer in self.__peers:
            peer_name = peer['peer']
            if self.__ari.peer_is_online(peer_name):
                peer['status'] = 'online'
            else:
                peer['status'] = 'offline'
            peers.append(peer)
        return peers

    def construct_channel_and_caller_id(self, phone, caller_id):
        peer = self.get_available_peer()

        if self.routed_number_peer(phone):
            peer = self.routed_number_peer(phone)

        channel = 'SIP/+{}@{}'.format(phone, peer['peer'])

        if self.__has_fixed_caller_id(peer) or len(caller_id) == 0:
            return {"channel": channel, "caller-id": peer['caller-id'], "peer": peer['peer']}
        return {"channel": channel, "caller-id": caller_id, "peer": peer['peer']}

    def get_available_peer(self):
        failing_peer = self.__cache.get(self.__FAIL_TRUNK_CACHE)
        for peer in self.__peers:
            peer_name = peer['peer']
            if failing_peer != peer_name and self.__ari.peer_is_online(peer_name):
                return peer
        return {}

    def routed_number_peer(self, phone: str):
        if self.__routed_numbers is None or len(self.__routed_numbers) <= 0:
            return False
        for route in self.__routed_numbers:
            peer = route['peer']
            number_format = route['format']
            if phone.startswith(number_format):
                return self.__get_peer_details(peer)
        return {}

    @staticmethod
    def __has_fixed_caller_id(peer):
        return peer["fixed-caller-id"] == 'true'

    def __get_peer_details(self, peer_name):
        for peer in self.__peers:
            if peer_name == peer['peer']:
                return peer
        return {}
