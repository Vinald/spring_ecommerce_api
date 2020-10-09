from asterisk.agi import AGI
from app.api.Apps import Apps
from app.ivr.Audio import Audio
from app.ivr.VXMLParser import VXMLParser
from app.utilities.Logger import Logger


class IVR:
    def __init__(self, agi: AGI, logger: Logger, app_manager: Apps, audio: Audio):
        self.__agi = agi
        self.__data = str(self.__agi.get_variable('data'))
        self.__audio = audio
        self.__logger = logger
        self.__app_manager = app_manager

    def run(self):
        self.__initialize()
        parser = VXMLParser(self.__agi, self.__logger, self.__audio)
        parser.process_xml(self.link)

    def __initialize(self):
        self.__logger.log_info('Initializing IVR')

        call_id = ''
        call_direction = 'INCOMING'

        if self.__data is not None and len(self.__data) > 0:
            # Outgoing details set up
            data = self.__data.split('&')
            token = data[3]
            call_id = data[0]
            jump_to = data[2]
            voice_url = self.__app_manager.get_voice_url(token)
            self.phone = data[1]
            call_direction = 'OUTGOING'
            outgoing_link = "{}?phone={}&callId={}&jumpTo={}"
            self.link = outgoing_link.format(voice_url, self.phone, call_id, jump_to)
        else:
            # Incoming details set up
            extension = str(self.__agi.env['agi_dnid'])
            token = self.__app_manager.get_token_by_dialed_number(extension)
            if token:
                voice_url = self.__app_manager.get_voice_url(token)
                self.phone = str(self.__agi.env['agi_callerid'])
                self.link = "{}?phone={}".format(voice_url, self.phone)
            else:
                exit_msg = "Extension does not exist: {}".format(extension)
                self.__logger.log_info(exit_msg)
                self.__agi.verbose(exit_msg)
                self.__agi.hangup()

        results = self.__app_manager.get_data(token)
        self.__logger.set_app(results['name'])
        self.__agi.set_variable("CDR(call_direction)", call_direction)
        self.__logger.set_phone(self.phone)
        self.__logger.log_info('Starting call')
        self.__logger.log_info('Call ID: {}'.format(call_id))
        self.__logger.log_info('Call Direction: {}'.format(call_direction))
        self.__logger.log_info('Starting Voice URL: {}'.format(self.link))
