import datetime
import json
import os
import pathlib
from datetime import date
from asterisk.ami import AMIClientAdapter, AMIClient
from redis import Redis
from app.api.Apps import Apps
from app.asterisk.AsteriskEventsHandler import AsteriskEventsHandler
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

asterisk_ari_config = config.get_section_content('asterisk-ari')

trunk_list = config.get_section_content('sip-trunks')

config.set_section('core')
log_level = config.get('log-level')
audio_path = config.get('audio-path')
max_channels = config.get_int('max-channels')
max_call_time = config.get_int('max-call-time-in-seconds')
routed_numbers = config.get('routed-numbers')
use_sip_trunks = config.get_bool('use-sip-trunks')

# Set log level
logger.set_level(log_level)

database = Database(config)
app_manager = Apps(database, logger)

config.set_section('redis')
redis_host = config.get('host')
redis_port = config.get_int('port')

cache = Redis(host=redis_host, port=redis_port)
asterisk_events_handler = AsteriskEventsHandler(logger, cache)

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

    if use_sip_trunks and len(trunk_list) > 0:
        trunk_manager = TrunkManager(trunk_list, routed_numbers)
        route_peer = trunk_manager.routed_number(phone)
        if route_peer:
            channel = 'SIP/+{}@{}'.format(phone, route_peer)
        else:
            available_peer = trunk_manager.get_available_peer()
            channel = 'SIP/+{}@{}'.format(phone, available_peer)

    date_today = date.today().strftime("%b-%d-%Y")
    application_name = app_manager.get_data(token)['name']

    logger.set_app(app_manager)
    logger.set_phone(phone)

    data = 'data={}&{}&{}&{}&{},' \
           'CDR(dialed_number)={},' \
           'CDR(date)={},' \
           'CDR(call_id)={},' \
           'CDR(sip_channel)={},' \
           'CDR(call_direction)=OUTGOING,' \
           'CDR(token)={},' \
           'CDR(application_name)={},' \
           'CDR(external_id)={}'

    adapter.Originate(
        Channel=channel,
        Exten='100',
        Priority=1,
        Context='ivr',
        CallerID='Call For Life Uganda',
        Variable=data.format(
            call_id,
            phone,
            flow,
            token,
            external_id,
            phone,
            date_today,
            call_id,
            channel,
            token,
            application_name,
            external_id,
        ),
        ActionID=call_id,
        Timeout=45000,
        Async=True
    )

    cache_data = json.dumps({
        'phone': phone,
        'initiated': 'no',
        'external_id': external_id,
        'status_link': status_link,
        'app-data': app_data
    }, default=date_object_converter)

    cache.set(call_id, cache_data, 3600)
