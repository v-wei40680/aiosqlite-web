
@get('/api/trades')
async def get_api_trades(*, page='1', request):
    page_index = get_page_index(page)
    """ mongo
    num = Trade.find().count()
    p = Page(num, page_index)
    print(p, page_index)
    if num == 0:
        return dict(page=p, trades=())
    trades = Trade.find().sort('created_at', pymongo.DESCENDING)
    datas = list(trades)
    for x in datas:
        del x['_id']
        x['created_at'] = d.strftime(x['created_at'],'%Y-%m-%d %H:%M:%S')
    data = dict(page=p, trades=datas)
    return data
    """
    
    num = await Flag.findNumber('count(id)')
    p = Page(num, page_index)
    if num == 0:
        return dict(page=p, trades=())
    flags = await Flag.findAll(orderBy='created_at desc', limit=(p.limit, p.offset))
    return dict(page=p, trades=flags)

@post('/api/trades')
async def api_create_trade(request, *, names, cookie):
    """
    """
    cs = parse_cookie(cookie)
    shopId = cs['x']
    print(shopId, names)
    if names != '':
        trades = []
        for name in names.splitlines():
            flag = Flag(nick=name, shop=cs['x'], tradeId='', created_at=d.now(), status='', createTime='', price='', flag='')
            ## trade = dict(nick=name, shop=cs['x'], tradeId='', created_at=d.now(), status='', createTime='', price='', flag='')
            ## num = Trade.find({'nick': name}).count()
            num = await Flag.findNumber('count(id)', "nick=?", [name])
            if num < 1:
                await flag.save()
                # trades.append(trade)
        # logging.info('trades: %s ' % trades)
        ## if trades != []:
        ##    Trade.insert_many(trades)
    else:
        #logging.info('no names')
        pass
    await update_trade(cs, names)
    return 'names save'

async def update_trade(cs, names):
    url1 = 'https://trade.taobao.com/trade/itemlist/asyncSold.htm?event_submit_do_query=1&_input_charset=utf8'
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(verify_ssl=False), headers=headers) as session:
        async with session.post(url1, data=ps, cookies=cs) as r:
            datas = await r.text()
            # print(r.status)
            datas = json.loads(datas)
            mainOrders = datas['mainOrders']
            trades = []
            for m in mainOrders[:]:
                trade = {}
                trade['tradeId'] = m['id']
                trade['nick'] = nick = m['buyer']['nick']
                trade['createTime'] = m['orderInfo']['createTime'] # 下单时间
                trade['price'] = m['payInfo']['actualFee']  # 总价格
                trade['flag'] = m['extra']['sellerFlag']  # 旗子
                trade['status'] = m['statusInfo']['text']  # 交易状态
                trade['shop'] = cs['x']
                if trade['nick'] in names and trade['flag'] != 5:
                    'do flag'
                    base_url = 'https://trade.taobao.com'
                    url = base_url + m['operations'][0]['dataUrl']
                    ps1 = get_params(params_flag)
                    ps1['_tb_token_'] = cs['_tb_token_']
                    ps1['biz_order_id'] = m['id']
                    ps1['flag'] = 2
                    print(url, ps1)
                    async with session.post(url, data=ps1, cookies=cs) as resp:
                        print(await r.text())
                        trade['flag'] = ps1['flag']
                condition = {'nick': nick}
                
                Trade.update_one(condition, {'$set': trade})
                # print(trade)
            # Trade.insert_many(trades)
            return 'parse trade'