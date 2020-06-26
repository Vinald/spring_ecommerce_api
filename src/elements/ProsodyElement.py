from asterisk.agi import AGI
from src.Logger import Logger
from datetime import datetime


class ProsodyElement:
    def __init__(self, agi: AGI, logger: Logger):
        self.__agi = agi
        self.__logger = logger

    def parse(self, say_as):
        # To parse format: <prosody rate="-20%"><say-as interpret-as="vxml:date">20200625</say-as></prosody>
        try:
            interpret = str(say_as['interpret-as'])
            if interpret == 'vxml:date':
                date = say_as.get_text()
                timestamp = datetime.strptime(date, '%Y%m%d').strftime('%A %d %B %Y')
                self.__agi.appexec('AGI', "googletts.agi,'{}',en,,0.8".format(timestamp))
        except Exception:
            raise Exception
            pass
