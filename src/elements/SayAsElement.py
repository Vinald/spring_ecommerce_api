from asterisk.agi import AGI
from src.Logger import Logger
from datetime import datetime


class SayAsElement:
    def __init__(self, agi: AGI, logger: Logger):
        self.__agi = agi
        self.__logger = logger

    def parse(self, say_as):
        try:
            # To parse format: <say-as type="address"> 1310 Villa Sti </say-as>
            if "type" in str(say_as):
                tts_type = str(say_as["say-as"])
                allowed_tts_types = ["address", "currency", "date:mdy", "date:y", "number:digit", "telephone", "time:h",
                                     "time:hm", "time:hms"]
                if tts_type in allowed_tts_types:
                    tts = say_as.get_text()
                    self.__agi.appexec('AGI', "googletts.agi,'{}',en,,0.8".format(tts))
            # To parse format: <prosody rate="-20%"><say-as interpret-as="vxml:date">20200625</say-as></prosody>
            if "interpret-as" in str(say_as):
                interpret = str(say_as["interpret-as"])
                if interpret == 'vxml:date':
                    date = say_as.get_text()
                    timestamp = datetime.strptime(date, '%Y%m%d').strftime('%A %d %B %Y')
                    self.__agi.appexec('AGI', "googletts.agi,'{}',en,,0.8".format(timestamp))
        except Exception as e:
            self.__logger.log_warning("VXML parse error: {}".format(str(e)))
            pass
