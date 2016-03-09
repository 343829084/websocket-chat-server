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
import pdb
import validators
import re

def str2hex(string):
    try:
        _hex = int(string,16)
    except ValueError:
        return False

    return ewebsockets.int2bytes(int(string, 16), int(len(string)/2))


def random_str(n):
    return ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(n))

def validate_username(name):
    regex = '^[A-Z][A-Za-z0-9]*$'
    pattern = re.compile(regex)
    if pattern.match(name) and len(name) > 2 and len(name) < 15:
        return True
    else:
        return False

def validate_hexstring(string):
    # It has to be even
    length = len(string)
    if length/2 != int(length/2):
        return False

    # It has to be a multiple of 16
    if length/16 != int(length/16):
        return False

    regex = '^[A-Fa-f0-9]+$'
    pattern = re.compile(regex)
    if pattern.match(string):
        return True
    else:
        return False


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
        self.load_room('Chatify.com')

    def start(self):
        self.server.start()

    def stop(self):
        self.server.stop()

    def handle_request(self, client, msg):
        logging.debug('{}: Received message: {}'.format(client.address(), msg))
        if len(msg) < 1:
            logging.error('{}: Received a message containing no type: {}'.format(client.address(), msg))
            return False
        try:
            message = json.JSONDecoder().decode(msg[1:])
            if type(message) != list:
                logging.error('{}: Received a message that after json decoding is not a list: {}'.format(client.address(), msg))
                return False

            if len(message) < 1:
                logging.error('{}: Received a message w/o msg_id: {}'.format(client.address(), msg))

        except json.JSONDecodeError:
            logging.error('{}: Failed to convert string to array: {}'.format(client.address(), msg[1:]))
            return False

        msg_id = message[0]
        if type(msg_id) != int:
            logging.error('{}: Received msg with unrecognized msg_id: {}({})'.format(client.address(), msg_id, type(msg_id)))
            return False
        message = message[1:]
        req_type = msg[0]
        enc = False;

        if req_type == request_ids['send_message']:
            if len(message) != 1:
                logging.error('{}: unexpected array length ({}) in send_message request'.format(
                    client.address(), len(message)
                ))
                return False
            if not client.logged_in:
                logging.error('{}: Client tried to send a message w/o being logged in'.format(client.address()))
                return False
            text = message[0]
            message_id, _time = self.db.add_message(client, message[0])
            self.rooms[client.room_name].broadcast_message(client.name, text, _time, message_id)
            response = []

        elif req_type == request_ids['get_key_iv']:
            if len(message) != 0:
                logging.error('{}: unexpected array length ({}) in get_key_iv request'.format(
                    client.address(), len(message)
                ))
                return False
            client.send_key_iv(msg_id)
            # Returning true already because the send_key_iv automatically replies to the client
            return True
        elif req_type == request_ids['enter_room']:
            if len(message) != 1:
                logging.error('{}: unexpected array length ({}) in enter_room request'.format(
                    client.address(), len(message)
                ))
                return False
            room_name = message[0]
            if type(room_name) != str:
                logging.error('{}: Tried to create a room with type(room_name)={}'.format(
                    client.address(), type(room_name)
                ))
                return False

            if room_name not in self.rooms and not validators.url(room_name):
                logging.error('{}: Tried to create a room with an invalid url as room name: {}'.format(
                    client.address(), room_name
                ))

            client.room_name = room_name
            self.load_room(room_name)
            response = []

        elif req_type == request_ids['get_messages']:
            if len(message) != 1:
                logging.error('{}: unexpected array length ({}) in get_messages request'.format(
                    client.address(), len(message)
                ))
                return False
            last_id = message[0]
            if type(last_id) != int:
                logging.error('{}: unexpected type(last_id) ({}:{}) in get_messages request'.format(
                    client.address(), last_id, type(last_id)
                ))
                return False

            messages = self.db.get_messages(client.room_name, last_id)
            response = [messages]

        elif req_type == request_ids['check_username'] or req_type == request_ids['check_email']:
            if len(message) != 1:
                logging.error('{}: unexpected array length ({}) in check_username request'.format(
                    client.address(), len(message)
                ))
                return False

            data = message[0]
            if type(data) != str:
                logging.error(
                    '{}: Username and email must be str type when checking availability, currently: {}'.format(
                        client.address(), type(data)
                    ))
                return False

            if req_type == request_ids['check_username']:
                column = 'name'
                data = data.capitalize()
                if not validate_username(data):
                    logging.error('{}: Tried to check an invalid username,'.format(client.address()) +
                                  ' this is checked client side and should not be a problem here (protocol error)')
                    return False
            else:
                column = 'email'
                data = data.lower()
                if not validators.email(data):
                    logging.error('{}: Tried to check an invalid email,'.format(client.address()) +
                                  ' this is checked client side and should not be a problem here (protocol error)')
                    return False

            exists = self.db.check_existence('users', column, data)
            response = [int(not exists)]

        elif req_type == request_ids['register']:
            if len(message) != 3:
                logging.error('{}: unexpected array length ({}) in register request'.format(
                    client.address(), len(message)
                ))
                return False
            email = message[0]
            name = message[1].capitalize()
            password = message[2]
            if type(email) != str or type(name) != str or type(password) != str:
                logging.error('{}: Tried to register and one or more of the '.format(client.address()) +
                              'email({}), name({}) and password({}) are of the wrong type'.format(
                    client.address(), type(email), type(name), type(password)
                ))
                return False

            if not validators.email(email):
                logging.error('{}: Tried to register an invalid email,'.format(client.address()) +
                              ' this is checked client side and should not be a problem here (protocol error)')
                return False

            name_availible = not self.db.check_existence('users', 'name', name)
            email_availible = not self.db.check_existence('users', 'email', email)
            if not name_availible or not email_availible:
                logging.debug('{}: name({}) or email({}) unavailable'.format(
                    client.address(), not name_availible, not email_availible
                ))
                response = [0, int(email_availible), int(name_availible)]
            else:
                self.db.new_user(email, name, password)
                response = [1]

        elif req_type == request_ids['login']:
            if len(message) != 2:
                logging.error('{}: unexpected array length ({}) in login request'.format(
                    client.address(), len(message)
                ))
                return False
            email = message[0]
            password = message[1]
            if type(email) != str or type(password) != str:
                logging.error('{}: Tried to login and one or more of the email({}) and password({}) are of the wrong type'.format(
                    client.address(), type(email), type(password)
                ))
                return False
            if not validators.email(email):
                logging.error('{}: Email is not a valid email ({}), this is checked '.format(
                    client.address(), email) +
                              'client side and should not be a problem here (protocol error)')
                return False

            data = self.db.validate_login(email, password)
            if data is not None:
                # not None means accepted login
                client.id, client.name = data
                client.logged_in = True
                logging.info('{} logged in'.format(client.address()))
            else:
                logging.info('{} login failed'.format(client.address()))
            response = [int(client.logged_in), client.name]

        elif req_type == request_ids['get_token']:
            if len(message) != 0:
                logging.error('{}: unexpected array length ({}) in get_token request'.format(
                    client.address(), len(message)
                ))
                return False
            if client.logged_in:
                token = self.db.new_token(client)
            else:
                logging.error('{}: Tried to get token w/o being logged in'.format(client.address()))
                return False
            response = [token]

        elif req_type == request_ids['auto_login']:
            if len(message) != 2:
                logging.error('{}: unexpected array length ({}) in auto_login request'.format(
                    client.address(), len(message)
                ))
                return False
            email = message[0]
            token = message[1]
            if type(email) != str or type(token) != str:
                logging.error('{}: Tried to login and one or more of the email({}) and password({}) are of the wrong type'.format(
                    client.address(), type(email), type(token)
                ))
                return False

            if not validators.email(email):
                logging.error('{}: Email is not a valid email ({}), this is checked '.format(
                    client.address(), email) +
                              'client side and should not be a problem here (protocol error)')
                return False

            data = self.db.validate_auto_login(client, email, token)
            new_token = ''
            if data is not None:
                client.id, client.name, new_token = data
                client.logged_in = True
                logging.info('{} logged in with token: {}'.format(
                    client.address(), token
                ))
                response = [int(client.logged_in), client.name, new_token]
            else:
                logging.info('{} auto login failed with token {}'.format(
                    client.address(), token
                ))
                response = [int(client.logged_in)]

        elif req_type == request_ids['logout']:
            if len(message) > 1:
                logging.error('{}: unexpected array length ({}) in logout request'.format(
                    client.address(), len(message)
                ))
                return False

            if not client.logged_in:
                logging.error('{}: Client tried to logout w/o being logged in'.format(client.address()))
                return False

            if len(message) == 1:
                token_to_remove = message[0]
                if type(message[0]) != str:
                    logging.error('{}: Client tried to logout with unexpected token type ({})'.format(
                        client.address(), type(token_to_remove)
                    ))
                    return False
                self.db.remove_token(client, token_to_remove)
                logging.debug('{}: Client logout removed unused token ({})'.format(
                        client.address(), token_to_remove
                ))

            client.logout()
            logging.debug('{}: logged out'.format(client.address()))
            response = []

        else:
            # logging.debug('Received message with unrecognized type: {}({})'.format(req_type, type(req_type)))
            return False

        client.send(req_type, [msg_id] + response, enc)
        return True



        # logging.debug('New request of type {} ({})'.format(msg['type'],
        #                                                    list(client_requests.keys())[list(client_requests.values()).index(msg['type'])]))
        # if 'type' not in msg:
        #     logging.debug("{}: Received a request that doesn't contain a type".format(client.websocket.address))
        #     return False
        #
        # if msg['type'] == client_requests['SINGLE_MESSAGE']:
        #     if client.logged_in:
        #         t = time()
        #         msg_id = self.db.insert('messages', {
        #             'user': client.name,
        #             'text': msg['text'],
        #             'room_name': client.room_name,
        #             'show': 1,
        #             'time': t
        #         })
        #         self.rooms[client.room_name].broadcast_message(client.name, msg['text'], t, msg_id)
        #         return_value = True
        #     else:
        #         return_value = False
        #
        #     client.send({
        #             'type': client_requests['SINGLE_MESSAGE'],
        #             'accepted': return_value
        #     })
        #     return return_value
        #
        # elif msg['type'] == client_requests['CHECK_USERNAME']:
        #     client.send({
        #             'type': client_requests['CHECK_USERNAME'],
        #             'available': self.db.check_existence('users', 'name', msg['name'])
        #     })
        #     return True
        # elif msg['type'] == client_requests['CHECK_EMAIL']:
        #     client.send({
        #             'type': client_requests['CHECK_EMAIL'],
        #             'available': self.db.check_existence('users', 'email', msg['email'])
        #     })
        #     return True
        # elif msg['type'] == client_requests['KEY_IV']:
        #     client.send_key()
        #     return True
        # elif msg['type'] == client_requests['REGISTER']:
        #     email = decrypt(str2hex(msg['email']), client.key, client.iv)
        #     name = decrypt(str2hex(msg['name']), client.key, client.iv).capitalize()
        #     password = decrypt(str2hex(msg['password']), client.key, client.iv)
        #
        #     email_available = not self.db.check_existence('users', 'email', email)
        #     name_available = not self.db.check_existence('users', 'name', name)
        #
        #     if email_available and name_available:
        #         logging.debug('{}: Register requested'.format(client.websocket.address))
        #         client.name = name
        #         client.verification_code = random_str(5)
        #         client.register_items = [email, name, password]
        #         send_email(email, 'Chat verification code', client.verification_code)
        #         client.send({
        #             'type': client_requests['REGISTER'],
        #             'accepted': True
        #         })
        #         # client.logged_in = True
        #     else:
        #         ad = ''
        #         if not email_available:
        #             ad += 'email exists '
        #         if not name_available:
        #             ad += 'name exists'
        #
        #         logging.debug('{}: registration denied ({})'.format(client.websocket.address, ad))
        #         client.send({
        #             'type': client_requests['REGISTER'],
        #             'accepted': False,
        #             'email': email_available,
        #             'name': name_available
        #         })
        #
        #     return True
        # elif msg['type'] == client_requests['VERIFY']:
        #     if msg['code'] == client.verification_code:
        #         accepted = True
        #         id = self.db.insert('users', {
        #             'email': client.register_items[0],
        #             'name': client.register_items[1],
        #             'password': client.register_items[2],
        #             'joined': time(),
        #             'last_online': time(),
        #             'tokens': '[]'
        #         })
        #         client.id = id
        #         client.logged_in = True
        #     else:
        #         accepted = False
        #
        #     client.send({
        #         'type': client_requests['VERIFY'],
        #         'accepted': accepted,
        #         'name': client.name
        #     })
        #
        # elif msg['type'] == client_requests['LOGIN']:
        #     response = {'type': client_requests['LOGIN']}
        #     email = decrypt(str2hex(msg['email']), client.key, client.iv)
        #     password = decrypt(str2hex(msg['password']), client.key, client.iv)
        #
        #     data = self.db.fetch('''SELECT id, name, password, tokens FROM users WHERE email="{}"'''.format(email))
        #     if data and data[2] == password:
        #         response['accepted'] = True
        #         client.name = data[1]
        #         client.id = data[0]
        #         if msg['request_token'] == True:
        #             new_token = random_str(64)
        #             response['token'] = encrypt(new_token.encode(), client.key, client.iv).hex()
        #             tokens = json.JSONDecoder().decode(data[3])
        #             tokens.append(new_token)
        #             if len(tokens) > 10:
        #                 tokens.pop(0)
        #             print('TOKENS', tokens)
        #             print('JSON', json.JSONEncoder().encode(tokens))
        #             self.db.execute("UPDATE users SET tokens=? WHERE Id=?",
        #                             (json.JSONEncoder().encode(tokens),
        #                              client.id))
        #     else:
        #         response['accepted'] = False
        #
        #     client.send(response)
        #
        #     return True
        # elif msg['type'] == client_requests['AUTO_LOGIN']:
        #     response = {'type': client_requests['AUTO_LOGIN']}
        #     email = decrypt(str2hex(msg['email']), client.key, client.iv)
        #     token = msg['token']
        #     data = self.db.fetch('''SELECT id, name, tokens FROM users WHERE email="{}"'''.format(email))
        #     tokens = json.JSONDecoder().decode(data[2])
        #     if token in tokens:
        #         response['accepted'] = True
        #         client.name = data[1]
        #         client.id = data[0]
        #         client.logged_in = True
        #         new_token = random_str(64)
        #         tokens[tokens.index(token)] = new_token
        #         response['token'] = encrypt(new_token.encode(), client.key, client.iv).hex()
        #         self.db.execute('''UPDATE users SET tokens = ? WHERE id = ?;''',
        #                         (json.JSONEncoder().encode(tokens),
        #                          client.id))
        #     else:
        #         response['accepted'] = False
        #
        #     client.send(response)
        #     return True
        #
        # elif msg['type'] == client_requests['LOGOUT']:
        #     client.name = 'temporary_name'
        #     client.logged_in = False
        #     client.send({
        #         'type': client_requests['LOGOUT']
        #     })
        #     return True
        #
        # elif msg['type'] == client_requests['ENTER_ROOM']:
        #     room_name = msg['name']
        #     if room_name not in self.rooms:
        #         self.load_room(room_name)
        #
        #     if client.room_name is not None:
        #         self.rooms[client.room_name].remove_client(client)
        #
        #     client.room_name = room_name
        #     self.rooms[room_name].add_client(client)
        #
        #     data = self.db.fetch(
        #         '''SELECT id, user, text, time FROM messages WHERE room_name = "{}" AND id > {}'''.format(
        #             room_name, msg['last_message']), all=True)
        #
        #     if data is not None:
        #         length = len(data)
        #     else:
        #         length = 0
        #     messages = list(range(length))
        #
        #     for i in range(length):
        #         messages[i] = {
        #             'id': data[i][0],
        #             'user': data[i][1],
        #             'text': data[i][2],
        #             'time': data[i][3],
        #         }
        #     client.send({
        #         'type': client_requests['ENTER_ROOM'],
        #         'room': room_name,
        #         'messages': messages
        #     })
        #     logging.debug('{} entered room {}'.format(client.name, room_name))
        #     return True
        # else:
        #     return False

    def load_room(self, name):
        data = self.db.execute('''SELECT id, name FROM rooms where name=?''', (name,), fetch='one')
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
            # logging.debug('Payload: {}'.format(frame.payload))
            if len(frame.payload) < 1:
                logging.debug('Received a text frame that contained less that 1 bytes: {}'.format(frame.payload))
                return False
            client_obj = self.clients[client.address]
            msg = frame.payload[1:].decode('utf-8')
            if frame.payload[0] == b'0'[0]:
                pass
            elif frame.payload[0] == b'1'[0] and type(client_obj.key) == bytes and type(client_obj.iv) == bytes:
                # Received a frame containing encrypted data
                msg = msg
                print('LENTGH', len(msg))
                if not validate_hexstring(msg):
                    logging.error('{}: Encrypted message is not a valid hex string: {}'.format(
                        client_obj.address(), msg
                    ))
                    return False
                try:
                    msg = decrypt(str2hex(msg), client_obj.key, client_obj.iv).decode('utf-8')
                except ValueError as e:
                    logging.error('{}: Failed to decrypt data: {}'.format(
                        client_obj.address(), e
                    ))
                    return False


            elif frame.payload[0] == b'1'[0] and (type(client_obj.key) != bytes or type(client_obj.iv) != bytes):
                logging.debug('Received an encrypted text frame w/o the client key or iv set')
                return False
            else:
                logging.error('{}: Received a text frame where the first byte (encrypted byte)'
                              ' was not 1 or 0, payload: {}'.format(client_obj.address(), frame.payload[0]))
                return False

            return self.handle_request(client_obj, msg)
        else:
            # logging.debug('Received a frame containing unaccepted opcode: {}'.format(frame.opcode))
            return True


    def handle_new_connection(self, client):
        return True

    def on_client_open(self, client):
        new_client = Client(
            websocket=client,
            send_limiter=self.send_threads_limiter
        )
        self.clients[client.address] = new_client

    def on_client_close(self, client):

        # client_obj = self.clients[client.address]
        # name = client_obj.name
        # self.rooms[client_obj.room_name].remove_client(client_obj)
        # if len(self.rooms[client_obj.room_name].clients) == 0:
        #     del self.rooms[client_obj.room_name]
        #     logging.debug('Removing room "{}" from memory because no users are left in it'.format(client_obj.name))
        del self.clients[client.address]
        # print('CLOSED: ', client.address)
        # logging.debug('{}: Disconnected'.format(name))
