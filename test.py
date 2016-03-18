#!/bin/env python3
import esockets
import websocketchat
import logging, sys
from websocket import create_connection
import json

root = logging.getLogger()
root.setLevel(logging.DEBUG)

ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
# formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
formatter = logging.Formatter('%(levelname)s - %(message)s')
ch.setFormatter(formatter)
root.addHandler(ch)

# chat = websocketchat.Chat()
# chat.start()


server = esockets.SocketServer(client_handler=websocketchat.ChatClientHandler)
server.start()


request_id = 0

client = create_connection('ws://' + server.host + ':' + str(server.port))
change_room = b'0' + b'6' + json.JSONEncoder().encode([request_id, 'facebook.com', -1]).encode()


key_iv = client.recv()
print('Key iv: ', key_iv)

request = change_room
print('Request: ', request)
client.send(request)

response = client.recv()
print('Response: ', response)

