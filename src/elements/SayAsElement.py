from asterisk.agi import AGI
from src.Logger import Logger


class SayAsElement:
    def __init__(self, agi: AGI, logger: Logger):
        self.__agi = agi
        self.__logger = logger

    def parse(self, say_as):
        # To parse format: <say-as type="address"> 1310 Villa Sti </say-as>
        try:
            tts_type = str(say_as["say-as"])
            allowed_tts_types = ["address", "currency", "date:mdy", "date:y", "number:digit", "telephone", "time:h",
                                 "time:hm", "time:hms"]
            if tts_type in allowed_tts_types:
                tts = say_as.get_text()
                self.__agi.appexec('AGI', "googletts.agi,'{}',en,,0.8".format(tts))
        except Exception:
            raise Exception
            pass
