# -*- coding: utf-8 -*-
import json
import os
from datetime import datetime
import pandas as pd


class MiitCrawlerJSONPipeline:
    """
    处理爬取到的数据并保存到JSON
    """
    def __init__(self):
        # 创建数据存储目录
        self.data_dir = 'crawled_data'
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
    
    def process_item(self, item, spider):
        """
        处理每个爬取到的项目并保存到JSON
        """
        # 生成文件名
        product_id = item.get('product_id', 'unknown')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{self.data_dir}/miit_data_{product_id}_{timestamp}.json"
        
        # 将数据转换为中文字段名称的字典
        chinese_item = {
            '图片链接': item.get('image_urls', []),
            '产品号': item.get('product_id', ''),
            '批次': item.get('batch', ''),
            '发布日期': item.get('publish_date', ''),
            '企业名称': item.get('company_name', ''),
            '产品型号名称': item.get('product_model_name', ''),
            '产品商标': item.get('product_trademark', ''),
            '生产地址': item.get('production_address', ''),
            '注册地址': item.get('registered_address', ''),
            '车辆型号': item.get('vehicle_model', ''),
            '车辆名称': item.get('vehicle_name', ''),
            '底盘ID': item.get('chassis_id', ''),
            '底盘型号及企业': item.get('chassis_model_and_company', ''),
            '车辆识别代号(VIN)': item.get('vin', ''),
            '燃料种类': item.get('fuel_type', ''),
            '油耗': item.get('fuel_consumption', ''),
            '排放依据标准': item.get('emission_standard', ''),
            '发动机生产企业': item.get('engine_manufacturer', ''),
            '发动机型号': item.get('engine_model', ''),
            '排量': item.get('displacement', ''),
            '反光标识企业': item.get('reflective_mark_company', ''),
            '其他': item.get('other_info', ''),
            '停产日期': item.get('production_end_date', ''),
            '停售日期': item.get('sales_end_date', '')
        }
        
        # 将数据写入JSON文件
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(chinese_item, f, ensure_ascii=False, indent=4)
            
        spider.logger.info(f"数据已保存到JSON文件: {filename}")
        
        return item


class MiitCrawlerExcelPipeline:
    """
    处理爬取到的数据并保存到Excel
    每10条数据写入一次文件, spider关闭时确保剩余数据也被写入
    """
    def __init__(self):
        # 创建数据存储目录
        self.data_dir = 'crawled_data'
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
        
        # 创建时间戳标识的Excel文件
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.excel_file = f"{self.data_dir}/miit_data.xlsx"
        
        # 创建一个空的数据列表用于存储数据
        self.data = []
        
        # 设置批次大小
        self.batch_size = 10
        
        # 批次计数器
        self.batch_count = 0
        
    def process_item(self, item, spider):
        """
        处理每个爬取到的项目并添加到数据列表
        每10条数据写入一次Excel文件
        """
        # 将item转为中文字段名称的字典并添加到数据列表
        chinese_item = {
            '序号':item.get('request_number'),
            '图片链接': str(item.get('image_urls', [])),  # 转为字符串以便在Excel中显示
            '产品号': item.get('product_id', ''),
            '批次': item.get('batch', ''),
            '发布日期': item.get('publish_date', ''),
            '企业名称': item.get('company_name', ''),
            '产品型号名称': item.get('product_model_name', ''),
            '产品商标': item.get('product_trademark', ''),
            '生产地址': item.get('production_address', ''),
            '注册地址': item.get('registered_address', ''),
            '车辆型号': item.get('vehicle_model', ''),
            '车辆名称': item.get('vehicle_name', ''),
            '底盘ID': item.get('chassis_id', ''),
            '底盘型号及企业': item.get('chassis_model_and_company', ''),
            '车辆识别代号(VIN)': item.get('vin', ''),
            '燃料种类': item.get('fuel_type', ''),
            '油耗': item.get('fuel_consumption', ''),
            '排放依据标准': item.get('emission_standard', ''),
            '发动机生产企业': item.get('engine_manufacturer', ''),
            '发动机型号': item.get('engine_model', ''),
            '排量': item.get('displacement', ''),
            '反光标识企业': item.get('reflective_mark_company', ''),
            '其他': item.get('other_info', ''),
            '停产日期': item.get('production_end_date', ''),
            '停售日期': item.get('sales_end_date', '')
        }
        
        self.data.append(chinese_item)
        self.batch_count += 1
        
        spider.logger.info(f"数据已添加到Excel队列, 产品号: {item.get('product_id', 'unknown')}, 当前队列数量: {self.batch_count}")
        
        # 每处理10条数据, 写入一次Excel
        if self.batch_count >= self.batch_size:
            self._write_to_excel(spider)
            # 重置数据列表和批次计数器
            self.data = []
            self.batch_count = 0
        
        return item
    
    def _write_to_excel(self, spider):
        """
        将当前数据批次写入Excel
        """
        if not self.data:
            spider.logger.warning("没有数据需要写入Excel")
            return
        
        # 将数据列表转换为DataFrame
        df = pd.DataFrame(self.data)
        
        # 设置Excel中的列顺序
        columns_order = [
            '序号', '产品号', '批次', '发布日期', 
            '企业名称', '产品型号名称', '产品商标',
            '生产地址', '注册地址',
            '车辆型号', '车辆名称', '底盘ID',
            '底盘型号及企业', '车辆识别代号(VIN)',
            '燃料种类', '油耗', '排放依据标准',
            '发动机生产企业', '发动机型号', '排量',
            '反光标识企业', '其他',
            '停产日期', '停售日期',
            '图片链接'
        ]
        
        # 重新排序列（如果列存在）
        existing_columns = [col for col in columns_order if col in df.columns]
        df = df[existing_columns]
        
        # 检查文件是否已经存在
        file_exists = os.path.isfile(self.excel_file)
        
        if file_exists:
            # 如果文件已存在, 读取现有数据
            existing_df = pd.read_excel(self.excel_file)
            # 合并数据
            df = pd.concat([existing_df, df], ignore_index=True)
        
        # 保存到Excel
        df.to_excel(self.excel_file, index=False, engine='openpyxl')
        spider.logger.info(f"已写入 {len(self.data)} 条数据到Excel文件: {self.excel_file}, 总数据量: {len(df)}")
    
    def close_spider(self, spider):
        """
        爬虫关闭时, 确保剩余数据（不足10条）也被写入Excel
        """
        if self.data:
            spider.logger.info(f"爬虫关闭, 写入剩余 {len(self.data)} 条数据到Excel")
            self._write_to_excel(spider)