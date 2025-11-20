from flask import Blueprint, request, jsonify
from app.services.database_service import DatabaseService
from app.utils.auth_decorator import login_required
from app.models.data_source import DataSource
import traceback

bp = Blueprint('database', __name__)

def handle_masked_password(data):
    """
    处理密码掩码的辅助函数
    如果密码是 ******，尝试从数据库获取真实密码
    返回: (success: bool, error_response: tuple or None)
    error_response 格式: (jsonify_response, status_code)
    """
    if data.get('password') == '******':
        if 'id' in data and data['id']:
            source = DataSource.query.get(data['id'])
            if source:
                data['password'] = source.password
                print(f"从数据源 {source.name} (ID: {source.id}) 获取真实密码")
                return True, None
            else:
                return False, (jsonify({
                    'success': False,
                    'error': f'未找到ID为 {data["id"]} 的数据源'
                }), 404)
        else:
            return False, (jsonify({
                'success': False,
                'error': '密码已被掩码，但未提供数据源ID'
            }), 400)
    
    # 最终检查
    if not data.get('password') or data.get('password') == '******':
        return False, (jsonify({
            'success': False,
            'error': '无法获取有效的数据库密码'
        }), 400)
    
    return True, None

@bp.route('/tables/<int:source_id>', methods=['GET'])
@login_required
def get_tables_by_source(source_id):
    """根据数据源ID获取表列表"""
    try:
        from app.models.data_source import DataSource
        
        # 获取数据源配置
        source = DataSource.query.get(source_id)
        if not source:
            return jsonify({
                'success': False,
                'error': '数据源不存在'
            }), 404
        
        # 构建数据库配置
        db_config = {
            'db_type': source.db_type,
            'host': source.host,
            'port': source.port,
            'database': source.database,
            'schema': getattr(source, 'schema', 'public'),
            'username': source.username,
            'password': source.password
        }
        
        tables = DatabaseService.get_tables(db_config)
        
        return jsonify({
            'success': True,
            'data': tables
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/fields/<int:source_id>/<table_name>', methods=['GET'])
@login_required
def get_table_fields_by_source(source_id, table_name):
    """根据数据源ID和表名获取字段列表"""
    try:
        from app.models.data_source import DataSource
        
        # 获取数据源配置
        source = DataSource.query.get(source_id)
        if not source:
            return jsonify({
                'success': False,
                'error': '数据源不存在'
            }), 404
        
        # 构建数据库配置
        db_config = {
            'db_type': source.db_type,
            'host': source.host,
            'port': source.port,
            'database': source.database,
            'schema': getattr(source, 'schema', 'public'),
            'username': source.username,
            'password': source.password
        }
        
        fields = DatabaseService.get_table_fields(db_config, table_name)
        
        return jsonify({
            'success': True,
            'data': fields
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/preview', methods=['POST'])
@login_required
def preview_data():
    """预览数据"""
    try:
        data = request.get_json()
        
        required_fields = ['data_source_id', 'table_name', 'fields']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'缺少必需字段: {field}'
                }), 400
        
        from app.models.data_source import DataSource
        
        # 获取数据源配置
        source = DataSource.query.get(data['data_source_id'])
        if not source:
            return jsonify({
                'success': False,
                'error': '数据源不存在'
            }), 404
        
        # 构建数据库配置
        db_config = {
            'db_type': source.db_type,
            'host': source.host,
            'port': source.port,
            'database': source.database,
            # 优先使用请求中的schema，如果没有则使用数据源配置的，最后默认为public
            'schema': data.get('schema') or getattr(source, 'schema', 'public'),
            'username': source.username,
            'password': source.password
        }
        
        print(f"预览数据 - 使用schema: {db_config['schema']}, 表: {data['table_name']}")
        
        table_name = data['table_name']
        fields = data['fields']
        limit = data.get('limit', 10)
        
        preview_data = DatabaseService.preview_data(db_config, table_name, fields, limit)
        
        return jsonify({
            'success': True,
            'data': preview_data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/test-connection', methods=['POST'])
def test_connection():
    """测试数据库连接"""
    try:
        data = request.get_json()
        
        required_fields = ['db_type', 'host', 'port', 'database', 'username', 'password']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'缺少必需字段: {field}'
                }), 400
        
        # 处理密码掩码
        success, error_response = handle_masked_password(data)
        if not success:
            return error_response
        
        is_connected = DatabaseService.test_connection(data)
        
        return jsonify({
            'success': True,
            'connected': is_connected,
            'message': '连接成功' if is_connected else '连接失败'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/tables', methods=['GET'])
@login_required
def get_tables_by_query_param():
    """通过查询参数获取数据库表列表"""
    try:
        source_id = request.args.get('source_id', type=int)
        if not source_id:
            return jsonify({
                'success': False,
                'error': '缺少必需参数: source_id'
            }), 400
        
        from app.models.data_source import DataSource
        
        # 获取数据源配置
        source = DataSource.query.get(source_id)
        if not source:
            return jsonify({
                'success': False,
                'error': '数据源不存在'
            }), 404
        
        # 构建数据库配置
        db_config = {
            'db_type': source.db_type,
            'host': source.host,
            'port': source.port,
            'database': source.database,
            'schema': getattr(source, 'schema', 'public'),
            'username': source.username,
            'password': source.password
        }
        
        tables = DatabaseService.get_tables(db_config)
        
        return jsonify({
            'success': True,
            'data': tables
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/tables', methods=['POST'])
@login_required
def get_tables():
    """获取数据库表列表"""
    try:
        data = request.get_json()
        print(f"获取表列表请求数据: {data}")
        
        required_fields = ['db_type', 'host', 'port', 'database', 'username', 'password']
        for field in required_fields:
            if field not in data:
                error_msg = f'缺少必需字段: {field}'
                print(f"验证失败: {error_msg}")
                return jsonify({
                    'success': False,
                    'error': error_msg
                }), 400
        
        # 处理密码掩码
        success, error_response = handle_masked_password(data)
        if not success:
            return error_response
        
        # 从请求中获取schema（如果前端传了）
        if 'schema' in data and data['schema']:
            print(f"使用请求中的schema: {data['schema']}")
        else:
            # 如果请求中没有schema，使用默认值
            data['schema'] = data.get('schema', 'public')
            print(f"使用默认schema: public")
        
        print(f"验证通过，开始获取表列表...")
        tables = DatabaseService.get_tables(data)
        print(f"成功获取 {len(tables)} 个表")
        
        return jsonify({
            'success': True,
            'data': tables
        })
    except Exception as e:
        print(f"获取表列表异常: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/fields', methods=['GET'])
@login_required
def get_table_fields_by_query():
    """通过查询参数获取表字段信息"""
    try:
        source_id = request.args.get('source_id', type=int)
        table_name = request.args.get('table_name')
        
        if not source_id or not table_name:
            return jsonify({
                'success': False,
                'error': '缺少必需参数: source_id, table_name'
            }), 400
        
        from app.models.data_source import DataSource
        
        # 获取数据源配置
        source = DataSource.query.get(source_id)
        if not source:
            return jsonify({
                'success': False,
                'error': '数据源不存在'
            }), 404
        
        # 构建数据库配置
        db_config = {
            'db_type': source.db_type,
            'host': source.host,
            'port': source.port,
            'database': source.database,
            'schema': getattr(source, 'schema', 'public'),
            'username': source.username,
            'password': source.password
        }
        
        fields = DatabaseService.get_table_fields(db_config, table_name)
        
        return jsonify({
            'success': True,
            'data': fields
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/fields', methods=['POST'])
@login_required
def get_table_fields():
    """获取表字段信息"""
    try:
        data = request.get_json()
        print(f"获取字段请求数据: {data}")
        
        required_fields = ['db_type', 'host', 'port', 'database', 'username', 'password', 'table_name']
        for field in required_fields:
            if field not in data:
                error_msg = f'缺少必需字段: {field}'
                print(f"验证失败: {error_msg}")
                return jsonify({
                    'success': False,
                    'error': error_msg
                }), 400
        
        # 处理密码掩码
        success, error_response = handle_masked_password(data)
        if not success:
            return error_response
        
        print(f"验证通过，开始获取字段信息...")
        db_config = {k: v for k, v in data.items() if k != 'table_name'}
        fields = DatabaseService.get_table_fields(db_config, data['table_name'])
        print(f"成功获取 {len(fields)} 个字段")
        
        return jsonify({
            'success': True,
            'data': fields
        })
    except Exception as e:
        print(f"获取字段异常: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500



@bp.route('/statistics', methods=['POST'])
@login_required
def get_data_statistics():
    """获取数据统计信息"""
    try:
        data = request.get_json()
        
        required_fields = ['db_type', 'host', 'port', 'database', 'username', 'password', 'table_name', 'fields']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'缺少必需字段: {field}'
                }), 400
        
        # 处理密码掩码
        success, error_response = handle_masked_password(data)
        if not success:
            return error_response
        
        db_config = {k: v for k, v in data.items() if k not in ['table_name', 'fields']}
        statistics = DatabaseService.get_data_statistics(db_config, data['table_name'], data['fields'])
        
        return jsonify({
            'success': True,
            'data': statistics
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/sources', methods=['GET'])
@login_required
def get_data_sources():
    """获取所有数据源"""
    try:
        print("API: 开始获取数据源列表...")
        sources = DatabaseService.get_data_sources()
        print(f"API: 成功获取 {len(sources)} 个数据源")
        
        return jsonify({
            'success': True,
            'data': sources
        })
    except Exception as e:
        print(f"API: 获取数据源失败: {str(e)}")
        print(f"API: 错误类型: {type(e).__name__}")
        import traceback
        print(f"API: 错误堆栈: {traceback.format_exc()}")
        
        return jsonify({
            'success': False,
            'error': f"加载数据源失败: {str(e)}"
        }), 500

@bp.route('/sources', methods=['POST'])
@login_required
def save_data_source():
    """保存数据源（返回时不包含密码）"""
    try:
        data = request.get_json()
        required_fields = ['name', 'db_type', 'host', 'port', 'database', 'username', 'password']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'缺少必需字段: {field}'
                }), 400
        # 自动测试连接
        is_connected = DatabaseService.test_connection(data)
        # 保存数据源并带上状态
        source = DatabaseService.save_data_source(
            name=data['name'],
            db_type=data['db_type'],
            host=data['host'],
            port=data['port'],
            database=data['database'],
            username=data['username'],
            password=data['password'],
            status=is_connected
        )
        # 返回时不包含真实密码
        return jsonify({
            'success': True,
            'data': source.to_dict(include_password=False)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/cnooc-config', methods=['GET'])
@login_required
def get_cnooc_config():
    """获取CNOOC数据库配置（不包含密码）"""
    try:
        config = DatabaseService.load_cnooc_config()
        # 移除密码字段，不向前端暴露
        if 'password' in config:
            config['password'] = '******'
        return jsonify({
            'success': True,
            'data': config
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/sources/<int:source_id>', methods=['GET'])
@login_required
def get_data_source(source_id):
    """获取单个数据源（不包含密码）"""
    try:
        from app.models.data_source import DataSource
        source = DataSource.query.get(source_id)
        
        if not source:
            return jsonify({
                'success': False,
                'error': '数据源不存在'
            }), 404
        
        # 不返回真实密码，只返回掩码
        return jsonify({
            'success': True,
            'data': source.to_dict(include_password=False)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/sources/<int:source_id>', methods=['PUT'])
@login_required
def update_data_source(source_id):
    """更新数据源配置"""
    try:
        from app.models.data_source import DataSource
        from app import db
        
        source = DataSource.query.get(source_id)
        if not source:
            return jsonify({
                'success': False,
                'error': '数据源不存在'
            }), 404
        
        data = request.get_json()
        
        # 更新字段
        if 'name' in data:
            source.name = data['name']
        if 'host' in data:
            source.host = data['host']
        if 'port' in data:
            source.port = data['port']
        if 'database' in data:
            source.database = data['database']
        if 'username' in data:
            source.username = data['username']
        # 只有当密码不是掩码时才更新（支持用户不修改密码的场景）
        if 'password' in data and data['password'] and data['password'] != '******':
            source.password = data['password']
        
        db.session.commit()
        
        # 返回时不包含真实密码
        return jsonify({
            'success': True,
            'data': source.to_dict(include_password=False)
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/sources/<int:source_id>', methods=['DELETE'])
@login_required
def delete_data_source(source_id):
    """删除数据源"""
    try:
        from app.models.data_source import DataSource
        from app import db
        
        source = DataSource.query.get(source_id)
        if not source:
            return jsonify({
                'success': False,
                'error': '数据源不存在'
            }), 404
        
        source.is_active = False
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '数据源已删除'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/field-values', methods=['GET'])
@login_required
def get_field_values():
    """获取指定字段的不同值（GET方法，通过查询参数）"""
    try:
        source_id = request.args.get('source_id', type=int)
        table_name = request.args.get('table_name')
        field_name = request.args.get('field_name')
        
        if not all([source_id, table_name, field_name]):
            return jsonify({
                'success': False,
                'error': '缺少必需参数: source_id, table_name, field_name'
            }), 400
        
        from app.models.data_source import DataSource
        
        # 获取数据源配置
        source = DataSource.query.get(source_id)
        if not source:
            return jsonify({
                'success': False,
                'error': '数据源不存在'
            }), 404
        
        # 构建数据库配置
        db_config = {
            'db_type': source.db_type,
            'host': source.host,
            'port': source.port,
            'database': source.database,
            'schema': getattr(source, 'schema', 'public'),
            'username': source.username,
            'password': source.password
        }
        
        # 获取字段的不同值
        distinct_values = DatabaseService.get_distinct_values(
            db_config, 
            table_name, 
            field_name
        )
        
        return jsonify({
            'success': True,
            'data': distinct_values
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/distinct-values', methods=['POST'])
@login_required
def get_distinct_values():
    """获取指定字段的不同值"""
    try:
        data = request.get_json()
        
        # 验证必需字段
        if not all(key in data for key in ['data_source_id', 'table_name', 'field_name']):
            return jsonify({
                'success': False,
                'error': '缺少必需参数: data_source_id, table_name, field_name'
            }), 400
        
        from app.models.data_source import DataSource
        
        # 获取数据源配置
        source = DataSource.query.get(data['data_source_id'])
        if not source:
            return jsonify({
                'success': False,
                'error': '数据源不存在'
            }), 404
        
        # 构建数据库配置
        db_config = {
            'db_type': source.db_type,
            'host': source.host,
            'port': source.port,
            'database': source.database,
            # 优先使用请求中的schema
            'schema': data.get('schema') or getattr(source, 'schema', 'public'),
            'username': source.username,
            'password': source.password
        }
        
        print(f"获取不同值 - schema: {db_config['schema']}, 表: {data['table_name']}, 字段: {data['field_name']}")
        
        # 获取字段的不同值
        distinct_values = DatabaseService.get_distinct_values(
            db_config, 
            data['table_name'], 
            data['field_name']
        )
        
        return jsonify({
            'success': True,
            'data': distinct_values
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/schemas', methods=['GET'])
@login_required
def get_schemas():
    """获取数据源的所有schema列表"""
    try:
        source_id = request.args.get('source_id', type=int)
        if not source_id:
            return jsonify({
                'success': False,
                'error': '缺少必需参数: source_id'
            }), 400
        
        from app.models.data_source import DataSource
        
        # 获取数据源配置
        source = DataSource.query.get(source_id)
        if not source:
            return jsonify({
                'success': False,
                'error': '数据源不存在'
            }), 404
        
        # 构建数据库配置
        db_config = {
            'db_type': source.db_type,
            'host': source.host,
            'port': source.port,
            'database': source.database,
            'schema': getattr(source, 'schema', 'public'),
            'username': source.username,
            'password': source.password
        }
        
        # 获取所有schema
        schemas = DatabaseService.get_schemas(db_config)
        
        return jsonify({
            'success': True,
            'data': schemas
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/schemas', methods=['POST'])
def get_schemas_by_config():
    """通过数据库配置获取所有schema列表"""
    try:
        data = request.get_json()
        
        required_fields = ['db_type', 'host', 'port', 'database', 'username', 'password']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'缺少必需字段: {field}'
                }), 400
        
        # 处理密码掩码
        success, error_response = handle_masked_password(data)
        if not success:
            return error_response
        
        # 获取所有schema
        schemas = DatabaseService.get_schemas(data)
        
        return jsonify({
            'success': True,
            'data': schemas
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/tag-data', methods=['POST'])
@login_required
def get_tag_data():
    """获取TAG数据（用于产品数据质检的趋势图）
    
    强制实施数据量限制，保护生产环境数据库
    """
    try:
        data = request.get_json()
        print(f"获取TAG数据请求: {data.keys()}")
        
        # 验证必需字段
        required_fields = ['db_type', 'host', 'port', 'database', 'username', 'password', 'table_name', 'tag_code']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'缺少必需字段: {field}'
                }), 400
        
        # 处理密码掩码
        success, error_response = handle_masked_password(data)
        if not success:
            return error_response
        
        # 强制实施数据量限制（最多300条，用于趋势图）
        limit = min(int(data.get('limit', 300)), 300)
        print(f"🔒 数据量限制: {limit} 条")
        
        # 构建数据库配置
        db_config = {
            'db_type': data['db_type'],
            'host': data['host'],
            'port': data['port'],
            'database': data['database'],
            'schema': data.get('schema', 'public'),
            'username': data['username'],
            'password': data['password']
        }
        
        table_name = data['table_name']
        tag_code = data['tag_code']
        tag_field_name = data.get('tag_field_name', 'tag_code')  # 支持动态字段名
        start_time = data.get('start_time')
        end_time = data.get('end_time')
        
        # 调用DatabaseService获取数据
        tag_data = DatabaseService.get_tag_data(
            db_config,
            table_name,
            tag_code,
            tag_field_name=tag_field_name,
            limit=limit,
            start_time=start_time,
            end_time=end_time
        )
        
        print(f"✅ 成功获取 {len(tag_data)} 条TAG数据")
        
        return jsonify({
            'success': True,
            'data': tag_data,
            'count': len(tag_data),
            'limit': limit
        })
    except Exception as e:
        print(f"❌ 获取TAG数据失败: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/anomaly-check', methods=['POST'])
@login_required
def anomaly_check():
    """产品数据异常检测（数据丢失、断流、数值异常）
    
    强制实施数据量限制，保护生产环境数据库
    """
    try:
        data = request.get_json()
        print(f"异常检测请求: {data.keys()}")
        
        # 验证必需字段
        required_fields = ['db_type', 'host', 'port', 'database', 'username', 'password', 
                          'table_name', 'tag_code', 'gap_thres', 'win_sec', 'z_win', 'z_thres']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'缺少必需字段: {field}'
                }), 400
        
        # 处理密码掩码
        success, error_response = handle_masked_password(data)
        if not success:
            return error_response
        
        # 强制实施数据量限制（最多50000条）
        MAX_LIMIT = 50000
        limit = min(int(data.get('limit', 10000)), MAX_LIMIT)
        print(f"🔒 数据量限制: {limit} 条（最大{MAX_LIMIT}条）")
        
        # 构建数据库配置
        db_config = {
            'db_type': data['db_type'],
            'host': data['host'],
            'port': data['port'],
            'database': data['database'],
            'schema': data.get('schema', 'public'),
            'username': data['username'],
            'password': data['password']
        }
        
        table_name = data['table_name']
        tag_code = data['tag_code']
        tag_field_name = data.get('tag_field_name', 'tag_code')  # 支持动态字段名
        gap_thres = int(data['gap_thres'])
        win_sec = int(data['win_sec'])
        z_win = int(data['z_win'])
        z_thres = float(data['z_thres'])
        start_time = data.get('start_time')
        end_time = data.get('end_time')
        
        # 调用DatabaseService执行异常检测
        result = DatabaseService.detect_anomalies(
            db_config,
            table_name,
            tag_code,
            tag_field_name=tag_field_name,
            gap_thres=gap_thres,
            win_sec=win_sec,
            z_win=z_win,
            z_thres=z_thres,
            limit=limit,
            start_time=start_time,
            end_time=end_time
        )
        
        anomalies_list = result.get('anomalies_list', [])
        print(f"✅ 异常检测完成: 发现 {len(anomalies_list)} 个异常")
        
        return jsonify({
            'success': True,
            'data': result,
            'anomaly_count': len(anomalies_list),
            'limit': limit
        })
    except Exception as e:
        print(f"❌ 异常检测失败: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500 