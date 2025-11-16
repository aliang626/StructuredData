#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
简单的登录限制器
使用内存字典存储登录尝试记录，防止暴力破解
"""

from datetime import datetime, timedelta
from collections import defaultdict

class LoginLimiter:
    """简单的登录限制器"""
    
    def __init__(self):
        # 存储登录尝试记录 {identifier: [attempt_times]}
        self.attempt_records = defaultdict(list)
        # 锁定记录 {identifier: lock_until_time}
        self.lock_records = {}
        
        # 配置
        self.max_attempts = 5  # 最大尝试次数
        self.window_seconds = 300  # 时间窗口（5分钟）
        self.lock_seconds = 300  # 锁定时长（5分钟）
    
    def get_identifier(self, username, ip):
        """
        生成唯一标识符
        :param username: 用户名
        :param ip: IP地址
        :return: 唯一标识符
        """
        return f"{username}:{ip}"
    
    def is_locked(self, identifier):
        """
        检查是否被锁定
        :param identifier: 唯一标识符
        :return: (是否锁定, 剩余锁定时间秒数)
        """
        if identifier in self.lock_records:
            lock_until = self.lock_records[identifier]
            now = datetime.now()
            
            if now < lock_until:
                # 仍在锁定期
                remaining = int((lock_until - now).total_seconds())
                return True, remaining
            else:
                # 锁定期已过，清理记录
                del self.lock_records[identifier]
                if identifier in self.attempt_records:
                    del self.attempt_records[identifier]
        
        return False, 0
    
    def can_attempt(self, username, ip):
        """
        检查是否可以尝试登录
        :param username: 用户名
        :param ip: IP地址
        :return: (是否可以尝试, 错误消息, 剩余次数)
        """
        identifier = self.get_identifier(username, ip)
        
        # 检查是否被锁定
        is_locked, remaining_time = self.is_locked(identifier)
        if is_locked:
            minutes = remaining_time // 60
            seconds = remaining_time % 60
            return False, f"账号已被锁定，请在{minutes}分{seconds}秒后重试", 0
        
        # 清理过期的尝试记录
        self._cleanup_old_attempts(identifier)
        
        # 检查尝试次数
        attempts = self.attempt_records[identifier]
        remaining = self.max_attempts - len(attempts)
        
        if remaining <= 0:
            # 超过最大尝试次数，锁定账号
            self._lock_account(identifier)
            return False, f"登录尝试次数过多，账号已被锁定{self.lock_seconds // 60}分钟", 0
        
        return True, "", remaining
    
    def record_attempt(self, username, ip, success=False):
        """
        记录登录尝试
        :param username: 用户名
        :param ip: IP地址
        :param success: 是否成功
        """
        identifier = self.get_identifier(username, ip)
        
        if success:
            # 登录成功，清理所有记录
            if identifier in self.attempt_records:
                del self.attempt_records[identifier]
            if identifier in self.lock_records:
                del self.lock_records[identifier]
        else:
            # 登录失败，记录尝试时间
            self.attempt_records[identifier].append(datetime.now())
            
            # 检查是否需要锁定
            attempts = self.attempt_records[identifier]
            if len(attempts) >= self.max_attempts:
                self._lock_account(identifier)
    
    def _lock_account(self, identifier):
        """锁定账号"""
        lock_until = datetime.now() + timedelta(seconds=self.lock_seconds)
        self.lock_records[identifier] = lock_until
    
    def _cleanup_old_attempts(self, identifier):
        """清理过期的尝试记录"""
        if identifier not in self.attempt_records:
            return
        
        cutoff_time = datetime.now() - timedelta(seconds=self.window_seconds)
        # 保留时间窗口内的尝试记录
        self.attempt_records[identifier] = [
            attempt_time for attempt_time in self.attempt_records[identifier]
            if attempt_time > cutoff_time
        ]
        
        # 如果没有记录了，删除该标识符
        if not self.attempt_records[identifier]:
            del self.attempt_records[identifier]
    
    def get_stats(self, username, ip):
        """
        获取登录统计信息
        :param username: 用户名
        :param ip: IP地址
        :return: {attempts: 尝试次数, remaining: 剩余次数, locked: 是否锁定}
        """
        identifier = self.get_identifier(username, ip)
        self._cleanup_old_attempts(identifier)
        
        is_locked, remaining_time = self.is_locked(identifier)
        attempts = len(self.attempt_records.get(identifier, []))
        remaining = max(0, self.max_attempts - attempts)
        
        return {
            'attempts': attempts,
            'remaining': remaining,
            'locked': is_locked,
            'lock_time': remaining_time if is_locked else 0
        }

# 全局单例
login_limiter = LoginLimiter()

