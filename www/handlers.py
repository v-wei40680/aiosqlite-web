#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'Michael Liao'

' url handlers '

import re, time, json, logging, hashlib, base64, asyncio
from datetime import datetime as d

import aiohttp
from aiohttp import web
from pyquery import PyQuery as pq

from coroweb import get, post
from apis import Page, APIValueError, APIResourceNotFoundError, APIPermissionError
from models import next_id, Trade, FaPiao, Cookie
from config import configs
from flag import parse_cookie, headers, get_params, params_orders, params_flag

def get_page_index(page_str):
    p = 1
    try:
        p = int(page_str)
    except ValueError as e:
        pass
    if p < 1:
        p = 1
    return p

@get('/')
def home(request):
    return 'redirect:/trades'

@get('/trades')
def get_trades(request):
    return {
        '__template__': 'trades.html',
    }

@get('/fapiaos')
def get_fapiaos(request):
    return {
        '__template__': 'fapiaos.html',
    }

ps = get_params(params_orders)
base_url = 'https://trade.taobao.com'

@get('/api/trades')
async def get_api_trades(*, page='1', request, page_size='200'):
    page_index = get_page_index(page)
    print('get api trades')
    num = await Trade.findNumber('count(id)')
    p = Page(num, page_index)
    if num == 0:
        return dict(page=p, trades=())
    trades = await Trade.findAll(orderBy='createTime desc', limit=(page_size, p.offset))
    return dict(page=p, trades=trades)

async def save_or_update_cookie(shopId, cookie):
    shop_cookie = Cookie(id=shopId, cookie_str=cookie)
    num = await Cookie.findNumber('count(id)', "id=?", [shopId,])
    if num == 0:
        await shop_cookie.save()
    else:
        shop_cookie = await Cookie.find(shopId)
        if shop_cookie.cookie_str != cookie:
            shop_cookie.cookie_str = cookie
            shop_cookie.updated_at = time.time()
            await shop_cookie.update()

async def fetch(session, url1, cs, names):
    async with session.post(url1, data=ps) as r:
        # 从天猫后台获取订单
        datas = await r.text()
        datas = json.loads(datas)
        for m in datas['mainOrders']:
            nick = m['buyer']['nick']
            tradeId = m['id']
            createTime = m['orderInfo']['createTime'] # 下单时间
            price = m['payInfo']['actualFee']  # 总价格
            flag = m['extra']['sellerFlag']  # 旗子
            status = m['statusInfo']['text']  # 交易状态
            shop = cs['x']
            if nick in names and flag != 5 and (status != '交易关闭' and status != '等待买家付款'):
                'do flag'
                url = base_url + m['operations'][0]['dataUrl']
                ps1 = get_params(params_flag)
                ps1['_tb_token_'] = cs['_tb_token_']
                ps1['biz_order_id'] = m['id']
                ps1['flag'] = 5
                ps1['memo'] = memo
                print(url, ps1)
                async with session.post(url, data=ps1) as resp:
                    # print(await resp.text())
                    flag = ps1['flag']
            num = await Trade.findNumber('count(id)', "id=?", [tradeId,]) 
            if nick in names:
                trade = Trade(id=tradeId, createTime=createTime, price=price, nick=nick, flag=flag, status=status, shop=shop)
                print("nums: ", num)
                if num == 0:
                    await trade.save()
            
            if num == 1:  
                trade = await Trade.find(tradeId)
                print('status', status, trade.status)
                if trade.flag != flag:
                    trade.flag = flag
                    await trade.update()
                if trade.status != status:
                    trade.status = status
                    await trade.update()
                if status == '卖家已发货' or status == '交易成功':
                    url_wuliu = 'https:' + m['payInfo']['operations'][0]['url']
                    print(trade, "wuliu :" , trade.wuliu, )
                    if trade.wuliu == "":
                        async with session.get(url_wuliu) as r:
                            info = await r.text()
                            doc = pq(info)
                            wuliu = doc('#J_NormalLogistics p').text()
                            trade.wuliu = wuliu
                            print(wuliu)
                            await trade.update()
                 
@post('/api/trades')
async def api_create_trade(request, *, names, cookie, pageNum, memo='', start='', end=''):
    """
    当旺旺出现时，保存订单
    """
    cs = parse_cookie(cookie)
    shopId = cs['x']
    await save_or_update_cookie(shopId, cookie)
    print(shopId, names)
    names = names.split('\n')
    url1 = 'https://trade.taobao.com/trade/itemlist/asyncSold.htm?event_submit_do_query=1&_input_charset=utf8'
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(verify_ssl=False), headers=headers, cookies=cs) as session:
        for page in range(1, int(pageNum)+1):
            ps['pageNum'] = page
            ps['dateBegin'] = str(int(d.timestamp(d.strptime(start, '%Y-%m-%d'))*1000))
            ps['dateEnd'] = str(int(d.timestamp(d.strptime(end, '%Y-%m-%d'))*1000))
            print('page', page)
            if page > 1:
                ps['prePageNo'] = page - 1
            await fetch(session, url1, cs, names)
                   

@post('/api/trades/{id}/delete')
async def api_delete_trades(id, request):
    trade = await Trade.find(id)
    await trade.remove()
    return dict(id=id)

@get('/api/fapiaos')
async def get_api_fapiaos(*, page='1', request, page_size='2000'):
    print(page_size)
    page_index = get_page_index(page)
    num = await FaPiao.findNumber('count(id)')
    p = Page(num, page_index)
    print(p, page_index)
    shop_cookies = await Cookie.findAll()
    if num == 0:
        return dict(page=p, trades=(), shop_cookies=shop_cookies)
    fapiaos = await FaPiao.findAll(orderBy='createTime desc', limit=(page_size, p.offset))
    return dict(page=p, trades=fapiaos, shop_cookies=shop_cookies)

@post('/api/fapiaos')
async def get_tm_trade(request, *, cookie, pageNum):
    cs = parse_cookie(cookie)
    shopId = cs['x']
    await save_or_update_cookie(shopId, cookie)
    url1 = 'https://trade.taobao.com/trade/itemlist/asyncSold.htm?event_submit_do_query=1&_input_charset=utf8'
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(verify_ssl=False), headers=headers, cookies=cs) as session:
        for page in range(1, int(pageNum)+1):
            ps['pageNum'] = page
            print('page', page)
            if page > 1:
                ps['prePageNo'] = page - 1
            async with session.post(url1, data=ps) as r:
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
                        async with session.get(mark_url) as r:
                            mark = await r.text()
                            mark = json.loads(mark)['tip']
                    else:
                        mark = ''
                    o = m['buyer']['operations']
                    if len(o) > 1:
                        # 有留言
                        try:
                            msg_url = base_url + o[1]['dataUrl']
                            async with session.get(msg_url) as r:
                                msg = await r.text()
                                msg = json.loads(msg)['tip']
                                print(msg)
                        except KeyError as e:
                            msg = ''
                            print(e)
                    else:
                        msg = ''
                    fapiao = FaPiao(nick=nick, shop=cs['x'], id=tradeId, status=status, createTime=createTime, price=price, flag=flag, mark=mark, msg=msg)
                    num = await FaPiao.findNumber('count(id)', "id=?", [tradeId,])
                    if num == 0:
                        await fapiao.save()
                    elif num == 1:
                        fapiao = await FaPiao.find(tradeId)
                        fapiao.status = status
                        fapiao.flag = flag
                        fapiao.mark = mark
                        await fapiao.update()

async def do_flag_and_mark(cs, shopId, ):
    url = base_url + "trade/memo/update_sell_memo.htm?seller_id={}&biz_order_id=".format(shopId, )
    ps1 = get_params(params_flag)
    ps1['_tb_token_'] = cs['_tb_token_']
    ps1['biz_order_id'] = m['id']
    ps1['flag'] = 5
    print(url, ps1)
    async with session.post(url, data=ps1) as resp:
        # print(await resp.text())
        flag = ps1['flag']
