from asterisk.agi import AGI
from bs4 import Tag
from app.elements.ProsodyElement import ProsodyElement
from app.ivr.Audio import Audio
from app.utilities.Logger import Logger


class BlockElement:
    def __init__(self, agi: AGI, audio: Audio, logger: Logger):
        self.__agi = agi
        self.__audio = audio
        self.__logger = logger

    def process(self, block: Tag):
        try:
            self.__parse_block(block)
        except Exception as e:
            self.__logger.log_warning("VXML parse error: {}".format(str(e)))
            self.__logger.log_warning("VXML: {}".format(str(block)))

    def __parse_block(self, block: Tag):
        prompts = block.find_all('prompt', recursive=False)
        prosody_parser = ProsodyElement(self.__agi, self.__logger, self.__audio)

        if len(prompts) > 0:
            for prompt in prompts:
                if prompt is not None:
                    audio_element = prompt.find('audio')
                    prosody_element = prompt.find('prosody')

                    if audio_element is not None:
                        src = audio_element.attrs['src']
                        audio_file = self.__audio.gen_audio_file(src)
                        self.__audio.stream(audio_file, self.__agi, self.__logger)

                    if prosody_element is not None:
                        prosody_parser.parse(prosody_element)
