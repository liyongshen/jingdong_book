# -*- coding: utf-8 -*-

import re

import scrapy
from jingdong.items import JingdongItem

class JingdongbookSpider(scrapy.Spider):
    name = 'jingdongbook'
    # 价格的url地址域名c0.3.cn
    allowed_domains = ['jd.com','c0.3.cn']
    start_urls = ['https://book.jd.com/booksort.html']

    def parse(self, response):
        node_list = response.xpath('//div[@class="mc"]/dl/dt')
        # print(node_list)
        for node in node_list:
            item = JingdongItem()
            item["b_type"] = node.xpath('./a/text()').extract_first()
            s_tpye_list = node.xpath('./following-sibling::dd[1]/em')
            # print(s_tpye_list)
            for s_tpye in s_tpye_list:
                item["s_type"] = s_tpye.xpath('./a/text()').extract_first()
                s_tpye_url = "http:" + s_tpye.xpath('./a/@href').extract_first()
                # print(s_tpye_url)

                yield scrapy.Request(s_tpye_url,
                                     callback=self.book_list,
                                     meta={"item":item})

    def book_list(self,response):
        booklist = response.xpath('//li[@class = "gl-item"]')
        item = response.meta["item"]
        for book in booklist:
            item["url"]='http:'+book.xpath('.//div[@class="p-name"]/a/@href').extract_first()
            item["name"]=book.xpath('.//div[@class="p-name"]/a/em/text()').extract_first()

            yield scrapy.Request(item["url"],
                                 callback=self.book_detail,
                                 meta={"item":item})
            # 下一页
            next_page = response.xpath('//a[@class = "pn-next"]')
            # print(next_page)
            if next_page:
                next_page_url = 'https://list.jd.com' + next_page.xpath('//a[@class = "pn-next"]/@href').extract_first()
                yield scrapy.Request(next_page_url,
                                     callback=self.book_list,
                                     meta={"item":item})

    def book_detail(self,response):

        if response.status == 200:
            item = response.meta["item"]
            base_url = 'https://c0.3.cn/stock?skuId=%s&venderId=%s&cat=%s&area=1_72_2799_0&extraParam={"originid":"1"}'
            # 将url里的{}和“”转为%7B%22originid%22:%221%22%7D，可用format拼接url
            # 'https://c0.3.cn/stock?skuId=25777087648&venderId=95406&cat=1713,3258,3297&area=1_72_2799_0&extraParam=%7B%22originid%22:%221%22%7D'

            #请求部分网址会出现错误UnicodeDecodeError: 'gbk' codec can't decode byte 0x81 in position 85253: illegal multibyte sequence
            # skuId = re.findall('\?skuId=(\d+?)&location',response.body.decode("gbk"),re.S)[0]
            # venderId = re.findall('venderId:(\d+?),',response.body.decode("gbk"),re.S)[0]
            # cat= re.findall("\?cat=(.*?)'.*?clstag",response.body.decode("gbk"),re.S)[0]
            skuId = re.findall('\?skuId=(\d+?)&location', response.text, re.S)[0]
            venderId = re.findall('venderId:(\d+?),', response.text, re.S)[0]
            cat = re.findall("\?cat=(.*?)'.*?clstag", response.text, re.S)[0]
            # 使用{}和.format拼接会出现错误，因为url里有extraParam={"originid":"1"}
            book_price_url = 'https://c0.3.cn/stock?skuId=%s&venderId=%s&cat=%s&area=1_72_2799_0&extraParam={"originid":"1"}' % (skuId,venderId,cat)


            yield scrapy.Request(book_price_url,
                                 meta={"item":item},
                                 callback=self.books_price)

    def books_price(self,response):

        item = response.meta["item"]
        item["price"]=re.findall('jdPrice.*?p":"(.*?)",',response.body.decode("gbk"),re.S)[0]

        yield item
