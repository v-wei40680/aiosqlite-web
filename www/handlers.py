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

from models import User, Blog, Comment, next_id, Flag, FaPiao
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

@get('/')
async def home(*, page='1', request):
    return 'redirect:/trades'

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

from flag import parse_cookie, headers, get_params, params_orders, params_flag

@get('/flag')
async def flag():
    flags = await Flag.findAll(orderBy='created_at desc')

    url = 'http://httpbin.org/cookies'
    cookies = {'cookies_are': 'working'}
    async with aiohttp.ClientSession(cookies=cookies) as session:
        async with session.get(url) as resp:
            r = resp.json()
            assert await resp.json() == {
            "cookies": {"cookies_are": "working"}}
    return {
        '__template__': 'flag.html',
        'flags': flags,
    }

@post('/flag')
async def post_flag(request, *, text):
    names = text
    print(names)
    for name in names.split():
        flag = Flag(nick=name, tradeId='')
        await flag.save()
    return 'redirect:/flag'

@get('/api/flag')
async def api_flag(*, page='1'):
    page_index = get_page_index(page)
    num = await Flag.findNumber('count(id)')
    p = Page(num, page_index)
    if num == 0:
        return dict(page=p, flags=())
    flags = await Flag.findAll(orderBy='created_at desc', limit=(p.limit, p.offset))
    return dict(page=p, flags=flags)

ps = get_params(params_orders)
base_url = 'https://trade.taobao.com'

@get('/trades')
async def get_trades(*, request):
    return {
        '__template__': 'trades.html',
    }

import json

@get('/api/trades')
async def get_api_trades(*, page='1', request):
    page_index = get_page_index(page)
    num = await Flag.findNumber('count(id)')
    p = Page(num, page_index)
    print(p, page_index)
    if num == 0:
        return dict(page=p, trades=())
    flags = await Flag.findAll(orderBy='createTime desc', limit=(200, p.offset))
    datas = list(flags)
    data = dict(page=p, trades=datas)
    return data

@post('/api/trades')
async def api_create_trade(request, *, names, cookie, pageNum):
    """
    """
    cs = parse_cookie(cookie)
    shopId = cs['x']
    print(shopId, names)
    if names != '':
        for name in names.splitlines():
            flag_num = await Flag.findNumber('count(id)', "nick=?", [name])
            if flag_num < 1:
                flag = Flag(nick=name, shop=cs['x'], tradeId='', created_at=d.now(), status='', createTime='', price='', flag='')
                await flag.save()
    else:
        #logging.info('no names')
        pass
    await update_trade(cs, names, pageNum)
    return 'names save'

async def update_trade(cs, names, pageNum):
    url1 = 'https://trade.taobao.com/trade/itemlist/asyncSold.htm?event_submit_do_query=1&_input_charset=utf8'
    base_url = 'https://trade.taobao.com'
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(verify_ssl=False), headers=headers) as session:
        for page in range(1, int(pageNum)+1):
            ps['pageNum'] = page
            print('page', page)
            if page > 1:
                ps['prePageNo'] = page - 1
            async with session.post(url1, data=ps, cookies=cs) as r:
                datas = await r.text()
                # print(r.status)
                datas = json.loads(datas)
                mainOrders = datas['mainOrders']
                for m in mainOrders[:]:
                    nick = m['buyer']['nick']
                    flag_num = await Flag.findNumber('count(id)', "nick=?", [nick])
                    if flag_num > 0:
                        flags = await Flag.findAll('nick=?', [nick], orderBy='createTime desc')
                        flag = flags[0]
                        print('flag', nick, flag)
                        flag.nick = m['buyer']['nick']
                        flag.tradeId = m['id']
                        flag.createTime = m['orderInfo']['createTime'] # 下单时间
                        flag.price = m['payInfo']['actualFee']  # 总价格
                        flag.flag = m['extra']['sellerFlag']  # 旗子
                        flag.status = m['statusInfo']['text']  # 交易状态
                        flag.shop = cs['x']
                        if flag.nick in names and flag.flag != 5 and flag.status != '交易关闭':
                            'do flag'
                            url = base_url + m['operations'][0]['dataUrl']
                            ps1 = get_params(params_flag)
                            ps1['_tb_token_'] = cs['_tb_token_']
                            ps1['biz_order_id'] = m['id']
                            ps1['flag'] = 5
                            print(url, ps1)
                            async with session.post(url, data=ps1, cookies=cs) as resp:
                                print(await r.text())
                                flag.flag = ps1['flag']
                        await flag.update()

@get('/fapiaos')
async def get_fapiaos(*, request):
    return {
        '__template__': 'fapiaos.html',
    }

@get('/api/fapiaos')
async def get_api_fapiaos(*, page='1', request):
    page_index = get_page_index(page)
    num = await FaPiao.findNumber('count(id)')
    p = Page(num, page_index)
    print(p, page_index)
    if num == 0:
        return dict(page=p, trades=())
    fapiaos = await FaPiao.findAll(orderBy='createTime desc', limit=(2000, p.offset))
    datas = list(fapiaos)
    data = dict(page=p, trades=datas)
    return data

@post('/api/fapiaos')
async def get_tm_trade(request, *, cookie, pageNum):
    cs = parse_cookie(cookie)
    shopId = cs['x']
    url1 = 'https://trade.taobao.com/trade/itemlist/asyncSold.htm?event_submit_do_query=1&_input_charset=utf8'
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(verify_ssl=False), headers=headers) as session:
        for page in range(1, int(pageNum)+1):
            ps['pageNum'] = page
            print('page', page)
            if page > 1:
                ps['prePageNo'] = page - 1
            async with session.post(url1, data=ps, cookies=cs) as r:
                datas = await r.text()
                # print(r.status)
                datas = json.loads(datas)
                mainOrders = datas['mainOrders']
                for m in mainOrders[:]:
                    nick = m['buyer']['nick']
                    tradeId = m['id']
                    createTime = m['orderInfo']['createTime'] # 下单时间
                    price = m['payInfo']['actualFee']  # 总价格
                    flag = m['extra']['sellerFlag']  # 旗子
                    status = m['statusInfo']['text']  # 交易状态
                    if len(m['operations'][0].keys()) == 7 and flag != 5:
                        # 有备注
                        mark_url = base_url+ m['operations'][0]['dataUrl']
                        async with session.get(mark_url, cookies=cs) as r:
                            mark = await r.text()
                            mark = json.loads(mark)['tip']
                    else:
                        mark = ''
                    o = m['buyer']['operations']
                    if len(o) > 1:
                        # 有留言
                        try:
                            msg_url = base_url + o[1]['dataUrl']
                            async with session.get(msg_url, cookies=cs) as r:
                                msg = await r.text()
                                msg = json.loads(msg)['tip']
                                print(msg)
                        except KeyError as e:
                            msg = ''
                            print(e)
                    else:
                        msg = ''
                    fapiao = FaPiao(nick=nick, shop=cs['x'], id=tradeId, created_at=d.now(), status=status, createTime=createTime, price=price, flag=flag, mark=mark, msg=msg)
                    await fapiao.save()