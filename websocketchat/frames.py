#!/bin/env python3

from ewebsockets import Frame, OpCode
import json


class Message:
    def __init__(self, user, room_id, time, text):
        self.user = user
        self.room_id = room_id
        self.time = time
        self.text = text

    def get_dict(self):
        return {'user': self.user,
                'room_id': self.room_id,
                'time': self.time,
                'text': self.text}

TYPE_SINGLE_MESSAGE = 0
TYPE_MASS_MESSAGE = 1
TYPE_CLIENTS_IN_ROOM = 2
TYPE_CLIENT_LEAVING_ROOM = 3
TYPE_CLIENT_ENTERING_ROOM = 4
TYPE_CLIENT_REGISTER_1 = 5
TYPE_CLIENT_REGISTER_2 = 6
TYPE_KEY_IV = 7

CONTENT_SINGLE_MESSAGE = ['type', 'user', 'room_id', 'time', 'text']
CONTENT_MASS_MESSAGE = ['type', 'messages']
CONTENT_CLIENTS_IN_ROOM = ['type', 'users', 'room_id']
CONTENT_CLIENT_LEAVING_ROOM = ['type', 'user']
CONTENT_CLIENT_ENTERING_ROOM = ['type', 'user']
CONTENT_KEY_IV = ['type', 'keyiv']
CONTENT_REGISTER_NAME = ['type', 'name']
CONTENT_REGISTER_PASS = ['type', 'password']

CONTENT = {TYPE_SINGLE_MESSAGE: CONTENT_SINGLE_MESSAGE,
           TYPE_MASS_MESSAGE: CONTENT_MASS_MESSAGE,
           TYPE_CLIENT_LEAVING_ROOM: CONTENT_CLIENT_LEAVING_ROOM,
           TYPE_CLIENT_ENTERING_ROOM: CONTENT_CLIENT_ENTERING_ROOM,
           TYPE_CLIENTS_IN_ROOM: CONTENT_CLIENTS_IN_ROOM,
           TYPE_KEY_IV: CONTENT_KEY_IV}

def data_frame(**kwargs):
    type = kwargs['type']
    content = CONTENT[type]
    if len(kwargs) != len(content):
        raise ValueError('Some content missing or not supposed to be there')
    for kwarg in kwargs:
        if kwarg not in content:
            raise ValueError('unexpected content {}'.format(kwarg))

    # return Frame(
    #     payload=json.JSONEncoder().encode(kwargs).encode(),
    #     mask=0,
    #     opcode=OpCode.TEXT
    # )
    return json.JSONEncoder().encode(kwargs)
