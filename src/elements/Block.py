from asterisk.agi import AGI
from bs4 import Tag
from src.Audio import Audio
from src.Logger import Logger


class Block:
    def __init__(self, agi: AGI, audio: Audio, logger: Logger):
        self.__agi = agi
        self.__audio = audio
        self.__logger = logger

    def process(self, block: Tag):
        try:
            self.__parse_block(block)
        except Exception as e:
            self.__logger.log_warning("VXML parse error: {}".format(str(e)))

    def __parse_block(self, block: Tag):
        prompts = block.find_all('prompt', recursive=False)
        if len(prompts) > 0:
            for prompt in prompts:
                if prompt is not None and prompt.find('audio') is not None:
                    audio = prompt.find('audio').attrs['src']
                    audio_file = self.__audio.gen_audio_file(audio)
                    self.__audio.stream(audio_file, self.__agi, self.__logger)
