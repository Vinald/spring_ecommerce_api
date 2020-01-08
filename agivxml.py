#! /usr/bin/env python

# Be sure to have all this libraries on your machine before executing this code.

import requests
import asterisk.agi
from bs4 import BeautifulSoup
import logging


logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    filename='/home/asteriskuser/pyfiles/app.log', # This "app.log" file is created automatically, just specify the correct home path to point to.
    filemode='w',
)

agi = asterisk.agi.AGI()

# Set maximum call time to 5 minutes
agi.set_autohangup(600)

# test_link = "http://192.168.88.222/motech-platform-server/module/callflows/in/voxeo/flows/MainFlow.vxml?phone=256750046950"

#The IP should point to where your MOTECH Machine.
base_link = 'http://192.168.88.222/motech-platform-server/module/callflows/in/voxeo/flows/MainFlow.vxml?phone='

phone = str(agi.env['agi_callerid'])


# This variable represents the call number if its an inbound call and the Outgoining call parameters
# if its an outgoining call.
data = str(agi.get_variable('data'))



def log_info(message):
    logging.info('[Number: {}]: {}'.format(phone, message))


log_info('Starting call')


if data is not None and len(data) > 0:
    # Outgoing Call Flow 
    data = data.split('&')
    phone = data[1]
    callId = data[0]
    jumpTo = data[2]

    log_info('Call ID: ' + callId)
    log_info('Patient number: ' + phone)
    log_info('Call Direction: OUTGOING')

    link = "{}{}&callId={}&jumpTo={}".format(base_link, phone, callId, jumpTo)
    log_info('Starting Voice URL: {}'.format(link))
else:
    # Incoming Call Flow
    log_info('Patient number: ' + phone)
    log_info('Call Direction: INCOMING')
    link = base_link + phone
    log_info('Starting Voice URL: {}'.format(link))


def process_xml(next_link):
    doc = BeautifulSoup(requests.get(next_link).content, "xml")
    doc.get_text()
    form = doc.find('form')
    field = doc.find('field')
    filled = doc.find('filled')
    blocks = doc.find_all('block')
    field_name = field.attrs['name']

    if field is not None and field_name is not None and field_name == 'finishedHearing':
        log_info('Processing uninterrupted hearing')
        return process_finished_hearing(blocks)

    if field is not None and len(filled) > 0:
        log_info('Starting Audio Dialogue')
        return process_audio_dialogue(form)


def process_finished_hearing(blocks):
    for index in range(len(blocks)):
        block = blocks[index]
        prompts = block.find_all('prompt')

        if len(prompts) > 0:
            for prompt in prompts:
                if prompt is not None and prompt.find('audio') is not None:
                    audio = prompt.find('audio').attrs['src']
                    log_info('Streaming Audio: {}'.format(play_audio_locally(audio)))
                    agi.stream_file(play_audio_locally(audio))
                    # agi.stream_file(audio)

        has_attributes = len(block.attrs) > 0

        if has_attributes:
            name = block.attrs['name']
            if name is not None and name == 'submit':
                goto = block.find('goto')
                next_link = goto.attrs['next']
                log_info('Processing next link: {}'.format(next_link))
                return process_xml(next_link)

        # logging.fatal('Next link not found in blocks. exiting')
        # agi.hangup()


def process_audio_dialogue(form):
    field = form.find('field')
    filled = form.find('filled')
    items = form.find_all('item')
    grammar = form.find('grammar')
    field_name = field.attrs['name']
    filled_name = filled.find('submit').attrs['namelist']
    filled_next_link = filled.find('submit').attrs['next']

    log_info('Field name: {}'.format(field_name))
    log_info('Filled name: {}'.format(filled_name))
    log_info('Next Link: {}'.format(filled_next_link))

    prompts = field.find_all('prompt')

    input_digit = ''

    for prompt in prompts:
        if prompt is not None and prompt.find('audio') is not None:
            audio = prompt.find('audio').attrs['src']
            timeout = prompt.attrs['timeout']

            if len(timeout) > 0 and timeout is not None:
                timeout = int(float(timeout[:-1]) * 200)
            else:
                timeout = 10000

            if filled_name.find('pin') >= 0:
                log_info('Streaming entering pin music: {}'.format(play_audio_locally(audio)))
                input_digit = agi.get_data(play_audio_locally(audio), timeout, 4)
                # input_digit = agi.get_data(audio, timeout, 4)
                # input_digit = '1234'
                if len(input_digit) == 4:                    
                    break
            else:
                log_info('Streaming dialogue music: {}'.format(play_audio_locally(audio)))
                input_digit = agi.get_data(play_audio_locally(audio), timeout, 1)
                # input_digit = agi.get_data(audio, timeout, 1)
                if len(input_digit) > 0:
                    break

    choices = []

    if grammar is not None and items is not None:
        for item in items:
            choices.append(int(item.get_text()))

        if int(input_digit) in choices:
            log_info('User entered: {} as their choice'.format(input_digit))
            return process_xml(filled_next_link + '&' + filled_name + '=' + str(input_digit))

        # Handle Invalid in put here
        log_info('User entered an invalid choice: {}'.format(input_digit))
        log_info('Hanging up')
        agi.hangup()

    if field_name == filled_name:        
        next_link = filled_next_link + '&' + filled_name + '=' + str(input_digit)
        agi.verbose(next_link)
        return process_xml(next_link)


# This function is intended to take the audio link, strip out the file name for the file to be played and 
# return the local file path to the same file, for streaming.
def play_audio_locally(audio_link):
    file = str(audio_link).split("/audio/en/")[-1]
    path = ("http://0.0.0.0:8001/en/" + str(file))
    return path


def handle_no_input(form):
    pass


def handle_no_match(form):
    pass


process_xml(link)
