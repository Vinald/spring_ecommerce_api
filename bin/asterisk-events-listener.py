import sys
import time
import requests

sys.path.append('..')
from app.core import client

events_link = "http://127.0.0.1:5000/ivr/events"


def event_listener(event, **kwargs):
    if event.name == 'OriginateResponse':
        link = "{}?name={}&status={}&call-id={}&unique-id={}"
        status = event.keys.get('Reason')
        call_id = event.keys.get('ActionID')
        unique_id = event.keys.get('Uniqueid')
        requests.get(link.format(events_link, event.name, status, call_id, unique_id))
    if event.name == 'Hangup':
        link = "{}?name={}&unique-id={}&channel={}"
        channel = event.keys.get('Channel')
        unique_id = event.keys.get('Uniqueid')
        requests.get(link.format(events_link, event.name, unique_id, channel))


client.add_event_listener(event_listener)

while True:
    client.send(b'')
    time.sleep(1)
