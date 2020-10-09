import os
from asterisk.agi import AGI
from app.utilities.Logger import Logger


class Audio:
    def __init__(self, path):
        self.__path = path

    def gen_audio_file(self, link):
        if self.__get_audio_path() is None:
            return link
        path = self.__get_audio_path() + link
        if not os.path.exists(path):
            return link
        return os.path.splitext(path)[0]

    @staticmethod
    def stream(audio_file: str, agi: AGI, logger: Logger):
        try:
            logger.log_info('Streaming audio: {}'.format(audio_file))
            agi.stream_file(audio_file)
        except Exception as e:
            msg = 'Failed to stream audio file -> {}: {}'
            logger.log_warning(msg.format(audio_file, str(e)))

    def __get_audio_path(self):
        if not os.path.exists(self.__path):
            return None
        if self.__path[-1] == '/':
            return self.__path.strip()[:-1]
        return self.__path
