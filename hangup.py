#!/usr/bin/env python3

import json
from os import path
import requests
from asterisk.agi import AGI
from redis import Redis
from src.Config import Config
from src.Hash import Hash
from src.Logger import Logger

agi = AGI()

project_dir = path.dirname(path.realpath(__file__))

logger = Logger(path.join(project_dir, 'logs'))
config = Config(project_dir, logger, 'app')

redis_host = str(config.get('redis_host'))
redis_port = config.get_int('redis_port')

cache = Redis(host=redis_host, port=redis_port)

key = Hash.hash(str(agi.env['agi_uniqueid']))
channel = str(agi.env['agi_channel'])
cache_result = cache.get(key)

if cache_result is not None:
    cache.delete(key)
    data = json.loads(cache_result)
    link = data['link']
    phone = data['phone']
    results = str(requests.get(link).content)
    log_msg = "Call hangup detected for channel: {} results: {}"
    logger.set_phone(phone)
    logger.log_info(log_msg.format(channel, results))
