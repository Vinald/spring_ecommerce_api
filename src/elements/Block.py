from datetime import datetime
from asterisk.agi import AGI
from bs4 import Tag
from src.Audio import Audio
from src.Logger import Logger
from src.elements.SayAsElement import SayAsElement
from src.elements.ProsodyElement import ProsodyElement

class Block:
    def __init__(self, agi: AGI, audio: Audio, logger: Logger):
        self.__agi = agi
        self.__audio = audio
        self.__logger = logger

    def process(self, block: Tag):
        try:
            self.__parse_block(block)
        except Exception as e:
            self.__logger.log_warning("Block Element VXML parse error: {}".format(str(e)))

    def __parse_block(self, block: Tag):
        prompts = block.find_all('prompt', recursive=False)
        say_as_parser = SayAsElement(self.__agi, self.__logger)
        prosody_parser = ProsodyElement(self.__agi, self.__logger)

        if len(prompts) > 0:
            for prompt in prompts:
                if prompt is not None:
                    audio_element = prompt.find('audio')
                    prosody_element = prompt.find('prosody')
                    say_as_element = prompt.find('say-as')

                    if audio_element is not None:
                        src = audio_element.attrs['src']
                        audio_file = self.__audio.gen_audio_file(src)
                        self.__audio.stream(audio_file, self.__agi, self.__logger)

                    if prosody_element is not None:
                        prosody_parser.parse(prosody_element)

                    if say_as_element is not None and not prosody_element:
                        say_as_parser.parse(say_as_element)
