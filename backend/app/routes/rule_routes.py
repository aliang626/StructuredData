from flask import Blueprint, request, jsonify
from app.services.rule_service import RuleService
from app.services.database_service import DatabaseService
from app.services.field_mapping_service import FieldMappingService
from app.utils.auth_decorator import login_required
from app.models.data_source import DataSource
import traceback

bp = Blueprint('rules', __name__)

# 创建字段映射服务实例
field_mapping_service = FieldMappingService()

def handle_masked_password_in_config(db_config):
    """
    处理db_config中的密码掩码
    如果密码是 ******，尝试从数据库获取真实密码
    返回: (success: bool, error_response: tuple or None)
    """
    if db_config.get('password') == '******':
        # 尝试从 db_config 中获取 id，或者从请求data中获取
        source_id = db_config.get('id') or db_config.get('data_source_id')
        if source_id:
            source = DataSource.query.get(source_id)
            if source:
                db_config['password'] = source.password
                print(f"从数据源 {source.name} (ID: {source.id}) 获取真实密码")
                return True, None
            else:
                return False, (jsonify({
                    'success': False,
                    'error': f'未找到ID为 {source_id} 的数据源'
                }), 404)
        else:
            return False, (jsonify({
                'success': False,
                'error': '密码已被掩码，但未提供数据源ID'
            }), 400)
    
    # 最终检查
    if not db_config.get('password') or db_config.get('password') == '******':
        return False, (jsonify({
            'success': False,
            'error': '无法获取有效的数据库密码'
        }), 400)
    
    return True, None

@bp.route('/libraries', methods=['GET'])
@login_required
def get_rule_libraries():
    """获取规则库列表"""
    try:
        libraries = RuleService.get_rule_libraries()
        return jsonify({
            'success': True,
            'data': libraries
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/libraries/<int:library_id>/rules', methods=['GET'])
@login_required
def get_current_rules(library_id):
    """获取某库的当前规则（无版本模式）"""
    try:
        rules = RuleService.get_latest_rules(library_id)
        return jsonify({'success': True, 'data': rules})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/libraries', methods=['POST'])
@login_required
def create_rule_library():
    """创建规则库"""
    try:
        data = request.get_json()
        
        if 'name' not in data:
            return jsonify({
                'success': False,
                'error': '缺少规则库名称'
            }), 400
        
        library = RuleService.create_rule_library(
            name=data['name'],
            description=data.get('description', ''),
            force_replace=data.get('force_replace', False)
        )
        
        return jsonify({
            'success': True,
            'data': library.to_dict()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/libraries/<int:library_id>/versions', methods=['GET'])
@login_required
def get_rule_versions(library_id):
    """保留向后兼容的接口：返回当前规则作为单一版本。

    为兼容部分前端实现，如果数据库已保存了当前规则，则返回一个包含 rules 的对象；
    若为空则返回空数组。
    """
    try:
        versions = RuleService.get_rule_versions(library_id)
        return jsonify({'success': True, 'data': versions})
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/libraries/<int:library_id>/rules', methods=['POST'])
@login_required
def save_current_rules(library_id):
    """无版本模式：保存为当前规则（新接口）。"""
    try:
        data = request.get_json()
        if 'rules' not in data:
            return jsonify({'success': False, 'error': '缺少必需字段: rules'}), 400

        version = RuleService.save_current_rules(
            library_id=library_id,
            rules=data['rules'],
            created_by=data.get('created_by', ''),
            description=data.get('description', '')
        )

        return jsonify({'success': True, 'data': version.to_dict()})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/libraries/save-by-name', methods=['POST'])
@login_required
def save_current_rules_by_name():
    """按名称保存当前规则：如果库不存在则自动创建。
    请求体: { name, description?, rules, created_by? }
    返回: 保存后的伪版本（current）的信息
    """
    try:
        data = request.get_json()
        required = ['name', 'rules']
        for f in required:
            if f not in data:
                return jsonify({'success': False, 'error': f'缺少必需字段: {f}'}), 400

        library = RuleService.get_or_create_library(
            name=data['name'].strip(),
            description=data.get('description', '').strip()
        )

        version = RuleService.save_current_rules(
            library_id=library.id,
            rules=data['rules'],
            created_by=data.get('created_by', ''),
            description=data.get('description', '')
        )

        return jsonify({'success': True, 'data': {
            'library': library.to_dict(),
            'version': version.to_dict()
        }})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/generate', methods=['POST'])
@login_required
def generate_rules():
    """从数据生成规则 - 基础规则生成接口"""
    try:
        data = request.get_json()
        
        # 参数验证
        required_fields = ['db_config', 'table_name', 'fields']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'缺少必需字段: {field}'
                }), 400
        
        # 处理密码掩码
        success, error_response = handle_masked_password_in_config(data['db_config'])
        if not success:
            return error_response
        
        # 验证字段列表
        if not isinstance(data['fields'], list) or len(data['fields']) == 0:
            return jsonify({
                'success': False,
                'error': '字段列表不能为空'
            }), 400
        
        # 默认规则类型（移除null_check和unique_check）
        rule_types = data.get('rule_types', ['range', 'outlier', 'cluster'])
        
        # 验证规则类型
        valid_rule_types = ['range', 'outlier', 'cluster', 'depth_interval']
        invalid_types = [rt for rt in rule_types if rt not in valid_rule_types]
        if invalid_types:
            return jsonify({
                'success': False,
                'error': f'不支持的规则类型: {", ".join(invalid_types)}'
            }), 400
        
        # 深度字段参数
        depth_field = data.get('depth_field')
        depth_interval = data.get('depth_interval', 10)
        
        # 验证深度区间参数
        if depth_interval <= 0:
            return jsonify({
                'success': False,
                'error': '深度区间必须大于0'
            }), 400
        
        # 如果指定了深度字段，自动添加深度区间分析
        if depth_field and 'depth_interval' not in rule_types:
            rule_types.append('depth_interval')
        
        # 生成规则
        rules = RuleService.generate_rules_from_data(
            db_config=data['db_config'],
            table_name=data['table_name'],
            fields=data['fields'],
            rule_types=rule_types,
            depth_field=depth_field,
            depth_interval=depth_interval
        )
        
        # 统计规则信息
        rule_count_by_type = {}
        for rule in rules:
            rule_type = rule['rule_type']
            rule_count_by_type[rule_type] = rule_count_by_type.get(rule_type, 0) + 1
        
        return jsonify({
            'success': True,
            'data': {
                'rules': rules,
                'summary': {
                    'total_rules': len(rules),
                    'rule_count_by_type': rule_count_by_type,
                    'fields_processed': len(data['fields']),
                    'depth_analysis': depth_field is not None
                }
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

@bp.route('/generate-statistical', methods=['POST'])
@login_required
def generate_statistical_rules():
    """生成基于统计分析的规则 - 高级统计分析接口"""
    try:
        data = request.get_json()
        
        # 参数验证
        required_fields = ['db_config', 'table_name', 'fields']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'缺少必需字段: {field}'
                }), 400
        
        # 处理密码掩码
        success, error_response = handle_masked_password_in_config(data['db_config'])
        if not success:
            return error_response
        
        # 验证字段列表
        if not isinstance(data['fields'], list) or len(data['fields']) == 0:
            return jsonify({
                'success': False,
                'error': '字段列表不能为空'
            }), 400
        
        # 统计分析专用的规则类型（支持更多高级分析）
        rule_type = data.get('rule_type', 'range')
        
        # 验证规则类型（统计分析支持的类型更全面）
        valid_statistical_types = [
            'range', 'outlier', 'cluster', 'depth_interval',
            'range_2sigma', 'range_percentile', 
            'outlier_3sigma', 'outlier_iqr', 'outlier_zscore',
            'cluster_kmeans', 'cluster_dbscan', 'cluster_group_ranges', 'manual_range',
            'frequency_analysis'
        ]
        if rule_type not in valid_statistical_types:
            return jsonify({
                'success': False,
                'error': f'统计分析不支持的规则类型: {rule_type}'
            }), 400
        
        # 深度字段参数（用于回归型数据分析）
        depth_field = data.get('depth_field')
        depth_interval = data.get('depth_interval', 10)
        
        # 验证深度字段和区间参数
        if depth_field:
            if depth_field not in data['fields']:
                return jsonify({
                    'success': False,
                    'error': f'深度字段 "{depth_field}" 不在字段列表中'
                }), 400
            
            if depth_interval <= 0 or depth_interval > 1000:
                return jsonify({
                    'success': False,
                    'error': '深度区间必须在1-1000米之间'
                }), 400
        
        # 验证深度区间分析的前置条件
        if rule_type == 'depth_interval' and not depth_field:
            return jsonify({
                'success': False,
                'error': '进行深度区间分析时必须指定深度字段'
            }), 400
        
        # 聚类分析参数
        cluster_params = {
            'max_clusters': data.get('max_clusters', 5),  # 最大聚类数
            'dbscan_eps': data.get('dbscan_eps', 0.5),   # DBSCAN eps参数
            'dbscan_min_samples': data.get('dbscan_min_samples', 5)  # DBSCAN最小样本数
        }

        # 手工固定范围型参数
        manual_ranges = data.get('manual_ranges')
        
        # 异常值检测参数
        outlier_params = {
            'zscore_threshold': data.get('zscore_threshold', 2.5),  # Z-score阈值
            'iqr_multiplier': data.get('iqr_multiplier', 1.5)      # IQR倍数
        }
        
        # 构建db_config，优先使用请求中的schema
        db_config = data['db_config'].copy()
        if 'schema' in data and data['schema']:
            db_config['schema'] = data['schema']
        elif 'schema' not in db_config:
            db_config['schema'] = 'public'
        
        print(f"规则生成 - 使用schema: {db_config.get('schema', 'public')}, 表: {data['table_name']}")
        
        # 生成统计分析规则
        rules = RuleService.generate_rules_from_data(
            db_config=db_config,
            table_name=data['table_name'],
            fields=data['fields'],
            rule_type=rule_type,
            depth_field=depth_field,
            depth_interval=depth_interval,
            cluster_params=cluster_params,
            outlier_params=outlier_params,
            group_by_field=data.get('group_by_field'),
            cluster_features=data.get('cluster_features'),
            manual_ranges=manual_ranges
        )
        
        # 详细统计分析结果
        rule_count_by_type = {rule_type: len(rules)}
        rule_count_by_field = {}
        statistical_summary = {}
        
        for rule in rules:
            field = rule['field']
            
            # 按字段统计
            rule_count_by_field[field] = rule_count_by_field.get(field, 0) + 1
            
            # 收集统计信息
            if 'params' in rule and 'mean' in rule['params']:
                if field not in statistical_summary:
                    statistical_summary[field] = {}
                statistical_summary[field][rule_type] = {
                    'mean': rule['params'].get('mean'),
                    'std': rule['params'].get('std'),
                    'range': [rule['params'].get('lower_bound'), rule['params'].get('upper_bound')]
                }
        
        # 分析类型分类
        analysis_types = {
            'range_analysis': [rule_type] if rule_type.startswith('range') else [],
            'outlier_detection': [rule_type] if rule_type.startswith('outlier') else [],
            'cluster_analysis': [rule_type] if rule_type.startswith('cluster') else [],
            'depth_analysis': [rule_type] if rule_type == 'depth_interval' else [],
            'frequency_analysis': [rule_type] if rule_type == 'frequency_analysis' else []
        }
        
        return jsonify({
            'success': True,
            'data': {
                'rules': rules,
                'summary': {
                    'total_rules': len(rules),
                    'fields_processed': len(data['fields']),
                    'rule_count_by_type': rule_count_by_type,
                    'rule_count_by_field': rule_count_by_field,
                    'analysis_types': analysis_types,
                    'statistical_summary': statistical_summary,
                    'depth_analysis': {
                        'enabled': depth_field is not None,
                        'depth_field': depth_field,
                        'depth_interval': depth_interval if depth_field else None
                    },
                    'parameters': {
                        'cluster_params': cluster_params,
                        'outlier_params': outlier_params
                    }
                }
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

@bp.route('/generate-advanced', methods=['POST'])
@login_required
def generate_advanced_rules():
    """生成高级规则 - 基于模型配置的规则生成"""
    try:
        data = request.get_json()
        
        # 参数验证
        required_fields = ['db_config', 'table_name', 'fields']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'缺少必需字段: {field}'
                }), 400
        
        # 处理密码掩码
        success, error_response = handle_masked_password_in_config(data['db_config'])
        if not success:
            return error_response
        
        # 验证字段列表
        if not isinstance(data['fields'], list) or len(data['fields']) == 0:
            return jsonify({
                'success': False,
                'error': '字段列表不能为空'
            }), 400
        
        model_config_id = data.get('model_config_id')
        
        # 如果提供了模型配置ID，验证其存在性
        if model_config_id:
            from app.models.model_config import ModelConfig
            model_config = ModelConfig.query.get(model_config_id)
            if not model_config:
                return jsonify({
                    'success': False,
                    'error': f'模型配置ID {model_config_id} 不存在'
                }), 400
        
        # 高级规则生成参数
        advanced_params = {
            'use_statistical_analysis': data.get('use_statistical_analysis', True),
            'include_correlation_analysis': data.get('include_correlation_analysis', False),
            'depth_field': data.get('depth_field'),
            'depth_interval': data.get('depth_interval', 10),
            'confidence_level': data.get('confidence_level', 0.95),  # 置信水平
            'outlier_sensitivity': data.get('outlier_sensitivity', 'medium')  # 异常值检测敏感度
        }
        
        # 验证置信水平
        if not (0.8 <= advanced_params['confidence_level'] <= 0.99):
            return jsonify({
                'success': False,
                'error': '置信水平必须在0.8-0.99之间'
            }), 400
        
        # 验证异常值检测敏感度
        valid_sensitivity = ['low', 'medium', 'high']
        if advanced_params['outlier_sensitivity'] not in valid_sensitivity:
            return jsonify({
                'success': False,
                'error': f'异常值检测敏感度必须是: {", ".join(valid_sensitivity)}'
            }), 400
        
        # 生成高级规则
        rules = RuleService.generate_advanced_rules(
            db_config=data['db_config'],
            table_name=data['table_name'],
            fields=data['fields'],
            model_config_id=model_config_id,
            advanced_params=advanced_params
        )
        
        # 统计高级规则信息
        rule_count_by_type = {}
        rule_count_by_field = {}
        advanced_features = {
            'statistical_analysis': 0,
            'correlation_analysis': 0,
            'depth_analysis': 0,
            'confidence_intervals': 0
        }
        
        for rule in rules:
            rule_type = rule['rule_type']
            field = rule['field']
            
            # 按类型统计
            rule_count_by_type[rule_type] = rule_count_by_type.get(rule_type, 0) + 1
            
            # 按字段统计
            rule_count_by_field[field] = rule_count_by_field.get(field, 0) + 1
            
            # 统计高级特性使用情况
            if 'statistical' in rule_type or 'sigma' in rule_type:
                advanced_features['statistical_analysis'] += 1
            if 'correlation' in rule_type:
                advanced_features['correlation_analysis'] += 1
            if 'depth' in rule_type:
                advanced_features['depth_analysis'] += 1
            if 'confidence' in rule.get('params', {}):
                advanced_features['confidence_intervals'] += 1
        
        return jsonify({
            'success': True,
            'data': {
                'rules': rules,
                'summary': {
                    'total_rules': len(rules),
                    'fields_processed': len(data['fields']),
                    'rule_count_by_type': rule_count_by_type,
                    'rule_count_by_field': rule_count_by_field,
                    'advanced_features': advanced_features,
                    'model_config_id': model_config_id,
                    'parameters': advanced_params
                }
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

@bp.route('/validate', methods=['POST'])
@login_required
def validate_rule():
    """验证单个规则"""
    try:
        data = request.get_json()
        
        required_fields = ['rule', 'data']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'缺少必需字段: {field}'
                }), 400
        
        import pandas as pd
        df = pd.DataFrame(data['data'])
        
        is_valid, message = RuleService.validate_rule(data['rule'], df)
        
        return jsonify({
            'success': True,
            'data': {
                'is_valid': is_valid,
                'message': message
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500



@bp.route('/validate-batch', methods=['POST'])
@login_required
def validate_rules_batch():
    """批量验证规则 - 支持统计分析和详细报告"""
    try:
        data = request.get_json()
        
        required_fields = ['rules', 'db_config', 'table_name']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'缺少必需字段: {field}'
                }), 400
        
        # 处理密码掩码
        success, error_response = handle_masked_password_in_config(data['db_config'])
        if not success:
            return error_response
        
        # 验证规则列表
        rules = data['rules']
        if not isinstance(rules, list) or len(rules) == 0:
            return jsonify({
                'success': False,
                'error': '规则列表不能为空'
            }), 400
        
        # 获取数据进行验证
        try:
            connection_string = DatabaseService.get_connection_string(data['db_config'], 'utf8')
            engine = DatabaseService.create_engine(connection_string)
            
            # 获取所有需要的字段
            fields = list(set([rule['field'] for rule in rules]))
            
            # 导入DatabaseService以使用quote_identifier方法
            from app.services.database_service import DatabaseService
            
            # 使用引号包装表名和字段名
            quoted_table_name = DatabaseService.quote_identifier(data['table_name'])
            
            # 构建完整的表名（包含schema）
            schema = data['db_config'].get('schema', 'public')
            if schema and schema != 'public':
                quoted_schema = DatabaseService.quote_identifier(schema)
                full_table_name = f"{quoted_schema}.{quoted_table_name}"
            else:
                full_table_name = quoted_table_name
            
            quoted_fields = [DatabaseService.quote_identifier(field) for field in fields]
            field_list = ', '.join(quoted_fields)
            query = f"SELECT {field_list} FROM {full_table_name}"
            
            # 支持数据采样以提高性能
            sample_size = data.get('sample_size', 10000)
            if sample_size > 0:
                query += f" LIMIT {sample_size}"
            
            df = pd.read_sql(query, engine)
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'数据获取失败: {str(e)}'
            }), 500
        
        # 批量验证规则
        validation_results = []
        summary_stats = {
            'total_rules': len(rules),
            'passed_rules': 0,
            'failed_rules': 0,
            'error_rules': 0,
            'validation_details': {}
        }
        
        import pandas as pd
        
        for i, rule in enumerate(rules):
            try:
                # 验证规则格式
                if 'field' not in rule or 'rule_type' not in rule:
                    validation_results.append({
                        'rule_index': i,
                        'rule_name': rule.get('name', f'Rule_{i}'),
                        'field': rule.get('field', 'unknown'),
                        'rule_type': rule.get('rule_type', 'unknown'),
                        'is_valid': False,
                        'error': '规则格式不正确，缺少必需字段',
                        'validation_stats': None
                    })
                    summary_stats['error_rules'] += 1
                    continue
                
                # 检查字段是否存在
                if rule['field'] not in df.columns:
                    validation_results.append({
                        'rule_index': i,
                        'rule_name': rule.get('name', f'Rule_{i}'),
                        'field': rule['field'],
                        'rule_type': rule['rule_type'],
                        'is_valid': False,
                        'error': f'字段 {rule["field"]} 在数据中不存在',
                        'validation_stats': None
                    })
                    summary_stats['error_rules'] += 1
                    continue
                
                # 执行规则验证
                is_valid, message, validation_stats = RuleService.validate_rule_detailed(rule, df)
                
                validation_results.append({
                    'rule_index': i,
                    'rule_name': rule.get('name', f'Rule_{i}'),
                    'field': rule['field'],
                    'rule_type': rule['rule_type'],
                    'is_valid': is_valid,
                    'message': message,
                    'validation_stats': validation_stats
                })
                
                if is_valid:
                    summary_stats['passed_rules'] += 1
                else:
                    summary_stats['failed_rules'] += 1
                
                # 收集字段级别的统计信息
                field = rule['field']
                if field not in summary_stats['validation_details']:
                    summary_stats['validation_details'][field] = {
                        'total_rules': 0,
                        'passed_rules': 0,
                        'failed_rules': 0,
                        'rule_types': []
                    }
                
                summary_stats['validation_details'][field]['total_rules'] += 1
                summary_stats['validation_details'][field]['rule_types'].append(rule['rule_type'])
                
                if is_valid:
                    summary_stats['validation_details'][field]['passed_rules'] += 1
                else:
                    summary_stats['validation_details'][field]['failed_rules'] += 1
                
            except Exception as e:
                validation_results.append({
                    'rule_index': i,
                    'rule_name': rule.get('name', f'Rule_{i}'),
                    'field': rule.get('field', 'unknown'),
                    'rule_type': rule.get('rule_type', 'unknown'),
                    'is_valid': False,
                    'error': f'验证过程中发生错误: {str(e)}',
                    'validation_stats': None
                })
                summary_stats['error_rules'] += 1
        
        # 计算总体统计信息
        summary_stats['success_rate'] = (
            summary_stats['passed_rules'] / summary_stats['total_rules'] * 100
            if summary_stats['total_rules'] > 0 else 0
        )
        
        summary_stats['data_info'] = {
            'total_records': len(df),
            'fields_validated': len(fields),
            'sample_size': sample_size if sample_size > 0 else len(df)
        }
        
        return jsonify({
            'success': True,
            'data': {
                'validation_results': validation_results,
                'summary': summary_stats
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

@bp.route('/libraries/<int:library_id>', methods=['GET'])
@login_required
def get_rule_library(library_id):
    """获取单个规则库"""
    try:
        from app.models.rule_model import RuleLibrary
        library = RuleLibrary.query.get(library_id)
        
        if not library:
            return jsonify({
                'success': False,
                'error': '规则库不存在'
            }), 404
        
        return jsonify({
            'success': True,
            'data': library.to_dict()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/libraries/<int:library_id>', methods=['PUT'])
@login_required
def update_rule_library(library_id):
    """更新规则库"""
    try:
        from app.models.rule_model import RuleLibrary
        from app import db
        
        library = RuleLibrary.query.get(library_id)
        if not library:
            return jsonify({
                'success': False,
                'error': '规则库不存在'
            }), 404
        
        data = request.get_json()
        
        if 'name' in data:
            library.name = data['name']
        if 'description' in data:
            library.description = data['description']
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': library.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/libraries/<int:library_id>', methods=['DELETE'])
@login_required
def delete_rule_library(library_id):
    """删除规则库"""
    try:
        from app.models.rule_model import RuleLibrary
        from app import db
        
        library = RuleLibrary.query.get(library_id)
        if not library:
            return jsonify({
                'success': False,
                'error': '规则库不存在'
            }), 404
        
        library.is_active = False
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '规则库已删除'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/versions/<int:version_id>', methods=['GET'])
@login_required
def get_rule_version(version_id):
    """获取单个规则版本"""
    try:
        from app.models.rule_model import RuleVersion
        version = RuleVersion.query.get(version_id)
        
        if not version:
            return jsonify({
                'success': False,
                'error': '规则版本不存在'
            }), 404
        
        return jsonify({
            'success': True,
            'data': version.to_dict()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/rule-types', methods=['GET'])
@login_required
def get_supported_rule_types():
    """获取支持的规则类型信息"""
    try:
        # 基础规则类型（移除了null_check和unique_check）
        basic_rule_types = {
            'range': {
                'name': '范围检查',
                'description': '检查数值是否在合理范围内',
                'applicable_data_types': ['numeric'],
                'subtypes': ['range_2sigma', 'range_percentile'],
                'parameters': ['mean', 'std', 'lower_bound', 'upper_bound']
            },
            'outlier': {
                'name': '异常值检测',
                'description': '识别数据中的异常值',
                'applicable_data_types': ['numeric'],
                'subtypes': ['outlier_3sigma', 'outlier_iqr', 'outlier_zscore'],
                'parameters': ['threshold', 'method', 'outlier_count']
            },
            'cluster': {
                'name': '聚类分析',
                'description': '对数据进行聚类分析和模式识别',
                'applicable_data_types': ['numeric'],
                'subtypes': ['cluster_kmeans', 'cluster_dbscan'],
                'parameters': ['n_clusters', 'cluster_centers', 'eps', 'min_samples']
            },
            'depth_interval': {
                'name': '深度区间分析',
                'description': '按深度区间进行统计分析（回归型数据）',
                'applicable_data_types': ['numeric'],
                'subtypes': ['depth_interval_stats'],
                'parameters': ['depth_field', 'depth_interval', 'interval_stats'],
                'requires': ['depth_field']
            }
        }
        
        # 统计分析专用规则类型
        statistical_rule_types = {
            'range_2sigma': {
                'name': '2σ范围检查',
                'description': '基于均值±2倍标准差的范围检查',
                'category': 'range',
                'method': '2sigma',
                'suitable_for': '正态分布数据'
            },
            'range_percentile': {
                'name': '分位数范围检查',
                'description': '基于25%-75%分位数的范围检查',
                'category': 'range',
                'method': 'percentile',
                'suitable_for': '对异常值鲁棒的范围验证'
            },
            'outlier_3sigma': {
                'name': '3σ异常值检测',
                'description': '基于均值±3倍标准差识别异常值',
                'category': 'outlier',
                'method': '3sigma',
                'suitable_for': '正态分布数据的异常值识别'
            },
            'outlier_iqr': {
                'name': 'IQR异常值检测',
                'description': '基于四分位距的1.5倍识别异常值',
                'category': 'outlier',
                'method': 'iqr',
                'suitable_for': '非正态分布数据的异常值识别'
            },
            'outlier_zscore': {
                'name': 'Z-score异常值检测',
                'description': '基于Z-score阈值识别异常值',
                'category': 'outlier',
                'method': 'zscore',
                'suitable_for': '标准化后的异常值识别'
            },
            'cluster_kmeans': {
                'name': 'K-means聚类分析',
                'description': '使用K-means算法进行数据聚类',
                'category': 'cluster',
                'method': 'kmeans',
                'suitable_for': '数据聚类和模式识别'
            },
            'cluster_dbscan': {
                'name': 'DBSCAN密度聚类',
                'description': '使用DBSCAN进行密度聚类和异常值检测',
                'category': 'cluster',
                'method': 'dbscan',
                'suitable_for': '密度聚类和异常值检测'
            },
            'frequency_analysis': {
                'name': '频率分析',
                'description': '分析分类型数据的分布频率',
                'category': 'categorical',
                'method': 'frequency',
                'suitable_for': '分类型数据的分布分析'
            }
        }
        
        # 数据类型分类
        data_type_categories = {
            'regression_data': {
                'name': '回归型数据',
                'description': '连续数值型数据，如孔隙度、渗透率等',
                'recommended_rules': ['range_2sigma', 'outlier_3sigma', 'depth_interval_stats'],
                'analysis_focus': '深度区间统计分析'
            },
            'cluster_data': {
                'name': '聚簇型数据',
                'description': '具有聚类特征的数据，如方位、角度等',
                'recommended_rules': ['cluster_kmeans', 'cluster_dbscan', 'outlier_iqr'],
                'analysis_focus': '聚类分析和模式识别'
            },
            'categorical_data': {
                'name': '分类型数据',
                'description': '离散分类数据，如岩性、地层等',
                'recommended_rules': ['frequency_analysis'],
                'analysis_focus': '频率分布分析'
            }
        }
        
        # API接口信息
        api_endpoints = {
            '/generate': {
                'name': '基础规则生成',
                'description': '生成基础的数据质量规则',
                'supported_rule_types': list(basic_rule_types.keys()),
                'use_case': '快速生成常用规则'
            },
            '/generate-statistical': {
                'name': '统计分析规则生成',
                'description': '基于高级统计分析生成规则',
                'supported_rule_types': list(statistical_rule_types.keys()),
                'use_case': '深度统计分析和规则生成'
            },
            '/generate-advanced': {
                'name': '高级规则生成',
                'description': '基于模型配置的高级规则生成',
                'supported_rule_types': list(basic_rule_types.keys()) + list(statistical_rule_types.keys()),
                'use_case': '结合模型配置的复杂规则生成'
            }
        }
        
        # 参数配置指南
        parameter_guide = {
            'depth_interval': {
                'name': '深度区间大小',
                'type': 'integer',
                'default': 10,
                'range': [1, 1000],
                'unit': '米',
                'description': '用于深度区间分析的区间大小'
            },
            'max_clusters': {
                'name': '最大聚类数',
                'type': 'integer',
                'default': 5,
                'range': [2, 10],
                'description': 'K-means聚类的最大聚类数'
            },
            'zscore_threshold': {
                'name': 'Z-score阈值',
                'type': 'float',
                'default': 2.5,
                'range': [1.5, 4.0],
                'description': 'Z-score异常值检测的阈值'
            },
            'confidence_level': {
                'name': '置信水平',
                'type': 'float',
                'default': 0.95,
                'range': [0.8, 0.99],
                'description': '统计分析的置信水平'
            }
        }
        
        return jsonify({
            'success': True,
            'data': {
                'basic_rule_types': basic_rule_types,
                'statistical_rule_types': statistical_rule_types,
                'data_type_categories': data_type_categories,
                'api_endpoints': api_endpoints,
                'parameter_guide': parameter_guide,
                'removed_types': {
                    'null_check': '空值检查（已移除）',
                    'unique_check': '唯一性检查（已移除）'
                },
                'version': '2.0.0',
                'last_updated': '2025-01-26'
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500 

@bp.route('/field-mapping/search', methods=['GET'])
@login_required
def search_field_mapping():
    """搜索字段映射"""
    try:
        query = request.args.get('q', '').strip()
        limit = min(int(request.args.get('limit', 20)), 50)
        
        if not query:
            return jsonify({
                'success': False,
                'error': '搜索查询不能为空'
            }), 400
        
        results = field_mapping_service.search_fields(query, limit)
        
        return jsonify({
            'success': True,
            'data': {
                'query': query,
                'results': results,
                'total_count': len(results)
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/field-mapping/info/<path:field_name>', methods=['GET'])
@login_required
def get_field_mapping_info(field_name):
    """获取字段映射信息"""
    try:
        field_info = field_mapping_service.get_field_info(field_name)
        
        return jsonify({
            'success': True,
            'data': field_info
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/field-mapping/all', methods=['GET'])
@login_required
def get_all_field_mappings():
    """获取所有字段映射"""
    try:
        mappings = field_mapping_service.get_all_mappings()
        
        return jsonify({
            'success': True,
            'data': {
                'mappings': mappings,
                'total_count': len(mappings)
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/field-mapping/translate', methods=['POST'])
@login_required
def translate_fields():
    """批量翻译字段名"""
    try:
        data = request.get_json()
        fields = data.get('fields', [])
        
        if not fields:
            return jsonify({
                'success': False,
                'error': '字段列表不能为空'
            }), 400
        
        translations = {}
        for field in fields:
            chinese_name = field_mapping_service.get_chinese_name(field)
            translations[field] = chinese_name
        
        return jsonify({
            'success': True,
            'data': {
                'translations': translations,
                'total_fields': len(fields)
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/field-mapping/translate-rules', methods=['POST'])
@login_required
def translate_rules():
    """批量翻译规则名称和类型"""
    try:
        data = request.get_json()
        rules = data.get('rules', [])
        
        if not rules:
            return jsonify({
                'success': False,
                'error': '规则列表不能为空'
            }), 400
        
        translations = {}
        for rule in rules:
            rule_name = rule.get('name', '')
            rule_type = rule.get('rule_type', '')
            
            if rule_name:
                chinese_name = field_mapping_service.get_rule_name_translation(rule_name)
                translations[f'name_{rule_name}'] = chinese_name
            
            if rule_type:
                chinese_type = field_mapping_service.get_rule_type_translation(rule_type)
                translations[f'type_{rule_type}'] = chinese_type
        
        return jsonify({
            'success': True,
            'data': {
                'translations': translations,
                'total_rules': len(rules)
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500 