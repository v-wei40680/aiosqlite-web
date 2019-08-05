#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Default configurations.
'''

__author__ = 'Michael Liao'

configs = {
    'debug': True,
    'db': {
        'host': '127.0.0.1',
        'port': 5432,
        'user': 'wwwdata',
        'password': 'wwwdata',
        'db': 'privateMsg',
        'maxsize': 10,
        'minsize': 1
    },
    'session': {
        'secret': 'Awesome'
    }
}

configs1 = {
    'debug': True,
    'db': {
        'host': '127.0.0.1',
        'port': 3306,
        'user': 'www-data',
        'password': 'www-data',
        'db': 'privateMsg'
    },
    'session': {
        'secret': 'Awesome'
    }
}

# dsn='dbname=%s user=%s password=%s host=%s' % (kw['db'], kw['user'], kw['password'], kw['host']),

