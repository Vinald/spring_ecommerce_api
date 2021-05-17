import datetime
import json
import time
from asterisk.agi import AGI
from app.api.Apps import Apps
from app.core import cache, date_object_converter
from app.ivr.Audio import Audio
from app.ivr.VXMLParser import VXMLParser
from app.utilities.Hash import Hash
from app.utilities.Logger import Logger


class IVR:
    def __init__(self, agi: AGI, logger: Logger, app_manager: Apps, audio: Audio):
        self.__agi = agi
        data = str(self.__agi.get_variable('data'))
        self.__data = [] if data == '' else data.split('&')
        self.__audio = audio
        self.__logger = logger
        self.__app_manager = app_manager

    def run(self):
        self.__initialize()
        parser = VXMLParser(self.__agi, self.__logger, self.__audio)
        parser.referer = self.link
        parser.process_xml(self.link)

    def __initialize(self):
        self.__logger.log_info('Initializing IVR')

        call_id = ''
        call_direction = 'INCOMING'

        if self.__data:
            # Outgoing details set up
            token = self.__data[1]
            call_id = self.__data[2]
            jump_to = self.__data[3]
            voice_url = self.__app_manager.get_voice_url(token)
            self.phone = self.__data[0]
            call_direction = 'OUTGOING'
            outgoing_link = "{}?phone={}&callId={}&jumpTo={}"
            self.link = outgoing_link.format(voice_url, self.phone, call_id, jump_to)
        else:
            # Incoming details set up
            extension = str(self.__agi.env['agi_dnid'])
            self.phone = str(self.__agi.env['agi_callerid'])
            external_id = Hash.hash(self.__agi.env['agi_uniqueid'])
            channel = str(self.__agi.env['agi_channel'])
            peer = str(channel.split('-')[0]).split('/')[1]

            cdr_data = {
                "app_name": "App (INCOMING UNKNOWN)",
                "creation_date": datetime.datetime.now(),
                "peer": peer,
                "caller_id": self.phone,
                "call_id": call_id,
                "dialed_number": extension,
                "external_id": external_id,
                "call_start_time": time.strftime('%H:%M:%S'),
                "call_direction": "INCOMING",
                "call_state": "ANSWERED",
            }

            cache.set(external_id, json.dumps({'phone': self.phone, 'is_incoming': 'true'}))
            cdr_cache_id = 'cdr-{}'.format(external_id)
            cache.set(cdr_cache_id, json.dumps(cdr_data, default=date_object_converter), 3600)

            token = self.__app_manager.get_token_by_dialed_number(extension)
            if token:
                voice_url = self.__app_manager.get_voice_url(token)
                self.link = "{}?phone={}".format(voice_url, self.phone)
            else:
                exit_msg = "Extension does not exist: {}".format(extension)
                self.__logger.log_info(exit_msg)
                self.__agi.verbose(exit_msg)
                self.__agi.hangup()

        results = self.__app_manager.get_data(token)
        app_name = results['name']

        try:
            user_id = int(results['user_id'])
        except Exception as e:
            user_id = 0
            self.__logger.log_info(f"App[{app_name}] has no attached user: {str(e)}")

        self.__logger.set_app(app_name)
        self.__logger.set_phone(self.phone)
        self.__logger.set_user_id(user_id)
        self.__logger.log_info('Starting call')
        self.__logger.log_info('Call ID: {}'.format(call_id))
        self.__logger.log_info('Call Direction: {}'.format(call_direction))
        self.__logger.log_info('Starting Voice URL: {}'.format(self.link))
