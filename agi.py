#!/usr/bin/env python3

import requests
import asterisk.agi
from bs4 import BeautifulSoup
import logging
from configparser import ConfigParser
import os
import time
from src.Audio import Audio

# Initialize the asterisk AGI
agi = asterisk.agi.AGI()

# Get script directory
working_dir = os.path.dirname(os.path.realpath(__file__))

# Initialize configuration parser
config = ConfigParser()

# Read config file
config.read(working_dir + '/config.ini')

# Grab the motech section from the config file
motech_config = config['motech']

# Get the host value for motech for example 172.17.0.1
motech_hostname = motech_config['host']

# Get the location that the audio files are stored locally on your machine
local_audio_file_path = motech_config['audio_path']

local_audio_path = Audio(local_audio_file_path)

# Deal with log settings like log level, log file, format etc
logging.basicConfig(
    level=logging.INFO,    
    format='[%(asctime)s] %(levelname)s: %(message)s',
    filename=working_dir + '/app.log',
    filemode='w',
)


# Set maximum call time to 5 minutes
agi.set_autohangup(300)

# Define the starting voice URL of the application
base_link = 'http://{}/motech-platform-server/module/callflows/in/voxeo/flows/MainFlow.vxml?phone='.format(motech_hostname)

# Capture the incoming caller number and save it in the phone variable
phone = str(agi.env['agi_callerid'])

# Define the variable to store info for outbound calls
data = str(agi.get_variable('data'))


# Define a custom log function
def log_info(message):
    logging.info('[Number: {}]: {}'.format(phone, message))


# Start logging
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
    phone = phone.strip()[1:]
    log_info('Patient number: ' + phone)
    log_info('Call Direction: INCOMING')
    link = base_link + phone
    log_info('Starting Voice URL: {}'.format(link))


def process_xml(next_link: str):
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
        prompts = block.find_all('prompt', recursive=False)

        if len(prompts) > 0:
            for prompt in prompts:
                if prompt is not None and prompt.find('audio') is not None:
                    audio = prompt.find('audio').attrs['src']
                    audio_file = local_audio_path.gen_audio_file(audio)
                    log_info('Streaming Audio: {}'.format(audio))
                    agi.stream_file(audio)

        has_attributes = len(block.attrs) > 0

        if has_attributes:
            name = block.attrs['name']
            if name is not None and name == 'submit':
                goto = block.find('goto')
                next_link = goto.attrs['next']
                log_info('Processing next link: {}'.format(next_link))
                return process_xml(next_link)

        # Fix me
        # logging.fatal('Next link not found in blocks. exiting')
        # agi.hangup()


def process_audio_dialogue(form, input_attempts=0, no_match_attempts=0):
    field = form.find('field')
    filled = form.find('filled')
    items = form.find_all('item')
    grammar = form.find('grammar')
    field_name = field.attrs['name']
    filled_name = filled.find('submit').attrs['namelist']
    filled_next_link = filled.find('submit').attrs['next']

    timeout = 1000
    default_timeout = 1000

    no_input_element = field.find_all('noinput', recursive=False)
    no_match_element = field.find_all('nomatch', recursive=False)

    log_info('Field name: {}'.format(field_name))
    log_info('Filled name: {}'.format(filled_name))
    log_info('Next Link: {}'.format(filled_next_link))

    prompts = field.find_all('prompt', recursive=False)

    input_digit = ''

    for prompt in prompts:
        if prompt is not None and prompt.find('audio') is not None:
            audio = prompt.find('audio').attrs['src']
            audio = local_audio_path.gen_audio_file(audio)
            timeout = prompt.attrs['timeout']

            if len(timeout) > 0 and timeout is not None:
                timeout = int(float(timeout[:-1]) * 1000)

            if filled_name.find('pin') >= 0:
                log_info('Streaming entering pin music: {}'.format(audio))
                input_digit = agi.get_data(audio, timeout, 4)

                if len(input_digit) == 4:
                    break
            else:
                log_info('Streaming dialogue music: {}'.format(audio))
                input_digit = agi.get_data(audio, default_timeout, 1)
                if len(input_digit) > 0:
                    break

    choices = []

    if len(input_digit) == 0:
        input_digit = agi.wait_for_digit(timeout)

    if len(input_digit) == 0:
        attempts = input_attempts + 1
        no_input = no_input_and_no_match(no_input_element)
        return process_no_input_and_no_match(no_input, attempts, no_match_attempts, form)

    if grammar is not None and items is not None:
        for item in items:
            choices.append(int(item.get_text()))

        if int(input_digit) in choices:
            log_info('User entered: {} as their choice'.format(input_digit))
            return process_xml(filled_next_link + '&' + filled_name + '=' + str(input_digit))

        time.sleep(5)

        # Handle Invalid in put here
        log_info('User entered an invalid choice: {}'.format(input_digit))
        match_attempts = no_match_attempts + 1
        no_match = no_input_and_no_match(no_match_element)
        return process_no_input_and_no_match(no_match, input_attempts, match_attempts, form, False)

    if field_name == filled_name:
        next_link = filled_next_link + '&' + filled_name + '=' + str(input_digit)
        return process_xml(next_link)


def no_input_and_no_match(elements):
    for element in elements:
        if element is not None and element.attrs['count'] is not None:
            submit = element.find('submit')
            prompt = element.find('prompt', recursive=False)
            timeout = 0
            next_link = None
            audio_file = None

            if submit is not None and submit.attrs['next'] is not None:
                next_link = submit.attrs['next']

            if prompt is not None:
                audio = prompt.find('audio', recursive=False)
                timeout = int(float(prompt.attrs['timeout'][:-1]) * 1000)
                audio_file = audio.attrs['src']

            return {
                "audio": audio_file,
                "count": int(element.attrs['count']),
                "timeout": timeout,
                "next_link": next_link,
            }

    return None


def process_no_input_and_no_match(element, input_attempts, no_match_attempts, form, no_input=True):
    count = element['count']
    audio = element['audio']
    next_link = str(element['next_link'])

    if input_attempts >= count or no_match_attempts >= count:
        if audio is not None:
            agi.stream_file(audio)
        if next_link is not None:
            if no_input:
                return process_xml(next_link + '&gNoInputEventCount=1')
            return process_xml(next_link + '&gNoMatchEventCount=1')

    return process_audio_dialogue(form, input_attempts, no_match_attempts)


process_xml(link)
