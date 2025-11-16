#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
简单的验证码生成器
使用PIL库生成图形验证码，不依赖外部服务
"""

from PIL import Image, ImageDraw, ImageFont, ImageFilter
import random
import string
import io
import base64
from datetime import datetime, timedelta

class SimpleCaptcha:
    """简单的验证码生成器"""
    
    def __init__(self):
        # 内存存储验证码（session_id: {code: 验证码, expire: 过期时间}）
        self.captcha_store = {}
        # 验证码有效期（秒）
        self.expire_seconds = 300  # 5分钟
    
    def generate_code(self, length=4):
        """生成随机验证码"""
        # 只使用大写字母和数字，避免混淆
        chars = string.ascii_uppercase + string.digits
        # 移除容易混淆的字符
        chars = chars.replace('O', '').replace('0', '').replace('I', '').replace('1', '')
        return ''.join(random.choices(chars, k=length))
    
    def generate_image(self, code):
        """生成验证码图片"""
        # 图片尺寸
        width, height = 120, 40
        
        # 创建图片（白色背景）
        image = Image.new('RGB', (width, height), (255, 255, 255))
        draw = ImageDraw.Draw(image)
        
        # 添加干扰线
        for _ in range(3):
            x1 = random.randint(0, width)
            y1 = random.randint(0, height)
            x2 = random.randint(0, width)
            y2 = random.randint(0, height)
            draw.line([(x1, y1), (x2, y2)], fill=(200, 200, 200), width=1)
        
        # 添加干扰点
        for _ in range(50):
            x = random.randint(0, width)
            y = random.randint(0, height)
            draw.point((x, y), fill=(200, 200, 200))
        
        # 绘制验证码文字
        try:
            # 尝试使用系统字体
            font = ImageFont.truetype("arial.ttf", 28)
        except:
            # 如果没有找到字体，使用默认字体
            font = ImageFont.load_default()
        
        # 计算文字位置（居中）
        char_width = width // len(code)
        for i, char in enumerate(code):
            # 随机偏移
            x = char_width * i + random.randint(5, 10)
            y = random.randint(5, 10)
            # 随机颜色
            color = (
                random.randint(0, 100),
                random.randint(0, 100),
                random.randint(0, 100)
            )
            draw.text((x, y), char, font=font, fill=color)
        
        # 轻微模糊
        image = image.filter(ImageFilter.SMOOTH)
        
        return image
    
    def create(self, session_id):
        """
        创建验证码
        :param session_id: 会话ID
        :return: (验证码文本, base64图片)
        """
        # 清理过期的验证码
        self._cleanup_expired()
        
        # 生成验证码
        code = self.generate_code()
        
        # 生成图片
        image = self.generate_image(code)
        
        # 转换为base64
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        img_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        # 存储验证码（小写存储，验证时不区分大小写）
        expire_time = datetime.now() + timedelta(seconds=self.expire_seconds)
        self.captcha_store[session_id] = {
            'code': code.lower(),
            'expire': expire_time,
            'attempts': 0  # 尝试次数
        }
        
        return code, f"data:image/png;base64,{img_base64}"
    
    def verify(self, session_id, user_input):
        """
        验证验证码
        :param session_id: 会话ID
        :param user_input: 用户输入
        :return: (是否正确, 错误消息)
        """
        if not session_id or session_id not in self.captcha_store:
            return False, "验证码已过期或不存在"
        
        captcha_data = self.captcha_store[session_id]
        
        # 检查是否过期
        if datetime.now() > captcha_data['expire']:
            del self.captcha_store[session_id]
            return False, "验证码已过期"
        
        # 检查尝试次数
        captcha_data['attempts'] += 1
        if captcha_data['attempts'] > 3:
            del self.captcha_store[session_id]
            return False, "验证码尝试次数过多"
        
        # 验证（不区分大小写）
        if user_input.lower() == captcha_data['code']:
            # 验证成功，删除验证码
            del self.captcha_store[session_id]
            return True, "验证成功"
        else:
            return False, "验证码错误"
    
    def _cleanup_expired(self):
        """清理过期的验证码"""
        now = datetime.now()
        expired_keys = [
            key for key, value in self.captcha_store.items()
            if now > value['expire']
        ]
        for key in expired_keys:
            del self.captcha_store[key]

# 全局单例
captcha_generator = SimpleCaptcha()

