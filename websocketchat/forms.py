#!/bin/env python3

import validators
import re
import json


def is_int(input):
    return type(input) == int


def is_str(input):
    return type(input) == str


def is_list(input):
    return type(input) == list


def is_bool(input):
    return is_int(input) and (input == 0 or input == 1)


def is_email(input):
    if not is_str(input):
        return False

    regex = r'^(([^<>()\[\]\\.,;:\s@"]+(\.[^<>()\[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$'
    pattern = re.compile(regex)

    if not pattern.match(input):
        return False

    return True

    # return validators.email(input) == True


def is_url(input):
    input = 'http://' + input
    if not is_str(input):
        return False

    return validators.url(input) == True


def validate_username(input):
    if not is_str(input):
        return False

    if len(input) < 3 or len(input) > 15:
        return False

    regex = '^[A-Za-z][A-Za-z0-9]*$'
    pattern = re.compile(regex)

    if not pattern.match(input):
        return False

    return True


def validate_hexstring(input):
    if not is_str(input):
        return False
    # It has to be even
    length = len(input)
    if length/2 != int(length/2):
        return False

    # It has to be a multiple of 16
    if length/16 != int(length/16):
        return False

    regex = '^[A-Fa-f0-9]+$'
    pattern = re.compile(regex)
    if pattern.match(input):
        return True
    else:
        return False

request_types = {
    '1': {
        'type': 'send_message',
        'expected_length': 1,
        'expected_types': [str],
        'description': ['text'],
        'validators': [is_str],
        'response': []
    },
    # '2': { # Messages are now automatically sent on enter_room request
    #     'type': 'get_messages',
    #     'expected_length': 1,
    #     'expected_types': [int],
    #     'description': ['last_id'],
    #     'validators': [is_int],
    #     'response': ['messages']
    # },
    '3': {
        'type': 'login',
        'expected_length': 3,
        'expected_types': [str, str, int],
        'description': ['email', 'password', 'request_token'],
        'validators': [is_email, is_str, is_bool],
        'response': ['accepted', 'name', 'request_email_verification', 'token']
    },
    '6': {
        'type': 'enter_room',
        'expected_length': 2,
        'expected_types': [str, int],
        'description': ['room_name', 'last_id'],
        'validators': [is_url, is_int],
        'response': ['messages']
    },
    '7': {
        'type': 'check_username',
        'expected_length': 1,
        'expected_types': [str],
        'description': ['name'],
        'validators': [validate_username],
        'response': ['is_available']
    },
    '8': {
        'type': 'check_email',
        'expected_length': 1,
        'expected_types': [str],
        'description': ['email'],
        'validators': [is_email],
        'response': ['is_available']
    },
    '9': {
        'type': 'register',
        'expected_length': 3,
        'expected_types': [str, str, str],
        'description': ['email', 'name', 'password'],
        'validators': [is_email, validate_username, is_str],
        'response': ['accepted', 'email_available', 'name_available']
    },
    'a': {
        'type': 'verify_email',
        'expected_length': 1,
        'expected_types': [str],
        'description': ['verification_code'],
        'validators': [is_str],
        'response': ['accepted']
    },
    'b': {
        'type': 'token_login',
        'expected_length': 2,
        'expected_types': [str, str],
        'description': ['email', 'token'],
        'validators': [is_email, is_str],
        'response': ['accepted', 'request_email_verification', 'name']
    },
    'c': {
        'type': 'logout',
        'expected_length': 1,
        'expected_types': [str],
        'description': ['token'],
        'validators': [is_str],
        'response': []
    },
    'd': {
        'type': 'new_verification_code',
        'expected_length': 0,
        'expected_types': [],
        'description': [],
        'validators': [],
        'response': []
    }
}

server_message_types = {
    'single_message': {
        'id': 'z'
    },
    'key_iv': {
        'id': 'y'
    }
}


def validate_request(request):
    """Handling of encryption happens prior to this function call
     so the structure of the request looks like:

        //------------------------------------------------
        //       1       |       2-end                   |
        //------------------------------------------------
        //   request_id  | request_array ([msg_id, ...)  |
        //------------------------------------------------
    """
    if len(request) < 4:
        return False, 'Request length < 4 (minimum e.x. "1[1]"'

    request_type = request[0]
    if request_type not in request_types:
        return False, 'Invalid request id ({})'.format(request_type)

    req = request_types[request_type]
    # Trying to decode rest of the request as a list
    try:
        request_array = json.JSONDecoder().decode(request[1:])
    except json.JSONDecodeError:
        return False, 'Failed to convert request_array to list in request {}'.format(req['type'])

    if not is_list(request_array):
        return False, 'request_array is not of type<list> after conversion in request {}'.format(req['type'])

    length = len(request_array)
    if length == 0:
        return False, 'request_array is missing a request_id in request {}'.format(req['type'])

    request_id = request_array[0]
    if not is_int(request_id):
        return False, 'request_id is of wrong type or missing in request {}'.format(req['type'])
    request_array = request_array[1:]

    if length-1 != req['expected_length']:
        return False, 'Unexpected length in request {}'.format(req['type'])

    for i in range(length-1):
        # [i+1] because msg_id is missing in the request_ids['validators'] list
        if not req['validators'][i](request_array[i]):
            return False, 'Failed when validating {} ({}) of request {}'.format(
                req['description'][i], request_array[i], req['type']
            )

    return True, [request_type, request_id, request_array]

