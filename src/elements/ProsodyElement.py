from asterisk.agi import AGI
from src.Logger import Logger
from src.elements.SayAsElement import SayAsElement


class ProsodyElement:
    def __init__(self, agi: AGI, logger: Logger):
        self.__agi = agi
        self.__logger = logger

    def parse(self, say_as):
        # To parse format: <prosody rate="-20%"><say-as interpret-as="vxml:date">20200625</say-as></prosody>
        say_as_parser = SayAsElement(self.__agi, self.__logger)
        say_as_parser.parse(str(say_as))
