# -*- coding: utf-8 -*-
import scrapy
from weibo.settings import MY_USER_AGENT2
import random
import weibo.settings
from scrapy import Selector
import json
import re


class ElecappSpiderSpider(scrapy.Spider):
    name = 'elecapp_spider'
    # allowed_domains = ['https://s.weibo.com/user?q=%E7%94%B5%E5%99%A8']
    # start_urls = ['http://https://s.weibo.com/user?q=%E7%94%B5%E5%99%A8/']
    custom_settings = {
        'ITEM_PIPELINES': {
            'weibo.pipelines.WeiboImagesPipeline': 300,
        }
    }

    header = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
        # 'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Cache-Control': 'max-age=0',
        # 'Connection': 'keep-alive',
        'Referer': 'https://m.weibo.cn/',
        # 'User-Agent': 'Opera/9.80 (Windows NT 6.1; U; zh-cn) Presto/2.9.168 Version/11.50',
    }

    def start_requests(self):
        user_agents = weibo.settings.MY_USER_AGENT2
        user_agent = random.choice(user_agents)
        self.header['User-Agent'] = user_agent
        # 存在107页用户页
        for i in range(1, 108):
            # i = 'https://m.weibo.cn/u/1801242144?uid=1801242144&t=0&luicode=10000011&lfid=100103type%3D3%26q%3D%E7%94%B5%E5%99%A8%26t%3D0'
            # i ='https://m.weibo.cn/detail/4451212902128176'
            next_url = 'https://m.weibo.cn/api/container/getIndex?containerid=100103type%3D3%26q%3D%E7%94%B5%E5%99%A8%26t%3D0&page_type=searchall&page=' + str(
                i)
            yield scrapy.Request(url=next_url, callback=self.parse, headers=self.header, meta={'i': i})

    def parse(self, response):
        """
        获取某页用户id
        """
        i = response.meta['i']
        jl = json.loads(response.body.decode('utf8'))
        # print(jl)
        data = jl['data']
        # 第一页用户页data['cards']第二个有效，其它第一个生效
        if i == 1:
            cards = data['cards'][1]
        else:
            cards = data['cards'][0]
        card_group = cards['card_group']
        # 一页存在十个用户
        for i in card_group:
            user = i['user']
            id = user['id']
            screen_name = user['screen_name']
            print(id, screen_name)
            # 第一页可以不用since_id
            next_url = 'https://m.weibo.cn/api/container/getIndex?containerid=107603' + str(id)
            yield scrapy.Request(url=next_url, callback=self.parse_user, headers=self.header,
                                 meta={'id': id, 'screen_name': screen_name})

    def parse_user(self, response):
        """
        具体到某个用户微博号，获取微博链接
        """
        id = response.meta['id']
        screen_name = response.meta['screen_name']
        jl = json.loads(response.body.decode('utf8'))
        # print(jl)
        data = jl['data']
        cards = data['cards']
        cardlistInfo = data['cardlistInfo']

        # 自身循环，since_id 决定微博的分页，上一页的微博含有第二页的since_id，最后一页没有这个参数
        if 'since_id' in cardlistInfo:
            since_id = cardlistInfo['since_id']
            print(since_id)
            next_url = 'https://m.weibo.cn/api/container/getIndex?containerid=107603' + str(id) + '&since_id=' + str(
                since_id)
            yield scrapy.Request(url=next_url, callback=self.parse_user, headers=self.header, meta={'id': id, 'screen_name':screen_name})

        for i in cards:
            card_type = i['card_type']
            if int(card_type) == 11:
                continue
            mblog = i['mblog']
            # 判断是否为转发微博
            if 'retweeted_status' in mblog:
                continue
            # 每篇微博id（大小写字母加数字）
            bid = mblog['bid']
            #     具体某个微博链接
            scheme = i['scheme']
            print(scheme)
            # 跳转到具体微博
            yield scrapy.Request(url=scheme, callback=self.parse_picture, headers=self.header,
                                 meta={'id': id, 'screen_name': screen_name,'bid': bid})

    def parse_picture(self, response):
        """
        进入一个微博抓取具体图片
        """
        item = {}
        item['id'] = response.meta['id']
        item['screen_name'] = response.meta['screen_name']
        item['bid'] = response.meta['bid']
        html = Selector(response)
        a = html.xpath('/html/body/script[1]/text()').extract_first()
        b = re.findall('render_data = (\[\{.*\])\[', a, re.S)[0]
        jl = json.loads(b)[0]
        status = jl['status']
        pics = status['pics']
        pic_urls = []
        # 每篇微博含有的图片
        for i in pics:
            # print(i)
            large = i['large']
            picture_url = large['url']
            pic_urls.append(picture_url)
        item['pic_urls'] = pic_urls
        yield item
