# -*- coding: utf-8 -*-
__author__ = 'nekocode'

import os
import time
import tornado.ioloop
import tornado.web
import urlparse
import json
import httplib2
from threading import Thread
import weixin_sougou

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
global gzh_cache
global caching_tasks_map
uin = 'MjYxMjk5NTcxNA=='
key = 'af154fdc40fed003ee9c38ad254e00ee07a23334f226598394d116e134e413d06c52aef44d401f6c0cb288853929bf03'
gzh_cache = {}
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
        global gzh_cache
        global caching_tasks_map
        if not self.__loop:
            cache_gzh_articles(self.__openid)
        else:
            print time.strftime('%m-%d %H:%M start autorefresh.', time.localtime(time.time()))
            while True:
                for k in gzh_cache:
                    print 'caching ' + k
                    cache_gzh_articles(k)
                    time.sleep(4)
                print time.strftime('%m-%d %H:%M refresh suc.', time.localtime(time.time()))
                time.sleep(300)

def cache_gzh_articles(openid):
    global gzh_cache
    if openid in caching_tasks_map:
        return
    caching_tasks_map[openid] = ''

    try:
        cookies = weixin_sougou.update_cookies()
        gzh_info = weixin_sougou.get_account_info(openid, cookies=cookies)
        gzh_articles = weixin_sougou.parse_list(openid)
        gzh = dict(info=gzh_info, articles=gzh_articles)

        # driver = webdriver.PhantomJS()
        # driver.get('http://weixin.sogou.com/gzh?openid=' + openid)
        # articles = []
        # elements = driver.find_elements_by_class_name('txt-box')
        # title = elements[0].find_element_by_id('weixinname').text + ' (' + elements[0].find_element_by_tag_name('span').text + ')'
        # for i in range(1, len(elements)):
        #     articles.append(Article(elements[i]))
        # driver.quit()
    except Exception:
        # todo:需要决定是否将没有的公众号也加入到map中
        gzh = dict()

    gzh_cache[openid] = gzh
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
        global gzh_cache
        # openid = self.get_query_argument('openid')
        if not openid:
            self.write(u'没有指定openid')
            return
        if openid not in gzh_cache:
            self.write(u'数据正在缓冲，请稍后再尝试请求')
            CacheThread(openid).start()
            return
        gzh = gzh_cache[openid]
        if 'info' not in gzh:
            self.write(u'请确定公众号openid无误')
            return

        info = gzh['info']
        content = '=======================================</br>'
        content += info['name'] + u'(微信号:' + info['account'] + ')</br>'
        content += '=======================================</br>'
        articles = gzh['articles']
        for article in articles:
            content += u'标题：<a href="' + article['link'] + '">' + article['title'] + '</a></br>'
            content += u'日期：' + article['date'] + '</br>'
            while True:
                rlt = get_wxarticle_state(article['link'])
                time.sleep(2)
                if rlt:
                    break
            article['read_num'], article['like_num'] = rlt
            content += u'阅读数：' + str(article['read_num']) + u'\t点赞数：' + str(article['like_num']) + '</br>'
            content += '=======================================</br>'

        self.write(content)


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
    CacheThread(loop=True).start()
    application.listen(8888)
    tornado.ioloop.IOLoop.instance().start()
