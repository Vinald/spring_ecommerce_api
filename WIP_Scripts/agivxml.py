#! /usr/bin/env python

import elementpath
from bs4 import BeautifulSoup 
import agitest as asterisk
import requests


###################################################
### FUNCTIONS TO INTERACT WITH MOTECH
###################################################


def process_xml(next_link):
    asterisk.agi.verbose("START PROCESSING")
    doc = BeautifulSoup(requests.get(next_link).content, "xml")
    form = doc.find('form')
    field = doc.find('field')
    filled = doc.find('filled')
    blocks = doc.find_all('block')
    field_name = field.attrs['name']
    asterisk.agi.verbose("break")

    if field is not None and field_name is not None and field_name == 'finishedHearing':
        for index in range(len(blocks)):
            block = blocks[index]
            prompts = block.find_all('prompt')            
            
            for prompt in prompts:
                if prompt is not None and prompt.find('audio') is not None:
                    audio = prompt.find('audio').attrs['src']
                    asterisk.agi.verbose("AUDIO FILE IS %s" % audio)
                    asterisk.agi.stream_file(audio)                    

            has_attributes = len(block.attrs) > 0
            if has_attributes:
                name = block.attrs['name']
                if name is not None and name == 'submit':
                    goto = block.find('goto')
                    next_link = goto.attrs['next']
                    asterisk.agi.verbose("NEXT LINK IS %s" % next_link)                    
                    return process_xml(next_link)

    if len(field) > 0 and len(filled) > 0:
        return process_audio_dialogue(form)


def process_audio_dialogue(form):
    field = form.find('field')
    filled = form.find('filled')
    field_name = field.attrs['name']
    filled_name = filled.find('submit').attrs['namelist']
    filled_next_link = filled.find('submit').attrs['next']

    prompts = field.find_all('prompt')

    if field_name == filled_name == 'pin':
        asterisk.agi.verbose("ASK FOR PIN")
        pin = asterisk.get_pin()
        next_link = filled_next_link + '&' + filled_name + '=' + pin
        asterisk.agi.verbose(next_link)
        return process_xml(next_link)
    

    for prompt in prompts:
        if prompt is not None and prompt.find('audio') is not None:
            audio = prompt.find('audio').attrs['src']
            asterisk.agi.verbose("PLAYING AUDIO")
            asterisk.agi.stream_file(audio)



# #########################################
# #####      Call Flows    
# #########################################



test_link = "http://192.168.88.226/motech-platform-server/module/callflows/in/voxeo/flows/MainFlow.vxml?phone=256750046950"



process_xml(test_link)



