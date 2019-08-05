#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Models for user, blog, comment.
'''

__author__ = 'Michael Liao'

import time, uuid

from orm import Model, StringField, BooleanField, FloatField, TextField, IntegerField

def next_id():
    return '%015d%s000' % (int(time.time() * 1000), uuid.uuid4().hex)

class User(Model):
    __table__ = 'users'

    id = StringField(primary_key=True, default=next_id, ddl='varchar(50)')
    email = StringField(ddl='varchar(50)')
    passwd = StringField(ddl='varchar(50)')
    admin = BooleanField()
    name = StringField(ddl='varchar(50)')
    image = StringField(ddl='varchar(500)')
    created_at = FloatField(default=time.time)

class Blog(Model):
    __table__ = 'blogs'

    id = StringField(primary_key=True, default=next_id, ddl='varchar(50)')
    user_id = StringField(ddl='varchar(50)')
    user_name = StringField(ddl='varchar(50)')
    user_image = StringField(ddl='varchar(500)')
    name = StringField(ddl='varchar(50)')
    summary = StringField(ddl='varchar(200)')
    content = TextField()
    created_at = FloatField(default=time.time)
    readable = BooleanField()
    read_count = IntegerField()

class Comment(Model):
    __table__ = 'comments'

    id = StringField(primary_key=True, default=next_id, ddl='varchar(50)')
    blog_id = StringField(ddl='varchar(50)')
    user_id = StringField(ddl='varchar(50)')
    user_name = StringField(ddl='varchar(50)')
    user_image = StringField(ddl='varchar(500)')
    content = TextField()
    created_at = FloatField(default=time.time)

class Flag(Model):
    __table__ = 'flags'
    id = StringField(primary_key=True, default=next_id, ddl='varchar(50)')
    nick = StringField(ddl='varchar(50)')
    tradeId = StringField(ddl='varchar(50)')
    created_at = FloatField(default=time.time)
    createTime = StringField(ddl='varchar(50)')
    flag = IntegerField()
    shop = StringField(ddl='varchar(50)')
    status = StringField(ddl='varchar(50)')

class Cookie(Model):
    __table__ = 'cookies'
    id = StringField(primary_key=True, ddl='varchar(50)')
    cookie_str = StringField(ddl='varchar(50)')