import time
import requests
from asterisk.agi import AGI
from bs4 import BeautifulSoup
from src.Audio import Audio
from src.Logger import Logger
from src.elements.BlockElement import BlockElement


class VXMLParser:
    def __init__(self, agi: AGI, logger: Logger, audio: Audio):
        self.agi = agi
        self.audio = audio
        self.logger = logger

    def process_xml(self, next_link: str):
        doc = BeautifulSoup(requests.get(next_link).content, "xml")
        form = doc.find('form')
        field = doc.find('field')
        filled = doc.find('filled')
        blocks = doc.find_all('block')
        field_name = field.attrs['name']

        if field is not None and field_name is not None and field_name == 'finishedHearing':
            self.logger.log_info('Processing uninterrupted hearing')
            return self.process_finished_hearing(blocks)

        if field is not None and len(filled) > 0:
            self.logger.log_info('Starting Audio Dialogue')
            return self.process_audio_dialogue(form)

    def process_blocks(self, blocks):
        block_parser = BlockElement(self.agi, self.audio, self.logger)
        for index in range(len(blocks)):
            block = blocks[index]
            block_parser.process(block)

    def process_finished_hearing(self, blocks):
        block_parser = BlockElement(self.agi, self.audio, self.logger)
        for index in range(len(blocks)):
            block = blocks[index]
            block_parser.process(block)

            has_attributes = len(block.attrs) > 0

            if has_attributes:
                name = block.attrs['name']
                if name is not None and name == 'submit':
                    goto = block.find('goto')
                    next_link = goto.attrs['next']
                    self.logger.log_info('Processing next link: {}'.format(next_link))
                    return self.process_xml(next_link)

            # Fix me
            # logging.fatal('Next link not found in blocks. exiting')
            # agi.hangup()

    def process_audio_dialogue(self, form, input_attempts=0, no_match_attempts=0):
        field = form.find('field')
        blocks = form.find_all('block', recursive=False)
        self.process_blocks(blocks)

        try:
            # Capture the length of DTMF, lets say like 4 digits
            # (type="digits?length=4")
            field_length = int(field.attrs['type'].split('=')[1])
        except Exception as e:
            self.logger.log_info(str(e))
            field_length = None

        filled = form.find('filled')
        items = form.find_all('item')
        grammar = form.find('grammar')
        field_name = field.attrs['name']

        try:
            filled_name = filled.find('submit').attrs['namelist']
        except Exception as e:
            self.logger.log_info(str(e))
            filled_name = filled.attrs['namelist']

        filled_next_link = filled.find('submit').attrs['next']

        timeout = 1000
        default_timeout = 1000

        no_input_element = field.find_all('noinput')
        no_match_element = field.find_all('nomatch')

        self.logger.log_info('Field name: {}'.format(field_name))
        self.logger.log_info('Filled name: {}'.format(filled_name))
        self.logger.log_info('Next Link: {}'.format(filled_next_link))

        prompts = field.find_all('prompt', recursive=False)

        input_digit = ''

        for prompt in prompts:
            if prompt is not None and prompt.find('audio') is not None:
                audio = prompt.find('audio').attrs['src']
                audio_file = self.audio.gen_audio_file(audio)
                timeout = prompt.attrs['timeout']

                if len(timeout) > 0 and timeout is not None:
                    timeout = int(float(timeout[:-1]) * 1000)

                if field_length is not None and field_length > 1:
                    self.logger.log_info('Streaming audio: {}'.format(audio_file))
                    input_digit = self.agi.get_data(audio_file, timeout, field_length)
                    time.sleep(2)
                    if len(input_digit) == field_length:
                        break
                else:
                    self.logger.log_info('Streaming audio: {}'.format(audio_file))
                    input_digit = self.agi.get_data(audio_file, default_timeout, 1)

                    if len(input_digit) > 0:
                        break

        choices = []

        if field_length is not None and len(input_digit) < field_length:
            input_digit = self.agi.get_data('silence/1', timeout, field_length)

        if len(input_digit) == 0 and field_length is None:
            input_digit = self.agi.wait_for_digit(timeout)

        if len(input_digit) == 0:
            attempts = input_attempts + 1
            no_input = self.no_input_and_no_match(no_input_element)
            return self.process_no_input_and_no_match(
                no_input,
                attempts,
                no_match_attempts,
                form
            )

        if grammar is not None and items is not None:
            for item in items:
                choices.append(int(item.get_text()))

            if int(input_digit) in choices:
                self.logger.log_info('Entered: {} as their choice'.format(input_digit))
                next_link = filled_next_link + '&' + filled_name + '=' + str(input_digit)
                return self.process_xml(next_link)

            time.sleep(5)

            # Handle Invalid in put here
            self.logger.log_info('Entered an invalid choice: {}'.format(input_digit))
            match_attempts = no_match_attempts + 1
            no_match = self.no_input_and_no_match(no_match_element)
            return self.process_no_input_and_no_match(
                no_match,
                input_attempts,
                match_attempts,
                form,
                False
            )

        if field_name == filled_name:
            next_link = filled_next_link + '&' + filled_name + '=' + str(input_digit)
            return self.process_xml(next_link)

    @staticmethod
    def no_input_and_no_match(elements):
        for element in elements:
            if element is not None and element.has_attr('count') and element.attrs['count'] is not None:
                submit = element.find('submit')
                prompt = element.find('prompt', recursive=False)
                timeout = 0
                next_link = None
                audio_file = None

                if submit is not None and submit.attrs['next'] is not None:
                    next_link = submit.attrs['next']

                if prompt is not None:
                    audio = prompt.find('audio', recursive=False)
                    timeout = int(float(prompt.attrs['timeout'][:-1]) * 1000)
                    audio_file = audio.attrs['src']

                return {
                    "audio": audio_file,
                    "count": int(element.attrs['count']),
                    "timeout": timeout,
                    "next_link": next_link,
                }

        return None

    def process_no_input_and_no_match(
        self,
        element,
        input_attempts,
        no_match_attempts,
        form,
        no_input=True
    ):
        count = element['count']
        audio = element['audio']
        next_link = str(element['next_link'])

        if input_attempts >= count or no_match_attempts >= count:
            if audio is not None:
                audio_file = self.audio.gen_audio_file(audio)
                self.logger.log_info('Streaming audio: {}'.format(audio_file))
                self.agi.stream_file(audio_file)
            if next_link is not None:
                if no_input:
                    return self.process_xml(next_link + '&gNoInputEventCount=1')
                return self.process_xml(next_link + '&gNoMatchEventCount=1')

        return self.process_audio_dialogue(form, input_attempts, no_match_attempts)
