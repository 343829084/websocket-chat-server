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



class Chat:
    def __init__(self,
                 max_send_threads=10,
                 send_timeout=2):

        self.server = ewebsockets.Websocket(
            handle_new_connection=self.handle_new_connection,
            handle_websocket_frame=self.handle_incoming_frame,
            on_client_open=self.on_client_open
        )
        self.rooms = {}
        self.db = ChatDb()
        self.send_threads_limiter = maxthreads.MaxThreads(max_send_threads)
        self.send_timeout = send_timeout
        self.clients = {}
        # self.answers = {
        #     client_forms['SINGLE_MESSAGE']: server_forms['',
        #     client_forms['LEAVE_ROOM']: self.answer_leave_room,
        #     client_forms['ENTER_ROOM']: 102,
        #     client_forms['LOGIN']: 104,
        #     client_forms['REGISTER_EMAIL']: 105,
        #     client_forms['REGISTER_USERNAME']: 106,
        #     client_forms['REGISTER_PASSWORD']: 107
        # }
    def start(self):
        self.open_room('Purgatory', 0)
        self.load_rooms()
        self.server.start()

    def stop(self):
        self.server.stop()

    def handle_request(self, client, msg):
        if msg['id'] == client_requests['SINGLE_MESSAGE']:
            if client.logged_in:
                t = time()
                msg_id = self.db.insert('messages', {
                    'user': client.name,
                    'text': msg['text'],
                    'room_id': client.room_id,
                    'show': 1,
                    'time': t
                })
                self.rooms[client.room_id].broadcast_message(client.name, msg['text'], t, msg_id)
                return True
            else:
                return False
        elif msg['id'] == client_requests['REGISTER_USERNAME']:

    # def handle_incoming_frame(self, client, frame):
    #     if frame.opcode == OpCode.TEXT:
    #         client_obj = self.clients[client.address]
    #         data = json.JSONDecoder().decode(frame.payload.decode('utf-8'))
    #         if data['type'] == client_forms['SINGLE_MESSAGE']:
    #             if client_obj.logged_in:
    #                 msg_time = time()
    #                 msg_id = self.db.insert('messages',{
    #                     'user': client_obj.name,
    #                     'text': data['text'],
    #                     'room_id': client_obj.room_id,
    #                     'show': 1,
    #                     'time': msg_time
    #                 })
    #                 self.rooms[client_obj.room_id].broadcast({
    #                         'type': server_forms['SINGLE_MESSAGE'],
    #                         'user': client_obj.name,
    #                         'time': msg_time,
    #                         'text': data['text'],
    #                         'id': msg_id
    #                 })
    #         elif data['type'] == client_forms['LOGIN']:
    #             client_obj.login()
    #         elif data['type'] == client_forms['ENTER_ROOM']:
    #             room_name = data.room_id
    #             if room_name in self.rooms:
    #                 self.rooms[client_obj.room_name].remove_client(client_obj)
    #                 self.rooms[room_name].add_client(client_obj)
    #                 client_obj.room_name = room_name
    #
    #                 messages = self.db.fetch('''SELECT id, text, user from messages WHERE room''')
    #     return True
    #
    # def handle_new_connection(self, client):
    #
    #     return True
    #
    # def on_client_open(self, client):
    #     new_client = Client(
    #         name='temporaty_name',
    #         websocket=client,
    #         send_limiter=self.send_threads_limiter,
    #         room_id=0
    #     )
    #     self.rooms[0].add_client(new_client)
    #     self.clients[client.address] = new_client
    #     new_client.send_key()
    #
    #     self.db.fetch('''SELECT id, text, user, time FROM messages where room_id''')
    #     # encrypted = encrypt(b'Hello from server', key, iv)
    #     # data2 = data_frame(type=TYPE_SINGLE_MESSAGE,
    #     #                    user='Zaebos',
    #     #                    time=time(),
    #     #                    text=encrypted.hex(),
    #     #                    id=1,
    #     #                    room_id=0,
    #     #                    )
    #     # print(data2)
    #     #
    #     # data3 = {'type': TYPE_MASS_MESSAGE,
    #     #          'messages': [
    #     #              {
    #     #                  'type': TYPE_SINGLE_MESSAGE,
    #     #                  'user': 'Zaebos',
    #     #                  'time': time(),
    #     #                  'text': encrypted.hex(),
    #     #                  'id': 1,
    #     #                  'room_id': 0
    #     #              },
    #     #              {
    #     #                  'type': TYPE_SINGLE_MESSAGE,
    #     #                  'user': 'Zaebos',
    #     #                  'time': time(),
    #     #                  'text': encrypted.hex(),
    #     #                  'id': 1,
    #     #                  'room_id': 0
    #     #              }
    #     #          ]}
    #     # new_client.send_data(data2)
    #     # new_client.send_data(data_frame(**data3))
    #
    # def add_room(self, name):
    #     room_id = self.db.insert('rooms', {'name': name, 'created': time()})
    #     self.open_room(name, room_id)
    #
    # def open_room(self, name, room_id):
    #     self.rooms[room_id] = ChatRoom(name, room_id)
    #
    # def load_rooms(self):
    #     db = self.db.connect()
    #     cursor = db.cursor()
    #     cursor.execute('''SELECT id, name FROM rooms''')
    #     all_rooms = cursor.fetchall()
    #     for room in all_rooms:
    #         self.open_room(room_id=room[0], name=room[1])
