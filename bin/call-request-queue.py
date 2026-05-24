#!/usr/bin/env python3
"""
Call request queue processor.

Polls Redis for queued calls and dispatches them when Asterisk has
free channels. Designed to be called by a cron job or systemd timer.
Exits cleanly after one drain pass so the scheduler controls frequency.
"""
import sys
import time
import requests

sys.path.append('..')

from app.asterisk.AsteriskARI import AsteriskARI
from app.core import max_channels, asterisk_ari_config, logger, cache
from app.manager.QueueManager import QueueManager

_API_URL = 'http://127.0.0.1:5000/ivr/queue'
_REQUEST_TIMEOUT = 10  # seconds

queue = QueueManager(cache)
asterisk_ari = AsteriskARI(asterisk_ari_config, logger, max_channels)

dispatched = 0

while asterisk_ari.has_free_channels() and not queue.is_empty():
    try:
        response = requests.get(_API_URL, timeout=_REQUEST_TIMEOUT)
        response.raise_for_status()
        data = response.json()
        logger.log_info('Queued call dispatched: {}'.format(str(data)))
        dispatched += 1
        time.sleep(1)
    except requests.exceptions.RequestException as e:
        logger.log_error('Queue processor failed to reach API: {}'.format(str(e)))
        sys.exit(1)

logger.log_info('Queue processor: dispatched {} call(s). Exiting.'.format(dispatched))
sys.exit(0)
