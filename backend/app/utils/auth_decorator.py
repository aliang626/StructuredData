#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
简单的认证装饰器
不使用复杂的JWT，使用session-based认证
"""

from functools import wraps
from flask import request, jsonify, session

def login_required(f):
    """
    登录验证装饰器
    检查session中是否有登录用户信息
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 检查session中是否有用户信息
        user = session.get('user')
        
        if not user:
            return jsonify({
                'success': False,
                'error': '未登录或登录已过期，请重新登录',
                'code': 'UNAUTHORIZED'
            }), 401
        
        # 将用户信息传递给被装饰的函数
        return f(*args, **kwargs)
    
    return decorated_function

def admin_required(f):
    """
    管理员权限验证装饰器
    检查用户是否是管理员
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 检查session中的用户信息
        user = session.get('user')
        
        if not user:
            return jsonify({
                'success': False,
                'error': '未登录或登录已过期，请重新登录',
                'code': 'UNAUTHORIZED'
            }), 401
        
        # 检查是否是管理员
        if user.get('role') != 'admin':
            return jsonify({
                'success': False,
                'error': '需要管理员权限',
                'code': 'FORBIDDEN'
            }), 403
        
        return f(*args, **kwargs)
    
    return decorated_function

def get_current_user():
    """
    获取当前登录用户
    :return: 用户信息字典或None
    """
    return session.get('user')

