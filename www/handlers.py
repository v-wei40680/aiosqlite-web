#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'Michael Liao'

' url handlers '

import re, time, json, logging, hashlib, base64, asyncio
from datetime import datetime as d

import markdown2

from faker import Faker
import aiohttp
from aiohttp import web

from coroweb import get, post
from apis import Page, APIValueError, APIResourceNotFoundError, APIPermissionError

from models import User, Blog, Comment, Fo, Message, next_id
from config import configs

COOKIE_NAME = 'awesession'
_COOKIE_KEY = configs.session.secret

fake = Faker('Zh_cn')

def check_admin(request):
    if request.__user__ is None or not request.__user__.admin:
        raise APIPermissionError()

def check_owner(request, blog):
    if request.__user__ is None:
        raise APIPermissionError()
    elif request.__user__.name != blog.user_name:
        raise APIPermissionError()

def get_page_index(page_str):
    p = 1
    try:
        p = int(page_str)
    except ValueError as e:
        pass
    if p < 1:
        p = 1
    return p

def user2cookie(user, max_age):
    '''
    Generate cookie str by user.
    '''
    # build cookie string by: id-expires-sha1
    expires = str(int(time.time() + max_age))
    s = '%s-%s-%s-%s' % (user.id, user.passwd, expires, _COOKIE_KEY)
    L = [user.id, expires, hashlib.sha1(s.encode('utf-8')).hexdigest()]
    return '-'.join(L)

def text2html(text):
    lines = map(lambda s: '<p>%s</p>' % s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'), filter(lambda s: s.strip() != '', text.split('\n')))
    return ''.join(lines)

async def cookie2user(cookie_str):
    '''
    Parse cookie and load user if cookie is valid.
    '''
    if not cookie_str:
        return None
    try:
        L = cookie_str.split('-')
        if len(L) != 3:
            return None
        uid, expires, sha1 = L
        if int(expires) < time.time():
            return None
        user = await User.find(uid)
        if user is None:
            return None
        s = '%s-%s-%s-%s' % (uid, user.passwd, expires, _COOKIE_KEY)
        if sha1 != hashlib.sha1(s.encode('utf-8')).hexdigest():
            logging.info('invalid sha1')
            return None
        user.passwd = '******'
        return user
    except Exception as e:
        logging.exception(e)
        return None

def today_timestamp():
    now = d.now()
    cday = d(now.year, now.month, now.day)
    return cday.timestamp()

@get('/blogs')
async def index(*, page='1', request):
    page_index = get_page_index(page)
    num = await Blog.findNumber('count(id)')
    page = Page(num)
    if num == 0:
        blogs = []
    else:
        if not request.__user__ or not request.__user__.admin:
            blogs = await Blog.findAll('readable=?', [True], orderBy='created_at desc', limit=(page.limit, page.offset))
        elif request.__user__.admin:
            blogs = await Blog.findAll(orderBy='created_at desc', limit=(page.limit, page.offset))
    return {
        '__template__': 'blogs.html',
        'page': page,
        'blogs': blogs
    }

@get('/')
async def fo(*, request):
    if request.__user__:
        user = request.__user__.name
        t = today_timestamp()
        num = await Fo.findNumber('count(id)', "user_name=? and created_at>?", [user, t])
    else:
        num = 0
    return {
        '__template__': 'fo.html',
        'num': num
    }

@get('/api/fo')
async def api_fo(*, request):
    if request.__user__:
        user = request.__user__.name
        t = today_timestamp()
        count = await Fo.findNumber('count(id)', "user_name=? and created_at>?", [user, t])
    else:
        count = 0
    return dict(count=count)

async def fetch(session, url):
    async with session.get(url) as response:
        return await response.text()

@get('/wx')
async def wx():
    return {
        '__template__': 'wxget.html',
    }

@post('/wx')
async def wx_post(*, request, url):
    async with aiohttp.ClientSession() as session:
        html = await fetch(session, url)
        r = re.search('<mpvoice.*name="(\w+).*fileid="(\w+)', html)
        base_url = 'https://res.wx.qq.com/voice/getvoice?mediaid='
        music_id = r.group(2)
        music_url = base_url + music_id + '.mp3'
        return {
            '__template__': 'wx.html',
            'music': dict(url=music_url, name=r.group(1))
        }

@get('/fos')
async def fos(*, request):
    num = await Fo.findNumber('count(id)', groupBy='user_name')
    page = Page(num)
    if num == 0:
        fos = []
    else:
        fos = await Fo.findGroup('user_name, count(id) count', orderBy='count(id) desc', limit=(page.limit, page.offset), groupBy='user_name')
    return {
        '__template__': 'fos.html',
        'page': page,
        'fos': fos
    }

@get('/api/fos')
async def api_fos(*, page='1'):
    page_index = get_page_index(page)
    num = await Fo.findNumber('count(id)')
    p = Page(num, page_index)
    if num == 0:
        return dict(page=p, fos=())
    fos = await Fo.findAll(orderBy='created_at desc', limit=(p.limit, p.offset))
    return dict(page=p, fos=fos)

@post('/api/fos')
async def api_create_fo(request):
    fo = Fo(user_name=request.__user__.name, fo_count='1')
    await fo.save()
    return fo

@get('/blog/{id}')
async def get_blog(id, request):
    blog = await Blog.find(id)
    if not request.__user__:
        blog.read_count += 1
    elif blog.user_name != request.__user__.name:
        blog.read_count += 1
    await blog.update()
    comments = await Comment.findAll('blog_id=?', [id], orderBy='created_at desc')
    for c in comments:
        c.html_content = text2html(c.content)
    blog.html_content = markdown2.markdown(blog.content)
    return {
        '__template__': 'blog.html',
        'blog': blog,
        'comments': comments
    }

@get('/register')
async def register():
    username = fake.name()
    email = fake.email()
    password = fake.numerify() + fake.numerify()
    u = dict(username=username, email=email, password=password)
    print(u)
    return {
        '__template__': 'register.html',
        'u': u
    }

@get('/signin')
async def signin():
    return {
        '__template__': 'signin.html'
    }

@post('/api/authenticate')
async def authenticate(*, email, passwd):
    if not email:
        raise APIValueError('email', 'Invalid email.')
    if not passwd:
        raise APIValueError('passwd', 'Invalid password.')
    users = await User.findAll('email=?', [email])
    if len(users) == 0:
        raise APIValueError('email', 'Email not exist.')
    user = users[0]
    # check passwd:
    sha1 = hashlib.sha1()
    sha1.update(user.id.encode('utf-8'))
    sha1.update(b':')
    sha1.update(passwd.encode('utf-8'))
    if user.passwd != sha1.hexdigest():
        raise APIValueError('passwd', 'Invalid password.')
    # authenticate ok, set cookie:
    r = web.Response()
    r.set_cookie(COOKIE_NAME, user2cookie(user, 86400), max_age=86400, httponly=True)
    user.passwd = '******'
    r.content_type = 'application/json'
    r.body = json.dumps(user, ensure_ascii=False).encode('utf-8')
    return r

@get('/signout')
async def signout(request):
    referer = request.headers.get('Referer')
    r = web.HTTPFound(referer or '/')
    r.set_cookie(COOKIE_NAME, '-deleted-', max_age=0, httponly=True)
    logging.info('user signed out.')
    return r

@get('/manage/')
async def manage():
    return 'redirect:/manage/blogs'

@get('/manage/comments')
async def manage_comments(*, page='1'):
    return {
        '__template__': 'manage_comments.html',
        'page_index': get_page_index(page)
    }

@get('/manage/blogs')
async def manage_blogs(*, page='1'):
    return {
        '__template__': 'manage_blogs.html',
        'page_index': get_page_index(page)
    }

@get('/manage/blogs/create')
async def manage_create_blog():
    return {
        '__template__': 'manage_blog_edit.html',
        'id': '',
        'action': '/api/blogs'
    }

@get('/manage/blogs/edit')
async def manage_edit_blog(*, id, request):
    blog = await Blog.find(id)
    check_owner(request, blog)
    return {
        '__template__': 'manage_blog_edit.html',
        'id': id,
        'action': '/api/blogs/%s' % id
    }

@get('/api/messages')
async def api_messages(*, page='1'):
    page_index = get_page_index(page)
    num = await Message.findNumber('count(id)')
    p = Page(num, page_index)
    if num == 0:
        return dict(page=p, messages=())
    messages = await Message.findAll(orderBy='created_at desc', limit=(p.limit, p.offset))
    return dict(page=p, messages=messages)

@get('/msg/{id}')
async def get_msg(id, request):
    msg = await Message.find(id)
    if not request.__user__:
        msg.read_count += 1
    elif msg.user_name != request.__user__.name or not request.__user__.admin:
        msg.read_count += 1
    await msg.update()
    msg.html_content = markdown2.markdown(msg.content)
    return {
        '__template__': 'msg.html',
        'msg': msg,
    }

@get('/messages')
async def messages(*, page='1', request):
    page_index = get_page_index(page)
    num = await Message.findNumber('count(id)')
    page = Page(num)
    if num == 0:
        messages = []
    else:
        messages = await Message.findAll(orderBy='created_at desc', limit=(page.limit, page.offset))
    return {
        '__template__': 'messages.html',
        'page': page,
        'messages': messages
    }

@get('/manage/messages')
async def manage_messages(*, page='1'):
    return {
        '__template__': 'manage_messages.html',
        'page_index': get_page_index(page)
    }

@get('/manage/messages/create')
async def manage_create_msg():
    return {
        '__template__': 'manage_msg_edit.html',
        'id': '',
        'action': '/api/messages'
    }

@get('/manage/messages/edit')
async def manage_edit_msg(*, id, request):
    msg = await Message.find(id)
    check_owner(request, msg)
    return {
        '__template__': 'manage_msg_edit.html',
        'id': id,
        'action': '/api/messages/%s' % id
    }

@get('/manage/users')
async def manage_users(*, page='1', request):
    check_admin(request)
    return {
        '__template__': 'manage_users.html',
        'page_index': get_page_index(page)
    }

@get('/api/comments')
async def api_comments(*, page='1'):
    page_index = get_page_index(page)
    num = await Comment.findNumber('count(id)')
    p = Page(num, page_index)
    if num == 0:
        return dict(page=p, comments=())
    comments = await Comment.findAll(orderBy='created_at desc', limit=(p.limit, p.offset))
    return dict(page=p, comments=comments)

@post('/api/blogs/{id}/comments')
async def api_create_comment(id, request, *, content):
    user = request.__user__
    if user is None:
        raise APIPermissionError('Please signin first.')
    if not content or not content.strip():
        raise APIValueError('content')
    blog = await Blog.find(id)
    if blog is None:
        raise APIResourceNotFoundError('Blog')
    comment = Comment(blog_id=blog.id, user_id=user.id, user_name=user.name, user_image=user.image, content=content.strip())
    await comment.save()
    return comment

@post('/api/comments/{id}/delete')
async def api_delete_comments(id, request):
    check_admin(request)
    c = await Comment.find(id)
    if c is None:
        raise APIResourceNotFoundError('Comment')
    await c.remove()
    return dict(id=id)

@get('/api/users')
async def api_get_users(*, page='1'):
    page_index = get_page_index(page)
    num = await User.findNumber('count(id)')
    p = Page(num, page_index)
    if num == 0:
        return dict(page=p, users=())
    users = await User.findAll(orderBy='created_at desc', limit=(p.limit, p.offset))
    for u in users:
        u.passwd = '******'
    return dict(page=p, users=users)

_RE_EMAIL = re.compile(r'^[a-z0-9\.\-\_]+\@[a-z0-9\-\_]+(\.[a-z0-9\-\_]+){1,4}$')
_RE_SHA1 = re.compile(r'^[0-9a-f]{40}$')

@post('/api/users')
async def api_register_user(*, email, name, passwd):
    if not name or not name.strip():
        raise APIValueError('name')
    if not email or not _RE_EMAIL.match(email):
        raise APIValueError('email')
    if not passwd or not _RE_SHA1.match(passwd):
        raise APIValueError('passwd')
    users = await User.findAll('email=?', [email])
    if len(users) > 0:
        raise APIError('register:failed', 'email', 'Email is already in use.')
    uid = next_id()
    sha1_passwd = '%s:%s' % (uid, passwd)
    user = User(id=uid, name=name.strip(), email=email, passwd=hashlib.sha1(sha1_passwd.encode('utf-8')).hexdigest(), image='http://www.gravatar.com/avatar/%s?d=mm&s=120' % hashlib.md5(email.encode('utf-8')).hexdigest())
    await user.save()
    # make session cookie:
    r = web.Response()
    r.set_cookie(COOKIE_NAME, user2cookie(user, 86400), max_age=86400, httponly=True)
    user.passwd = '******'
    r.content_type = 'application/json'
    r.body = json.dumps(user, ensure_ascii=False).encode('utf-8')
    return r

@get('/api/blogs')
async def api_blogs(*, page='1'):
    page_index = get_page_index(page)
    num = await Blog.findNumber('count(id)')
    p = Page(num, page_index)
    if num == 0:
        return dict(page=p, blogs=())
    blogs = await Blog.findAll(orderBy='created_at desc', limit=(p.limit, p.offset))
    return dict(page=p, blogs=blogs)

@get('/api/blogs/user')
async def api_blogs_user(*, page='1', request):
    user = request.__user__.name
    page_index = get_page_index(page)
    if not request.__user__.admin:
        num = await Blog.findNumber('count(id)', "user_name=?", [user])
    else:
        num = await Blog.findNumber('count(id)')
    p = Page(num, page_index)
    if num == 0:
        return dict(page=p, blogs=())
    if not request.__user__.admin:
        blogs = await Blog.findAll("user_name=?", [user], orderBy='created_at desc', limit=(p.limit, p.offset))
    else:
        blogs = await Blog.findAll(orderBy='created_at desc', limit=(p.limit, p.offset))
    return dict(page=p, blogs=blogs)

@get('/blogs/{user}')
async def user(*, page='1', user):
    page_index = get_page_index(page)
    num = await Blog.findNumber('count(id)', "user_name=? and readable=?", [user, True])
    page = Page(num)
    if num == 0:
        blogs = []
    else:
        blogs = await Blog.findAll("user_name=? and readable=?", [user, True], orderBy='created_at desc', limit=(page.limit, page.offset))
    return {
        '__template__': 'blogs.html',
        'page': page,
        'blogs': blogs
    }

@get('/api/blogs/{id}')
async def api_get_blog(*, id):
    blog = await Blog.find(id)
    return blog

@post('/api/blogs')
async def api_create_blog(request, *, name, summary, content, readable):
    if not name or not name.strip():
        raise APIValueError('name', 'name cannot be empty.')
    if not summary or not summary.strip():
        raise APIValueError('summary', 'summary cannot be empty.')
    if not content or not content.strip():
        raise APIValueError('content', 'content cannot be empty.')
    blog = Blog(user_id=request.__user__.id, user_name=request.__user__.name, user_image=request.__user__.image, name=name.strip(), summary=summary.strip(), content=content.strip(), readable=readable)
    await blog.save()
    return blog

@post('/api/blogs/{id}')
async def api_update_blog(id, request, *, name, summary, content):
    blog = await Blog.find(id)
    check_owner(request, blog)
    if not name or not name.strip():
        raise APIValueError('name', 'name cannot be empty.')
    if not summary or not summary.strip():
        raise APIValueError('summary', 'summary cannot be empty.')
    if not content or not content.strip():
        raise APIValueError('content', 'content cannot be empty.')
    blog.name = name.strip()
    blog.summary = summary.strip()
    blog.content = content.strip()
    await blog.update()
    return blog

@post('/api/blogs/{id}/delete')
async def api_delete_blog(request, *, id):
    # check_admin(request)
    blog = await Blog.find(id)
    check_owner(request, blog)
    await blog.remove()
    return dict(id=id)

@post('/api/blogs/{id}/showOrHide')
async def api_show_or_hide_blog(request, *, id):
    blog = await Blog.find(id)
    check_owner(request, blog)
    if blog.readable == False:
        blog.readable = True
    else:
        blog.readable = False
    await blog.update()
    return dict(id=id)

@get('/api/messages/{id}')
async def api_get_messages(*, id):
    msg = await Message.find(id)
    return msg

@post('/api/messages')
async def api_create_msg(request, *, to_user, name, summary, content):
    if not to_user or not to_user.strip():
        raise APIValueError('to_user', 'to_user cannot be empty.')
    if not name or not name.strip():
        raise APIValueError('name', 'name cannot be empty.')
    if not summary or not summary.strip():
        raise APIValueError('summary', 'summary cannot be empty.')
    if not content or not content.strip():
        raise APIValueError('content', 'content cannot be empty.')
    msg = Message(user_id=request.__user__.id, user_name=request.__user__.name, user_image=request.__user__.image, to_user=to_user.strip(), name=name.strip(), summary=summary.strip(), content=content.strip())
    await msg.save()
    return msg

@post('/api/messages/{id}')
async def api_update_msg(id, request, *, name, summary, content):
    msg = await Message.find(id)
    check_owner(request, msg)
    if not name or not name.strip():
        raise APIValueError('name', 'name cannot be empty.')
    if not summary or not summary.strip():
        raise APIValueError('summary', 'summary cannot be empty.')
    if not content or not content.strip():
        raise APIValueError('content', 'content cannot be empty.')
    msg.name = name.strip()
    msg.summary = summary.strip()
    msg.content = content.strip()
    await msg.update()
    return msg

@post('/api/messages/{id}/delete')
async def api_delete_msg(request, *, id):
    # check_admin(request)
    msg = await Message.find(id)
    check_owner(request, msg)
    await msg.remove()
    return dict(id=id)
