from itertools import count
import time
import os
import json

from tornado import httpclient, gen, ioloop

from flag import params_orders, cookie, headers, get_params


class AsyncCrawler(object):
    def __init__(self, concurrency):
        """
        Args:
            concurrency: 并发数
        """
        self.concurrency = concurrency
 
    def start_url(self):
        """
        返回起始地址列表
        Returns: 
            可迭代的url列表或tonado.httpclient.HTTPRequest对象列表
        """
        pass
 
    def parse_list(self, response):
        """
        解析列表页
        Args:
            response: tonado.httpclient.HTTPResponse对象
        Returns:
            可迭代的url列表或tonado.httpclient.HTTPRequest对象列表
        """
        pass
 
    def parse_item(self, response):
        """
        解析详情页
        Args:
            response: tonado.httpclient.HTTPResponse对象
        Returns:
            任意对象，作为pipe_item方法的item参数传递
        """
        pass
    
    def pipe_item(self, item):
        """
        存储内存
        Args:
            item: parse_item方法的返回值
        """
        pass
 
    @gen.coroutine
    def request(self, req):
        # 请求地址，获取列表，请求列表项
        try:
            response = yield httpclient.AsyncHTTPClient().fetch(req)
            _list = self.parse_list(response)
            for sub_req in _list:
                sub_res = yield httpclient.AsyncHTTPClient().fetch(sub_req)
                ret = self.parse_item(sub_res)
                self.pipe_item(ret)
        except httpclient.HTTPError as e:
            print(e)
 
    @gen.coroutine
    def worker(self):
        # 单个协程，每次从起始地址取一个地址，爬取该地址，不断循环，直到迭代器退出
        try:
            while True:
                req = next(self.itor)
                yield self.request(req)
        except StopIteration:
            pass
 
    def run(self):
        # 起始地址，作为一个迭代器
        self.itor = iter(self.start_url())
 
        # 启动多个协程
        @gen.coroutine
        def _run():
            yield [self.worker() for _ in range(self.concurrency)]
 
        #等待所有协程完成
        ioloop.IOLoop.current().run_sync(_run)


class TestCrawler(AsyncCrawler):
 
    def __init__(self, concurrency, dirname):
        self.dirname = dirname
        super(TestCrawler, self).__init__(concurrency)
    
    def start_url(self):
        url = 'http://httpbin.org/get'
        url = 'http://127.0.0.1:5000/api/trades'
        for i in range(1):
            yield httpclient.HTTPRequest(url, headers={'User-Agent': 'Mozilla/5.0'})
 
    def build_request(self, url, method='GET', body=None):
        return httpclient.HTTPRequest(url, 
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.132 Safari/537.36', 
                'cookie': cookie, 'referer': 'https://trade.taobao.com'},
            body=body, method=method
        )
 
    def parse_list(self, response):
        url = 'http://httpbin.org/post'
        url = 'https://trade.taobao.com/trade/itemlist/asyncSold.htm?event_submit_do_query=1&_input_charset=utf8'
        body = json.dumps(get_params(params_orders))
        return [self.build_request(url, method='POST', body=body)]
 
    def parse_item(self, response):
        return json.loads(response.body)
    
    def pipe_item(self, item):
        print(item)
 
crawler = TestCrawler(2, 'girls')
crawler.run()