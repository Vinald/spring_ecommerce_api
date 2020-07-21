from asterisk.agi import AGI
from src.Logger import Logger
from src.elements.SayAsElement import SayAsElement


class ProsodyElement:
    def __init__(self, agi: AGI, logger: Logger):
        self.__agi = agi
        self.__logger = logger

    def parse(self, prosody):
        # To parse format: <prosody rate="-20%"><say-as interpret-as="vxml:date">20200625</say-as></prosody>
        try:
            say_as_parser = SayAsElement(self.__agi, self.__logger)
            say_as_parser.parse(prosody.find('say-as'))
        except Exception as e:
            self.__logger.log_warning('Prosody Element parse error: {}'.format(str(e)))
