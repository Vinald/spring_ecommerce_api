from datetime import datetime
import requests
from requests.auth import HTTPBasicAuth
from app.utilities.Logger import Logger


class AsteriskARI:
    def __init__(self, config: dict, logger: Logger, max_channels: int):
        self.__logger = logger
        self.__config = config
        self.__max_channels = max_channels
        self.__initialize()

    def get_max_channels(self):
        return int(self.__max_channels)

    def has_free_channels(self):
        return self.number_of_active_channels() < self.__max_channels

    def number_of_active_channels(self):
        return len(self.__get_channels())

    def peer_is_online(self, peer_name):
        for peer in self.__get_peers():
            if peer_name == peer['resource'] and peer['state'] == 'online':
                return True
        return False

    def get_up_time(self):
        info = self.__get_asterisk_info()
        if not info:
            return 'n/a'
        start_date = datetime.strptime(info['status']['startup_time'], '%Y-%m-%dT%H:%M:%S.%f%z')
        return "{} day(s)".format((datetime.now(start_date.tzinfo) - start_date).days)

    def all_peers_are_offline(self):
        states = []
        for peer in self.__get_peers():
            states.append(peer['state'])
        return "online" not in states

    def __get_asterisk_info(self):
        response = self.__send_request('/asterisk/info')
        return {} if response is None else dict(response.json())

    def __get_peers(self):
        response = self.__send_request('/endpoints/SIP')
        return [] if response is None else list(response.json())

    def __get_channels(self):
        response = self.__send_request('/channels')
        return {} if response is None else list(response.json())

    def __send_request(self, uri: str):
        try:
            url = self.base_link + uri
            return requests.get(url, auth=self.auth)
        except Exception as e:
            self.__logger.log_error("Asterisk ARI. Failed to get data: {}".format(str(e)))
            return None

    def __initialize(self):
        port = self.__config['port']
        hostname = self.__config['host']
        self.auth = HTTPBasicAuth(self.__config['user'], self.__config['pass'])
        self.base_link = "http://{}:{}/ari".format(hostname, port)
