import subprocess
import psutil
from src.AsteriskARI import AsteriskARI
from src.manager.QueueManager import QueueManager


class Dashboard:
    def __init__(self, ari: AsteriskARI, queue: QueueManager):
        self.ari = ari
        self.queue = queue

    def get_stats(self):
        return {
            'cpu': psutil.cpu_percent(),
            'disk': psutil.disk_usage('/').percent,
            'memory': psutil.virtual_memory().percent,
            'channels': self.ari.number_of_active_channels(),
            'queued_calls': self.queue.get_number_of_queued_calls(),
            'max_sip_channels': self.ari.max_channels,
            'processed_calls': self.__get_processed_calls()
        }

    @staticmethod
    def __get_processed_calls():
        cmd = "asterisk -rx 'core show channels'"
        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
        for line in process.stdout:
            string = str(line.decode('utf8'))
            if "processed" in string:
                return int(string.split(" ")[0])
        return 0
