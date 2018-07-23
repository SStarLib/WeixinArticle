from urllib.parse import urlencode
import pymongo
from requests.exceptions import ConnectionError
import requests
from pyquery import PyQuery as pq
from config import *


class weixin:
    def __init__(self, url, keyword, page=1):
        self.data = {
            'query': keyword,
            'type': '2',
            'page': page,
            'ie': 'utf8',
        }
        self.headers = {
            'Cookie': 'CXID = EC94C09EC9CE822D10774B09AE7D87CC;ad = 3optvyllll2bSBHXlllllVHVuLtlllllXMwQ5yllll9llllljZlll5 @ @ @ @ @ @ @ @ @ @;SUID = 3D16E29F5B68860A5B459B670001B473;IPLOC = CN1100;SUV = 1532324570162007;pgv_pvi = 9663309824;pgv_si = s4210301952;ABTEST = 7 | 1532324575 | v1;weixinIndexVisited = 1;JSESSIONID = aaamYCC7jd3Cq9GMroHsw;sct = 2;td_cookie = 18446744072937228543;ppinf = 5 | 1532324650 | 1533534250 | dHJ1c3Q6MToxfGNsaWVudGlkOjQ6MjAxN3x1bmlxbmFtZToxMTc6JUU4JUJGJTk5JUU2JTk4JUFGJUU0JUI4JTgwJUU0JUJEJThEJUU0JUI4JThEJUU2JTg0JUJGJUU5JTgwJThGJUU5JTlDJUIyJUU1JUE3JTkzJUU1JTkwJThEJUU3JTlBJTg0JUU3JUJEJTkxJUU1JThGJThCfGNydDoxMDoxNTMyMzI0NjUwfHJlZm5pY2s6MTE3OiVFOCVCRiU5OSVFNiU5OCVBRiVFNCVCOCU4MCVFNCVCRCU4RCVFNCVCOCU4RCVFNiU4NCVCRiVFOSU4MCU4RiVFOSU5QyVCMiVFNSVBNyU5MyVFNSU5MCU4RCVFNyU5QSU4NCVFNyVCRCU5MSVFNSU4RiU4Qnx1c2VyaWQ6NDQ6bzl0Mmx1QjhLdWJwVkdKNFNtVFhnbFRhZG9jTUB3ZWl4aW4uc29odS5jb218;pprdig = jsi66I_WrnGiYs2UUy_bbNpMBOH - 77Y2zrs06 - p1bfNPqWk - 6V0Uh5QEsSPERzlc5098w_tx0uB - qhIVGPe1Dd1qWkTnq71k1GITBe_671As6MSGOmnTyXiXVomvTptj82BhEqQPnZP9Z9GaAt5joPmcLaSthYmmDRFS9LZtr04;sgid = 12 - 36218815 - AVtVayqEbYtQhY3gice4KHu8;ppmdig = 1532324650000000f05805cec49bcbf6dd49a85a7b48ed39;PHPSESSID = mdlffk6fi5pu8lacttgh43lni4;SUIR = D7C5314CD2D6A376CCD521B9D354F458;SNUID = EFFD0974ECE99D4FAC8EA633EC860E0D;seccodeRight = success;successCount = 2 | Mon, 23Jul201805: 52:40GMT;refresh = 1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36',
            'Host': 'weixin.sogou.com',
            'Upgrade-Insecure-Requests': '1',
        }
        self.url = url
        self.proxy_url = PROXY_URL
        self.proxy = None
        self.MaxCount = MAX_COUNT
        client=pymongo.MongoClient(MONGO_URI)
        self.db=client[MONGO_DB]

    # 获取文章的url
    def get_html(self, count=1):
        '''
        从搜狗搜索上抓取微信文章网页信息
        :param count: 连接失败最大尝试次数
        :return: 返回网页内容
        '''
        queries = urlencode(self.data)
        url = self.url + queries
        if count >= self.MaxCount:
            print('Tried too many counts')
            return None
        try:
            if self.proxy:
                proxies = {
                    "http": "http://{}".format(self.proxy.strip()),
                }
                respone = requests.get(url, allow_redirects=False, headers=self.headers, proxies=proxies)
            else:
                respone = requests.get(url, allow_redirects=False, headers=self.headers)
            if respone.status_code == 200:
                return respone.text
            if respone.status_code == 302:
                print('302')
                self.proxy = self.get_proxy()
                if self.proxy:
                    print('Using proxy', self.proxy)
                    return self.get_html()
                else:
                    print('Get proxy failed')
                    return None
        except ConnectionError as e:
            print('Error Occurred', e.args)
            proxy = self.get_proxy()
            count += 1
            return self.get_html(count)

    def get_proxy(self):
        '''
        获取代理
        :return: 代理
        '''
        try:
            response = requests.get(self.proxy_url)
            if response.status_code == 200:
                return response.text
            return None
        except ConnectionError:
            return None

    def parse_html(self, html):
        '''
        pyquery获取微信文章的url
        :param html: 网页文本内容
        :return: 生成器：文章url
        '''
        data = pq(html)
        items = data('#main > div.news-box > ul li .txt-box h3 a').items()
        for item in items:
            yield item.attr('href')

    # 通过文章的url获取文章内容
    def get_article(self, url):
        '''
        :param url: 文章url
        :return: 网页内容
        '''
        try:
            response = requests.get(url)
            if response.status_code == 200:
                return response.text
            return None
        except ConnectionError:
            return None

    def parse_article(self, text):
        data = pq(text)
        title = data('#activity-name').text()
        content = data('#js_content').text()
        nickname = data('#js_name').text()
        date = data('#publish_time').text()
        weNum = data('#js_profile_qrcode > div > p:nth-child(3) > span').text()
        return {
            'title': title,
            'content': content,
            'date': date,
            'nickname': nickname,
            'weNum': weNum,
        }
    #保存到MongoDB数据库
    def save_mongo(self):
        if self.db['articles'].update({'title':self.data['title']},{'$set':self.data},True):
            print('Saved to mongo',self.data['title'])
        else:
            print('Saved to Mongo Failed',self.data['title'])

    def search_article(self):
        html = self.get_html()
        if html:
            for ar_url in self.parse_html(html):
                text = self.get_article(ar_url)
                info = self.parse_article(text)
                if info:
                    self.save_mongo(info)

        else:
            print('未获取到网页信息')


if __name__ == '__main__':
    base_url = 'http://weixin.sogou.com/weixin?'
    for page in range(1,51):
        wx=weixin(base_url,KEYWORD,page)
        wx.search_article()

