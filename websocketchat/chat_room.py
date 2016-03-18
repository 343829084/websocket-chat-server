#!/bin/env python3

from .forms import *
import logging
import json
import maxthreads

broadcast_threads = maxthreads.MaxThreads(100)


class ChatRoom:
    def __init__(self, name, room_id):
        self.name = name
        self.room_id = room_id
        self.clients = []

    def add_client(self, client):
        client.room_name = self.name
        self.clients.append(client)
        logging.debug('{}: {} entered room'.format(self.name, client.name()))

    def remove_client(self, client):
        try:
            client.room_name = None
            self.clients.remove(client)
            logging.debug('{}: {} exited room'.format(self.name, client.name()))
        except ValueError:
            logging.debug('Failed to remove {} from {}'.format(client.name(), self.name))

    def broadcast(self, type, message_array, encrypt=b'0'):
        logging.debug('{}: Broadcasting message: {}'.format(self.name, message_array))
        for client in self.clients:
            broadcast_threads.start_thread(
                target=client.send_response,
                args=(type, message_array, encrypt)
            )
            # client.send(type_id, message_array, encrypt)

    def broadcast_message(self, msg_id, time, user, text):
        # self.broadcast({
        #     'type': server_forms['SINGLE_MESSAGE'],
        #     'user': user,
        #     'text': text,
        #     'time': time,
        #     'id': msg_id
        # })
        self.broadcast(
            type=server_message_types['single_message']['id'],
            message_array=[msg_id, time, user, text]
        )

