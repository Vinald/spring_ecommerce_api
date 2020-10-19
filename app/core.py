import datetime
import json
import os
import pathlib
from asterisk.ami import AMIClientAdapter, AMIClient
from redis import Redis
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.api.Apps import Apps
from app.asterisk.AsteriskARI import AsteriskARI
from app.asterisk.AsteriskEventsHandler import AsteriskEventsHandler
from app.manager.CDRManager import CDRManager
from app.manager.CacheManager import CacheManager
from app.manager.TrunkManager import TrunkManager
from app.utilities.Config import Config
from app.utilities.Database import Database
from app.utilities.Logger import Logger

project_dir = pathlib.Path(os.path.dirname(os.path.realpath(__file__))).parent

logger = Logger(project_dir)
config = Config(project_dir, logger)

config.set_section('asterisk-ami')
ami_host = config.get('host')
ami_user = config.get('user')
ami_pass = config.get('pass')
ami_port = config.get_int('port')

config.set_section('database')
db_user = config.get('user')
db_pass = config.get('pass')
db_host = config.get('host')
db_port = config.get_int('port')
db_name = config.get('database')

db_link = 'mysql+pymysql://{}:{}@{}:{}/{}?charset=utf8mb4'
engine = create_engine(db_link.format(db_user, db_pass, db_host, db_port, db_name))
Session = sessionmaker(bind=engine)

asterisk_ari_config = config.get_section_content('asterisk-ari')

trunk_list = config.get_section_content('sip-trunks')

config.set_section('core')
log_level = config.get('log-level')
audio_path = config.get('audio-path')
max_channels = config.get_int('max-channels')
max_call_time = config.get_int('max-call-time-in-seconds')
routed_numbers = config.get('routed-numbers')
use_sip_trunks = config.get_bool('use-sip-trunks')
dates_audio_path = config.get('dates-audio-path')

# Set log level
logger.set_level(log_level)

database = Database(config)
app_manager = Apps(database, logger)

config.set_section('redis')
redis_host = config.get('host')
redis_port = config.get_int('port')

cache = Redis(host=redis_host, port=redis_port)

cache_manager = CacheManager(config, logger)
cdr_manager = CDRManager(cache_manager, database, logger)

asterisk_events_handler = AsteriskEventsHandler(logger, cache, cdr_manager)

asterisk_ari = AsteriskARI(asterisk_ari_config, logger, max_channels)

client = AMIClient(address=ami_host, port=ami_port)
client.login(username=ami_user, secret=ami_pass)

adapter = AMIClientAdapter(client)


def initialize_log():
    logger.set_app()
    logger.set_phone()


def date_object_converter(o):
    if isinstance(o, datetime.datetime):
        return o.__str__()


def initiate_call(call_data):
    flow = call_data['flow']
    phone = call_data['phone']
    token = call_data['token']
    call_id = call_data['call_id']
    app_data = call_data['app-data']
    external_id = call_data['external_id']
    status_link = app_data['status_url']

    channel = 'SIP/{}'.format(phone)
    caller_id = app_data['phone']

    if use_sip_trunks and len(trunk_list) > 0:
        trunk_manager = TrunkManager(asterisk_ari, cache_manager, trunk_list, routed_numbers)
        outbound_call_details = trunk_manager.construct_channel_and_caller_id(phone, caller_id)
        channel = outbound_call_details['channel']
        caller_id = outbound_call_details['caller-id']

    logger.set_app(app_manager)
    logger.set_phone(phone)

    future = adapter.Originate(
        Channel=channel,
        Exten='100',
        Priority=1,
        Context='ivr',
        CallerID=caller_id,
        Variable='data={}&{}&{}&{}&{}'.format(
            call_id,
            phone,
            flow,
            token,
            external_id,
        ),
        ActionID=call_id,
        Timeout=40000,
        Async=True
    )

    logger.log_info("Originate response: {}".format(future.response))

    cdr_data = {
        "app_name": app_data["name"],
        "creation_date": datetime.datetime.now(),
        "token": app_data['token'],
        "peer": channel,
        "caller_id": channel,
        "call_id": call_id,
        "dialed_number": phone,
        "external_id": external_id,
        "call_direction": "OUTGOING"
    }

    cdr_cache_id = 'cdr-{}'.format(call_id)
    cache.set(cdr_cache_id, json.dumps(cdr_data, default=date_object_converter), 3600)

    cache_data = json.dumps({
        'phone': phone,
        'initiated': 'no',
        'external_id': external_id,
        'status_link': status_link,
        'app-data': app_data
    }, default=date_object_converter)

    cache.set(call_id, cache_data, 3600)
