import requests
from requests.auth import HTTPBasicAuth
from src.Config import Config
from src.Logger import Logger


class AsteriskARI:
    def __init__(self, config: Config, logger: Logger):
        self.logger = logger
        self.config = config
        self.__initialize()

    def get_channels(self):
        response = self.__send_request('/channels')
        return {} if response is None else list(response.json())

    def has_free_channels(self):
        return self.number_of_active_channels() < self.max_channels

    def number_of_active_channels(self):
        return len(self.get_channels())

    def __send_request(self, uri: str):
        try:
            url = self.base_link + uri
            return requests.get(url, auth=self.auth)
        except Exception as e:
            self.logger.log_error("Asterisk ARI. Failed to get data: {}".format(str(e)))
            return None

    def __initialize(self):
        self.config.set_section('ari')
        port = self.config.get('port')
        hostname = self.config.get('hostname')
        self.auth = HTTPBasicAuth(self.config.get('username'), self.config.get('password'))
        self.base_link = "http://{}:{}/ari".format(hostname, port)
        self.max_channels = self.config.get_int('max_channels')
