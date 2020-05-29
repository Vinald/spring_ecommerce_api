import os

from asterisk.agi import AGI

from src.Logger import Logger


class Audio:
    def __init__(self, path):
        self.path = path

    def get_audio_path(self):
        if not os.path.exists(self.path):
            return None
        if self.path[-1] == '/':
            return self.path.strip()[:-1]
        return self.path

    def gen_audio_file(self, link):
        if self.get_audio_path() is None:
            return link
        path = self.get_audio_path() + link
        if not os.path.exists(path):
            return link
        return os.path.splitext(path)[0]

    @staticmethod
    def stream(file: str, agi: AGI, logger: Logger):
        try:
            logger.log_info('Streaming audio: {}'.format(file))
            agi.stream_file(file)
        except Exception as e:
            msg = 'Failed to stream audio file -> {}: {}'
            logger.log_warning(msg.format(file, str(e)))
