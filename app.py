import sys
from io import BytesIO

import telegram
from flask import Flask, request, send_file

from fsm import TocMachine


API_TOKEN = 'Your Telegram API Token'
WEBHOOK_URL = 'Your Webhook URL'

app = Flask(__name__)
bot = telegram.Bot(token=API_TOKEN)
machine = TocMachine(
    states=[
        'init',
        'qr_year',
        'qr_month',
        'qr_result',
        'qa_board',
        'qa_push_num',
        'qa_result',
        'qw_word',
        'qw_result'
    ],
    transitions=[
        {
            'trigger': 'advance',
            'source': 'init',
            'dest': 'qr_year',
            'conditions': 'if_do_query_receipt'
        },
        {
            'trigger': 'advance',
            'source': 'qr_year',
            'dest': 'qr_month',
            'conditions': 'if_year_valid'
        },
        {
            'trigger': 'advance',
            'source': 'qr_month',
            'dest': 'qr_result',
            'conditions': 'if_month_valid'
        },
        {
            'trigger': 'advance',
            'source': 'init',
            'dest': 'qa_board',
            'conditions': 'if_do_query_article'
        },
        {
            'trigger': 'advance',
            'source': 'qa_board',
            'dest': 'qa_push_num',
            'conditions': 'if_board_valid'
        },
        {
            'trigger': 'advance',
            'source': 'qa_push_num',
            'dest': 'qa_result',
            'conditions': 'if_push_num_valid'
        },
        {
            'trigger': 'advance',
            'source': 'init',
            'dest': 'qw_word',
            'conditions': 'if_do_query_word'
        },
        {
            'trigger': 'advance',
            'source': 'qw_word',
            'dest': 'qw_result'
        },
        {
            'trigger': 'go_back',
            'source': [
                'qr_result',
                'qa_result',
                'qw_result'
            ],
            'dest': 'init'
        }
    ],
    initial='init',
    auto_transitions=False,
    show_conditions=True,
)


def _set_webhook():
    status = bot.set_webhook(WEBHOOK_URL)
    if not status:
        print('Webhook setup failed')
        sys.exit(1)
    else:
        print('Your webhook URL has been set to "{}"'.format(WEBHOOK_URL))


@app.route('/hook', methods=['POST'])
def webhook_handler():
    update = telegram.Update.de_json(request.get_json(force=True), bot)
    machine.advance(update)
    return 'ok'


@app.route('/show-fsm', methods=['GET'])
def show_fsm():
    byte_io = BytesIO()
    machine.graph.draw(byte_io, prog='dot', format='png')
    byte_io.seek(0)
    return send_file(byte_io, attachment_filename='fsm.png', mimetype='image/png')


if __name__ == "__main__":
    _set_webhook()
    app.run()
