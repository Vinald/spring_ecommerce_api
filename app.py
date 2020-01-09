from flask import Flask, request, jsonify
from asterisk.ami import AMIClient
from asterisk.ami import AMIClientAdapter


app = Flask(__name__)


client = AMIClient(address='127.0.0.1', port=5038)
client.login(username='norman', secret='1234')


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
        Exten='300',
        Priority=1,
        Context='from-internal',
        CallerID='Call For Life Uganda',
        Variable='data={}&{}&{}'.format(call_id, phone, flow),
        ActionID=call_id,
        _callback=callback_response
    )

    return jsonify({'status': 'IN_PROGRESS'})


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
