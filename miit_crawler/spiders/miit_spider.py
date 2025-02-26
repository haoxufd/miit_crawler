# -*- coding: utf-8 -*-
import scrapy
import logging
from ..items import MiitCrawlerItem

from miit_crawler.exceptions import CaptchaRecognitionError
import json

import pandas


class MiitSpider(scrapy.Spider):
    name = 'miit_spider'
    allowed_domains = ['app.miit-eidc.org.cn']
    
    def __init__(self, *args, **kwargs):
        super(MiitSpider, self).__init__(*args, **kwargs)
        self.logger.setLevel(logging.INFO)
        try:
            df = pandas.read_excel('crawled_data/miit_data.xlsx')
            self.last_num = int(df.iloc[-1, 0].item())
        except FileNotFoundError as e:
            self.logger.error(f"文件 crawled_data/miit_data.xlsx 不存在: {e}")
            self.last_num = 0
        with open('urls.json', 'r') as f:
            self.start_urls = json.load(f)[self.last_num:]
    def start_requests(self):
        """
        启动爬虫的起始请求
        """
        for i, url in enumerate(self.start_urls):
            self.logger.info(f"开始抓取: {url}")
            yield scrapy.Request(url=url, callback=self.parse, meta={'number': i + self.last_num + 1})
    
    def parse(self, response):
        """
        解析页面
        """
        # 检查是否仍在验证页面
        if "访问行为验证" in response.text:
            self.logger.warning("仍然在验证页面，验证可能失败")
            # 如果仍在验证页面，重新请求
            raise CaptchaRecognitionError("滑块验证失败")
            
        self.logger.info("成功获取内容页面，开始解析...")
        
        # 创建Item
        item = MiitCrawlerItem()

        item["request_url"] = response.request.url
        item["request_number"] = response.request.meta['number']
        
        # 提取图片URL
        image_urls = []
        for img in response.css('img[src^="getPic"]'):
            img_url = response.urljoin(img.attrib['src'])
            image_urls.append(img_url)
        item['image_urls'] = image_urls
        
        # 提取基本信息
        item['product_id'] = response.xpath('//tr/td[contains(text(), "产品号")]/following-sibling::td/span/text()').get('').strip()
        item['batch'] = response.xpath('//tr/td[contains(text(), "批次")]/following-sibling::td/span/text()').get('').strip()
        item['publish_date'] = response.xpath('//tr/td[contains(text(), "发布日期")]/following-sibling::td/span/text()').get('').strip()
        
        # 提取企业信息
        item['company_name'] = response.xpath('//tr/td[contains(text(), "企业名称")]/following-sibling::td/span/text()').get('').strip()
        # 提取产品型号名称 (在HTML中未明确标出，可能需要从其他字段获取)
        item['product_model_name'] = response.xpath('//tr/td[contains(text(), "车辆型号")]/following-sibling::td/span/text()').get('').strip()
        item['product_trademark'] = response.xpath('//tr/td[contains(text(), "产品商标")]/following-sibling::td/span/text()').get('').strip()
        item['production_address'] = response.xpath('//tr/td[contains(text(), "生产地址")]/following-sibling::td/span/text()').get('').strip()
        # 注册地址在HTML中未找到，设为空字符串
        item['registered_address'] = ''
        
        # 提取车辆信息
        item['vehicle_model'] = response.xpath('//tr/td[contains(text(), "车辆型号")]/following-sibling::td/span/text()').get('').strip()
        item['vehicle_name'] = response.xpath('//tr/td[contains(text(), "车辆名称")]/following-sibling::td/span/text()').get('').strip()
        item['chassis_id'] = response.xpath('//tr/td[contains(text(), "底盘ID")]/following-sibling::td/span/text()').get('').strip()
        item['chassis_model_and_company'] = response.xpath('//tr/td[contains(text(), "底盘型号及企业")]/following-sibling::td/span/text()').get('').strip()
        item['vin'] = response.xpath('//tr/td[contains(text(), "车辆识别代号")]/following-sibling::td/span/text()').get('').strip()
        
        # 提取燃料和排放信息
        item['fuel_type'] = response.xpath('//tr/td[contains(text(), "燃料种类")]/following-sibling::td/span/text()').get('').strip()
        item['fuel_consumption'] = response.xpath('//tr/td[contains(text(), "油耗")]/following-sibling::td/span/text()').get('').strip()
        item['emission_standard'] = response.xpath('//tr/td[contains(text(), "排放依据标准")]/following-sibling::td/span/text()').get('').strip()
        
        # 提取发动机信息
        item['engine_manufacturer'] = response.xpath('//tr/td[contains(text(), "发动机生产企业")]/following-sibling::td/span/text()').get('').strip()
        item['engine_model'] = response.xpath('//tr/td[contains(text(), "发动机型号")]/following-sibling::td/span/text()').get('').strip()
        item['displacement'] = response.xpath('//tr/td[contains(text(), "排量")]/following-sibling::td/span/text()').get('').strip()
        
        # 提取其他信息
        item['reflective_mark_company'] = response.xpath('//tr/td[contains(text(), "反光标识企业")]/following-sibling::td/span/text()').get('').strip()
        item['other_info'] = response.xpath('//tr/td[contains(text(), "其它")]/following-sibling::td/span/text()').get('').strip()
        item['production_end_date'] = response.xpath('//tr/td[contains(text(), "停产日期")]/following-sibling::td/span/text()').get('').strip()
        item['sales_end_date'] = response.xpath('//tr/td[contains(text(), "停售日期")]/following-sibling::td/span/text()').get('').strip()
        
        yield item