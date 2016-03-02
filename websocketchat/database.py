#!/bin/env python3

import sqlite3


class ChatDb:
    def __init__(self):
        self.name = 'chat.db'
        self.db = sqlite3.connect('chat.db', check_same_thread=False)
        # self.cursor = self.db.cursor()
        self.tables = {'users': {'id': 'INTEGER PRIMARY KEY AUTOINCREMENT',
                                 'name': 'TEXT',
                                 'email': 'TEXT',
                                 'password': 'TEXT',
                                 'joined': 'INTEGER',
                                 'last_online': 'INTEGER'},

                       'messages': {'id': 'INTEGER PRIMARY KEY AUTOINCREMENT',
                                    'user': 'TEXT',
                                    'text': 'TEXT',
                                    'room_name': 'TEXT',
                                    'show': 'INTEGER',
                                    'time': 'INTEGER'},
                       'rooms': {'id': 'INTEGER PRIMARY KEY AUTOINCREMENT',
                                 'name': 'TEXT',
                                 'created': 'INTEGER'}

                       }
        self.create_tables()

    def connect(self):
        # return sqlite3.connect(self.name)
        return self.db

    def close(self):
        self.db.close()

    def execute(self, command, entries=None, commit=False):
        db = sqlite3.connect(self.name)
        cursor = db.cursor()
        row_id = None
        if entries is not None:
            cursor.execute(command, entries)
            db.commit()
        else:
            cursor.execute(command)
        if commit:
            row_id = cursor.lastrowid
            db.commit()
        # db.close()
        return row_id

    def insert(self, table, entries):
        db = self.connect()
        cursor = db.cursor()

        command = '''INSERT INTO {}({}) VALUES({}?)'''.format(table,
                                                              ', '.join(entries.keys()),
                                                              '?,'*(len(entries)-1))
        entries = tuple(entries.values())

        cursor.execute(command, entries)
        row_id = cursor.lastrowid
        db.commit()
        # db.close()
        return row_id

    def create_table(self, name, entries):
        db = self.connect()
        cursor = db.cursor()
        columns = list(entries.items())
        for i in range(len(columns)):
            columns[i] = ' '.join(columns[i])

        columns = ', '.join(columns)
        cursor.execute('''CREATE TABLE IF NOT EXISTS {}({})'''.format(name, columns))
        db.commit()
        # # db.close()

    def create_tables(self):

        for table in self.tables:
            self.create_table(table, self.tables[table])

    def check_existence(self, table, column, entry):
        db = self.connect()
        cursor = db.cursor()
        if type(entry) == str:
            entry = '"' + entry + '"'
        else:
            entry = str(entry)
        cursor.execute('''SELECT id FROM {} WHERE {}={}'''.format(table, column, entry))
        # print('''SELECT EXISTS(SELECT 1 FROM {} WHERE {}={})'''.format(table,
        #                                                                         column,
        #                                                                         entry))
        # # cursor.execute('''SELECT EXISTS(SELECT 1 FROM {} WHERE {}={})'''.format(table,
        #                                                                         column,
        #                                                                         entry))
        # db.close()
        if cursor.fetchone() is not None:
            return True
        else:
            return False

    def fetch(self, command, all=False):
        db = self.connect()
        cursor = db.cursor()
        cursor.execute(command)

        if all:
            data = cursor.fetchall()
        else:
            data = cursor.fetchone()
        # db.close()
        return data










