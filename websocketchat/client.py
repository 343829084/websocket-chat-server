#!/bin/env python3
from .crypto import *
from time import time
from .forms import *
import logging
# from .chat_server import str2hex
import json

class Client:
    def __init__(self, websocket, send_limiter, room_name=None, name='NaN'):
        self.name = name
        self.id = None
        self.websocket = websocket
        self.room_name = room_name
        self.send_limiter = send_limiter
        self.last_activity = time()
        self.time_connected = time()
        self.logged_in = False
        self.key = None
        self.iv = None
        self.verification_code = None
        self.email = None

    def address(self):
        return '{}({}:{})'.format(self.name, self.websocket.address[0], self.websocket.address[1])

    def send(self, request_type, text, enc=False, timeout=-1):
        if type(text) == str:
            _text = text
        elif type(text) == dict or type(text) == list:
            _text = json.JSONEncoder().encode(text)
        else:
            raise ValueError

        if enc:
            _text = '1' + encrypt((request_type + _text).encode(), self.key, self.iv).hex()
        else:
            _text = '0' + request_type + _text

        # self.send_limiter.start_thread(
        #     target=self.websocket.send_text,
        #     args=(_text, timeout)
        # )
        return self.websocket.send_text(_text, timeout)
        print('Sending: ', _text)
        # print('_text')
        # logging.debug('{}: Sent message: {}'.format(self.address(), _text))

    # def send_message(self, message, timeout=-1):
    #     self.send(message.make_json(), timeout)
    #
    # def send_mass_message(self, messages, timeout=-1):
    #     packed_messages = list(range(len(messages)))
    #     for i in range(len(messages)):
    #         packed_messages[i] = messages[i].make_json()
    #     self.send({
    #         'type': server_forms['MASS_MESSAGE'],
    #         'messages': packed_messages
    #     }, timeout)
    def logout(self):
        self.logged_in = False
        self.name = 'NaN'
        self.email = None
        self.verification_code = None
        self.id = None

    def send_key_iv(self, timeout=-1):
        self.key, self.iv = generate_key_and_iv()

        # server_message = "0y['key', 'iv']"
        self.send(server_message_ids['key_iv']['id'], [self.key.hex(), self.iv.hex()])

    def change_room(self, msg_id, room_name, messages, timeout=-1):
        self.room_name = room_name
        self.send(request_ids['enter_room'], [])


    # def login(self, accept=True, timeout=-1):
    #     self.send({
    #         'type': client_requests['LOGIN'],
    #         'accepted': accept,
    #         'name': self.name
    #     }, timeout)
    #     if accept:
    #         self.logged_in = True
    #         logging.debug('{}: login success'.format(self.websocket.address))
    #     else:
    #         logging.debug('{}: login failed'.format(self.websocket.address))
    #
    # def register_email(self, accept, timeout=-1):
    #     self.send({
    #         'type': server_forms['REGISTER_EMAIL'],
    #         'accepted': accept
    #     }, timeout)
    #
    # def register_username(self, accept, timeout=-1):
    #     self.send({
    #         'type': server_forms['REGISTER_USERNAME'],
    #         'accepted': accept
    #     }, timeout)
    #
    # def register_password(self, accept, timeout=-1):
    #     self.send({
    #         'type': server_forms['REGISTER_PASSWORD'],
    #         'accepted': accept
    #     }, timeout)

    # def request_responce(self, type, accept):
    #     self.send({
    #         'type': type,
    #         'accept': accept
    #     })

    # def handle_request(self, msg):
    #     if msg['type'] == client_requests['SINGLE_MESSAGE']:
    #         if self.logged_in:
    #             return_value = True
    #         else:
    #             return_value = False
    #         self.send({
    #                 'type': client_requests['SINGLE_MESSAGE'],
    #                 'accepted': return_value
    #         })
    #         return return_value
    #
    #     elif msg['type'] == client_requests['CHECK_USERNAME']:
    #         self.send({
    #                 'type': client_requests['CHECK_USERNAME'],
    #                 'available': self.db.check_existence('users', 'name', msg['name'])
    #         })
    #         return True
    #     elif msg['type'] == client_requests['CHECK_EMAIL']:
    #         self.send({
    #                 'type': client_requests['CHECK_EMAIL'],
    #                 'available': self.db.check_existence('users', 'email', msg['email'])
    #         })
    #         return True
    #     elif msg['type'] == client_requests['KEY_IV']:
    #         self.send_key()
    #         return True
    #     elif msg['type'] == client_requests['REGISTER']:
    #         email = decrypt(str2hex(msg['email']), self.key, self.iv)
    #         name = decrypt(str2hex(msg['name']), self.key, self.iv)
    #         password = decrypt(str2hex(msg['password']), self.key, self.iv)
    #
    #         email_available = not self.db.check_existence('users', 'email', email)
    #         name_available = not self.db.check_existence('users', 'name', name)
    #
    #         if email_available and name_available:
    #             self.db.insert('users', {
    #                 'name': name,
    #                 'email': email,
    #                 'password': password,
    #                 'joined': time(),
    #                 'last_online': time()
    #             })
    #             logging.debug('{}: Registered'.format(self.websocket.address))
    #             accepted = True
    #             self.logged_in = True
    #             self.name = name
    #         else:
    #             logging.debug('{}: registration denied'.format(self.websocket.address))
    #             accepted = False
    #
    #         self.send({
    #             'type': client_requests['REGISTER'],
    #             'accepted': accepted,
    #             'name': name
    #         })
    #         return True
    #     elif msg['type'] == client_requests['LOGIN']:
    #
    #         email = decrypt(str2hex(msg['email']), self.key, self.iv)
    #         password = decrypt(str2hex(msg['password']), self.key, self.iv)
    #         data = self.db.fetch('''SELECT name, password FROM users WHERE email="{}"'''.format(email))
    #         if data and data[1] == password:
    #             self.name = data[0]
    #             self.login(accept=True)
    #         else:
    #             self.login(accept=False)
    #
    #         return True
    #     elif msg['type'] == client_requests['ENTER_ROOM']:
    #         room_name = msg['name']
    #         if room_name not in self.rooms:
    #             self.load_room(room_name)
    #
    #         if self.room_name is not None:
    #             self.rooms[room_name].remove_client(client)
    #         self.room_name = room_name
    #         self.rooms[room_name].add_client(client)
    #
    #         data = self.db.fetch('''SELECT id, user, text, time FROM messages WHERE room_name="{}"'''.format(room_name), all=True)
    #         if data is not None:
    #             length = len(data)
    #         else:
    #             length = 0
    #         messages = list(range(length))
    #
    #         for i in range(length):
    #             messages[i] = {
    #                 'id': data[i][0],
    #                 'user': data[i][1],
    #                 'text': data[i][2],
    #                 'time': data[i][3]
    #             }
    #         self.send({
    #             'type': client_requests['ENTER_ROOM'],
    #             'messages': messages
    #         })
    #         return True
    #     else:
    #         return False
