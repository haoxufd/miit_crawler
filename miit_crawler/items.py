# -*- coding: utf-8 -*-
from matplotlib.pyplot import sca
import scrapy


class MiitCrawlerItem(scrapy.Item):
    """
    定义要收集的数据项
    """
    request_number = scrapy.Field()
    request_url = scrapy.Field()
    # 图片相关
    image_urls = scrapy.Field()  # 所有图片的 url 列表
    
    # 基本信息
    product_id = scrapy.Field()  # 产品号
    batch = scrapy.Field()  # 批次
    publish_date = scrapy.Field()  # 发布日期
    
    # 企业信息
    company_name = scrapy.Field()  # 企业名称
    product_model_name = scrapy.Field()  # 产品型号名称
    product_trademark = scrapy.Field()  # 产品商标
    production_address = scrapy.Field()  # 生产地址
    registered_address = scrapy.Field()  # 注册地址
    
    # 车辆信息
    vehicle_model = scrapy.Field()  # 车辆型号
    vehicle_name = scrapy.Field()  # 车辆名称
    chassis_id = scrapy.Field()  # 底盘ID
    chassis_model_and_company = scrapy.Field()  # 底盘型号及企业
    vin = scrapy.Field()  # 车辆识别代号（VIN）
    
    # 燃料和排放信息
    fuel_type = scrapy.Field()  # 燃料种类
    fuel_consumption = scrapy.Field()  # 油耗
    emission_standard = scrapy.Field()  # 排放依据标准
    
    # 发动机信息
    engine_manufacturer = scrapy.Field()  # 发动机生产企业
    engine_model = scrapy.Field()  # 发动机型号
    displacement = scrapy.Field()  # 排量
    
    # 其他信息
    reflective_mark_company = scrapy.Field()  # 反光标识企业
    other_info = scrapy.Field()  # 其他
    production_end_date = scrapy.Field()  # 停产日期
    sales_end_date = scrapy.Field()  # 停售日期