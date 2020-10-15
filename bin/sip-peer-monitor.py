import datetime
import os
import sys

sys.path.append('..')
from app.core import database, logger, config, asterisk_ari, cache_manager
from app.utilities.Email import Email

connection = database.get_conn()
cursor = database.get_cursor()

failing_trunk = 'failing-trunk'
offline_cache_key = 'peers-offline'

table_name = 'cdr'


def send_mail(msg_body, subject):
    config.set_section('email-recipients')
    try:
        mail_send_to = list(config.get('to'))
    except Exception as e:
        mail_send_to = None
        logger.log_error("SIP Trunk monitor email TO: {}".format(str(e)))

    try:
        mail_send_cc = list(config.get('cc'))
    except Exception as e:
        mail_send_cc = None
        logger.log_error("SIP Trunk monitor email CC: {}".format(str(e)))

    email = Email(mail_send_to, subject, msg_body, mail_send_cc)
    email.send_email()


if not asterisk_ari.all_peers_are_offline() and cache_manager.cache_exists(offline_cache_key):
    cache_manager.delete(offline_cache_key)

if asterisk_ari.all_peers_are_offline():
    if not cache_manager.cache_exists(offline_cache_key):
        cache_manager.save(offline_cache_key, 'true', 18000)
        msg = """Hello,
All peers have gone offline. Please check asterisk ASAP.

Regards,
Academy IS Team.
"""
        send_mail(msg, "CRITICAL, PEERS STATUS")


# Query used to select the last trunk status entry from the database
sql = "SELECT call_state, peer FROM `{}` ORDER BY `creation_date` DESC LIMIT 20".format(table_name)
cursor.execute(sql)
results = cursor.fetchall()

peers = []
call_states = []

for result in results:
    peers.append(result['peer'])
    call_states.append(result['call_state'])

if "FAILED" in call_states and (len(set(call_states)) == 1) and (len(set(peers)) == 1):
    if not cache_manager.cache_exists(failing_trunk):
        peer = peers[0]
        cache_manager.save(failing_trunk, peer, 18000)
        msg = """Hello,
Calls are failing on peer: {}. Please check asterisk ASAP.

Regards,
Academy IS Team.
"""
        send_mail(msg.format(peer), "INFO, {} PEER Call Failure".format(peer))


date_now = datetime.datetime.now().strftime('%b-%d-%Y %X')
update_cron_log = "echo {}: sip-peer-monitor.py has ran successfully >> {}"
os.system(update_cron_log.format(date_now, os.path.join(logger.get_log_dir(), 'cron-jobs.log')))

connection.close()
exit(0)
