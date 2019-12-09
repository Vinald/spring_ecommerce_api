from lxml import etree
import os
import re
# from xml.dom import minidom
from bs4 import BeautifulSoup as bs

link = "http://192.168.88.251/motech-platform-server/module/callflows/in/voxeo/flows/MainFlow.vxml?phone=256750046950"


def parse_file(link):
    root = etree.parse(link)
    var = (etree.tostring(root))    
    return (var)


def go_to_pin(parsed_file):
    parsed_xml_file = bs(''.join(parsed_file), features="lxml")    
    for tag in (parsed_xml_file.find_all(re.compile("goto"))):
        t =  tag.attrs

    if t is not None:
        next = (t['next'])
        print (next)
            
    welcome_xml = parse_file(next)
    print(welcome_xml)


#########################
## CODE BODY
#########################


parsed_file = parse_file(link)
go_to_pin(parsed_file)
