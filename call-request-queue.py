#!/usr/bin/env python3

import time
import requests
import core
from src.AsteriskARI import AsteriskARI
from src.manager.QueueManager import QueueManager

queue = QueueManager(core.cache)
asterisk_ari = AsteriskARI(core.config, core.logger)

while True:
    if asterisk_ari.has_free_channels() and not queue.is_empty():
        data = requests.get('http://127.0.0.1:5000/ivr/queue').json()
        core.logger.log_info('Queued call response: {}'.format(str(data)))
        time.sleep(5)
    else:
        break

exit(0)
