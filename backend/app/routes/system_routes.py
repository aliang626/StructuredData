from flask import Blueprint, jsonify, request, session
from datetime import datetime, timedelta
from app.models.model_config import ModelConfig
from app.models.data_source import DataSource
from app.models.rule_model import RuleLibrary
from app.models.quality_result import QualityResult
from app import db
from app.services.sso_service import sso_service
from app.utils.auth_decorator import login_required, admin_required
import pandas as pd
import os
import traceback

bp = Blueprint('system_routes', __name__)

@bp.route('/health', methods=['GET'])
def health():
    try:
        # 测试数据库连接
        from sqlalchemy import text
        db.session.execute(text('SELECT 1'))
        db.session.commit()
        return jsonify({'status': 'healthy', 'db': 'ok'})
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'db': 'error', 'error': str(e)}), 500

@bp.route('/stats', methods=['GET'])
@login_required
def stats():
    try:
        print("=== system_routes 统计API被调用 ===")
        # 从数据库查询真实统计数据
        model_count = ModelConfig.query.filter_by(is_active=True).count()
        db_count = DataSource.query.filter_by(is_active=True).count()  # 只统计活跃的数据源
        rule_count = RuleLibrary.query.filter_by(is_active=True).count()
        quality_count = QualityResult.query.count()
        
        print(f"system_routes - 模型配置: {model_count}, 数据源: {db_count}, 规则库: {rule_count}, 质检任务: {quality_count}")
        
        return jsonify({
            'success': True, 
            'data': {
                'modelCount': model_count,
                'dbCount': db_count,
                'ruleCount': rule_count,
                'qualityCount': quality_count
            }
        })
    except Exception as e:
        print(f"system_routes 统计API异常: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'获取统计数据失败: {str(e)}'
        }), 500

@bp.route('/activities', methods=['GET'])
@login_required
def activities():
    try:
        activities_list = []
        activity_id = 1
        
        # 获取最近7天的活动记录
        seven_days_ago = datetime.now() - timedelta(days=7)
        
        # 查询最近的模型配置活动
        recent_models = ModelConfig.query.filter(
            ModelConfig.created_at >= seven_days_ago
        ).order_by(ModelConfig.created_at.desc()).limit(5).all()
        
        for model in recent_models:
            activities_list.append({
                'id': activity_id,
                'content': f'创建了模型配置: {model.name}',
                'time': model.created_at.strftime('%Y-%m-%d %H:%M'),
                'type': 'success'
            })
            activity_id += 1
        
        # 查询最近的数据源活动
        recent_datasources = DataSource.query.filter(
            DataSource.created_at >= seven_days_ago
        ).order_by(DataSource.created_at.desc()).limit(3).all()
        
        for ds in recent_datasources:
            activities_list.append({
                'id': activity_id,
                'content': f'添加了数据源: {ds.name}',
                'time': ds.created_at.strftime('%Y-%m-%d %H:%M'),
                'type': 'info'
            })
            activity_id += 1
        
        # 查询最近的质量检测活动
        recent_quality = QualityResult.query.filter(
            QualityResult.created_at >= seven_days_ago
        ).order_by(QualityResult.created_at.desc()).limit(5).all()
        
        for quality in recent_quality:
            activity_type = 'success' if quality.pass_rate >= 0.8 else 'warning' if quality.pass_rate >= 0.6 else 'error'
            activities_list.append({
                'id': activity_id,
                'content': f'完成质量检测，通过率: {quality.pass_rate:.1%}',
                'time': quality.created_at.strftime('%Y-%m-%d %H:%M'),
                'type': activity_type
            })
            activity_id += 1
        
        # 按时间排序并限制数量
        activities_list.sort(key=lambda x: x['time'], reverse=True)
        activities_list = activities_list[:10]  # 最多显示10条活动
        
        # 如果没有活动记录，提供默认消息
        if not activities_list:
            activities_list = [{
                'id': 1,
                'content': '暂无最近活动记录',
                'time': datetime.now().strftime('%Y-%m-%d %H:%M'),
                'type': 'info'
            }]
        
        return jsonify({'success': True, 'data': activities_list})
        
    except Exception as e:
        # 如果查询失败，返回默认活动记录
        return jsonify({
            'success': True, 
            'data': [{
                'id': 1,
                'content': f'系统活动查询异常: {str(e)}',
                'time': datetime.now().strftime('%Y-%m-%d %H:%M'),
                'type': 'error'
            }]
        }) 

# ========== 井名白名单管理API ==========

@bp.route('/well-whitelist', methods=['GET'])
# @login_required  # 临时移除登录验证
def get_well_whitelist():
    """获取井名质检白名单列表"""
    try:
        from flask import request
        
        # 获取分页参数
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('pageSize', 10))
        
        # 参数验证
        if page < 1:
            page = 1
        if page_size < 1 or page_size > 100:
            page_size = 10
        
        # 计算CSV文件路径
        backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        csv_path = os.path.join(backend_dir, 'block_info.csv')
        
        if not os.path.exists(csv_path):
            return jsonify({
                'success': False,
                'error': '白名单文件不存在'
            }), 404
        
        # 读取CSV文件
        df = pd.read_csv(csv_path, dtype=str)
        
        # 转换为列表格式，只返回井名质检需要的字段
        whitelist = []
        for idx, row in df.iterrows():
            whitelist.append({
                'id': idx + 1,
                'code': str(row.get('代号', '')).strip(),
                'name': str(row.get('名称', '')).strip(),
                'description': str(row.get('描述', f"{row.get('区块编号', '')} - {row.get('名称', '')}")).strip()
            })
        
        # 计算分页
        total = len(whitelist)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        
        # 分页数据
        paginated_data = whitelist[start_idx:end_idx]
        
        return jsonify({
            'success': True,
            'data': paginated_data,
            'total': total,
            'page': page,
            'pageSize': page_size,
            'totalPages': (total + page_size - 1) // page_size,
            'hasNext': end_idx < total,
            'hasPrev': page > 1
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/well-whitelist', methods=['POST'])
# @admin_required  # 临时移除登录验证
def add_well_whitelist():
    """添加井名质检白名单项"""
    try:
        from flask import request
        data = request.get_json()
        
        # 验证必需字段
        if not data.get('code') or not data.get('name'):
            return jsonify({
                'success': False,
                'error': '代号和名称不能为空'
            }), 400
        
        # 计算CSV文件路径
        backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        csv_path = os.path.join(backend_dir, 'block_info.csv')
        
        if not os.path.exists(csv_path):
            return jsonify({
                'success': False,
                'error': '白名单文件不存在'
            }), 404
        
        # 读取现有数据
        df = pd.read_csv(csv_path, dtype=str)
        
        # 检查代号是否已存在
        code = data['code'].strip().upper()
        if code in df['代号'].str.upper().values:
            return jsonify({
                'success': False,
                'error': f'代号 {code} 已存在'
            }), 400
        
        # 添加新行，支持描述字段
        new_row = {
            '区块编号': f"新增/{len(df)+1}",
            '名称': data['name'].strip(),
            '代号': code,
            '英文名称': f"({data['name'].strip()})",
            '描述': data.get('description', '').strip() or f"新增/{len(df)+1} - {data['name'].strip()}"
        }
        
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        
        # 保存到CSV文件
        df.to_csv(csv_path, index=False, encoding='utf-8')
        
        return jsonify({
            'success': True,
            'message': '添加成功',
            'data': {
                'code': code,
                'name': data['name'].strip()
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/well-whitelist/<code>', methods=['PUT'])
# @admin_required  # 临时移除登录验证
def update_well_whitelist(code):
    """更新井名质检白名单项"""
    try:
        from flask import request
        data = request.get_json()
        
        # 计算CSV文件路径
        backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        csv_path = os.path.join(backend_dir, 'block_info.csv')
        
        if not os.path.exists(csv_path):
            return jsonify({
                'success': False,
                'error': '白名单文件不存在'
            }), 404
        
        # 读取现有数据
        df = pd.read_csv(csv_path, dtype=str)
        
        # 查找要更新的行
        mask = df['代号'].str.upper() == code.upper()
        if not mask.any():
            return jsonify({
                'success': False,
                'error': f'未找到代号为 {code} 的记录'
            }), 404
        
        # 更新名称
        if 'name' in data and data['name'].strip():
            df.loc[mask, '名称'] = data['name'].strip()
            # 同时更新英文名称
            df.loc[mask, '英文名称'] = f"({data['name'].strip()})"
        
        # 更新描述
        if 'description' in data:
            df.loc[mask, '描述'] = data['description'].strip()
        
        # 保存到CSV文件
        df.to_csv(csv_path, index=False, encoding='utf-8')
        
        return jsonify({
            'success': True,
            'message': '更新成功'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/well-whitelist/<code>', methods=['DELETE'])
# @admin_required  # 临时移除登录验证
def delete_well_whitelist(code):
    """删除井名质检白名单项"""
    try:
        # 计算CSV文件路径
        backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        csv_path = os.path.join(backend_dir, 'block_info.csv')
        
        if not os.path.exists(csv_path):
            return jsonify({
                'success': False,
                'error': '白名单文件不存在'
            }), 404
        
        # 读取现有数据
        df = pd.read_csv(csv_path, dtype=str)
        
        # 查找要删除的行
        mask = df['代号'].str.upper() == code.upper()
        if not mask.any():
            return jsonify({
                'success': False,
                'error': f'未找到代号为 {code} 的记录'
            }), 404
        
        # 删除行
        df = df[~mask]
        
        # 保存到CSV文件
        df.to_csv(csv_path, index=False, encoding='utf-8')
        
        return jsonify({
            'success': True,
            'message': '删除成功'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/well-whitelist/search', methods=['GET'])
# @login_required  # 临时移除登录验证
def search_well_whitelist():
    """搜索井名质检白名单"""
    try:
        from flask import request
        query = request.args.get('q', '').strip()
        
        if not query:
            return jsonify({
                'success': False,
                'error': '搜索关键词不能为空'
            }), 400
        
        # 获取分页参数
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('pageSize', 10))
        
        # 参数验证
        if page < 1:
            page = 1
        if page_size < 1 or page_size > 100:
            page_size = 10
        
        # 计算CSV文件路径
        backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        csv_path = os.path.join(backend_dir, 'block_info.csv')
        
        if not os.path.exists(csv_path):
            return jsonify({
                'success': False,
                'error': '白名单文件不存在'
            }), 404
        
        # 读取CSV文件
        df = pd.read_csv(csv_path, dtype=str)
        
        # 搜索匹配的记录（主要搜索代号和名称）
        mask = (
            df['代号'].str.contains(query, case=False, na=False) |
            df['名称'].str.contains(query, case=False, na=False)
        )
        
        filtered_df = df[mask]
        
        # 转换为列表格式
        results = []
        for idx, row in filtered_df.iterrows():
            results.append({
                'id': idx + 1,
                'code': str(row.get('代号', '')).strip(),
                'name': str(row.get('名称', '')).strip(),
                'description': f"{row.get('区块编号', '')} - {row.get('名称', '')}"
            })
        
        # 计算分页
        total = len(results)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        
        # 分页数据
        paginated_data = results[start_idx:end_idx]
        
        return jsonify({
            'success': True,
            'data': paginated_data,
            'total': total,
            'page': page,
            'pageSize': page_size,
            'totalPages': (total + page_size - 1) // page_size,
            'hasNext': end_idx < total,
            'hasPrev': page > 1
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ========== SSO单点登录API ==========

@bp.route('/auth/sso/verify-token', methods=['POST'])
def verify_sso_token():
    """验证SSO token并获取用户信息"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': '请求数据不能为空'
            }), 400
        
        token = data.get('token')
        if not token:
            return jsonify({
                'success': False,
                'error': 'Token不能为空'
            }), 400
        
        print(f"收到SSO token验证请求: token={token}")
        
        # 调用SSO服务验证token
        result = sso_service.verify_token(token)
        
        if result['success']:
            # 将用户信息存储到session（用于后续接口认证）
            session['user'] = result['user']
            session.permanent = True  # 使session持久化
            
            return jsonify({
                'success': True,
                'data': result['user'],
                'message': result['message']
            })
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 401
            
    except Exception as e:
        print(f"SSO token验证异常: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'Token验证异常: {str(e)}'
        }), 500

@bp.route('/auth/sso/refresh-appcode', methods=['POST'])
def refresh_sso_appcode():
    """刷新SSO appCode（用于调试和故障排除）"""
    try:
        print("收到刷新appCode请求")
        app_code = sso_service.refresh_app_code()
        
        if app_code:
            return jsonify({
                'success': True,
                'data': {'appCode': app_code},
                'message': 'AppCode刷新成功'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'AppCode刷新失败'
            }), 500
            
    except Exception as e:
        print(f"刷新appCode异常: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'刷新appCode异常: {str(e)}'
        }), 500

@bp.route('/auth/logout', methods=['POST'])
def logout():
    """用户登出"""
    try:
        # 清除session
        session.pop('user', None)
        session.clear()
        
        return jsonify({
            'success': True,
            'message': '登出成功'
        })
    except Exception as e:
        print(f"登出异常: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'登出失败: {str(e)}'
        }), 500

@bp.route('/auth/captcha', methods=['GET'])
def get_captcha():
    """获取验证码"""
    try:
        from app.utils.simple_captcha import captcha_generator
        import uuid
        
        # 生成唯一会话ID
        session_id = str(uuid.uuid4())
        
        # 生成验证码
        code, image_base64 = captcha_generator.create(session_id)
        
        return jsonify({
            'success': True,
            'data': {
                'session_id': session_id,
                'image': image_base64
            }
        })
    except Exception as e:
        print(f"生成验证码异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'生成验证码失败: {str(e)}'
        }), 500

@bp.route('/auth/legacy/login', methods=['POST'])
def legacy_login():
    """传统登录方式（用户名密码），作为SSO的备用方案"""
    try:
        from app.utils.simple_captcha import captcha_generator
        from app.utils.login_limiter import login_limiter
        import hashlib
        
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': '请求数据不能为空'
            }), 400
        
        username = data.get('username')
        password = data.get('password')
        captcha_code = data.get('captcha')
        session_id = data.get('session_id')
        
        if not username or not password:
            return jsonify({
                'success': False,
                'error': '用户名和密码不能为空'
            }), 400
        
        # 获取客户端IP
        client_ip = request.remote_addr or request.headers.get('X-Real-IP', 'unknown')
        
        # 1. 检查登录限制
        can_attempt, error_msg, remaining = login_limiter.can_attempt(username, client_ip)
        if not can_attempt:
            return jsonify({
                'success': False,
                'error': error_msg,
                'need_captcha': True
            }), 429
        
        # 2. 验证验证码（始终要求）
        if not captcha_code or not session_id:
            return jsonify({
                'success': False,
                'error': '请输入验证码',
                'remaining_attempts': remaining,
                'need_captcha': True
            }), 400
        
        # 验证验证码
        is_valid, captcha_msg = captcha_generator.verify(session_id, captcha_code)
        if not is_valid:
            # 记录失败尝试
            login_limiter.record_attempt(username, client_ip, success=False)
            return jsonify({
                'success': False,
                'error': captcha_msg,
                'remaining_attempts': remaining - 1,
                'need_captcha': True
            }), 400
        
        # 3. 验证用户名密码
        # 简单的用户数据库（生产环境应使用真实数据库）
        users = {
            'admin': {
                'password_hash': 'pbkdf2:sha256:600000$xKj8vY2wN5qR7Pts$8b3c9d6e5f4a3b2c1d0e9f8a7b6c5d4e3f2a1b0c9d8e7f6a5b4c3d2e1f0a9b8c',
                'user_info': {
                    "id": 1,
                    "username": "admin",
                    "name": "系统管理员",
                    "role": "admin",
                    "avatar": "",
                    "email": "admin@system.com",
                    "department": "系统管理部",
                    "phone": "",
                    "loginType": "legacy"
                }
            }
        }
        
        # 验证用户存在
        if username not in users:
            login_limiter.record_attempt(username, client_ip, success=False)
            return jsonify({
                'success': False,
                'error': '用户名或密码错误',
                'remaining_attempts': remaining - 1,
                'need_captcha': True
            }), 401
        
        # 使用简单的哈希验证（为了兼容性，使用SHA256）
        # 新密码：Cnooc@2025!Secure
        password_sha256 = hashlib.sha256(password.encode()).hexdigest()
        stored_hash = 'bfb333e7f9797822890c4165e428126ba569ef0e7bd0eecafdb31d74e9830981'
        
        if password_sha256 == stored_hash:
            # 登录成功，清除失败记录
            login_limiter.record_attempt(username, client_ip, success=True)
            user_info = users[username]['user_info'].copy()
            
            # 将用户信息存储到session（用于后续接口认证）
            session['user'] = user_info
            session.permanent = True  # 使session持久化
            
            return jsonify({
                'success': True,
                'data': user_info,
                'message': '登录成功'
            })
        else:
            # 登录失败，记录尝试
            login_limiter.record_attempt(username, client_ip, success=False)
            return jsonify({
                'success': False,
                'error': '用户名或密码错误',
                'remaining_attempts': remaining - 1,
                'need_captcha': True
            }), 401
            
    except Exception as e:
        print(f"传统登录异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'登录异常: {str(e)}'
        }), 500

# SSO测试接口（开发调试用）
@bp.route('/auth/sso/test', methods=['GET'])
def test_sso():
    """测试SSO服务连通性"""
    try:
        # 测试获取appCode
        app_code = sso_service.get_app_code()
        
        if app_code:
            return jsonify({
                'success': True,
                'data': {
                    'appCode': app_code,
                    'message': 'SSO服务连通正常'
                }
            })
        else:
            return jsonify({
                'success': False,
                'error': 'SSO服务连接失败'
            }), 500
            
    except Exception as e:
        print(f"SSO测试异常: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'SSO测试异常: {str(e)}'
        }), 500

@bp.route('/auth/sso/test-token-format', methods=['POST'])
def test_token_format():
    """测试token格式和编码"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': '请求数据不能为空'
            }), 400
        
        token = data.get('token')
        if not token:
            return jsonify({
                'success': False,
                'error': 'Token不能为空'
            }), 400
        
        # 获取appCode
        app_code = sso_service.get_app_code()
        if not app_code:
            return jsonify({
                'success': False,
                'error': '无法获取appCode'
            })
        
        # 构造query参数
        import json as json_lib
        import urllib.parse
        
        query_data = {
            "jsonObj": {
                "token": token
            }
        }
        
        query_json = json_lib.dumps(query_data, ensure_ascii=False)
        query_encoded = urllib.parse.quote(query_json)
        
        # 构造完整URL
        base_url = "http://10.77.78.162/apigateway/zhySdk/tokenCheck"
        full_url = f"{base_url}?appCode={app_code}&query={query_encoded}"
        
        return jsonify({
            'success': True,
            'data': {
                'token_info': {
                    'length': len(token),
                    'has_special_chars': any(c in token for c in '!@#$%^&*()'),
                    'preview': token[:10] + '...' + token[-10:] if len(token) > 20 else token
                },
                'app_code': app_code,
                'query_json': query_json,
                'query_encoded_length': len(query_encoded),
                'full_url_length': len(full_url),
                'test_url': base_url + '?appCode=' + app_code + '&query=' + query_encoded[:50] + '...'
            }
        })
        
    except Exception as e:
        print(f"测试token格式异常: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'测试异常: {str(e)}'
        }), 500