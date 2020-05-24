from asterisk.agi import AGI
from src.AppManager import AppManager
from src.Audio import Audio
from src.Logger import Logger
from src.VXMLParser import VXMLParser


class IVR:
    def __init__(self, agi: AGI, logger: Logger, app_manager: AppManager, audio: Audio):
        self.agi = agi
        self.data = str(self.agi.get_variable('data'))
        self.audio = audio
        self.logger = logger
        self.app_manger = app_manager

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
            token = data[3]
            call_id = data[0]
            jump_to = data[2]
            voice_url = self.app_manger.get_voice_url(token)
            self.phone = data[1]
            call_direction = 'OUTGOING'
            outgoing_link = "{}?phone={}&callId={}&jumpTo={}"
            self.link = outgoing_link.format(voice_url, self.phone, call_id, jump_to)
        else:
            # Incoming details set up
            token = str(self.agi.get_variable('token'))
            voice_url = self.app_manger.get_voice_url(token)
            self.phone = str(self.agi.env['agi_callerid'])
            self.link = "{}?phone={}".format(voice_url, self.phone)

        self.logger.set_phone(self.phone)
        self.logger.log_info('Starting call')
        self.logger.log_info('Call ID: {}'.format(call_id))
        self.logger.log_info('Call Direction: {}'.format(call_direction))
        self.logger.log_info('Starting Voice URL: {}'.format(self.link))
