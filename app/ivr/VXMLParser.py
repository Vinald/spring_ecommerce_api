import time
import requests
from asterisk.agi import AGI
from bs4 import BeautifulSoup
from app.core import log_vxml
from app.elements.BlockElement import BlockElement
from app.ivr.Audio import Audio
from app.utilities.Logger import Logger

# CHANGED: added a timeout for all outbound VXML HTTP requests.
# Without this, a slow/dead external VXML server would block the AGI channel
# indefinitely, tying up a SIP trunk for the duration of the TCP timeout.
_HTTP_TIMEOUT = 10


class VXMLParser:
    def __init__(self, agi: AGI, logger: Logger, audio: Audio):
        self.__agi = agi
        self.__audio = audio
        self.__logger = logger
        self.__session = None
        self.referer = None

    def process_xml(self, next_link: str):
        """
        CHANGED: was recursive — process_xml() called itself on every VXML goto.
        A VXML app with many steps (long surveys, deep menus) would exhaust
        Python's default recursion limit (~1000) and raise an unhandled
        RecursionError mid-call. Refactored to an iterative while loop:
        each step returns the next URL to follow, or None to stop.
        """
        current_link = next_link
        while current_link:
            current_link = self.__process_single_step(current_link)

    def __process_single_step(self, link: str):
        """Process one VXML document. Returns the next link, or None to stop."""
        doc = BeautifulSoup(self.__get_content(link), "xml")
        if log_vxml:
            self.__logger.log_info("VXML: {}".format(doc))

        form = doc.find('form')
        field = doc.find('field')
        filled = doc.find('filled')
        blocks = doc.find_all('block')

        # FIXED (Copilot review): the previous fix returned None immediately when
        # field was absent. However, many valid VXML documents are block-only
        # (e.g. a prompt + <goto> with no user input required). Returning None
        # would silently terminate those call flows.
        #
        # New logic:
        #   1. If the document has blocks but no <field>, execute the blocks and
        #      follow any <goto> found inside them (block-only / announcement flow).
        #   2. If it has a <field name='finishedHearing'>, run the listening flow.
        #   3. If it has a <field> + <filled>, run the audio dialogue flow.
        #   4. Only return None (end of flow) when none of the above applies.

        if field is None:
            if blocks:
                # Block-only document — process blocks and follow any goto.
                self.__logger.log_info('Block-only VXML document (no <field>): {}'.format(link))
                return self.__process_block_only(blocks)
            # Truly empty document — nothing to do.
            self.__logger.log_warning('Empty VXML document (no <field> or <block>): {}'.format(link))
            return None

        field_name = field.attrs.get('name')

        if field_name == 'finishedHearing':
            self.__logger.log_info('Processing uninterrupted hearing')
            return self.__process_finished_hearing(blocks)

        if filled is not None and len(filled) > 0:
            self.__logger.log_info('Starting Audio Dialogue')
            return self.__process_audio_dialogue(form)

        return None

    def __process_block_only(self, blocks):
        """
        Execute blocks from a block-only VXML document (no <field> element).
        Returns the next link from the first <goto> found, or None if none exists.
        """
        block_parser = BlockElement(self.__agi, self.__audio, self.__logger)
        for block in blocks:
            block_parser.process(block)
            goto = block.find('goto')
            if goto is not None:
                next_link = goto.attrs.get('next')
                if next_link:
                    self.__logger.log_info('Block-only goto: {}'.format(next_link))
                    return next_link
        return None

    def __process_blocks(self, blocks):
        block_parser = BlockElement(self.__agi, self.__audio, self.__logger)
        for block in blocks:
            block_parser.process(block)

    def __process_finished_hearing(self, blocks):
        block_parser = BlockElement(self.__agi, self.__audio, self.__logger)
        for block in blocks:
            block_parser.process(block)
            if len(block.attrs) > 0:
                name = block.attrs.get('name')
                if name == 'submit':
                    goto = block.find('goto')
                    if goto is not None:
                        next_link = goto.attrs.get('next')
                        self.__logger.log_info('Processing next link: {}'.format(next_link))
                        return next_link
        return None

    def __process_audio_dialogue(self, form, input_attempts=0, no_match_attempts=0):
        field = form.find('field')
        blocks = form.find_all('block', recursive=False)
        self.__process_blocks(blocks)

        try:
            field_length = int(field.attrs['type'].split('=')[1])
        except Exception as e:
            self.__logger.log_info(str(e))
            field_length = None

        filled = form.find('filled')
        items = form.find_all('item')
        grammar = form.find('grammar')
        field_name = field.attrs.get('name')

        try:
            filled_name = filled.find('submit').attrs['namelist']
        except Exception as e:
            self.__logger.log_info(str(e))
            filled_name = filled.attrs.get('namelist')

        filled_next_link = filled.find('submit').attrs['next']

        timeout = 1000
        default_timeout = 1000

        no_input_element = field.find_all('noinput')
        no_match_element = field.find_all('nomatch')

        self.__logger.log_info('Field name: {}'.format(field_name))
        self.__logger.log_info('Filled name: {}'.format(filled_name))
        self.__logger.log_info('Next Link: {}'.format(filled_next_link))

        prompts = field.find_all('prompt', recursive=False)
        input_digit = ''

        for prompt in prompts:
            if prompt is not None and prompt.find('audio') is not None:
                audio = prompt.find('audio').attrs['src']
                audio_file = self.__audio.gen_audio_file(audio)
                raw_timeout = prompt.attrs.get('timeout', '')
                if raw_timeout:
                    timeout = int(float(raw_timeout[:-1]) * 1000)

                if field_length is not None and field_length > 1:
                    self.__logger.log_info('Streaming audio: {}'.format(audio_file))
                    input_digit = self.__agi.get_data(audio_file, timeout, field_length)
                    time.sleep(2)
                    if len(input_digit) == field_length:
                        break
                else:
                    self.__logger.log_info('Streaming audio: {}'.format(audio_file))
                    input_digit = self.__agi.get_data(audio_file, default_timeout, 1)
                    if len(input_digit) > 0:
                        break

        if field_length is not None and len(input_digit) < field_length:
            input_digit = self.__agi.get_data('silence/1', timeout, field_length)

        if len(input_digit) == 0 and field_length is None:
            input_digit = self.__agi.wait_for_digit(timeout)

        if len(input_digit) == 0:
            attempts = input_attempts + 1
            no_input = self.__no_input_and_no_match(no_input_element)
            return self.__process_no_input_and_no_match(
                no_input, attempts, no_match_attempts, form
            )

        if grammar is not None and items is not None:
            choices = []
            for item in items:
                choices.append(int(item.get_text()))

            if int(input_digit) in choices:
                self.__logger.log_info('Entered: {} as their choice'.format(input_digit))
                return filled_next_link + '&' + filled_name + '=' + str(input_digit)

            time.sleep(5)
            self.__logger.log_info('Entered an invalid choice: {}'.format(input_digit))
            match_attempts = no_match_attempts + 1
            no_match = self.__no_input_and_no_match(no_match_element)
            return self.__process_no_input_and_no_match(
                no_match, input_attempts, match_attempts, form, False
            )

        if field_name == filled_name:
            return filled_next_link + '&' + filled_name + '=' + str(input_digit)

        return None

    @staticmethod
    def __no_input_and_no_match(elements):
        for element in elements:
            if element is not None and element.has_attr('count'):
                submit = element.find('submit')
                prompt = element.find('prompt', recursive=False)
                timeout = 0
                next_link = None
                audio_file = None

                if submit is not None:
                    next_link = submit.attrs.get('next')

                if prompt is not None:
                    audio = prompt.find('audio', recursive=False)
                    raw_timeout = prompt.attrs.get('timeout', '0s')
                    timeout = int(float(raw_timeout[:-1]) * 1000)
                    if audio is not None:
                        audio_file = audio.attrs.get('src')

                return {
                    "audio": audio_file,
                    "count": int(element.attrs['count']),
                    "timeout": timeout,
                    "next_link": next_link,
                }
        return None

    def __process_no_input_and_no_match(
        self, element, input_attempts, no_match_attempts, form, no_input=True
    ):
        if element is None:
            self.__logger.log_warning('No noinput/nomatch element found — ending dialogue')
            return None

        count = element['count']
        audio = element['audio']
        next_link = str(element['next_link']) if element['next_link'] else None

        if input_attempts >= count or no_match_attempts >= count:
            if audio is not None:
                audio_file = self.__audio.gen_audio_file(audio)
                self.__logger.log_info('Streaming audio: {}'.format(audio_file))
                self.__agi.stream_file(audio_file)
            if next_link is not None:
                suffix = '&gNoInputEventCount=1' if no_input else '&gNoMatchEventCount=1'
                return next_link + suffix

        return self.__process_audio_dialogue(form, input_attempts, no_match_attempts)

    def __get_content(self, link):
        if not self.__session:
            self.__session = requests.Session()
        # CHANGED: added timeout — see module-level _HTTP_TIMEOUT comment above.
        return self.__session.get(
            link,
            headers={'referer': self.referer},
            timeout=_HTTP_TIMEOUT
        ).text
