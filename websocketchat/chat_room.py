#!/bin/env python3

from .forms import *
import logging

class ChatRoom:
    def __init__(self, name, room_id):
        self.name = name
        self.room_id = room_id
        self.clients = []

    def add_client(self, client):
        self.clients.append(client)

    def remove_client(self, client):
        try:
            self.clients.remove(client)
            logging.debug('Removed {} from {}'.format(client.name, self.name))
        except ValueError:
            logging.debug('Failed to remove {} from {}'.format(client.name, self.name))

    def broadcast(self, data, timeout=-1):
        for client in self.clients:
            client.send(data, timeout)

    def broadcast_message(self, user, text, time, msg_id):
        self.broadcast({
            'type': server_forms['SINGLE_MESSAGE'],
            'user': user,
            'text': text,
            'time': time,
            'id': msg_id
        })