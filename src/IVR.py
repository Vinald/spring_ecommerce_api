from asterisk.agi import AGI
from src.Audio import Audio
from src.Logger import Logger
from src.VXMLParser import VXMLParser


class IVR:
    def __init__(self, link: str, agi: AGI, logger: Logger, audio: Audio):
        self.agi = agi
        self.link = link
        self.data = str(self.agi.get_variable('data'))
        self.phone = str(self.agi.env['agi_callerid'])
        self.audio = audio
        self.logger = logger

    def run(self):
        self.__initialize()
        parser = VXMLParser(self.agi, self.logger, self.audio)
        parser.process_xml(self.link)

    def __initialize(self):
        self.logger.log_info('Initializing IVR')

        call_id = ''
        call_direction = 'INCOMING'

        if self.data is not None and len(self.data) > 0:
            # Outgoing details set up
            data = self.data.split('&')
            call_id = data[0]
            jump_to = data[2]
            self.phone = data[1]
            call_direction = 'OUTGOING'
            outgoing_link = "{}{}&callId={}&jumpTo={}"
            self.link = outgoing_link.format(self.link, self.phone, call_id, jump_to)
        else:
            # Incoming details set up
            self.link = str(self.link + self.phone)

        self.logger.set_phone(self.phone)
        self.logger.log_info('Starting call')
        self.logger.log_info('Call ID: {}'.format(call_id))
        self.logger.log_info('Patient number: {}'.format(self.phone))
        self.logger.log_info('Call Direction: {}'.format(call_direction))
        self.logger.log_info('Starting Voice URL: {}'.format(self.link))
