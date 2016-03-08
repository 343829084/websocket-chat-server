#!/bin/env python3


import json
from time import time as current_time

request_ids = {
    'send_message': '1',
    'get_messages': '2',
    'login': '3',
    'get_key_iv': '4',
    'get_token': '5',
    'enter_room': '6',
    'check_username': '7',
    'check_email': '8',
    'register': '9',
    'validate': 'a',
    'single_message': 'b'
}

client_requests = {
    'SINGLE_MESSAGE': 100,
    'LEAVE_ROOM': 101,
    'ENTER_ROOM': 102,
    'LOGIN': 104,
    'CHECK_EMAIL': 105,
    'CHECK_USERNAME': 106,
    'REGISTER': 107,
    'KEY_IV': 109,
    'VERIFY': 110,
    'LOGOUT': 111,
    'AUTO_LOGIN': 112
}

# forms that the server can spontaneously send out w/o a client request
server_forms = {
    'SINGLE_MESSAGE': 200,
}


class Message:
    def __init__(self, client, msg, time=current_time()):
        self.text = msg['text']
        self.user = client.name
        self.room_id = client.room_id
        self.time = time
        self.id = id

    def make_json(self):
        return {
            'type': server_forms['SINGLE_MESSAGE'],
            'text': self.text,
            'user': self.user,
            'time': self.time,
            'id': self.id
        }



# TYPE_SINGLE_MESSAGE = 0
# TYPE_MASS_MESSAGE = 1
# TYPE_CLIENTS_IN_ROOM = 2
# TYPE_CLIENT_LEAVING_ROOM = 3
# TYPE_CLIENT_ENTERING_ROOM = 4
# TYPE_CLIENT_REGISTER_1 = 5
# TYPE_CLIENT_REGISTER_2 = 6
# TYPE_KEY_IV = 7
# TYPE_LOGIN = 8
# TYPE_LOGIN_RESPONCE = 9
#
# CONTENT_SINGLE_MESSAGE = ['type', 'user', 'id', 'room_id', 'time', 'text']
# CONTENT_MASS_MESSAGE = ['type', 'messages']
# CONTENT_CLIENTS_IN_ROOM = ['type', 'users', 'room_id']
# CONTENT_CLIENT_LEAVING_ROOM = ['type', 'user']
# CONTENT_CLIENT_ENTERING_ROOM = ['type', 'user']
# CONTENT_KEY_IV = ['type', 'key', 'iv']
# CONTENT_REGISTER_NAME = ['type', 'name']
# CONTENT_REGISTER_PASS = ['type', 'password']
# CONTENT_LOGIN = ['type', 'email', 'hash']
# CONTENT_LOGIN_RESPONCE = ['type', 'accepted']
#
# CONTENT = {TYPE_SINGLE_MESSAGE: CONTENT_SINGLE_MESSAGE,
#            TYPE_MASS_MESSAGE: CONTENT_MASS_MESSAGE,
#            TYPE_CLIENT_LEAVING_ROOM: CONTENT_CLIENT_LEAVING_ROOM,
#            TYPE_CLIENT_ENTERING_ROOM: CONTENT_CLIENT_ENTERING_ROOM,
#            TYPE_CLIENTS_IN_ROOM: CONTENT_CLIENTS_IN_ROOM,
#            TYPE_KEY_IV: CONTENT_KEY_IV,
#            TYPE_LOGIN: CONTENT_LOGIN,
#            TYPE_LOGIN_RESPONCE: CONTENT_LOGIN_RESPONCE}
#
#
# def data_frame(**kwargs):
#     type = kwargs['type']
#     content = CONTENT[type]
#     if len(kwargs) != len(content):
#         raise ValueError('Some content missing or not supposed to be there')
#     for kwarg in kwargs:
#         if kwarg not in content:
#             raise ValueError('unexpected content {}'.format(kwarg))
#
#     # return Frame(
#     #     payload=json.JSONEncoder().encode(kwargs).encode(),
#     #     mask=0,
#     #     opcode=OpCode.TEXT
#     # )
#     return json.JSONEncoder().encode(kwargs)
