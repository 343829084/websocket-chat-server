#!/bin/env python3

import ewebsockets
from ewebsockets import Frame, OpCode
from time import time
import maxthreads
from .forms import *
import logging
from .chat_room import *
from .database import *
from .client import Client
from .crypto import *
import random, string
from .email_functions import *


def str2hex(string):
    return ewebsockets.int2bytes(int(string, 16), int(len(string)/2))


def random_str(n):
    return ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(n))


class Chat:
    def __init__(self,
                 max_send_threads=10,
                 send_timeout=2):

        self.server = ewebsockets.Websocket(
            handle_new_connection=self.handle_new_connection,
            handle_websocket_frame=self.handle_incoming_frame,
            on_client_open=self.on_client_open,
            on_client_close=self.on_client_close,
            esockets_kwargs= {
                'port': 25565,
                # 'host': '192.168.1.3'
            }
        )
        self.rooms = {}
        self.db = ChatDb()
        self.send_threads_limiter = maxthreads.MaxThreads(max_send_threads)
        self.send_timeout = send_timeout
        self.clients = {}

    def start(self):
        self.server.start()

    def stop(self):
        self.server.stop()

    def handle_request(self, client, msg):
        logging.debug('New request of type {} ({})'.format(msg['type'],
                                                           list(client_requests.keys())[list(client_requests.values()).index(msg['type'])]))
        if 'type' not in msg:
            logging.debug("{}: Received a request that doesn't contain a type".format(client.websocket.address))
            return False

        if msg['type'] == client_requests['SINGLE_MESSAGE']:
            if client.logged_in:
                t = time()
                msg_id = self.db.insert('messages', {
                    'user': client.name,
                    'text': msg['text'],
                    'room_name': client.room_name,
                    'show': 1,
                    'time': t
                })
                self.rooms[client.room_name].broadcast_message(client.name, msg['text'], t, msg_id)
                return_value = True
            else:
                return_value = False

            client.send({
                    'type': client_requests['SINGLE_MESSAGE'],
                    'accepted': return_value
            })
            return return_value

        elif msg['type'] == client_requests['CHECK_USERNAME']:
            client.send({
                    'type': client_requests['CHECK_USERNAME'],
                    'available': self.db.check_existence('users', 'name', msg['name'])
            })
            return True
        elif msg['type'] == client_requests['CHECK_EMAIL']:
            client.send({
                    'type': client_requests['CHECK_EMAIL'],
                    'available': self.db.check_existence('users', 'email', msg['email'])
            })
            return True
        elif msg['type'] == client_requests['KEY_IV']:
            client.send_key()
            return True
        elif msg['type'] == client_requests['REGISTER']:
            email = decrypt(str2hex(msg['email']), client.key, client.iv)
            name = decrypt(str2hex(msg['name']), client.key, client.iv).capitalize()
            password = decrypt(str2hex(msg['password']), client.key, client.iv)

            email_available = not self.db.check_existence('users', 'email', email)
            name_available = not self.db.check_existence('users', 'name', name)

            if email_available and name_available:
                logging.debug('{}: Register requested'.format(client.websocket.address))
                client.name = name
                client.verification_code = random_str(5)
                client.register_items = [email, name, password]
                send_email(email, 'Chat verification code', client.verification_code)
                client.send({
                    'type': client_requests['REGISTER'],
                    'accepted': True
                })
                # client.logged_in = True
            else:
                ad = ''
                if not email_available:
                    ad += 'email exists '
                if not name_available:
                    ad += 'name exists'

                logging.debug('{}: registration denied ({})'.format(client.websocket.address, ad))
                client.send({
                    'type': client_requests['REGISTER'],
                    'accepted': False,
                    'email': email_available,
                    'name': name_available
                })

            return True
        elif msg['type'] == client_requests['VERIFY']:
            if msg['code'] == client.verification_code:
                accepted = True
                id = self.db.insert('users', {
                    'email': client.register_items[0],
                    'name': client.register_items[1],
                    'password': client.register_items[2],
                    'joined': time(),
                    'last_online': time(),
                    'tokens': '[]'
                })
                client.id = id
                client.logged_in = True
            else:
                accepted = False

            client.send({
                'type': client_requests['VERIFY'],
                'accepted': accepted,
                'name': client.name
            })

        elif msg['type'] == client_requests['LOGIN']:
            response = {'type': client_requests['LOGIN']}
            email = decrypt(str2hex(msg['email']), client.key, client.iv)
            password = decrypt(str2hex(msg['password']), client.key, client.iv)

            data = self.db.fetch('''SELECT id, name, password, tokens FROM users WHERE email="{}"'''.format(email))
            if data and data[2] == password:
                response['accepted'] = True
                client.name = data[1]
                client.id = data[0]
                if msg['request_token'] == True:
                    new_token = random_str(64)
                    response['token'] = encrypt(new_token.encode(), client.key, client.iv).hex()
                    tokens = json.JSONDecoder().decode(data[3])
                    tokens.append(new_token)
                    if len(tokens) > 10:
                        tokens.pop(0)
                    print('TOKENS', tokens)
                    print('JSON', json.JSONEncoder().encode(tokens))
                    self.db.execute("UPDATE users SET tokens=? WHERE Id=?",
                                    (json.JSONEncoder().encode(tokens),
                                     client.id))
            else:
                response['accepted'] = False

            client.send(response)

            return True
        elif msg['type'] == client_requests['AUTO_LOGIN']:
            response = {'type': client_requests['AUTO_LOGIN']}
            email = decrypt(str2hex(msg['email']), client.key, client.iv)
            token = msg['token']
            data = self.db.fetch('''SELECT id, name, tokens FROM users WHERE email="{}"'''.format(email))
            tokens = json.JSONDecoder().decode(data[2])
            if token in tokens:
                response['accepted'] = True
                client.name = data[1]
                client.id = data[0]
                client.logged_in = True
                new_token = random_str(64)
                tokens[tokens.index(token)] = new_token
                response['token'] = encrypt(new_token.encode(), client.key, client.iv).hex()
                self.db.execute('''UPDATE users SET tokens = ? WHERE id = ?;''',
                                (json.JSONEncoder().encode(tokens),
                                 client.id))
            else:
                response['accepted'] = False

            client.send(response)
            return True

        elif msg['type'] == client_requests['LOGOUT']:
            client.name = 'temporary_name'
            client.logged_in = False
            client.send({
                'type': client_requests['LOGOUT']
            })
            return True

        elif msg['type'] == client_requests['ENTER_ROOM']:
            room_name = msg['name']
            if room_name not in self.rooms:
                self.load_room(room_name)

            if client.room_name is not None:
                self.rooms[client.room_name].remove_client(client)

            client.room_name = room_name
            self.rooms[room_name].add_client(client)

            data = self.db.fetch(
                '''SELECT id, user, text, time FROM messages WHERE room_name = "{}" AND id > {}'''.format(
                    room_name, msg['last_message']), all=True)

            if data is not None:
                length = len(data)
            else:
                length = 0
            messages = list(range(length))

            for i in range(length):
                messages[i] = {
                    'id': data[i][0],
                    'user': data[i][1],
                    'text': data[i][2],
                    'time': data[i][3],
                }
            client.send({
                'type': client_requests['ENTER_ROOM'],
                'room': room_name,
                'messages': messages
            })
            logging.debug('{} entered room {}'.format(client.name, room_name))
            return True
        else:
            return False

    def load_room(self, name):
        data = self.db.fetch('''SELECT id, name FROM rooms where name="{}"'''.format(name))
        if data is None:
            room_id = self.db.insert('rooms', {
                'name': name,
                'created': time()
            })
            logging.debug('Room "{}" created'.format(name))
        else:

            room_id = data[0]
        self.rooms[name] = ChatRoom(name, room_id)
        logging.debug('Room "{}" loaded'.format(name))

    def handle_incoming_frame(self, client, frame):
        if frame.opcode == OpCode.TEXT:
            try:
                msg = json.JSONDecoder().decode(frame.payload.decode('utf-8'))
                return self.handle_request(self.clients[client.address], msg)
            except json.JSONDecodeError:
                return False
        else:
            return False

    def handle_new_connection(self, client):
        return True

    def on_client_open(self, client):
        new_client = Client(
            name='temporaty_name',
            websocket=client,
            send_limiter=self.send_threads_limiter
        )
        self.clients[client.address] = new_client

    def on_client_close(self, client):
        client_obj = self.clients[client.address]
        name = client_obj.name
        self.rooms[client_obj.room_name].remove_client(client_obj)
        if len(self.rooms[client_obj.room_name].clients) == 0:
            del self.rooms[client_obj.room_name]
            logging.debug('Removing room "{}" from memory because no users are left in it'.format(client_obj.name))
        del self.clients[client.address]
        logging.debug('{}: Disconnected'.format(name))
