# app/routes/lstm_anomaly_routes.py
import traceback
import numpy as np
from app.services.database_service import DatabaseService
from app.services.lstm_anomaly_service import LSTMAnomalyService
from flask import Blueprint, request, jsonify
from app.models.model_registry import get_model_config_by_param  # 导入我们新的配置获取函数
from app.utils.auth_decorator import login_required

bp = Blueprint('lstm_anomaly_routes', __name__)


@bp.route('/models', methods=['POST'])
@login_required
def create_model_config():
    """创建LSTM异常检测模型配置"""
    try:
        data = request.get_json()
        model_config = LSTMAnomalyService.create_model_config(data)
        return jsonify({
            'success': True,
            'data': model_config.to_dict()
        }), 201
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/models/<int:model_id>', methods=['GET'])
@login_required
def get_model_config(model_id):
    """获取指定ID的模型配置"""
    try:
        model_config = LSTMAnomalyService.get_model_config(model_id)
        if not model_config:
            return jsonify({
                'success': False,
                'error': 'Model config not found'
            }), 404

        return jsonify({
            'success': True,
            'data': model_config.to_dict()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/models/active', methods=['GET'])
@login_required
def get_active_model_config():
    """获取激活的模型配置"""
    try:
        model_type = request.args.get('type')
        model_config = LSTMAnomalyService.get_active_model_config(model_type)
        if not model_config:
            return jsonify({
                'success': False,
                'error': f'No active model config found for type: {model_type}'
            }), 404

        return jsonify({
            'success': True,
            'data': model_config.to_dict()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/models/<int:model_id>', methods=['PUT'])
@login_required
def update_model_config(model_id):
    """更新模型配置"""
    try:
        model_config = LSTMAnomalyService.get_model_config(model_id)
        if not model_config:
            return jsonify({
                'success': False,
                'error': 'Model config not found'
            }), 404

        data = request.get_json()
        updated_config = LSTMAnomalyService.update_model_config(model_id, data)
        return jsonify({
            'success': True,
            'data': updated_config.to_dict()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/predict', methods=['POST'])
@login_required
def predict_well():

    """对井的序列数据进行异常预测"""
    try:
        data = request.get_json()
        model_id = data.get('model_id')
        model_type = data.get('model_type')

        # 获取模型配置
        if model_id:
            model_config = LSTMAnomalyService.get_model_config(model_id)
        else:
            model_config = LSTMAnomalyService.get_active_model_config(model_type)

        if not model_config:
            return jsonify({
                'success': False,
                'error': 'No model config found'
            }), 404

        # 根据模型类型进行预测
        predictions, probabilities = LSTMAnomalyService.predict_well(model_config, **data)

        return jsonify({
            'success': True,
            'data': {
                'predictions': predictions,
                'probabilities': probabilities,
                'model_id': model_config.id
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/detect-for-ui', methods=['POST'])
@login_required
def detect_for_ui():
    try:
        data = request.get_json()

        # 这是修改后的新逻辑，它检查的是 data_source_id
        required_fields = ['data_source_id', 'table_name', 'well_id', 'parameter']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'error': f'缺少必需字段: {field}'}), 400

        data_source_id = data['data_source_id']
        table_name = data['table_name']
        well_id = data['well_id']
        parameter = data['parameter']

        # 如果前端传了 schema，我们要在下面用到它
        target_schema = data.get('schema')
        
       # 🔒 强制实施数据量限制，保护生产环境
        MAX_LIMIT = 50000
        raw_limit = data.get('limit')
        
        # [修复] 处理 limit 为 None 的情况 (对应前端"全部数据")
        if raw_limit is None:
            limit = MAX_LIMIT  # 如果用户选了"全部"，为了安全，强制限制为最大值
            print(f"ℹ️ 用户选择全量数据，系统强制限制为 {MAX_LIMIT} 条以保护性能")
        else:
            limit = int(raw_limit)
            
        limit = min(limit, MAX_LIMIT)  # 双重保险，确保不超过最大值
        start_date = data.get('start_date')  # 可选的时间范围
        end_date = data.get('end_date')
        
        print(f"🔒 LSTM异常检测数据量限制: {limit} 条（最大{MAX_LIMIT}条）")
        if start_date or end_date:
            print(f"   时间范围: {start_date or '最早'} ~ {end_date or '最新'}")

        from app.models.data_source import DataSource
        
        # 1. 直接查询 DataSource 对象
        source = DataSource.query.get(data_source_id)
        if not source:
            return jsonify({'success': False, 'error': f'ID为 {data_source_id} 的数据源配置未找到'}), 404
        
        # 2. 手动构建 db_config 字典
        db_config = {
            'db_type': source.db_type,
            'host': source.host,
            'port': source.port,
            'database': source.database,
            # 优先使用前端传来的 schema，没有才用默认的
            'schema': target_schema if target_schema else getattr(source, 'schema', 'public'),
            'username': source.username,
            'password': source.password
        }

        # 使用获取到的 db_config 进行后续操作（添加limit参数）
        full_sequence_data = DatabaseService.get_well_parameter_sequence(
            db_config, 
            table_name, 
            well_id, 
            parameter,
            limit=limit,
            start_date=start_date,
            end_date=end_date
        )

        if not full_sequence_data:
            return jsonify({'success': True, 'anomalies': [], 'message': '未查询到相关数据', 'total_points': 0})

        # ... (后续逻辑保持不变) ...
        pre_checked_anomalies = []
        clean_sequence_for_model = []

        for point in full_sequence_data:
            value = point.get('value')
            try:
                numeric_value = float(value) if value is not None else None
            except (ValueError, TypeError):
                numeric_value = None

            if numeric_value == 0 or numeric_value is None:
                pre_checked_anomalies.append({
                    'value': 0 if numeric_value == 0 else 'N/A',
                    'type': '数据缺失',
                    'timestamp': point.get('date_time_index') or point.get('tag_time')
                })
            else:
                point['value'] = numeric_value
                clean_sequence_for_model.append(point)

        model_config_dict = get_model_config_by_param(parameter)
        model_anomalies = []

        if not model_config_dict:
            print(f"Warning: 未找到参数 '{parameter}' 对应的模型配置，跳过模型检测。")
        elif not clean_sequence_for_model:
            print(f"Warning: 清洗后无有效数据可供模型预测。")
        else:
            value_sequence = [item['value'] for item in clean_sequence_for_model]
            try:
                numeric_array = np.array(value_sequence, dtype=float)
                clean_value_list = numeric_array.tolist()
                predictions, _ = LSTMAnomalyService.predict_well_from_dict(model_config_dict,
                                                                           generic_seq=clean_value_list)
                for i, pred in enumerate(predictions):
                    if pred == 1:
                        original_point = clean_sequence_for_model[i]
                        model_anomalies.append({
                            'value': original_point['value'],
                            'type': '模型检测异常',
                            'timestamp': original_point.get('date_time_index') or original_point.get('tag_time')
                        })
            except ValueError as e:
                print(f"ERROR: Failed to convert sequence to numeric array before prediction. Error: {e}")
                return jsonify(
                    {'success': False, 'error': f'数据序列中包含无法转换为数字的值，无法进行模型预测。错误: {e}'}), 500

        all_anomalies = pre_checked_anomalies + model_anomalies
        all_anomalies.sort(key=lambda x: x['timestamp'] or '')

        return jsonify({
            'success': True,
            'anomalies': all_anomalies,
            'total_points': len(full_sequence_data)
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500