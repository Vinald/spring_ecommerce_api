from asterisk.agi import AGI
from src.AppManager import AppManager
from src.Audio import Audio
from src.Logger import Logger
from src.Hash import Hash
from src.VXMLParser import VXMLParser


class IVR:
    def __init__(self, agi: AGI, logger: Logger, app_manager: AppManager, audio: Audio):
        self.agi = agi
        self.data = str(self.agi.get_variable('data'))
        self.audio = audio
        self.logger = logger
        self.app_manager = app_manager

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
            external_id = data[4]
            self.logger.set_external_id(external_id)
            voice_url = self.app_manager.get_voice_url(token)
            self.phone = data[1]
            call_direction = 'OUTGOING'
            outgoing_link = "{}?phone={}&callId={}&jumpTo={}"
            self.link = outgoing_link.format(voice_url, self.phone, call_id, jump_to)
        else:
            # Incoming details set up
            extension = str(self.agi.env['agi_dnid'])
            token = self.app_manager.get_token_by_dialed_number(extension)
            if token:
                voice_url = self.app_manager.get_voice_url(token)
                self.phone = str(self.agi.env['agi_callerid'])
                external_id = Hash.hash(str(self.agi.env['agi_uniqueid']))
                self.logger.set_external_id(external_id)
                self.link = "{}?phone={}".format(voice_url, self.phone)
            else:
                exit_msg = "Extension does not exist: {}".format(extension)
                self.logger.log_info(exit_msg)
                self.agi.verbose(exit_msg)
                self.agi.hangup()

        results = self.app_manager.get_data(token)
        self.logger.set_app(results['name'])
        self.logger.set_token(results['token'])
        self.agi.set_variable("CDR(call_direction)", call_direction)
        self.logger.set_phone(self.phone)
        self.logger.log_info('Starting call')
        self.logger.log_info('Call ID: {}'.format(call_id))
        self.logger.log_info('Call Direction: {}'.format(call_direction))
        self.logger.log_info('Starting Voice URL: {}'.format(self.link))
