#! /usr/bin/env python

from bs4 import BeautifulSoup 
import agitest as asterisk
import requests


###################################################
### FUNCTIONS TO INTERACT WITH MOTECH
###################################################

test_link = "http://192.168.88.226/motech-platform-server/module/callflows/in/voxeo/flows/MainFlow.vxml?phone=256750046950"




def process_xml(next_link):
    doc = BeautifulSoup(requests.get(next_link).content, "xml")
    doc.get_text()
    form = doc.find('form')
    field = doc.find('field')
    filled = doc.find('filled')
    blocks = doc.find_all('block')
    field_name = field.attrs['name']

    if field is not None and field_name is not None and field_name == 'finishedHearing':
        return process_finished_hearing(blocks)

    if len(field) > 0 and len(filled) > 0:
        return process_audio_dialogue(form)


def process_finished_hearing(blocks):
    for index in range(len(blocks)):
        block = blocks[index]
        prompts = block.find_all('prompt')

        if len(prompts) > 0:
            for prompt in prompts:
                if prompt is not None and prompt.find('audio') is not None:
                    audio = prompt.find('audio').attrs['src']
                    asterisk.agi.stream_file(audio)

        has_attributes = len(block.attrs) > 0

        if has_attributes:
            name = block.attrs['name']
            if name is not None and name == 'submit':
                goto = block.find('goto')
                next_link = goto.attrs['next']
                return process_xml(next_link)


def process_audio_dialogue(form):
    escape_digits = '1234567890*#'
    field = form.find('field')
    filled = form.find('filled')
    items = form.find_all('item')
    grammar = form.find('grammar')
    field_name = field.attrs['name']
    filled_name = filled.find('submit').attrs['namelist']
    filled_next_link = filled.find('submit').attrs['next']

    prompts = field.find_all('prompt')

    input_digit = 0

    for prompt in prompts:
        if prompt is not None and prompt.find('audio') is not None:
            audio = prompt.find('audio').attrs['src']
            timeout = prompt.attrs['timeout']

            if len(timeout) > 0 and timeout is not None:
                timeout = int(float(timeout[:-1]) * 100)
            else:
                timeout = 10000

            if filled_name.find('pin') >= 0:
                input_digit = asterisk.agi.get_data(audio, timeout, 4)
                if len(input_digit) == 4:
                    break
            else:
                input_digit = asterisk.agi.get_data(audio, timeout, 4)
                if len(input_digit) > 0:
                    asterisk.agi.verbose(input_digit, 3)
                    break

    choices = []

    if grammar is not None and items is not None:
        for item in items:
            choices.append(int(item.get_text()))
        
        return process_xml(filled_next_link + '&' + filled_name + '=' + input_digit)
      
    if field_name == filled_name:
        # pin = '1234'
        next_link = filled_next_link + '&' + filled_name + '=' + input_digit
        return process_xml(next_link)


process_xml(test_link)
