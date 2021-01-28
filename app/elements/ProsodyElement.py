from asterisk.agi import AGI
from app.elements.SayAsElement import SayAsElement
from app.ivr.Audio import Audio
from app.utilities.Logger import Logger


class ProsodyElement:
    def __init__(self, agi: AGI, logger: Logger, audio: Audio):
        self.__agi = agi
        self.__audio = audio
        self.__logger = logger

    def parse(self, prosody):
        # To parse format: <prosody rate="-20%"><say-as interpret-as="vxml:date">20200625</say-as></prosody>
        try:
            say_as_parser = SayAsElement(self.__agi, self.__logger, self.__audio)
            say_as_parser.parse(prosody.find('say-as'))
        except Exception as e:
            self.__logger.log_warning('Prosody Element parse error: {}'.format(str(e)))
