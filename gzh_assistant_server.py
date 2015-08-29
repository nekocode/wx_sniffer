# -*- coding: utf-8 -*-
__author__ = 'nekocode'

import os
import time
import tornado.ioloop
import tornado.web
import urlparse
import json
import httplib2
from threading import Thread, Lock
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

global key_map
global gzh_cache
global caching_tasks_map
global get_key_locker
key_map = {
    'MjYxMjk5NTcxNA==': 'af154fdc40fed003c991ef25a66bb72b39cd762c4d06b2c082e12162787a309bc5725877f69587e0d625366f310102de'
}
gzh_cache = {}
caching_tasks_map = {}
get_now_time = lambda: time.strftime('%m-%d %H:%M', time.localtime(time.time()))
get_key_locker = Lock()

def get_key(openid):
    global get_key_locker
    __uin = ''
    __key = ''

    if get_key_locker.acquire():
        for uin in key_map:
            key = key_map[uin]
            used = False
            for caching_task_openid in caching_tasks_map:
                used_key = caching_tasks_map[caching_task_openid]
                if used_key == key:
                    used = True
                    break
            if not used:
                __uin = uin
                __key = key
                caching_tasks_map[openid] = key
                break

        get_key_locker.release()

    return __uin, __key

def get_wxarticle_state(url, uin, key):
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
        if not self.__loop:
            cache_gzh_articles(self.__openid)
        else:
            while True:
                time.sleep(600)
                print get_now_time() + 'start auto refresh.'
                for k in gzh_cache:
                    print get_now_time() + ' caching ' + gzh_cache[k]['info']['name'] + '.'
                    cache_gzh_articles(k)
                    time.sleep(4)
                print time.strftime('%m-%d %H:%M refresh suc.', time.localtime(time.time()))

def cache_gzh_articles(openid):
    if openid in caching_tasks_map:
        return
    uin, key = get_key(openid)
    if key == '':
        # 如果key被占用光的话，就循环等待
        print 'waiting for vaild key...'
        while key == '':
            uin, key = get_key(openid)
            time.sleep(4)
        print 'get vaild key, start caching.'

    try:
        cookies = weixin_sougou.update_cookies()
        gzh_info = weixin_sougou.get_account_info(openid, cookies=cookies)
        gzh_articles = weixin_sougou.parse_list(openid)
        for gzh_article in gzh_articles:
            rlt = get_wxarticle_state(gzh_article['link'], uin, key)
            time.sleep(2)
            if rlt:
                # 正常返回阅读数以及点赞数
                gzh_article['read_num'], gzh_article['like_num'] = rlt
            else:
                # key失效，结束缓存任务
                print 'err: a key has been invalid!(in task:' + gzh_info['name'] + ')'
                caching_tasks_map.pop(openid)
                return
        gzh = dict(info=gzh_info, articles=gzh_articles)

        # driver = webdriver.PhantomJS()
        # driver.get('http://weixin.sogou.com/gzh?openid=' + openid)
        # articles = []
        # elements = driver.find_elements_by_class_name('txt-box')
        # title = elements[0].find_ element_by_id('weixinname').text + ' (' + elements[0].find_element_by_tag_name('span').text + ')'
        # for i in range(1, len(elements)):
        #     articles.append(Article(elements[i]))
        # driver.quit()
    except Exception:
        # todo:需要决定是否将没有的公众号也加入到map中
        gzh = dict()

    gzh_cache[openid] = gzh
    caching_tasks_map.pop(openid)


class GzhHandler(tornado.web.RequestHandler):
    def data_received(self, chunk):
        pass

    def get(self, openid):
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
            self.write(u'公众号openid好像错误了，正在尝试重新缓冲改公众号数据')
            gzh_cache.pop(openid)
            CacheThread(openid).start()
            return

        info = gzh['info']
        content = '=======================================</br>'
        content += info['name'] + u'(微信号:' + info['account'] + ')</br>'
        content += '=======================================</br>'
        articles = gzh['articles']
        for article in articles:
            content += u'标题：<a href="' + article['link'] + '">' + article['title'] + '</a></br>'
            content += u'日期：' + article['date'] + '</br>'
            content += u'阅读数：' + str(article['read_num']) + u'\t点赞数：' + str(article['like_num']) + '</br>'
            content += '=======================================</br>'

        self.write(content)


class UpdateKeyHandler(tornado.web.RequestHandler):
    def data_received(self, chunk):
        pass

    def post(self, *args, **kwargs):
        global key_map
        post_json = json.loads(self.request.body)
        key_map[post_json['uin']] = post_json['key']
        print get_now_time() + ' refresh key suc.'
        self.write('suc')

global openid_map
openid_map = {
    'oIWsFtyUalZI0CvjGJi7htE0Vuk8': u'华工人',
    'oIWsFt4AIyhWhM2kZXI86sLjzXCU': u'广美人',
    'oIWsFt6S9QnZvoC1RZtWxvm-vPQ4': u'广大人',
    'oIWsFt8Vd7ryx-ghoKdrFZ6kgRWs': u'广外人',
    'oIWsFt4LLIjN4dD6QTk7aYPMLfK4': u'中大人',
    'oIWsFtzeW2YZK_fqJ5RUVYYRNfxI': u'广工人',
    'oIWsFt3_3HS1wZ12YpoT41W7za4g': u'华师人',
    'oIWsFt9GAKT7FNQRKQ4wOwO7aBSs': u'广中医人',
    'oIWsFt_JPW_VaLPvEINekS6yXC08': u'暨大人',
    'oIWsFt7ZQGPGSIol6qxYNUSkAiIU': u'华农人',
    'oIWsFt2Xw2o7OUbKH3Txg0cJ66TA': u'壹大学',
    'oIWsFt-tphuh--mRkYQI-TePFFBo': u'广州高校资讯',
    'oIWsFt_MIf0rZrJCHomQkQyo-AdU': u'e先每日资讯',
}

class MainHandler(tornado.web.RequestHandler):
    def data_received(self, chunk):
        pass

    def get(self, *args, **kwargs):
        content = ''
        for openid in openid_map:
            content += '</br><a href="/gzh/' + openid + '" style="color:#666; font-size:20px;">' + openid_map[openid] + '</a></br>'
            if openid in gzh_cache:
                articles = gzh_cache[openid]['articles']
                for article in articles:
                    if ':' in article['date']:
                        content += u'标题：<a href="' + article['link'] + '">' + article['title'] + '</a></br>'
                        content += u'阅读数：' + str(article['read_num']) +\
                                   u'\t点赞数：' + str(article['like_num']) + '</br>'
                        
        self.write(content)


settings = {
    "static_path": os.path.join(os.path.dirname(__file__), "static")
}

application = tornado.web.Application([
    (r"/", MainHandler),
    (r"/gzh/(.*)", GzhHandler),
    (r"/key", UpdateKeyHandler)
], **settings)


if __name__ == "__main__":
    CacheThread(loop=True).start()
    application.listen(8888)
    tornado.ioloop.IOLoop.instance().start()
