import datetime
import json
import os
import pathlib
import threading
from redis import Redis
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.api.Applications import Applications
from app.api.Apps import Apps
from app.api.Login import Login
from app.api.Logs import Logs
from app.api.Profile import Profile
from app.api.ReportTypes import ReportTypes
from app.api.Reports import Reports
from app.api.Users import Users
from app.asterisk.AsteriskARI import AsteriskARI
from app.asterisk.AsteriskEventsHandler import AsteriskEventsHandler
from app.manager.CDRManager import CDRManager
from app.manager.CacheManager import CacheManager
from app.manager.TrunkManager import TrunkManager
from app.utilities.Config import Config
from app.utilities.Database import Database
from app.utilities.Logger import Logger
from app.utilities.Mailer import Mailer

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
engine = create_engine(
    db_link.format(db_user, db_pass, db_host, db_port, db_name),
    pool_pre_ping=True,
    pool_timeout=20,
    pool_recycle=900,
)
Session = sessionmaker(bind=engine)

asterisk_ari_config = config.get_section_content('asterisk-ari')

trunk_list = config.get_section_content('sip-trunks')
routed_numbers = config.get_section_content('routed-numbers')

roles = config.get_section_content('roles')

config.set_section('core')
log_vxml = config.get_bool('log-vxml')
log_level = config.get('log-level')
audio_path = config.get('audio-path')
max_channels = config.get_int('max-channels')
max_call_time = config.get_int('max-call-time-in-seconds')
use_sip_trunks = config.get_bool('use-sip-trunks')
dates_audio_path = config.get('dates-audio-path')
secret_key = config.get('secret-key')

# Set log level
logger.set_level(log_level)

database = Database(config)
app_manager = Apps(database, logger)

# Set up mailer
mailer = Mailer(config.set_section('email-server'), logger)

# Set up Redis
config.set_section('redis')
redis_host = config.get('host')
redis_port = config.get_int('port')
cache = Redis(host=redis_host, port=redis_port)
cache_manager = CacheManager(config, logger)

cdr_manager = CDRManager(cache_manager, database, logger)

asterisk_events_handler = AsteriskEventsHandler(logger, cache, cdr_manager)

asterisk_ari = AsteriskARI(asterisk_ari_config, logger, max_channels)

peer_manager = TrunkManager(asterisk_ari, cache_manager, trunk_list, routed_numbers)

# Connect to Asterisk AMI in a background thread so a down Asterisk
# does not prevent the Flask app from starting.
adapter = None
_ami_lock = threading.Lock()


def _connect_ami():
    global adapter
    try:
        from asterisk.ami import AMIClientAdapter, AMIClient
        client = AMIClient(address=ami_host, port=ami_port)
        client.login(username=ami_user, secret=ami_pass)
        with _ami_lock:
            adapter = AMIClientAdapter(client)
        logger.log_info("AMI connection established")
    except Exception as e:
        logger.log_error("AMI connection failed (will retry on next call): {}".format(str(e)))


threading.Thread(target=_connect_ami, daemon=True).start()

cron_dir = '/etc/cron.d'
bin_dir = os.path.join(project_dir, 'bin')

apps_api = Applications(logger)
users_api = Users(logger, mailer)
login_api = Login(logger)
reports_api = Reports(bin_dir, cron_dir, database.get_conn(), logger)
report_types_api = ReportTypes(logger)
logs_api = Logs(os.path.join(project_dir, 'logs'))
profile_api = Profile(logger)


def initialize_log():
    logger.set_app()
    logger.set_phone()


def date_object_converter(o):
    if isinstance(o, datetime.datetime):
        return o.__str__()


def initiate_call(call_data):
    global adapter
    with _ami_lock:
        if adapter is None:
            logger.log_error("AMI not connected — cannot initiate call")
            return

    flow = call_data['flow']
    phone = call_data['phone']
    token = call_data['token']
    call_id = call_data['call_id']
    app_data = call_data['app-data']
    external_id = call_data['external_id']
    status_link = app_data['status_url']

    peer = ""
    channel = 'SIP/{}'.format(phone)
    caller_id = app_data['caller_id']

    if use_sip_trunks and len(trunk_list) > 0:
        outbound_call_details = peer_manager.construct_channel_and_caller_id(phone, caller_id)
        peer = outbound_call_details['peer']
        channel = outbound_call_details['channel']
        caller_id = outbound_call_details['caller-id']

    logger.set_app(app_data['name'])
    logger.set_phone(phone)

    if "+" not in caller_id:
        caller_id = "+{}".format(caller_id)

    with _ami_lock:
        adapter.Originate(
            Channel=channel,
            Exten='100',
            Priority=1,
            Context='ivr',
            CallerID="{} <{}>".format(caller_id, caller_id),
            Variable='data={}&{}&{}&{}'.format(phone, token, call_id, flow),
            ActionID=call_id,
            Timeout=40000,
            Async=True
        )

    cdr_data = {
        "app_name": app_data["name"],
        "creation_date": datetime.datetime.now(),
        "token": app_data['token'],
        "peer": peer,
        "caller_id": caller_id,
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
