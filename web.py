#!/usr/bin/python3
CHAT_FOLDER = 'data/rooms' # without slash at the end

import os
import time
import flask
import requests
import markupsafe

from hashlib import sha256
from datetime import datetime

app = flask.Flask(__name__, static_url_path='/')
app.secret_key = open('key.secret').read()

replacer = {
    '[SYSTEM]': '[system]',
}

def chat(room: str='root', text=None, full_write=False):
    chat_file = f'{CHAT_FOLDER}/{room.replace("/", "__").replace(".", "_")}.txt'

    if not os.path.exists(chat_file):
        open(chat_file, 'w').write('')
    
    if full_write:
        open(f'{CHAT_FOLDER}/{room}.txt', 'w').write(text)
    elif text:
        open(f'{CHAT_FOLDER}/{room}.txt', 'a').write(f'[{str(datetime.now().strftime("%m/%d/%Y %H:%M:%S:%f"))[:22]}] {text}\n')
    
    return open(f'{CHAT_FOLDER}/{room}.txt').read().split('\n')

@app.route('/')
def home():
    return flask.redirect('/@root')

@app.route('/help')
def help():
    return flask.render_template('help.html')

@app.route('/@<room>', methods=['GET', 'POST'])
def room(room):
    chat(room) # initialize the chat file
    room_file = f'{CHAT_FOLDER}/{room}.txt'

    input_text = markupsafe.escape(flask.request.form.get('message')) or ''

    for k, v in replacer.items():
        input_text = input_text.replace(k, v)
    
    if input_text == '!help':
        return flask.redirect('/help')

    if input_text == '!rooms':
        text = ''
        for room_name in os.listdir(CHAT_FOLDER):
            if room_name.endswith('.txt'):
                text += f'{room_name.replace(".txt", "")} '

        chat(room, f'[SYSTEM] Rooms: {text}')

    if input_text == '!source':
        file_hash = sha256(open('web.py').read().encode('utf-8')).hexdigest()
        chat(room, f'[SYSTEM] web.py is being send with SHA 256 hash <<{file_hash}>>')
        
        return flask.send_file('web.py')

    if input_text == '!export':
        return flask.send_file(room_file, as_attachment=True)

    if input_text.startswith('!import '):
        chat(room, requests.get(input_text.split('!import ')[1]).text, full_write=True)

    if input_text.startswith('!room '):
        return flask.redirect(f'/@{input_text.split()[1]}')

    if input_text and str(input_text) != 'None':
        chat(room, input_text)

    if input_text == '!clear':
        open(room_file, 'w').write('')
        chat(room, '[SYSTEM] Cleared whole chat.')

    if 'title' in input_text.lower() and 'google' in input_text.lower():
        chat(room, '[SYSTEM] [AI] The tab\'s title is "Google" for security purposes: other programs won\'t know you\'re using Plasma.')

    if input_text == '!info':
        chat(room, '[SYSTEM] Messages: ' + str(len(chat())))

    if input_text.startswith('!delete '):
        new_history = []
        history = chat()

        for line in history:
            if not input_text.split('!delete ')[1] in line:
                new_history.append(line)

        open(room_file, 'w').write('\n'.join(new_history))
        chat(room, '[SYSTEM] Deleted message(s).')

    return flask.render_template('index.html', messages=chat(room), room=room)

app.run(debug=True, port=7777)
