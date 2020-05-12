#!/usr/bin/env python3

from flask import Flask, request, redirect
from asterisk.ami import AMIClient
from asterisk.ami import AMIClientAdapter
from asterisk.ami.event import Event
import os
import time
from collections import Counter
from src.Config import Config
from src.Logger import Logger
from src.AppWebListener import AppWebListener

working_dir = os.path.dirname(os.path.realpath(__file__))

# Initiate Logger
logger = Logger(working_dir)

ami_config = Config(working_dir, logger, 'ami')
motech_config = Config(working_dir, logger, 'motech')

ami_host = ami_config.get_ami_host()
ami_user = ami_config.get_ami_user()
ami_pass = ami_config.get_ami_pass()
ami_port = ami_config.get_ami_port()
ami_trunk = ami_config.get_sip_trunk()


state = ''
status_base_link = motech_config.get_status_base_url()


app = Flask(__name__)


client = AMIClient(address=ami_host, port=ami_port)
client.login(username=ami_user, secret=ami_pass)

# Initiate Web_Listener class
app_web_listener = AppWebListener(logger, status_base_link)


def callback_response(response):
    logger.log_info(response)


dict = {}

def event_listener(event, **kwargs):
    global state

    # private_dict = {}
    if str(event.name) == 'OriginateResponse':

        ActionID = str(event.keys.get('ActionID'))
        # print(event.count("ActionID"))
        # count = 1
        # private_dict["CallID"] = [ActionID]
        #
        # while private_dict["CallID"] == ActionID:
        #     private_dict["CallID"] = [ActionID, count]
        #     count = count + 1
        channel_status_num = str(event.keys.get('Reason'))
        state = app_web_listener.channel_statuses(channel_status_num)
        my_status = app_web_listener.channel_statuses(channel_status_num)
        # if len(dict) >= 1 and list(dict.keys())[0] is not None and list(dict.keys())[0] != ActionID:
        #     dict.update({"{}: Duplicate".format(ActionID): my_status})
        # else:
        #     dict[ActionID] = my_status
        print('I passed here')
        if len(dict) >= 1 and ActionID in dict.keys():
            dict.update({"{} -- Duplicate".format(ActionID): my_status})
        else:
            print("and picked this option")
            dict.update({ActionID: my_status})
            # dict[ActionID] = my_status



        print(dict)
        print(list(dict.keys())[0])
        print(list(dict.values())[0])

    else:
        pass



    #
    # if str(event.name) == 'OriginateResponse':
    #     ActionID = str(event.keys.get('ActionID'))
    #     channel_status_num = str(event.keys.get('Reason'))
    #     my_status = app_web_listener.channel_statuses(channel_status_num)
    #
    #     dict["ID"] = ActionID
    #     dict["Count"] = count
    #     count = count + 1
    #     try:
    #         channel_status_num = str(event.keys.get('Reason'))
    #         ActionID = str(event.keys.get('ActionID'))
    #         state = app_web_listener.channel_statuses(channel_status_num)
    #         dict[ActionID] = state
    #     except Exception as e:
    #         logger.log_info('Event Listener Error : {}'.format(str(e)))
    # else:
    #     pass


@app.route('/', methods=['GET', 'POST'])
def index():
    flow = request.args.get('jumpTo')
    phone = request.args.get('phone')
    call_id = request.args.get('callId')

    logger.log_info("Call request from external app: {}".format(request.url))

    adapter = AMIClientAdapter(client)

    channel = 'SIP/' + phone

    if ami_trunk is not None and len(ami_trunk) > 0:
        channel = 'SIP/{}/+{}'.format(ami_trunk, phone)

    adapter.Originate(
        Channel=channel,
        Exten='100',
        Priority=1,
        Context='ivr',
        CallerID='Call For Life Uganda',
        Variable='data={}&{}&{}&{},CDR(dialed_number)={}'.format(call_id, phone, flow, channel, phone),
        ActionID=call_id,
        Timeout=45000,
        Async=True,
        _callback=callback_response
    )

    dict.clear()

    client.add_event_listener(event_listener)

    print("loading")
    while len(dict) == 0:
        time.sleep(0.5)
    print("this has passed")

    if call_id in dict.keys():
        print("now am getting there, and the state is: ", dict[call_id])



    # if call_id in dict.keys():
    #     print("now am getting there, and the state is: ", dict[call_id])



    # for keys in dict.keys():
    #     while call_id != keys:
    #         time.sleep(0.5)
    #     print("now am getting there, and the state is: ", dict[keys])

    complete_status_counter = int(360)


    global state
    if state != "":
        state = ""
        while state == "":
            time.sleep(0.5)
        link = app_web_listener.gen_motech_reply(call_id, channel, state, complete_status_counter)
        return redirect(link)
    else:
        while state == "":
            time.sleep(0.5)
        link = app_web_listener.gen_motech_reply(call_id, channel, state, complete_status_counter)
        return redirect(link)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
