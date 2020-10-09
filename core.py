import json
import os
from datetime import date
from asterisk.ami import AMIClientAdapter, AMIClient
from redis import Redis
from src.AppDatabase import AppDatabase
from src.AppManager import AppManager
from src.AppWebListener import AppWebListener
from src.Config import Config
from src.Logger import Logger
from src.manager.TrunkManager import TrunkManager
from src.utils import date_object_converter

project_dir = os.path.dirname(os.path.realpath(__file__))

# Initiate Logger
logger = Logger(os.path.join(project_dir, 'logs'))
config = Config(project_dir, logger)

config.set_section('ami')
ami_host = config.get_ami_host()
ami_user = config.get_ami_user()
ami_pass = config.get_ami_pass()
ami_port = config.get_ami_port()
ami_sip_trunk_number = config.get("sip_trunk_number")
trunk_list = config.get_sip_trunk_list()
routed_numbers = config.get('routed_numbers')

database = AppDatabase(config)
app_manager = AppManager(database, logger)

config.set_section('app')
redis_host = str(config.get('redis_host'))
redis_port = config.get_int('redis_port')

cache = Redis(host=redis_host, port=redis_port)
app_web_listener = AppWebListener(logger, cache)

client = AMIClient(address=ami_host, port=ami_port)
client.login(username=ami_user, secret=ami_pass)

adapter = AMIClientAdapter(client)


def ami_client():
    ami = AMIClient(address=ami_host, port=ami_port)
    ami.login(username=ami_user, secret=ami_pass)
    return ami


def initialize_log():
    logger.set_app()
    logger.set_phone()


def initiate_call(call_data):
    flow = call_data['flow']
    phone = call_data['phone']
    token = call_data['token']
    call_id = call_data['call_id']
    app_data = call_data['app-data']
    external_id = call_data['external_id']
    status_link = app_data['status_url']

    channel = 'SIP/{}'.format(phone)

    if trunk_list is not None and len(trunk_list) > 0:
        trunk_manager = TrunkManager(trunk_list, routed_numbers)
        route_peer = trunk_manager.routed_number(phone)
        if route_peer:
            channel = 'SIP/+{}@{}'.format(phone, route_peer)
        else:
            available_peer = trunk_manager.get_available_peer()
            channel = 'SIP/+{}@{}'.format(phone, available_peer)

    date_today = date.today().strftime("%b-%d-%Y")
    sip_trunk_number = ami_sip_trunk_number

    application_name = app_manager.get_data(token)['name']

    logger.set_app(app_manager)
    logger.set_phone(phone)

    data = 'data={}&{}&{}&{}&{},' \
           'CDR(dialed_number)={},' \
           'CDR(date)={},' \
           'CDR(call_id)={},' \
           'CDR(sip_trunk_number)={},' \
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
            sip_trunk_number,
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
