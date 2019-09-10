#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Models for flag, fapiaos
'''

__author__ = 'Michael Liao'

import time, uuid

from orm import Model, StringField, BooleanField, FloatField, TextField, IntegerField

def next_id():
    return str(int(time.time() * 1000))

class Trade(Model):
    __table__ = 'trades'
    id = StringField(primary_key=True, ddl='varchar(50)')
    nick = StringField(ddl='varchar(50)')
    created_at = FloatField(default=time.time)
    createTime = StringField(ddl='varchar(50)')
    flag = IntegerField()
    price = FloatField()
    shop = StringField(ddl='varchar(50)')
    status = StringField(ddl='varchar(50)')
    wuliu = StringField(ddl='varchar(50)', default="")

class FaPiao(Model):
    __table__ = 'fapiaos'
    id = StringField(primary_key=True, ddl='varchar(50)')
    nick = StringField(ddl='varchar(50)')
    created_at = FloatField(default=time.time)
    createTime = StringField(ddl='varchar(50)')
    flag = StringField(ddl='varchar(50)')
    price = StringField(ddl='varchar(50)')
    shop = StringField(ddl='varchar(50)')
    status = StringField(ddl='varchar(50)')
    mark = TextField()
    msg = TextField()

class Cookie(Model):
    __table__ = 'cookies'
    id = StringField(primary_key=True, ddl='varchar(50)')
    cookie_str = StringField(ddl='varchar(50)')
    created_at = FloatField(default=time.time)
    updated_at = FloatField()