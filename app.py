#!/usr/bin/env python3

from flask import Flask, request, jsonify
from asterisk.ami import AMIClient
from asterisk.ami import AMIClientAdapter
from configparser import ConfigParser
import os


working_dir = os.path.dirname(os.path.realpath(__file__))

config = ConfigParser()
config.read(working_dir + '/config.ini')

# Grab the ami section from the config file
ami = config['ami']

ami_host = ami['host']
ami_user = ami['user']
ami_pass = ami['pass']
ami_port = int(ami['port'])

app = Flask(__name__)


client = AMIClient(address=ami_host, port=ami_port)
client.login(username=ami_user, secret=ami_pass)


def callback_response(response):
    print(response)


@app.route('/', methods=['GET', 'POST'])
def index():
    flow = request.args.get('jumpTo')
    phone = request.args.get('phone')
    call_id = request.args.get('callId')

    adapter = AMIClientAdapter(client)

    future = adapter.Originate(
        Channel='SIP/' + phone,
        Exten='100',
        Priority=1,
        Context='ivr',
        CallerID='Call For Life Uganda',
        Variable='data={}&{}&{}'.format(call_id, phone, flow),
        ActionID=call_id,
        _callback=callback_response
    )

    return jsonify({'status': 'IN_PROGRESS'})


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
