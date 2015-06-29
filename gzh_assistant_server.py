# -*- coding: utf-8 -*-
__author__ = 'nekocode'

import os
import time
import tornado.ioloop
import tornado.web
import urlparse
import json
import httplib2
from selenium import webdriver
from threading import Thread

__send_headers = {
    'Host': 'mp.weixin.qq.com',
    'User-Agent':
        'Mozilla/5.0 (Linux; U; Android 4.4.4; zh-cn; MI 3W Build/KTU84P) '
        'AppleWebKit/533.1 (KHTML, like Gecko)Version/4.0 MQQBrowser/5.4 TBS/025411 '
        'Mobile Safari/533.1 MicroMessenger/6.1.0.73_r1097298.543 NetType/WIFI',
    'Accept': 'text/xml, text/html, application/xhtml+xml, image/png, text/plain, */*;q=0.8',
    'Accept-Charset': 'utf-8, iso-8859-1, utf-16, *;q=0.7',
    'Accept-Encoding': 'gzip',
    'Connection': 'keep-alive',
    'X-Requested-With': 'XMLHttpRequest'
}

global uin
global key
global html_cache
global caching_tasks_map
uin = 'MjYxMjk5NTcxNA=='
key = 'af154fdc40fed003a2cc2d85d51f776fe0ece39d0c7b9db211b14292833abf15150633dd4e0907ef5120a7adc4c89097'
html_cache = {
    'no_cache': u'数据正在缓冲，请稍后再尝试请求'
}
caching_tasks_map = {}


def get_wxarticle_state(url):
    global uin
    global key
    if len(key) == 0:
        return None
    query = urlparse.urlparse(url).query
    params = urlparse.parse_qs(query)
    __biz = params["__biz"][0]
    mid = params["mid"][0]
    sn = params["sn"][0]
    idx = params["idx"][0]
    url = 'http://mp.weixin.qq.com/mp/getappmsgext'
    url += '?' + '__biz=' + __biz + '&mid=' + mid + '&sn=' + sn + '&idx=' \
           + idx + '&devicetype=android-10&version=&f=json' \
           + '&uin=' + uin + '&key=' + key
    __http = httplib2.Http()
    response, content = __http.request(url, 'GET', headers=__send_headers)
    # content = content.decode('utf-8', 'replace').encode(sys.getfilesystemencoding())
    try:
        rlt_json = json.loads(content)
        return rlt_json['appmsgstat']['read_num'], rlt_json['appmsgstat']['like_num']
    except Exception:
        return None

class CacheThread(Thread):
    __loop = False

    def __init__(self, openid='', loop=False):
        Thread.__init__(self)
        self.__openid = openid
        self.__loop = loop

    def run(self):
        global html_cache
        global caching_tasks_map
        if not self.__loop:
            cache_gzh_articles(self.__openid)
        else:
            while True:
                for k in html_cache:
                    cache_gzh_articles(k)
                    time.sleep(4)
                time.sleep(300)

def cache_gzh_articles(openid):
    global html_cache
    if openid in caching_tasks_map:
        return
    caching_tasks_map[openid] = ''

    try:
        driver = webdriver.PhantomJS()
        driver.get('http://weixin.sogou.com/gzh?openid=' + openid)
        articles = []
        elements = driver.find_elements_by_class_name('txt-box')
        title = elements[0].find_element_by_id('weixinname').text + ' (' + elements[0].find_element_by_tag_name('span').text + ')'
        for i in range(1, len(elements)):
            articles.append(Article(elements[i]))
        driver.quit()
        content = '=======================================</br>'
        content += title + '</br>'
        content += '=======================================</br>'
        for article in articles:
            content += u'标题：<a href="' + article.url + '">' + article.title + '</a></br>'
            content += u'日期：' + article.date + '</br>'
            while True:
                rlt = get_wxarticle_state(article.url)
                time.sleep(2)
                if rlt:
                    break
            article.read_num, article.like_num = rlt
            content += u'阅读数：' + str(article.read_num) + u'\t点赞数：' + str(article.like_num) + '</br>'
            content += '=======================================</br>'
    except Exception:
        # todo:需要决定是否将没有的公众号也加入到map中
        content = u'不存在该公众号，请检查openid是否输入错误'

    html_cache[openid] = content
    caching_tasks_map.pop(openid)


class Article(object):
    def __init__(self, web_element):
        a = web_element.find_element_by_class_name('news_lst_tab')
        self.title = a.text
        self.url = a.get_attribute('href')
        p = web_element.find_elements_by_tag_name('p')
        self.review = p[0].text
        self.date = p[1].text
        self.read_num = ''
        self.like_num = ''


class MainHandler(tornado.web.RequestHandler):
    def data_received(self, chunk):
        pass

    def get(self, openid):
        global html_cache
        # openid = self.get_query_argument('openid')
        if not openid:
            self.write(u'没有指定openid')
            return
        if openid not in html_cache:
            self.write(html_cache['no_cache'])
            CacheThread(openid).start()
            return
        self.write(html_cache[openid])


class UpdateKeyHandler(tornado.web.RequestHandler):
    def data_received(self, chunk):
        pass

    def post(self, *args, **kwargs):
        global uin
        global key
        uin = self.get_argument("uin", "")
        key = self.get_argument("key", "")


settings = {
    "static_path": os.path.join(os.path.dirname(__file__), "static")
}

application = tornado.web.Application([
    (r"/gzh/(.*)", MainHandler),
    (r"/key", UpdateKeyHandler)
], **settings)

if __name__ == "__main__":
    application.listen(8888)
    tornado.ioloop.IOLoop.instance().start()
    CacheThread(loop=True).start()
