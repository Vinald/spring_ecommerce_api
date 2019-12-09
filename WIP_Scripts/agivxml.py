#! /usr/bin/env python

import sys
import re
import time
import elementpath
from xml.etree import ElementTree as et
import lxml.etree as el
import os
import re
from xml.dom import minidom
from bs4 import BeautifulSoup as bs
import agitest as asterisk


###################################################
### FUNCTIONS TO INTERACT WITH MOTECH
###################################################

#This function cleans the environment that may contain previous meta files
def clean_env():
    os.system("cd /home/asteriskuser/pyfiles")
    os.system("rm -f *Main*")
    os.system("rm -f *?_*")


#Uses BeautifulSoup to parse the XML file
def parse_file(vxml_link):    
    root = el.parse(vxml_link)
    parsed_file = (el.tostring(root))
    asterisk.agi.verbose("The following Link has been succesfully parsed: %s" % vxml_link)
    return(parsed_file)
    

#Find the <block> tag in the code
def find_block(parsed_xml_file):
    x = (parsed_xml_file.find_all("block"))
    for tag in (parsed_xml_file.find_all(re.compile("goto"))):
        t =  tag.attrs

    if t is not None:
        next = (t['next'])
        return (next)


#Find the <audio> tags in the code
def find_audio(parsed_xml_file):
    x = (parsed_xml_file.find_all("audio"))
    for tag in x:
        t = tag.attrs

    if t is not None:
        audio = (t['src'])
        audio_file = str(audio).split("en/")[-1]

    return(audio_file)




#########################################
#####      Call Flows
#########################################



test_link = "http://192.168.88.251/motech-platform-server/module/callflows/in/voxeo/flows/MainFlow.vxml?phone=256750046950"

asterisk.agi.verbose("STARTING VXML FILE PROCESSING FOR INBOUND CALL")

clean_env()
x =parse_file(test_link)

asterisk.agi.say_number(1)






