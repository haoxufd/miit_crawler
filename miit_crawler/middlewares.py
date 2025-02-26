# -*- coding: utf-8 -*-
from scrapy import signals
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver import ActionChains
import time
import logging
import traceback
from scrapy.http import HtmlResponse
import requests
from PIL import Image
import numpy as np
from captcha_recognizer.recognizer import Recognizer

from miit_crawler.exceptions import ImageDownloadError

import os


class SliderCaptchaSolver:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.recognizer = Recognizer()
    
    def download_image(self, image_url):
        # 发送 GET 请求获取图片内容
        response = requests.get(image_url)

        # 检查请求是否成功
        if response.status_code == 200:
            # 获取图片的文件名
            file_name = image_url.split('/')[-1]
            # 保存图片到本地
            with open(file_name, 'wb') as file:
                file.write(response.content)
            self.logger.info(f"Successfully download picture {file_name}")
        else:
            raise ImageDownloadError(f"Status code {response.status_code} while downloading {image_url}")
    
    def get_slide_distance(self, browser):
        try:
            # 等待验证码图片加载
            WebDriverWait(browser, 5).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'yidun_bg-img'))
            )
            
            # 获取背景图片
            bg_img_element = browser.find_element(By.CLASS_NAME, 'yidun_bg-img')
            bg_img_url = bg_img_element.get_attribute('src')
            self.logger.info(f"Downloaded picture {bg_img_url}")
            self.download_image(bg_img_url)
            bg_img_file = bg_img_url.split('/')[-1]
            
            # 获取页面上图片的显示尺寸和实际尺寸
            displayed_width = bg_img_element.size['width']
            actual_width, _ = Image.open(bg_img_file).size
            
            self.logger.info(f"Displayed Width: {displayed_width}")
            self.logger.info(f"Actual Width: {actual_width}")
            
            # 计算比例系数
            scale_factor = displayed_width / actual_width

            self.logger.info(f"Scale Factor: {scale_factor}")
            
            box = self.detect_puzzle_piece_boundary(bg_img_file)
            os.remove(bg_img_file)
            self.logger.info(f"Deleted {bg_img_file}")

            raw_distance = box[0] + 10
            adjusted_distance = raw_distance * scale_factor
            
            return adjusted_distance
        
        except ImageDownloadError as e:
            self.logger.error(f"下载图片时出错: {str(e)}")
            self.logger.error(traceback.format_exc())
            raise e

        except Exception as e:
            self.logger.error(f"获取滑动距离时出错: {str(e)}")
            self.logger.error(traceback.format_exc())
            raise e
    def detect_puzzle_piece_boundary(self, image_file):
        box, _ = self.recognizer.identify_gap(source=image_file)
        return box
    
    def generate_slide_track(self, distance):
        """
        生成滑动轨迹
        模拟人类滑动行为：先加速后减速，并添加适当随机性和微调
        
        参数:
        distance: 需要滑动的总距离
        
        返回:
        track: 滑动轨迹列表，每个元素表示每次移动的距离
        """
        # 初始化轨迹列表
        track = []
        
        # 设置加速过程占总距离的比例
        accelerate_ratio = 0.65
        
        # 当前位置
        current = 0
        
        # 初速度，单位:像素/次
        v0 = 0
        
        # 时间间隔，单位:秒
        t = 0.6
        
        # 加速度，单位:像素/次²
        accelerate_a = 10
        decelerate_a = -3
        
        # 加速过程
        accelerate_distance = distance * accelerate_ratio
        while current < accelerate_distance:
            # 使用物理公式计算移动距离：s = v0 * t + 0.5 * a * t^2
            s = v0 * t + 0.5 * accelerate_a * t * t
            # 加入随机微扰，模拟人手抖动
            s = s + np.random.uniform(-0.5, 0.5)
            
            # 确保不会过冲
            if current + s > accelerate_distance:
                s = accelerate_distance - current
            
            # 更新当前速度：v = v0 + a * t
            v0 = v0 + accelerate_a * t
            
            # 添加到轨迹
            track.append(round(s, 2))
            current += s
        
        # 减速过程
        while current < distance:
            # 使用物理公式计算移动距离：s = v0 * t + 0.5 * a * t^2
            s = v0 * t + 0.5 * decelerate_a * t * t
            # 加入随机微扰，但在接近目标时减小扰动
            remaining = distance - current
            if remaining > 10:
                s = s + np.random.uniform(-0.5, 0.5)
            else:
                s = s + np.random.uniform(-0.2, 0.2)
            
            # 确保不会过冲
            if current + s > distance:
                s = distance - current
            
            # 更新当前速度：v = v0 + a * t
            v0 = max(0, v0 + decelerate_a * t)  # 速度不能为负
            
            # 添加到轨迹
            track.append(round(s, 2))
            current += s
        
        # 最后添加一些小的回退，模拟人类对准动作
        if len(track) > 3:
            track[-1] = max(0, track[-1] - np.random.uniform(0, 1))
            
        # 确保总和等于目标距离，修正最后一步
        moved = sum(track)
        if moved != distance:
            track[-1] += (distance - moved)
        
        self.logger.info(f"生成滑动轨迹: {len(track)}步, 总距离: {sum(track)}")
        return track


class SeleniumMiddleware(object):
    """
    优化的Scrapy中间件, 用于处理滑块验证
    """

    def __init__(self, crawler):
        super(SeleniumMiddleware, self).__init__()
        self.logger = logging.getLogger(__name__)
        
        # 初始化Chrome选项
        self.chrome_options = Options()
        self.chrome_options.add_argument('--headless')  # 取消无头模式以便观察
        self.chrome_options.add_argument('--no-sandbox')
        self.chrome_options.add_argument('--disable-dev-shm-usage')
        self.chrome_options.add_argument('--disable-gpu')
        self.chrome_options.add_argument('--window-size=1920,1080')
        
        # 设置用户代理
        self.chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36')
        
        # 初始化浏览器
        self.browser = webdriver.Chrome(options=self.chrome_options)
        self.logger.info("Selenium浏览器已初始化")
        
        # 初始化滑块验证求解器
        self.captcha_solver = SliderCaptchaSolver()
        
        # 关联信号，确保爬虫关闭时关闭浏览器
        crawler.signals.connect(self.spider_closed, signal=signals.spider_closed)

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)

    def process_request(self, request, spider):
        """
        处理包含滑块验证的请求
        """
        # 仅处理特定URL的请求
        assert 'queryCpData' in request.url
            
        self.logger.info(f"使用Selenium处理请求: {request.url}")
        
        # 访问页面
        self.browser.get(request.url)
            
        max_attempts = 3  # 最大尝试次数
        attempt = 0
        while attempt < max_attempts:
            attempt += 1
            self.logger.info(f"开始处理滑块验证... 第{attempt}次尝试")
            
            try:
                # 等待滑块和继续访问按钮加载
                slider = WebDriverWait(self.browser, 3).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "yidun_slider"))
                )
                submit_button = WebDriverWait(self.browser, 3).until(
                    EC.element_to_be_clickable((By.ID, "submit-btn"))
                )
                self.logger.info("滑块和提交按钮已加载")
                
                # 计算滑动距离
                distance = self.captcha_solver.get_slide_distance(self.browser)
                self.logger.info(f"滑动距离: {distance}像素")
                
                # 执行滑动操作
                action = ActionChains(self.browser)
                action.click_and_hold(slider)
                action.move_by_offset(distance, 0)
                
                # 释放鼠标
                action.release().perform()
                self.logger.info("滑块拖动完成")

                time.sleep(0.5)

                yidun_top_right = WebDriverWait(self.browser, 3).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "yidun_top__right"))
                )
                if yidun_top_right.size["width"] == 0:
                    # 右上角的刷新按钮被隐藏, 说明滑块验证成功

                    # 点击继续访问按钮
                    submit_button.click()
                    self.logger.info("已点击提交按钮")
                    
                    # 等待页面加载完成
                    time.sleep(0.5)

                    break

            except Exception as e:
                self.logger.error(f"处理滑块验证时出错: {str(e)}")
                self.logger.error(traceback.format_exc())
        
        # 获取最终页面内容
        body = self.browser.page_source
        current_url = self.browser.current_url
        
        # 返回Response对象
        return HtmlResponse(
            url=current_url,
            body=body,
            encoding='utf-8',
            request=request
        )
    
    def download_car_image(self):
        # 找到所有的img元素
        img_elements = self.browser.find_elements(By.TAG_NAME, "img")
        self.logger.info(f"找到 {len(img_elements)} 个图片元素")
        
        # 准备保存图片的目录
        images_dir = "images"
        os.makedirs(images_dir, exist_ok=True)

        images = []
        # 获取每个图片并直接从浏览器中提取数据
        for i, img in enumerate(img_elements):
            # 获取图片属性
            img_src = img.get_attribute("src")
            img_alt = img.get_attribute("alt")
            
            # 使用JavaScript获取图片为Base64
            # 这段JS会创建一个canvas并绘制图片，然后返回base64数据
            canvas_js = """
            var img = arguments[0];
            var canvas = document.createElement('canvas');
            canvas.width = img.naturalWidth;
            canvas.height = img.naturalHeight;
            var ctx = canvas.getContext('2d');
            ctx.drawImage(img, 0, 0);
            return canvas.toDataURL('image/png');
            """
            
            # 执行JavaScript获取图片数据
            img_data_url = self.browser.execute_script(canvas_js, img)

            # 如果成功获取到图片数据
            if img_data_url and img_data_url.startswith('data:image/'):
                # 从data URL提取base64编码的图片数据
                import base64
                # 移除"data:image/png;base64,"前缀
                img_data = img_data_url.split(',')[1]
                # 解码base64数据
                img_binary = base64.b64decode(img_data)
                
                # 创建文件名和路径
                file_name = f"{img_alt}.png"
                clean_filename = ''.join(c if c.isalnum() or c in '._- ' else '_' for c in file_name)
                file_path = os.path.join(images_dir, clean_filename)
                
                # 保存图片
                with open(file_path, 'wb') as f:
                    f.write(img_binary)
                
                self.logger.info(f"成功保存图片: {file_path}")

                # 记录图片信息
                images.append({
                    "src": img_src,
                    "alt": img_alt,
                    "saved_path": file_path,
                    "width": img.size['width'],
                    "height": img.size['height']
                })
            else:
                self.logger.warning(f"无法获取图片数据: {img_src}")
                images.append({
                    "src": img_src,
                    "alt": img_alt,
                    "saved_path": None,
                    "width": img.size['width'],
                    "height": img.size['height']
                })
        
        return images
            
    def spider_closed(self, spider):
        """
        爬虫关闭时关闭浏览器
        """
        if self.browser:
            self.browser.quit()
            self.logger.info("Selenium浏览器已关闭")