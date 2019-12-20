# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
from scrapy.pipelines.images import ImagesPipeline
import scrapy
import hashlib


# class WeiboPipeline(object):
#     def process_item(self, item, spider):
#         return item


class WeiboImagesPipeline(ImagesPipeline):
    def get_media_requests(self, item, info):
        id = item['id']
        bid = item['bid']
        for img_url in item['pic_urls']:
            print(img_url)
            yield scrapy.Request(url=img_url, meta={'id': id, 'img_url': img_url, 'bid': bid})

    def file_path(self, request, response=None, info=None):
        id = request.meta['id']
        bid = request.meta['bid']
        img_url = request.meta['img_url']
        sha1 = hashlib.sha1()
        sha1.update(img_url.encode('utf8'))
        apath = "./" + str(id) + '/' + str(bid) + '/'
        path = apath + sha1.hexdigest() + '.jpg'
        return path

    def item_completed(self, results, item, info):
        print(results)
        return item
