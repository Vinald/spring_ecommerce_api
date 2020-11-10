import subprocess
import psutil
from app.asterisk.AsteriskARI import AsteriskARI
from app.manager.CDRManager import CDRManager
from app.manager.QueueManager import QueueManager
from app.manager.TrunkManager import TrunkManager
from app.utilities.Logger import Logger


class Dashboard:
    def __init__(
        self,
        ari: AsteriskARI,
        queue: QueueManager,
        logger: Logger,
        cdr_manager: CDRManager,
        peer_manager: TrunkManager
    ):
        self.__ari = ari
        self.__queue = queue
        self.__logger = logger
        self.__cdr_manager = cdr_manager
        self.__peer_manager = peer_manager

    def get_stats(self):
        return {
            'cpu': psutil.cpu_percent(),
            'disk': psutil.disk_usage('/').percent,
            'memory': psutil.virtual_memory().percent,
            'channels': self.__ari.number_of_active_channels(),
            'queued_calls': self.__queue.get_number_of_queued_calls(),
            'max_sip_channels': self.__ari.get_max_channels(),
            'processed_calls': self.__cdr_manager.get_number_of_processed_calls(),
            'asterisk_up_time': self.__ari.get_up_time(),
            'server_up_time': self.__get_server_up_time(),
            'peers': self.__peer_manager.get_all_peers(),
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
                        process.terminate()
                        return "{} hour(s) and {} minute(s)".format(hours, minutes)
                    process.terminate()
                    return up_time
            process.terminate()
            return 'n/a'
        except Exception as e:
            self.__logger.log_error("Dashboard: {}".format(str(e)))
            return 'n/a'

    def __get_service_up_time(self, service):
        try:
            cmd = "service {} status | grep active".format(service)
            process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
            for line in process.stdout:
                string = str(line.decode('utf8'))
                if "active" in string:
                    raw_up_time = str(string.split(';')[1].strip())
                    process.terminate()
                    return raw_up_time.split('ago')[0].strip()
            process.terminate()
            return 'n/a'
        except Exception as e:
            self.__logger.log_error("Dashboard: {}".format(str(e)))
            return 'n/a'
