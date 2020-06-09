from datetime import datetime
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
                if prompt is not None:
                    audio_element = prompt.find('audio')
                    if audio_element is not None:
                        src = audio_element.attrs['src']
                        audio_file = self.__audio.gen_audio_file(src)
                        self.__audio.stream(audio_file, self.__agi, self.__logger)

                    prosody = prompt.find('prosody')
                    if prosody is not None:
                        self.__parse_say_as(prosody.find('say-as'))

    def __parse_say_as(self, say_as):
        interpret = str(say_as['interpret-as'])
        if interpret == 'vxml:date':
            date = say_as.get_text()
            timestamp = datetime.strptime(date, '%Y%m%d').strftime('%A %d %B %Y')
            self.__agi.appexec('AGI', "googletts.agi,'{}',en,,0.8".format(timestamp))
