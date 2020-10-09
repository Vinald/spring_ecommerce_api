import datetime
import json
import os
import pathlib
from redis import Redis

project_dir = pathlib.Path(os.path.dirname(os.path.realpath(__file__))).parent

config_file = open(os.path.join(project_dir, 'config.json'))
config = json.load(config_file)
config_file.close()

redis_config = config['redis']

cache = Redis(host=redis_config['host'], port=int(redis_config['port']))


def date_object_converter(o):
    if isinstance(o, datetime.datetime):
        return o.__str__()
