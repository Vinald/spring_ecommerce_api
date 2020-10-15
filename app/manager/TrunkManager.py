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
        self.__trunks = trunks
        self.__routed_numbers = routed_numbers

    def get_available_peer(self):
        failing_peer = self.__cache.get(self.__FAIL_TRUNK_CACHE)
        for trunk in self.__trunks:
            peer = trunk['peer']
            if failing_peer != peer and self.__ari.peer_is_online(peer):
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
