import time
from asterisk.agi import AGI
from datetime import datetime
from app.ivr.Audio import Audio
from app.utilities.Logger import Logger


class SayAsElement:
    def __init__(self, agi: AGI, logger: Logger, audio: Audio):
        self.__agi = agi
        self.__audio = audio
        self.__logger = logger

    def parse(self, say_as):
        interpret = str(say_as['interpret-as'])
        if interpret == 'vxml:date':
            date = say_as.get_text()
            date_obj = datetime.strptime(date, '%Y%m%d')
            files = [date_obj.strftime("%A"), date_obj.day, date_obj.strftime("%b").lower()]
            dates_audio_path = self.__audio.get_dates_audio_path()
            try:
                for file in files:
                    self.__agi.stream_file("{}/{}".format(dates_audio_path, file))
            except Exception as e:
                time.sleep(2)
                self.__logger.log_warning("Dates stream error: {}.".format(str(e)))
                self.__logger.log_warning("Defaulting to asterisk TTS for dates")
                self.__agi.say_date(date_obj.timestamp())

    # Todo. Parse more types initially done by Conrad Ekisa
    # def parse(self, say_as):
    #     try:
    #         # To parse format: <say-as type="address"> 1310 Villa Sti </say-as>
    #         if "type" in str(say_as):
    #             tts_type = str(say_as["say-as"])
    #             allowed_tts_types = ["address", "currency", "date:mdy", "date:y", "number:digit", "telephone",
    #             "time:h", "time:hm", "time:hms"]
    #             if tts_type in allowed_tts_types:
    #                 tts = say_as.get_text()
    #                 self.__agi.appexec('AGI', "googletts.agi,'{}',en,,0.8".format(tts))
    #         # To parse format: <prosody rate="-20%"><say-as interpret-as="vxml:date">20200625</say-as></prosody>
    #         if "interpret-as" in str(say_as):
    #             interpret = str(say_as["interpret-as"])
    #             if interpret == 'vxml:date':
    #                 date = say_as.get_text()
    #                 timestamp = datetime.strptime(date, '%Y%m%d').strftime('%A %d %B %Y')
    #                 self.__agi.appexec('AGI', "googletts.agi,'{}',en,,0.8".format(timestamp))
    #     except Exception as e:
    #         self.__logger.log_warning("SayAs Element VXML parse error: {}".format(str(e)))
