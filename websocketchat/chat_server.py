#!/bin/env python3

import ewebsockets
from time import time
import sqlite3
import json
import maxthreads
from .frames import *
from .crypto import *

class ChatDb:
    def __init__(self):
        self.db = sqlite3.connect('chat.db')
        self.cursor = self.db.cursor()

        self.tables = {'users': {'id': 'INTEGER PRIMARY KEY AUTOINCREMENT',
                                 'name': 'TEXT',
                                 'password': 'TEXT',
                                 'joined': 'INTEGER',
                                 'last_online': 'INTEGER'},

                       'messages': {'id': 'INTEGER PRIMARY KEY AUTOINCREMENT',
                                    'user': 'TEXT',
                                    'type': 'INTEGER',
                                    'text': 'TEXT',
                                    'room': 'TEXT',
                                    'show': 'INTEGER',
                                    'time': 'INTEGER'},

                       'rooms': {'id': 'INTEGER PRIMARY KEY AUTOINCREMENT',
                                 'name': 'TEXT',
                                 'created': 'INTEGER'}

                       }
        self.create_tables()

    def insert(self, table, entries):
        self.cursor.execute('''INSERT INTO {}({}) VALUES({}?)'''.format(table,
                                                                        ', '.join(entries.keys()),
                                                                        '?,'*(len(entries)-1)),
                            tuple(entries.values()))
        row_id = self.cursor.lastrowid
        self.db.commit()
        return row_id

    def create_table(self, name, entries):
        columns = list(entries.items())
        for i in range(len(columns)):
            columns[i] = ' '.join(columns[i])

        columns = ', '.join(columns)
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS {}({})'''.format(name, columns))
        self.db.commit()

    def create_tables(self):
        for table in self.tables:
            self.create_table(table, self.tables[table])


class ChatRoom:
    def __init__(self, name, room_id):
        self.name = name
        self.room_id = room_id
        self.clients = []

    def add_client(self, client):
        self.clients.append(client)

    def remove_client(self, client):
        self.clients.remove(client)

    def broadcast(self, data):
        """
        :param data: A Data object
        :return:
        """
        for client in self.clients:
            client.send_data(data)


class Client:
    def __init__(self, name, websocket, send_limiter, room_id):
        self.name = name
        self.websocket = websocket
        self.room_id = room_id
        self.send_limiter = send_limiter
        self.last_activity = time()
        self.time_connected = time()
        self.logged_in = False

    def send_data(self, data, timeout=-1, binary=False):
        """Sends a websocket text frame
        :param data: A Data object
        :return:
        """
        if binary:
            target = self.websocket.send_binary
        else:
            target = self.websocket.send_text

        self.send_limiter.start_thread(
            target=target,
            args=(data, timeout)
        )



# class Commands:

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

    def start(self):
        self.open_room('Purgatory', 0)
        self.load_rooms()
        self.server.start()

    def stop(self):
        self.server.stop()

    def handle_incoming_frame(self, client, frame):
        return True

    def handle_new_connection(self, client):
        return True

    def on_client_open(self, client):
        new_client = Client(
            name='temporaty_name',
            websocket=client,
            send_limiter=self.send_threads_limiter,
            room_id=0
        )
        self.rooms[1].add_client(new_client)

        key, iv = generate_key_and_iv()

        data = data_frame(type=TYPE_KEY_IV,
                          keyiv='{}').encode().replace(b'{}', key+iv)
        print('DATA: ', data, type(data))
        new_client.send_data(data, self.send_timeout, binary=True)

    def add_room(self, name):
        room_id = self.db.insert('rooms', {'name': name, 'created': time()})
        self.open_room(name, room_id)

    def open_room(self, name, room_id):
        self.rooms[room_id] = ChatRoom(name, room_id)

    def load_rooms(self):
        self.db.cursor.execute('''SELECT id, name FROM rooms''')
        all_rooms = self.db.cursor.fetchall()
        for room in all_rooms:
            self.open_room(room_id=room[0], name=room[1])


    # def register(self, client):



