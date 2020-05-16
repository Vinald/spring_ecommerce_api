#!/usr/bin/env python3

from os import path
import requests
from asterisk.agi import AGI
from redis import Redis
from src.Config import Config
from src.Hash import Hash
from src.Logger import Logger

agi = AGI()

working_dir = path.dirname(path.realpath(__file__))

logger = Logger(working_dir)
config = Config(working_dir, logger, 'app')

redis_host = str(config.get('redis_host'))
redis_port = config.get_int('redis_port')

cache = Redis(host=redis_host, port=redis_port)

key = Hash.hash(str(agi.env['agi_uniqueid']))
channel = str(agi.env['agi_channel'])
status_link = cache.get(key)

if status_link is not None:
    cache.delete(key)
    results = str(requests.get(status_link).content)
    logger.log_info("Call hangup detected for channel: {}".format(channel))
