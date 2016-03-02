#!/bin/env python3
from .crypto import *
from time import time
from .forms import *


class Client:
    def __init__(self, name, websocket, send_limiter, room_id):
        self.name = name
        self.websocket = websocket
        self.room_id = room_id
        self.send_limiter = send_limiter
        self.last_activity = time()
        self.time_connected = time()
        self.logged_in = False
        self.key, self.iv = generate_key_and_iv()

    def send(self, text, timeout=-1):
        if type(text) == str or type(text) == bytes:
            self.send_limiter.start_thread(
                target=self.websocket.send_text,
                args=(text, timeout)
            )
        elif type(text) == dict:
            self.send_limiter.start_thread(
                target=self.websocket.send_json,
                args=(text, timeout)
            )

    def send_message(self, message, timeout=-1):
        self.send(message.make_json(), timeout)

    def send_mass_message(self, messages, timeout=-1):
        packed_messages = list(range(len(messages)))
        for i in range(len(messages)):
            packed_messages[i] = messages[i].make_json()
        self.send({
            'type': server_forms['MASS_MESSAGE'],
            'messages': packed_messages
        }, timeout)

    def send_key(self, timeout=-1):
        self.send({
            'type': server_forms['KEY_IV'],
            'key': self.key.hex(),
            'iv': self.iv.hex()
        }, timeout)

    def login(self, accept=True, timeout=-1):
        self.send({
            'type': server_forms['LOGIN'],
            'accepted': accept
        }, timeout)
        if accept:
            self.logged_in = True

    def register_email(self, accept, timeout=-1):
        self.send({
            'type': server_forms['REGISTER_EMAIL'],
            'accepted': accept
        }, timeout)

    def register_username(self, accept, timeout=-1):
        self.send({
            'type': server_forms['REGISTER_USERNAME'],
            'accepted': accept
        }, timeout)

    def register_password(self, accept, timeout=-1):
        self.send({
            'type': server_forms['REGISTER_PASSWORD'],
            'accepted': accept
        }, timeout)

    def request_responce(self, type, accept):
        self.send({
            'type': type,
            'accept': accept
        })
