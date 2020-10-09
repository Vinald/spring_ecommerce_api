import time
import requests
from app.asterisk.AsteriskARI import AsteriskARI
from app.core import max_channels, asterisk_ari_config, logger, cache
from app.manager.QueueManager import QueueManager

queue = QueueManager(cache)
asterisk_ari = AsteriskARI(asterisk_ari_config, logger, max_channels)

while True:
    if asterisk_ari.has_free_channels() and not queue.is_empty():
        data = requests.get('http://127.0.0.1:5000/ivr/queue').json()
        logger.log_info('Queued call response: {}'.format(str(data)))
        time.sleep(2)
    else:
        break

exit(0)
