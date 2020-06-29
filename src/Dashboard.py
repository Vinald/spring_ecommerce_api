import subprocess
import psutil
from src.AsteriskARI import AsteriskARI
from src.Logger import Logger
from src.manager.QueueManager import QueueManager


class Dashboard:
    def __init__(self, ari: AsteriskARI, queue: QueueManager, logger: Logger):
        self.ari = ari
        self.queue = queue
        self.logger = logger

    def get_stats(self):
        return {
            'cpu': psutil.cpu_percent(),
            'disk': psutil.disk_usage('/').percent,
            'memory': psutil.virtual_memory().percent,
            'channels': self.ari.number_of_active_channels(),
            'queued_calls': self.queue.get_number_of_queued_calls(),
            'max_sip_channels': self.ari.max_channels,
            'processed_calls': self.__get_processed_calls(),
            'asterisk_up_time': self.__get_service_up_time('asterisk'),
            'ivr_api_up_time': self.__get_service_up_time('ivr-api'),
            'server_up_time': self.__get_server_up_time(),
        }

    def __get_server_up_time(self):
        try:
            process = subprocess.Popen("uptime", shell=True, stdout=subprocess.PIPE)
            for line in process.stdout:
                string = str(line.decode('utf8'))
                if "up" in string:
                    up_time = str(string.split(',')[0].split('up')[1].strip())
                    if ":" in up_time:
                        hours = up_time.split(':')[0]
                        minutes = up_time.split(':')[1]
                        return "{} hour(s) and {} minute(s)".format(hours, minutes)
                    return up_time
            return 'n/a'
        except Exception as e:
            self.logger.log_error("Dashboard: {}".format(str(e)))
            return 'n/a'

    def __get_service_up_time(self, service):
        try:
            cmd = "service {} status | grep active".format(service)
            process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
            for line in process.stdout:
                string = str(line.decode('utf8'))
                if "active" in string:
                    raw_up_time = str(string.split(';')[1].strip())
                    return raw_up_time.split('ago')[0].strip()
            return 'n/a'
        except Exception as e:
            self.logger.log_error("Dashboard: {}".format(str(e)))
            return 'n/a'

    def __get_processed_calls(self):
        try:
            cmd = "asterisk -rx 'core show channels'"
            process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
            for line in process.stdout:
                string = str(line.decode('utf8'))
                if "processed" in string:
                    return int(string.split(" ")[0])
            return 0
        except Exception as e:
            self.logger.log_error("Dashboard: {}".format(str(e)))
            return 0
