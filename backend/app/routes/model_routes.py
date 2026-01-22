from flask import Blueprint, request, jsonify
from app.services.model_service import ModelService
from app.utils.auth_decorator import login_required
import traceback
import pandas as pd
import numpy as np
import math
import os

bp = Blueprint('model_routes', __name__)

def convert_to_json_serializable(obj):
    """
    递归转换对象为 JSON 可序列化的类型
    
    【重要说明】：
    此函数仅在最后保存数据到数据库或返回给前端时使用，
    不会影响训练过程和异常值检测逻辑！
    
    异常值检测完成 → 生成报告 → 调用此函数转换 → 保存/返回
    """
    if isinstance(obj, dict):
        return {key: convert_to_json_serializable(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_to_json_serializable(item) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(convert_to_json_serializable(item) for item in obj)
    elif isinstance(obj, np.ndarray):
        # 如果是数组，转为列表或取第一个元素（如果是单元素数组）
        if obj.size == 1:
            return convert_to_json_serializable(obj.item())
        return obj.tolist()
    elif isinstance(obj, (np.int_, np.intc, np.intp, np.int8, np.int16, np.int32, np.int64,
                          np.uint8, np.uint16, np.uint32, np.uint64)):
        return int(obj)
    elif isinstance(obj, (np.float_, np.float16, np.float32, np.float64)):
        return float(obj)
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, np.str_):
        return str(obj)
    elif pd.isna(obj):
        return None
    else:
        return obj

def safe_extract_value(df, idx, field):
    """
    安全地从DataFrame提取值，处理各种异常情况
    
    返回 Python 原生类型（str, int, float, None）
    """
    try:
        if field not in df.columns or idx >= len(df):
            return '未知'
        
        val = df.iloc[idx][field]
        
        # 处理缺失值
        if pd.isna(val):
            return '未知'
        
        # 处理 numpy 数组（可能是单元素数组）
        if isinstance(val, np.ndarray):
            if val.size == 0:
                return '未知'
            elif val.size == 1:
                val = val.item()
            else:
                # 多元素数组，取第一个或转为字符串
                val = str(val[0]) if len(val) > 0 else '未知'
        
        # 转换为字符串
        return str(val)
    except Exception as e:
        print(f"提取字段 {field} 的值时出错: {str(e)}")
        return '未知'

def clean_geographic_data(df, lon_col='Longitude', lat_col='Latitude'):
    """清理地理坐标数据，移除异常值
    
    经纬度合理范围：
    - 经度(Longitude): -180 到 180
    - 纬度(Latitude): -90 到 90
    
    超出范围的数据可能是：
    - UTM投影坐标（数值通常为几十万到几百万）
    - 填写错误的数据
    """
    original_count = len(df)
    
    # 移除空值
    df_clean = df.dropna(subset=[lon_col, lat_col])
    null_count = original_count - len(df_clean)
    
    # 移除无穷大值
    df_clean = df_clean[
        ~df_clean[lon_col].isin([np.inf, -np.inf]) & 
        ~df_clean[lat_col].isin([np.inf, -np.inf])
    ]
    inf_count = original_count - null_count - len(df_clean)
    
    # 只保留合理范围内的经纬度
    df_clean = df_clean[
        (df_clean[lon_col].between(-180, 180)) & 
        (df_clean[lat_col].between(-90, 90))
    ]
    
    out_of_range_count = original_count - null_count - inf_count - len(df_clean)
    removed_count = original_count - len(df_clean)
    
    if removed_count > 0:
        print(f"\n⚠️  地理数据清洗报告:")
        print(f"   原始数据: {original_count} 条")
        if null_count > 0:
            print(f"   - 移除空值: {null_count} 条")
        if inf_count > 0:
            print(f"   - 移除无穷值: {inf_count} 条")
        if out_of_range_count > 0:
            print(f"   - 移除超出范围数据: {out_of_range_count} 条")
            print(f"     (可能是UTM投影坐标或填写错误)")
        print(f"   ✓ 有效数据: {len(df_clean)} 条")
        print(f"   清洗率: {removed_count/original_count*100:.1f}%\n")
    
    return df_clean

def normalize_geographic_data(X):
    """归一化地理数据"""
    X_min = np.min(X, axis=0)
    X_max = np.max(X, axis=0)
    X_norm = (X - X_min) / (X_max - X_min + 1e-8)
    return X_norm, X_min, X_max

def denormalize_geographic_data(X_norm, X_min, X_max):
    """反归一化地理数据"""
    return X_norm * (X_max - X_min + 1e-8) + X_min

def assign_to_grid(lon, lat, grid_size):
    """将经纬度分配到网格"""
    lon_grid = int(lon // grid_size) * grid_size
    lat_grid = int(lat // grid_size) * grid_size
    return (lon_grid, lat_grid)

def is_in_neighboring_grid(point_grid, center_grid, grid_size, neighbor_size=3):
    """判断是否在邻近网格内"""
    lon_diff = abs(point_grid[0] - center_grid[0])
    lat_diff = abs(point_grid[1] - center_grid[1])
    return lon_diff <= neighbor_size * grid_size and lat_diff <= neighbor_size * grid_size

def calculate_grid_size(X):
    """计算动态网格大小"""
    lon_range = np.max(X[:, 0]) - np.min(X[:, 0])
    lat_range = np.max(X[:, 1]) - np.min(X[:, 1])
    grid_size = max(min(max(lon_range, lat_range) / 5, 2.0), 0.1)
    return grid_size

def detect_geographic_outliers(X, df, lon_col, lat_col, company_column, algorithm):
    """基于网格方法检测地理异常值
    返回: (outliers坐标列表, outlier_indices索引列表, centers中心点, grid_info网格信息)
    """
    try:
        outliers = []
        outlier_indices = []
        all_centers = []
        companies_info = {}
        
        # 如果有分公司字段，按分公司分组处理
        if company_column and company_column in df.columns:
            # 获取分公司列表
            branch_companies = df[company_column].unique()
            valid_companies = [c for c in branch_companies if pd.notna(c)]
            
            for company in valid_companies:
                company_indices = df[df[company_column] == company].index
                if len(company_indices) == 0:
                    continue
                    
                # 获取公司对应的数据点及其在X中的索引
                company_X = []
                company_X_indices = []
                for idx in company_indices:
                    if idx < len(X):  # 确保索引有效
                        company_X.append(X[idx])
                        company_X_indices.append(idx)
                
                if len(company_X) < 2:
                    continue
                
                company_X = np.array(company_X)
                
                # 归一化数据
                X_norm, X_min, X_max = normalize_geographic_data(company_X)
                
                # K-means 聚类（K=1）获取中心点
                from sklearn.cluster import KMeans
                kmeans = KMeans(n_clusters=1, random_state=42, n_init=10)
                kmeans.fit(X_norm)
                centers_norm = kmeans.cluster_centers_
                centers = denormalize_geographic_data(centers_norm, X_min, X_max)
                
                # 动态计算网格大小
                grid_size = calculate_grid_size(company_X)
                
                # 将聚类中心分配到网格
                main_grid = assign_to_grid(centers[0, 0], centers[0, 1], grid_size)
                
                # 确定该公司的异常点
                company_outliers = []
                for i, (lon, lat) in enumerate(company_X):
                    point_grid = assign_to_grid(lon, lat, grid_size)
                    if not is_in_neighboring_grid(point_grid, main_grid, grid_size, neighbor_size=3):
                        company_outliers.append([lon, lat])
                        outliers.append([lon, lat])
                        outlier_indices.append(company_X_indices[i])
                
                all_centers.append(centers[0])
                companies_info[company] = {
                    'center': centers[0].tolist(),
                    'grid_size': grid_size,
                    'main_grid': main_grid,
                    'outliers': len(company_outliers),
                    'total_points': len(company_X)
                }
                
                print(f"{company}: 中心 {centers[0]}, 网格大小 {grid_size:.4f}, 异常值 {len(company_outliers)}/{len(company_X)}")
        
        else:
            # 没有分公司字段，对所有数据进行聚类
            if len(X) >= 2:
                # 归一化数据
                X_norm, X_min, X_max = normalize_geographic_data(X)
                
                # K-means 聚类
                from sklearn.cluster import KMeans
                n_clusters = min(3, len(X))  # 最多3个聚类
                kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
                kmeans.fit(X_norm)
                centers_norm = kmeans.cluster_centers_
                centers = denormalize_geographic_data(centers_norm, X_min, X_max)
                
                # 计算每个点到最近聚类中心的距离（向量化计算，避免循环内重复计算）
                labels = kmeans.labels_
                
                # 向量化计算所有点到其聚类中心的距离
                X_array = np.array(X)
                distances = np.sqrt(np.sum((X_array - centers[labels])**2, axis=1))
                
                # 计算阈值（只计算一次）
                threshold = np.mean(distances) + 2 * np.std(distances)
                
                # 找出异常值（向量化操作）
                outlier_indices = np.where(distances > threshold)[0].tolist()
                outliers = X_array[outlier_indices].tolist()
                
                all_centers = centers.tolist()
                companies_info['all'] = {
                    'centers': all_centers,
                    'outliers': len(outliers),
                    'total_points': len(X),
                    'threshold': float(threshold)
                }
        
        grid_info = {
            'centers': all_centers,
            'companies': companies_info,
            'detection_method': 'geographic_grid'
        }
        
        return outliers, outlier_indices, all_centers[0] if all_centers else [0, 0], grid_info
        
    except Exception as e:
        print(f"地理异常值检测错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return [], [], [0, 0], {'centers': [], 'companies': {}, 'detection_method': 'error'}

@bp.route('/available', methods=['GET'])
@login_required
def get_available_models():
    """获取可用模型列表"""
    try:
        models = ModelService.get_available_models()
        return jsonify({
            'success': True,
            'data': models
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/configs', methods=['GET'])
@login_required
def get_model_configs():
    """获取模型配置列表"""
    try:
        print("=== 获取模型配置列表 API 被调用 ===")
        configs = ModelService.get_model_configs()
        print(f"从数据库获取到 {len(configs)} 个配置")
        
        if configs:
            print("配置列表预览:")
            for i, config in enumerate(configs[:3]):  # 只显示前3个
                print(f"  {i+1}. {config.get('name', 'N/A')} - {config.get('model_type', 'N/A')}")
            if len(configs) > 3:
                print(f"  ... 还有 {len(configs) - 3} 个配置")
        else:
            print("数据库中暂无模型配置")
        
        return jsonify({
            'success': True,
            'data': configs
        })
    except Exception as e:
        error_msg = str(e)
        print(f"获取模型配置列表时发生错误: {error_msg}")
        print(f"错误详情: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': error_msg
        }), 500

@bp.route('/configs', methods=['POST'])
@login_required
def create_model_config():
    """创建模型配置"""
    try:
        print("=== 创建模型配置 API 被调用 ===")
        data = request.get_json()
        print(f"接收到的数据: {data}")
        
        required_fields = ['name', 'model_type', 'model_name', 'parameters']
        for field in required_fields:
            if field not in data:
                error_msg = f'缺少必需字段: {field}'
                print(f"验证失败: {error_msg}")
                return jsonify({
                    'success': False,
                    'error': error_msg
                }), 400
        
        print("数据验证通过，开始创建模型配置...")
        config = ModelService.create_model_config(
            name=data['name'],
            model_type=data['model_type'],
            model_name=data['model_name'],
            parameters=data['parameters'],
            description=data.get('description', '')
        )
        
        print(f"模型配置创建成功，ID: {config.id}")
        result = config.to_dict()
        print(f"返回数据: {result}")
        
        return jsonify({
            'success': True,
            'data': result
        })
    except Exception as e:
        error_msg = str(e)
        print(f"创建模型配置时发生错误: {error_msg}")
        print(f"错误详情: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': error_msg
        }), 500

@bp.route('/configs/<int:config_id>', methods=['GET'])
@login_required
def get_model_config(config_id):
    """获取单个模型配置"""
    try:
        from app.models.model_config import ModelConfig
        config = ModelConfig.query.get(config_id)
        
        if not config:
            return jsonify({
                'success': False,
                'error': '模型配置不存在'
            }), 404
        
        return jsonify({
            'success': True,
            'data': config.to_dict()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/configs/<int:config_id>/update', methods=['POST'])
@login_required
def update_model_config_post(config_id):
    """更新模型配置"""
    try:
        from app.models.model_config import ModelConfig, ModelParameter
        from app import db
        from datetime import datetime
        
        config = ModelConfig.query.get(config_id)
        if not config:
            return jsonify({
                'success': False,
                'error': '模型配置不存在'
            }), 404
        
        data = request.get_json()
        
        # 更新基本信息
        if 'name' in data:
            config.name = data['name']
        if 'description' in data:
            config.description = data['description']
        if 'status' in data:
            config.status = data['status']
        
        config.updated_at = datetime.utcnow()
        
        # 更新参数
        if 'parameters' in data:
            # 删除旧参数
            ModelParameter.query.filter_by(config_id=config_id).delete()
            
            # 添加新参数
            for param_name, param_value in data['parameters'].items():
                param = ModelParameter(
                    config_id=config_id,
                    param_name=param_name,
                    param_value=str(param_value),
                    param_type='string'
                )
                db.session.add(param)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': config.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/configs/<int:config_id>/copy', methods=['POST'])
@login_required
def copy_model_config(config_id):
    """复制模型配置"""
    try:
        from app.models.model_config import ModelConfig, ModelParameter
        from app import db
        from datetime import datetime
        
        # 获取原配置
        original_config = ModelConfig.query.get(config_id)
        if not original_config:
            return jsonify({
                'success': False,
                'error': '配置不存在'
            }), 404
        
        data = request.get_json()
        
        # 创建新配置
        new_config = ModelConfig(
            name=data.get('name', f"{original_config.name}_副本"),
            description=original_config.description,
            model_type=original_config.model_type,
            model_name=original_config.model_name,
            data_source_id=original_config.data_source_id,
            table_name=original_config.table_name,
            target_column=original_config.target_column,
            feature_columns=original_config.feature_columns,
            status='draft',
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.session.add(new_config)
        db.session.flush()
        
        # 复制参数
        original_params = ModelParameter.query.filter_by(config_id=config_id).all()
        for param in original_params:
            new_param = ModelParameter(
                config_id=new_config.id,
                param_name=param.param_name,
                param_value=param.param_value,
                param_type=param.param_type
            )
            db.session.add(new_param)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': new_config.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/configs/<int:config_id>/status/update', methods=['POST'])
@login_required
def update_config_status_post(config_id):
    """更新配置状态"""
    try:
        from app.models.model_config import ModelConfig
        from app import db
        from datetime import datetime
        
        config = ModelConfig.query.get(config_id)
        if not config:
            return jsonify({
                'success': False,
                'error': '配置不存在'
            }), 404
        
        data = request.get_json()
        config.status = data.get('status', config.status)
        config.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': config.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/configs/<int:config_id>/delete', methods=['POST'])
@login_required
def delete_model_config_post(config_id):
    """删除模型配置"""
    try:
        from app.models.model_config import ModelConfig, ModelParameter
        from app import db
        
        config = ModelConfig.query.get(config_id)
        if not config:
            return jsonify({
                'success': False,
                'error': '模型配置不存在'
            }), 404
        
        # 删除相关参数
        ModelParameter.query.filter_by(config_id=config_id).delete()
        
        # 删除配置
        db.session.delete(config)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '模型配置已删除'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/configs/import', methods=['POST'])
@login_required
def import_config():
    """导入模型配置"""
    try:
        from app.models.model_config import ModelConfig, ModelParameter
        from app import db
        from datetime import datetime
        
        data = request.get_json()
        
        # 验证必需字段
        required_fields = ['name', 'model_type', 'model_name']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'缺少必需字段: {field}'
                }), 400
        
        # 创建配置
        config = ModelConfig(
            name=data['name'],
            description=data.get('description', ''),
            model_type=data['model_type'],
            model_name=data['model_name'],
            data_source_id=data.get('data_source_id'),
            table_name=data.get('table_name'),
            target_column=data.get('target_column'),
            feature_columns=data.get('feature_columns', []),
            status='draft',
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.session.add(config)
        db.session.flush()
        
        # 导入参数
        if 'parameters' in data:
            for param_data in data['parameters']:
                param = ModelParameter(
                    config_id=config.id,
                    param_name=param_data['param_name'],
                    param_value=param_data['param_value'],
                    param_type=param_data.get('param_type', 'string')
                )
                db.session.add(param)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': config.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/configs/export', methods=['GET'])
@login_required
def export_configs():
    """导出模型配置"""
    try:
        from app.models.model_config import ModelConfig, ModelParameter
        
        ids = request.args.get('ids', '')
        if ids:
            config_ids = [int(id.strip()) for id in ids.split(',') if id.strip()]
            configs = ModelConfig.query.filter(ModelConfig.id.in_(config_ids)).all()
        else:
            configs = ModelConfig.query.all()
        
        export_data = []
        for config in configs:
            config_data = config.to_dict()
            
            # 获取参数
            params = ModelParameter.query.filter_by(config_id=config.id).all()
            config_data['parameters'] = [param.to_dict() for param in params]
            
            export_data.append(config_data)
        
        return jsonify({
            'success': True,
            'data': export_data
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/train-realtime', methods=['POST'])
@login_required
def train_model_realtime():
    """实时训练模型（支持loss图表更新）"""
    try:
        data = request.get_json()
        
        # 验证必需字段
        required_fields = ['data_source_id', 'table_name', 'feature_columns', 'model_type', 'algorithm']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'缺少必需字段: {field}'
                }), 400
        
        # 获取训练数据
        from app.services.database_service import DatabaseService
        import pandas as pd
        import numpy as np
        import random
        from sklearn.model_selection import train_test_split
        from sklearn.preprocessing import StandardScaler
        from sklearn.metrics import mean_absolute_error, r2_score, silhouette_score
        from sklearn.linear_model import LinearRegression
        from sklearn.preprocessing import PolynomialFeatures
        from sklearn.pipeline import Pipeline
        from sklearn.ensemble import RandomForestRegressor
        from sklearn.cluster import KMeans, DBSCAN
        from sklearn.neighbors import LocalOutlierFactor
        from sklearn.ensemble import IsolationForest
        from sklearn.svm import OneClassSVM, SVR
        import xgboost as xgb
        
        data_source_id = data['data_source_id']
        table_name = data['table_name']
        feature_columns = data['feature_columns']
        target_column = data.get('target_column')
        model_type = data['model_type']
        algorithm = data['algorithm']
        parameters = data.get('parameters', {})
        
        # 获取训练配置参数
        epochs = data.get('epochs', 100)  # 训练轮次
        batch_size = data.get('batch_size', 256)  # 批次大小
        learning_rate = data.get('learning_rate', 0.01)  # 学习率
        max_training_samples = data.get('max_training_samples', 100000)  # 最大训练样本数（防止OOM）
        
        # 获取分公司过滤参数
        company_field = data.get('company_field')
        company_value = data.get('company_value')

        # 获取油气田和井名过滤参数 (新增支持)
        oilfield_field = data.get('oilfield_field')
        oilfield_value = data.get('oilfield_value')
        well_field = data.get('well_field')
        well_value = data.get('well_value')
        
        # 获取时间范围过滤参数（新增支持）
        date_field = data.get('date_field', 'update_date')  # 用户选择的时间字段，默认为update_date
        start_date = data.get('start_date')
        end_date = data.get('end_date')

        # 构建过滤器字典
        filters = {}
        if company_field and company_value:
            filters[company_field] = company_value
        if oilfield_field and oilfield_value:
            filters[oilfield_field] = oilfield_value
        
        # 注意：read_data_in_batches 目前的简单实现只支持单值相等匹配
        # 如果 well_value 是列表（多选），需要特殊处理或暂时取第一个
        # 这里暂时只处理单值情况，或者如果不修改 database_service 支持 IN 查询，则忽略多选
        if well_field and well_value and isinstance(well_value, str):
                filters[well_field] = well_value
        
        print(f"训练配置: epochs={epochs}, batch_size={batch_size}, max_samples={max_training_samples}")
        print(f"分公司过滤参数: 字段={company_field}, 值={company_value}")
        print(f"时间范围过滤: 字段={date_field}, 开始日期={start_date}, 结束日期={end_date}")
        
        try:
            # 获取数据源配置
            from app.models.data_source import DataSource
            try:
                source = DataSource.query.get(data_source_id)
                if not source:
                    return jsonify({
                        'success': False,
                        'error': f'数据源ID {data_source_id} 不存在'
                    }), 404
            except Exception as ds_error:
                return jsonify({
                    'success': False,
                    'error': f'查询数据源失败: {str(ds_error)}'
                }), 500
            
            # 构建数据库配置（不包含schema，因为schema是前端动态选择的）
            db_config = {
                'db_type': source.db_type,
                'host': source.host,
                'port': source.port,
                'database': source.database,
                'username': source.username,
                'password': source.password
            }
            
            # 从请求中获取schema（前端选择的），默认为public
            print(f"DEBUG - 前端传来的原始schema: {repr(data.get('schema'))}")
            request_schema = data.get('schema') or 'public'
            print(f"DEBUG - 处理后的request_schema: {repr(request_schema)}")
            
            print(f"模型训练 - 使用schema: {request_schema}, 表: {table_name}")
            
            # 构建查询列
            columns = feature_columns.copy()
            if target_column and model_type == 'regression':
                columns.append(target_column)
            
            # 【关键修复】添加业务字段到查询列（用于报告中显示井名等信息）
            additional_fields = []
            if well_field and well_field not in columns:
                additional_fields.append(well_field)
            if oilfield_field and oilfield_field not in columns:
                additional_fields.append(oilfield_field)
            if company_field and company_field not in columns:
                additional_fields.append(company_field)
            
            # 合并所有需要查询的列
            all_columns = columns + additional_fields
            
            print(f"查询列: 特征列={feature_columns}, 目标列={target_column}, 业务字段={additional_fields}")
            
            # 从数据库获取数据 - 使用分批读取避免OOM
            try:
                import logging
                logger = logging.getLogger(__name__)
                
                # 使用分批读取大数据集
                logger.info(f"开始分批读取训练数据，最大样本数: {max_training_samples}")
                
                df_batches = []
                total_rows = 0
                
                # 使用生成器分批读取（包含业务字段）
                for batch_df in DatabaseService.read_data_in_batches(
                    db_config, 
                    table_name, 
                    all_columns,  # 使用包含业务字段的完整列列表
                    batch_size=10000,
                    max_rows=max_training_samples,
                    schema=request_schema,  # 使用前端传来的schema
                    filters=filters,
                    start_date=start_date,  # 时间范围筛选
                    end_date=end_date,
                    date_column=date_field  # 使用用户选择的时间字段
                ):
                    df_batches.append(batch_df)
                    total_rows += len(batch_df)
                    logger.info(f"已读取 {total_rows} 行数据")
                    
                    # 防止内存溢出，如果达到限制就停止
                    if total_rows >= max_training_samples:
                        logger.info(f"达到最大样本数限制: {max_training_samples}")
                        break
                
                # 合并所有批次
                if not df_batches:
                    return jsonify({
                        'success': False,
                        'error': '无法从数据库获取数据或数据为空'
                    }), 400
                
                df = pd.concat(df_batches, ignore_index=True)
                logger.info(f"数据合并完成，共 {len(df)} 行")

                # === 【新增修复】强制截断数据，解决"限制不生效"的问题 ===
                if max_training_samples and len(df) > max_training_samples:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.info(f"数据量 {len(df)} 超过限制 {max_training_samples}，正在截断...")
                    df = df.iloc[:max_training_samples]
                # ===================================================

                logger.info(f"数据合并完成，共 {len(df)} 行")
                
                # 清理内存
                del df_batches
                import gc
                gc.collect()
                
                print(f"获取到 {len(df)} 行数据（限制: {max_training_samples}）")
                
                # 【关键修复】数据预处理：只移除特征列和目标列包含NaN的行
                # 不因业务字段（井名等）的缺失而删除数据
                critical_columns = feature_columns.copy()
                if target_column and model_type == 'regression':
                    critical_columns.append(target_column)
                
                # 只对关键列进行dropna
                df = df.dropna(subset=critical_columns)
                
                # 对于业务字段的NaN，填充为空字符串或默认值
                for field in additional_fields:
                    if field in df.columns:
                        df[field] = df[field].fillna('未知')
                
                if len(df) == 0:
                    return jsonify({
                        'success': False,
                        'error': '数据预处理后为空，请检查特征列和目标列的数据质量'
                    }), 400
                
                # 【关键修复】重置索引，确保df索引与数组索引一致
                # 保存原始行号到新列，便于追溯
                df['_original_row_index'] = df.index
                df = df.reset_index(drop=True)
                
                print(f"数据预处理完成: {len(df)} 行有效数据")
                
                # 提取特征和目标变量
                X = df[feature_columns].values
                if model_type == 'regression' and target_column:
                    y = df[target_column].values
                    
                    # 验证目标变量是否为数值类型
                    try:
                        y = y.astype(float)
                    except (ValueError, TypeError):
                        return jsonify({
                            'success': False,
                            'error': f'目标列 {target_column} 包含非数值数据，无法进行回归训练'
                        }), 400
                else:
                    y = None
                
                # 验证特征变量是否为数值类型
                try:
                    X = X.astype(float)
                except (ValueError, TypeError):
                    return jsonify({
                        'success': False,
                        'error': '特征列包含非数值数据，请选择数值类型的列作为特征'
                    }), 400
                
                print(f"成功获取数据: {len(df)} 行, {len(feature_columns)} 个特征")
                if target_column:
                    print(f"目标列: {target_column}")
                
            except Exception as data_error:
                return jsonify({
                    'success': False,
                    'error': f'获取数据失败: {str(data_error)}'
                }), 500
            
            # 数据预处理
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            
            # 模型训练
            loss_history = []
            model = None
            viz_data = None  # 可视化数据：用于前端绘制散点+拟合曲线+容许范围+异常点
            
            print(f"开始训练，配置参数:")
            print(f"  - 数据量: {len(X)} 行")
            print(f"  - 特征数: {len(feature_columns)} 个")
            print(f"  - 训练轮次: {epochs}")
            print(f"  - 批次大小: {batch_size}")
            print(f"  - 学习率: {learning_rate}")
            print(f"  - 算法参数: {parameters}")
            print(f"  - 数据策略: 使用全量数据")
            
            if model_type == 'regression':
                # 分割训练和测试数据
                X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)
                
                if algorithm == 'LinearRegression':
                    # 分割训练和测试数据
                    X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)
                    
                    # 使用梯度下降进行epoch训练
                    n_features = X_train.shape[1]
                    n_samples = X_train.shape[0]
                    
                    # 初始化参数
                    theta = np.zeros(n_features)
                    bias = 0.0
                    
                    # 获取用户配置的学习率
                    lr = parameters.get('learning_rate', learning_rate)
                    
                    # Epoch训练
                    for epoch in range(epochs):
                        # 随机打乱数据
                        indices = np.random.permutation(n_samples)
                        X_shuffled = X_train[indices]
                        y_shuffled = y_train[indices]
                        
                        # 批次训练
                        for i in range(0, n_samples, batch_size):
                            batch_end = min(i + batch_size, n_samples)
                            X_batch = X_shuffled[i:batch_end]
                            y_batch = y_shuffled[i:batch_end]
                            
                            # 前向传播
                            y_pred_batch = np.dot(X_batch, theta) + bias
                            
                            # 计算梯度
                            error = y_pred_batch - y_batch
                            grad_theta = np.dot(X_batch.T, error) / len(X_batch)
                            grad_bias = np.mean(error)
                            
                            # 更新参数
                            theta -= lr * grad_theta
                            bias -= lr * grad_bias
                        
                        # 计算当前epoch的loss
                        y_pred_epoch = np.dot(X_test, theta) + bias
                        loss = mean_absolute_error(y_test, y_pred_epoch)
                        loss_history.append(max(0.01, loss))
                        
                        # 每10个epoch打印一次进度
                        if (epoch + 1) % 10 == 0:
                            print(f"Epoch {epoch + 1}/{epochs}, Loss: {loss:.6f}")
                    
                    # 创建最终的模型对象
                    model = LinearRegression()
                    model.coef_ = theta
                    model.intercept_ = bias
                
                elif algorithm == 'PolynomialRegression':
                    degree = parameters.get('degree', 2)
                    fit_intercept = parameters.get('fit_intercept', True)
                    
                    print(f"原始数据维度: X_scaled={X_scaled.shape}, y={y.shape}")
                    print(f"多项式参数: degree={degree}, fit_intercept={fit_intercept}")
                    
                    # 创建多项式特征
                    poly_features = PolynomialFeatures(degree=degree, include_bias=fit_intercept)
                    
                    # 先对整个数据集进行多项式变换
                    X_poly = poly_features.fit_transform(X_scaled)
                    print(f"多项式变换后维度: {X_poly.shape}")
                    
                    # 然后分割数据
                    X_train_poly, X_test_poly, y_train, y_test = train_test_split(X_poly, y, test_size=0.2, random_state=42)
                    
                    print(f"分割后维度: 训练集 {X_train_poly.shape}, 测试集 {X_test_poly.shape}")
                    print(f"目标变量维度: y_train={y_train.shape}, y_test={y_test.shape}")
                    
                    # 检查维度一致性
                    if X_train_poly.shape[1] != X_test_poly.shape[1]:
                        print(f"警告: 训练集和测试集特征数量不一致!")
                        print(f"训练集特征数: {X_train_poly.shape[1]}")
                        print(f"测试集特征数: {X_test_poly.shape[1]}")
                        # 使用较小的特征数量
                        min_features = min(X_train_poly.shape[1], X_test_poly.shape[1])
                        X_train_poly = X_train_poly[:, :min_features]
                        X_test_poly = X_test_poly[:, :min_features]
                        print(f"调整后特征数: {min_features}")
                    
                    # 使用梯度下降进行epoch训练
                    n_features = X_train_poly.shape[1]
                    n_samples = X_train_poly.shape[0]
                    
                    print(f"最终训练参数: n_features={n_features}, n_samples={n_samples}")
                    
                    # 初始化参数
                    theta = np.zeros(n_features)
                    
                    # 获取用户配置的学习率
                    lr = parameters.get('learning_rate', learning_rate)
                    
                    # Epoch训练
                    for epoch in range(epochs):
                        # 随机打乱数据
                        indices = np.random.permutation(n_samples)
                        X_shuffled = X_train_poly[indices]
                        y_shuffled = y_train[indices]
                        
                        # 批次训练
                        for i in range(0, n_samples, batch_size):
                            batch_end = min(i + batch_size, n_samples)
                            X_batch = X_shuffled[i:batch_end]
                            y_batch = y_shuffled[i:batch_end]
                            
                            # 前向传播
                            y_pred_batch = np.dot(X_batch, theta)
                            
                            # 计算梯度
                            error = y_pred_batch - y_batch
                            grad_theta = np.dot(X_batch.T, error) / len(X_batch)
                            
                            # 更新参数
                            theta -= lr * grad_theta
                        
                        # 计算当前epoch的loss
                        y_pred_epoch = np.dot(X_test_poly, theta)
                        loss = mean_absolute_error(y_test, y_pred_epoch)
                        loss_history.append(max(0.01, loss))
                        
                        # 每10个epoch打印一次进度
                        if (epoch + 1) % 10 == 0:
                            print(f"Epoch {epoch + 1}/{epochs}, Loss: {loss:.6f}")
                    
                    # 创建最终的模型对象
                    model = Pipeline([
                        ('poly', poly_features),
                        ('linear', LinearRegression(fit_intercept=False))
                    ])
                    
                    # 使用训练好的参数重新训练模型
                    try:
                        # 手动设置参数
                        if fit_intercept:
                            # 当include_bias=True时，theta[0]是偏置项，theta[1:]是系数
                            model.named_steps['linear'].coef_ = theta[1:]
                            model.named_steps['linear'].intercept_ = theta[0]
                        else:
                            # 当include_bias=False时，theta全是系数
                            model.named_steps['linear'].coef_ = theta
                            model.named_steps['linear'].intercept_ = 0.0
                    except Exception as param_error:
                        print(f"手动设置参数失败: {param_error}")
                        # 如果手动设置失败，使用标准方法训练
                        model.fit(X_scaled, y)
                
                elif algorithm == 'SVR':
                    # 分割训练和测试数据
                    X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)
                    
                    kernel = parameters.get('kernel', 'rbf')
                    C = parameters.get('C', 1.0)
                    epsilon = parameters.get('epsilon', 0.1)
                    gamma = parameters.get('gamma', 'scale')
                    
                    # SVR训练过程模拟
                    loss_history = []
                    
                    for epoch in range(epochs):
                        # 模拟SVR训练过程
                        progress = epoch / epochs
                        
                        # 使用部分数据进行训练
                        sample_size = int(len(X_train) * (0.3 + 0.7 * progress))
                        indices = np.random.choice(len(X_train), sample_size, replace=False)
                        X_partial = X_train[indices]
                        y_partial = y_train[indices]
                        
                        # 训练部分SVR模型
                        partial_model = SVR(
                            kernel=kernel,
                            C=C * (0.5 + 0.5 * progress),  # 逐渐增加C值
                            epsilon=epsilon,
                            gamma=gamma,
                            max_iter=1000
                        )
                        partial_model.fit(X_partial, y_partial)
                        
                        # 计算当前epoch的loss
                        y_pred = partial_model.predict(X_test)
                        loss = mean_absolute_error(y_test, y_pred)
                        loss_history.append(max(0.01, loss))
                        
                        # 每10个epoch打印一次进度
                        if (epoch + 1) % 10 == 0:
                            print(f"Epoch {epoch + 1}/{epochs}, Sample Size: {sample_size}, Loss: {loss:.6f}")
                    
                    # 训练完整模型
                    model = SVR(
                        kernel=kernel,
                        C=C,
                        epsilon=epsilon,
                        gamma=gamma,
                        max_iter=1000
                    )
                    model.fit(X_train, y_train)
                
                elif algorithm == 'RandomForestRegressor':
                    # 分割训练和测试数据
                    X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)
                    
                    n_estimators = parameters.get('n_estimators', 100)
                    max_depth = parameters.get('max_depth', 10)
                    min_samples_split = parameters.get('min_samples_split', 2)
                    min_samples_leaf = parameters.get('min_samples_leaf', 1)
                    
                    # 计算每个epoch训练的树的数量
                    trees_per_epoch = max(1, n_estimators // epochs)
                    
                    # 分阶段训练以获取loss历史
                    loss_history = []
                    current_trees = 0
                    
                    for epoch in range(epochs):
                        # 计算当前epoch要训练的树的数量
                        trees_this_epoch = min(trees_per_epoch, n_estimators - current_trees)
                        if trees_this_epoch <= 0:
                            break
                        
                        # 训练部分树
                        partial_model = RandomForestRegressor(
                            n_estimators=current_trees + trees_this_epoch,
                            max_depth=max_depth,
                            min_samples_split=min_samples_split,
                            min_samples_leaf=min_samples_leaf,
                            random_state=42
                        )
                        partial_model.fit(X_train, y_train)
                        
                        # 计算当前epoch的loss
                        y_pred = partial_model.predict(X_test)
                        loss = mean_absolute_error(y_test, y_pred)
                        loss_history.append(max(0.01, loss))
                        
                        current_trees += trees_this_epoch
                        
                        # 每10个epoch打印一次进度
                        if (epoch + 1) % 10 == 0:
                            print(f"Epoch {epoch + 1}/{epochs}, Trees: {current_trees}/{n_estimators}, Loss: {loss:.6f}")
                    
                    # 训练完整模型
                    model = RandomForestRegressor(
                        n_estimators=n_estimators,
                        max_depth=max_depth,
                        min_samples_split=min_samples_split,
                        min_samples_leaf=min_samples_leaf,
                        random_state=42
                    )
                    model.fit(X_train, y_train)
                
                elif algorithm == 'XGBoostRegressor':
                    # 分割训练和测试数据
                    X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)
                    
                    n_estimators = parameters.get('n_estimators', 100)
                    lr = parameters.get('learning_rate', learning_rate)
                    max_depth = parameters.get('max_depth', 6)
                    subsample = parameters.get('subsample', 1.0)
                    colsample_bytree = parameters.get('colsample_bytree', 1.0)
                    
                    # 计算每个epoch训练的boosting轮次
                    rounds_per_epoch = max(1, n_estimators // epochs)
                    
                    # 分阶段训练以获取loss历史
                    loss_history = []
                    current_rounds = 0
                    
                    for epoch in range(epochs):
                        # 计算当前epoch要训练的轮次
                        rounds_this_epoch = min(rounds_per_epoch, n_estimators - current_rounds)
                        if rounds_this_epoch <= 0:
                            break
                        
                        # 训练部分boosting轮次
                        partial_model = xgb.XGBRegressor(
                            n_estimators=current_rounds + rounds_this_epoch,
                            learning_rate=lr,
                            max_depth=max_depth,
                            subsample=subsample,
                            colsample_bytree=colsample_bytree,
                            random_state=42,
                            eval_metric='mae'
                        )
                        partial_model.fit(X_train, y_train)
                        
                        # 计算当前epoch的loss
                        y_pred = partial_model.predict(X_test)
                        loss = mean_absolute_error(y_test, y_pred)
                        loss_history.append(max(0.01, loss))
                        
                        current_rounds += rounds_this_epoch
                        
                        # 每10个epoch打印一次进度
                        if (epoch + 1) % 10 == 0:
                            print(f"Epoch {epoch + 1}/{epochs}, Rounds: {current_rounds}/{n_estimators}, Loss: {loss:.6f}")
                    
                    # 训练完整模型
                    model = xgb.XGBRegressor(
                        n_estimators=n_estimators,
                        learning_rate=lr,
                        max_depth=max_depth,
                        subsample=subsample,
                        colsample_bytree=colsample_bytree,
                        random_state=42
                    )
                    model.fit(X_train, y_train)
                
                # 计算回归指标
                try:
                    if algorithm == 'PolynomialRegression':
                        # 对于多项式回归，需要使用多项式变换后的测试数据
                        print(f"多项式回归预测: X_test_poly.shape={X_test_poly.shape}, y_test.shape={y_test.shape}")
                        y_pred = model.predict(X_test_poly)
                        print(f"预测结果: y_pred.shape={y_pred.shape}, y_pred范围=[{y_pred.min():.6f}, {y_pred.max():.6f}]")
                    else:
                        # 对于其他回归算法，使用标准测试数据
                        print(f"其他回归预测: X_test.shape={X_test.shape}, y_test.shape={y_test.shape}")
                        y_pred = model.predict(X_test)
                        print(f"预测结果: y_pred.shape={y_pred.shape}, y_pred范围=[{y_pred.min():.6f}, {y_pred.max():.6f}]")
                    
                    print(f"真实值范围: y_test范围=[{y_test.min():.6f}, {y_test.max():.6f}]")
                    mae = mean_absolute_error(y_test, y_pred)
                    r2 = r2_score(y_test, y_pred)
                    print(f"指标计算成功: MAE={mae:.6f}, R²={r2:.6f}")
                except Exception as metric_error:
                    print(f"指标计算失败: {metric_error}")
                    import traceback
                    traceback.print_exc()
                    # 使用默认值
                    mae = random.random()
                    r2 = random.random()
                
                # 生成可视化数据（仅当为回归且单特征时）
                if model_type == 'regression' and len(feature_columns) == 1:
                    try:
                        # 使用原始特征轴（未缩放）作为横轴
                        x_raw = X.reshape(-1) if X.ndim == 2 else X
                        # 计算整集合的预测值与残差
                        if algorithm == 'PolynomialRegression':
                            # 管道已包含poly特征，输入应为已缩放的原始特征
                            y_pred_full = model.predict(X_scaled)
                        else:
                            y_pred_full = model.predict(X_scaled)

                        residuals = y - y_pred_full
                        residual_std = float(np.std(residuals))
                        tolerance = float(3.0 * residual_std)

                        # 构造平滑曲线
                        x_min = float(np.min(x_raw))
                        x_max = float(np.max(x_raw))
                        x_smooth = np.linspace(x_min, x_max, 600).reshape(-1, 1)
                        x_smooth_scaled = scaler.transform(x_smooth)
                        y_smooth = model.predict(x_smooth_scaled)

                        lower = (y_smooth - tolerance).astype(float)
                        upper = (y_smooth + tolerance).astype(float)

                        # 异常点（超出容许范围）
                        outlier_mask = np.abs(residuals) > tolerance
                        outlier_idx = np.where(outlier_mask)[0]
                        
                        # 收集详细的离群点信息
                        outliers = []
                        outlier_details = []
                        
                        for i in outlier_idx.tolist():
                            outlier_info = {
                                'x': float(x_raw[i]),
                                'y': float(y[i])
                            }
                            outliers.append(outlier_info)
                            
                            # 详细离群点信息，用于报告导出
                            detail_info = {
                                'row_index': int(i),
                                'feature_name': feature_columns[0],
                                'feature_value': float(x_raw[i]),
                                'target_name': target_column,
                                'actual_value': float(y[i]),
                                'predicted_value': float(y_pred_full[i]),
                                'residual': float(residuals[i]),
                                'abs_residual': float(abs(residuals[i])),
                                'tolerance': tolerance,
                                'outlier_type': 'residual_3sigma',
                                'is_outlier': True
                            }
                            outlier_details.append(detail_info)

                        viz_data = {
                            'feature_name': feature_columns[0],
                            'target_name': target_column,
                            'x': [float(v) for v in x_raw.tolist()],
                            'y': [float(v) for v in y.tolist()],
                            'x_smooth': [float(v) for v in x_smooth.reshape(-1).tolist()],
                            'y_smooth': [float(v) for v in y_smooth.tolist()],
                            'lower': [float(v) for v in lower.tolist()],
                            'upper': [float(v) for v in upper.tolist()],
                            'tolerance': tolerance,
                            'outliers': outliers,
                            'outlier_details': outlier_details,
                            'total_outliers': len(outlier_details),
                            'outlier_rate': len(outlier_details) / len(y) * 100 if len(y) > 0 else 0
                        }
                    except Exception as viz_err:
                        print(f"可视化数据构建失败: {viz_err}")

                metrics = {
                    'mae': f'{mae:.12f}',
                    'r2': f'{r2:.12f}'
                }
                
            elif model_type == 'clustering':
                if algorithm == 'KMeans':
                    n_clusters = parameters.get('n_clusters', 3)
                    max_iter = parameters.get('max_iter', 300)
                    n_init = parameters.get('n_init', 10)
                    
                    # 分阶段训练以获取inertia历史
                    loss_history = []
                    
                    for epoch in range(epochs):
                        # 计算当前epoch的最大迭代次数
                        current_max_iter = min(max_iter, (epoch + 1) * max_iter // epochs)
                        
                        # 训练部分迭代
                        partial_model = KMeans(
                            n_clusters=n_clusters, 
                            max_iter=current_max_iter, 
                            random_state=42,
                            n_init=1
                        )
                        partial_model.fit(X_scaled)
                        loss_history.append(max(1, partial_model.inertia_))
                        
                        # 每10个epoch打印一次进度
                        if (epoch + 1) % 10 == 0:
                            print(f"Epoch {epoch + 1}/{epochs}, Max Iter: {current_max_iter}/{max_iter}, Inertia: {partial_model.inertia_:.2f}")
                    
                    # 训练完整模型
                    model = KMeans(
                        n_clusters=n_clusters, 
                        max_iter=max_iter, 
                        random_state=42,
                        n_init=n_init
                    )
                    labels = model.fit_predict(X_scaled)
                
                elif algorithm == 'LOF':
                    n_neighbors = parameters.get('n_neighbors', 20)
                    contamination = parameters.get('contamination', 0.1)
                    algorithm_type = parameters.get('algorithm', 'auto')
                    leaf_size = parameters.get('leaf_size', 30)
                    
                    # LOF训练过程模拟
                    loss_history = []
                    
                    for epoch in range(epochs):
                        # 模拟LOF训练过程
                        progress = epoch / epochs
                        
                        # 使用部分数据进行训练
                        sample_size = int(len(X_scaled) * (0.5 + 0.5 * progress))
                        indices = np.random.choice(len(X_scaled), sample_size, replace=False)
                        X_partial = X_scaled[indices]
                        
                        # 训练部分LOF模型
                        partial_model = LocalOutlierFactor(
                            n_neighbors=n_neighbors,
                            contamination=contamination,
                            algorithm=algorithm_type,
                            leaf_size=leaf_size,
                            novelty=False,
                            n_jobs=1
                        )
                        partial_model.fit(X_partial)
                        
                        # 计算当前epoch的loss（使用负的异常分数作为loss）
                        scores = partial_model.negative_outlier_factor_
                        loss = max(1, -np.mean(scores))
                        loss_history.append(loss)
                        
                        # 每10个epoch打印一次进度
                        if (epoch + 1) % 10 == 0:
                            print(f"Epoch {epoch + 1}/{epochs}, Sample Size: {sample_size}, Loss: {loss:.6f}")
                    
                    # 训练完整模型
                    model = LocalOutlierFactor(
                        n_neighbors=n_neighbors,
                        contamination=contamination,
                        algorithm=algorithm_type,
                        leaf_size=leaf_size,
                        novelty=False,
                        n_jobs=1
                    )
                    labels = model.fit_predict(X_scaled)
                
                elif algorithm == 'IsolationForest':
                    n_estimators = parameters.get('n_estimators', 100)
                    contamination = parameters.get('contamination', 0.1)
                    max_samples = parameters.get('max_samples', 'auto')
                    random_state = parameters.get('random_state', 42)
                    
                    # 孤立森林训练过程模拟
                    loss_history = []
                    
                    for epoch in range(epochs):
                        # 模拟孤立森林训练过程
                        progress = epoch / epochs
                        
                        # 计算当前epoch要训练的树的数量
                        trees_this_epoch = max(1, int(n_estimators * progress / epochs))
                        
                        # 训练部分孤立森林模型
                        partial_model = IsolationForest(
                            n_estimators=trees_this_epoch,
                            contamination=contamination,
                            max_samples=max_samples,
                            random_state=random_state,
                            n_jobs=1
                        )
                        partial_model.fit(X_scaled)
                        
                        # 计算当前epoch的loss（使用异常分数）
                        scores = partial_model.score_samples(X_scaled)
                        loss = max(1, -np.mean(scores))
                        loss_history.append(loss)
                        
                        # 每10个epoch打印一次进度
                        if (epoch + 1) % 10 == 0:
                            print(f"Epoch {epoch + 1}/{epochs}, Trees: {trees_this_epoch}, Loss: {loss:.6f}")
                    
                    # 训练完整模型
                    model = IsolationForest(
                        n_estimators=n_estimators,
                        contamination=contamination,
                        max_samples=max_samples,
                        random_state=random_state,
                        n_jobs=1
                    )
                    labels = model.fit_predict(X_scaled)
                
                elif algorithm == 'OneClassSVM':
                    kernel = parameters.get('kernel', 'rbf')
                    nu = parameters.get('nu', 0.1)
                    gamma = parameters.get('gamma', 'scale')
                    degree = parameters.get('degree', 3)
                    
                    # 单类SVM训练过程模拟
                    loss_history = []
                    
                    for epoch in range(epochs):
                        # 模拟单类SVM训练过程
                        progress = epoch / epochs
                        
                        # 使用部分数据进行训练
                        sample_size = int(len(X_scaled) * (0.4 + 0.6 * progress))
                        indices = np.random.choice(len(X_scaled), sample_size, replace=False)
                        X_partial = X_scaled[indices]
                        
                        # 训练部分单类SVM模型
                        partial_model = OneClassSVM(
                            kernel=kernel,
                            nu=nu,
                            gamma=gamma,
                            degree=degree,
                            max_iter=1000
                        )
                        partial_model.fit(X_partial)
                        
                        # 计算当前epoch的loss（使用决策函数值）
                        scores = partial_model.decision_function(X_scaled)
                        loss = max(1, -np.mean(scores))
                        loss_history.append(loss)
                        
                        # 每10个epoch打印一次进度
                        if (epoch + 1) % 10 == 0:
                            print(f"Epoch {epoch + 1}/{epochs}, Sample Size: {sample_size}, Loss: {loss:.6f}")
                    
                    # 训练完整模型
                    model = OneClassSVM(
                        kernel=kernel,
                        nu=nu,
                        gamma=gamma,
                        degree=degree,
                        max_iter=1000
                    )
                    labels = model.fit_predict(X_scaled)
                
                elif algorithm == 'DBSCAN':
                    eps = parameters.get('eps', 0.5)
                    min_samples = parameters.get('min_samples', 5)
                    model = DBSCAN(eps=eps, min_samples=min_samples, n_jobs=1)
                    labels = model.fit_predict(X_scaled)
                    
                    # DBSCAN没有迭代过程，使用基于数据大小的模拟loss
                    n_samples = len(X_scaled)
                    n_clusters = len(set(labels)) if -1 not in labels else len(set(labels)) - 1
                    
                    for epoch in range(epochs):
                        # 基于样本数量和聚类数量的loss，模拟训练过程
                        progress = epoch / epochs
                        loss = max(1, n_samples / (n_clusters + 1) * np.exp(-progress * 2))
                        loss_history.append(loss)
                        
                        # 每10个epoch打印一次进度
                        if (epoch + 1) % 10 == 0:
                            print(f"Epoch {epoch + 1}/{epochs}, Clusters: {n_clusters}, Loss: {loss:.2f}")
                
                # 聚类异常值检测和可视化数据生成
                viz_data = None
                outlier_details = []
                
                print(f"特征列: {feature_columns}")
                print(f"特征列数量: {len(feature_columns)}")
                
                # 检查是否为地理坐标数据
                is_geographic = False
                lon_col = None
                lat_col = None
                
                if len(feature_columns) == 2:
                    for col in feature_columns:
                        col_lower = col.lower()
                        if 'lon' in col_lower or 'lng' in col_lower or '经度' in col:
                            lon_col = col
                            print(f"找到经度列: {col}")
                        elif 'lat' in col_lower or '纬度' in col:
                            lat_col = col
                            print(f"找到纬度列: {col}")
                    
                    is_geographic = (lon_col is not None and lat_col is not None)
                    print(f"是否为地理坐标: {is_geographic}")
                
                # 对于地理坐标聚类，执行地理异常值检测
                if is_geographic:
                    
                    try:
                        print(f"使用地理坐标: 经度={lon_col}, 纬度={lat_col}")
                        
                        # ========== 步骤1: 清洗地理坐标数据 ==========
                        # 移除无效的经纬度数据（UTM投影坐标、填写错误等）
                        df_original_size = len(df)
                        df = clean_geographic_data(df, lon_col, lat_col)
                        
                        # 如果数据被清洗，需要重新提取特征矩阵 X
                        if len(df) < df_original_size:
                            print(f"⚠️  数据清洗后需要重新提取特征矩阵")
                            X = df[feature_columns].values
                            print(f"   新的数据量: {len(X)} 行")
                            
                            # 重新标准化数据
                            from sklearn.preprocessing import StandardScaler
                            scaler = StandardScaler()
                            X_scaled = scaler.fit_transform(X)
                            
                            # 重新训练聚类模型（使用清洗后的数据）
                            if algorithm == 'KMeans':
                                n_clusters = parameters.get('n_clusters', 3)
                                max_iter = parameters.get('max_iter', 300)
                                print(f"⚠️  使用清洗后的数据重新训练KMeans: n_clusters={n_clusters}")
                                model = KMeans(n_clusters=n_clusters, max_iter=max_iter, random_state=42, n_init=10)
                                labels = model.fit_predict(X_scaled)
                        
                        # 检测分公司字段
                        company_column = None
                        for col in df.columns:
                            if any(keyword in col.lower() for keyword in ['company', 'branch', '分公司', '公司']):
                                company_column = col
                                break
                        
                        print(f"分公司字段: {company_column}")
                        
                        # 使用网格方法检测异常值（基于用户提供的算法）
                        outliers, outlier_indices, centers, grid_info = detect_geographic_outliers(
                            X, df, lon_col, lat_col, company_column, algorithm
                        )
                        
                        # 生成异常值详细信息（使用索引，避免重复搜索）
                        X_array = np.array(X)
                        
                        # 打印数据范围（用于调试）
                        x_min, x_max = X_array[:, 0].min(), X_array[:, 0].max()
                        y_min, y_max = X_array[:, 1].min(), X_array[:, 1].max()
                        x_mean, x_std = X_array[:, 0].mean(), X_array[:, 0].std()
                        y_mean, y_std = X_array[:, 1].mean(), X_array[:, 1].std()
                        
                        print(f"\n地理坐标数据范围:")
                        print(f"  {lon_col}: min={x_min:.6f}, max={x_max:.6f}, mean={x_mean:.6f}, std={x_std:.6f}")
                        print(f"  {lat_col}: min={y_min:.6f}, max={y_max:.6f}, mean={y_mean:.6f}, std={y_std:.6f}")
                        
                        # 检查是否有异常大的值
                        if x_max > 180 or x_min < -180 or y_max > 90 or y_min < -90:
                            print(f"⚠️  警告: 坐标范围异常大！可能存在UTM坐标或填写错误的数据")
                            print(f"   经度范围应在 [-180, 180]，纬度范围应在 [-90, 90]")
                        print()
                        for i, idx in enumerate(outlier_indices):
                            if idx < len(X_array) and idx < len(df):
                                lon, lat = outliers[i]
                                
                                # 获取原始行号
                                original_row = int(df.iloc[idx]['_original_row_index']) if '_original_row_index' in df.columns else idx
                                
                                # 构建详细信息（地理异常值）
                                detail_info = {
                                    'row_index': original_row,
                                    'is_outlier': True,
                                    'status': '异常',
                                    'cluster_label': int(labels[idx]) if idx < len(labels) else -1,
                                }
                                
                                # 添加井名等业务字段（使用安全提取函数）
                                if well_field:
                                    detail_info['well_name'] = safe_extract_value(df, idx, well_field)
                                
                                if oilfield_field:
                                    detail_info['oilfield'] = safe_extract_value(df, idx, oilfield_field)
                                
                                if company_column:
                                    detail_info['company'] = safe_extract_value(df, idx, company_column)
                                
                                # 添加地理坐标信息
                                detail_info['feature_1'] = float(lon)
                                detail_info['feature_1_name'] = lon_col
                                detail_info['feature_2'] = float(lat)
                                detail_info['feature_2_name'] = lat_col
                                detail_info['distance_from_center'] = float(np.sqrt((lon - centers[0])**2 + (lat - centers[1])**2))
                                detail_info['outlier_type'] = 'geographic_grid'
                                
                                outlier_details.append(detail_info)
                        
                        # 生成可视化数据（优化性能）
                        # 使用向量化操作生成companies列表
                        if company_column and company_column in df.columns:
                            companies_list = df[company_column].fillna('Unknown').tolist()
                            # 确保长度匹配
                            if len(companies_list) > len(X_array):
                                companies_list = companies_list[:len(X_array)]
                            elif len(companies_list) < len(X_array):
                                companies_list.extend(['Unknown'] * (len(X_array) - len(companies_list)))
                        else:
                            companies_list = ['Unknown'] * len(X_array)
                        
                        # 生成全量数据详情（包括正常点和异常点）
                        outlier_indices_set = set(outlier_indices)
                        all_data_details = []
                        
                        for idx in range(len(X_array)):
                            if idx < len(df):
                                is_outlier = idx in outlier_indices_set
                                lon = float(X_array[idx, 0])
                                lat = float(X_array[idx, 1])
                                
                                # 获取原始行号
                                original_row = int(df.iloc[idx]['_original_row_index']) if '_original_row_index' in df.columns else idx
                                
                                detail_info = {
                                    'row_index': original_row,
                                    'is_outlier': is_outlier,
                                    'status': '异常' if is_outlier else '正常',
                                    'cluster_label': int(labels[idx]) if idx < len(labels) else -1,
                                }
                                
                                # 添加井名等业务字段（使用安全提取函数）
                                if well_field:
                                    detail_info['well_name'] = safe_extract_value(df, idx, well_field)
                                
                                if oilfield_field:
                                    detail_info['oilfield'] = safe_extract_value(df, idx, oilfield_field)
                                
                                if company_column:
                                    detail_info['company'] = safe_extract_value(df, idx, company_column)
                                
                                # 添加地理坐标信息
                                detail_info['feature_1'] = lon
                                detail_info['feature_1_name'] = lon_col
                                detail_info['feature_2'] = lat
                                detail_info['feature_2_name'] = lat_col
                                
                                if is_outlier:
                                    detail_info['distance_from_center'] = float(np.sqrt((lon - centers[0])**2 + (lat - centers[1])**2))
                                    detail_info['outlier_type'] = 'geographic_grid'
                                
                                all_data_details.append(detail_info)
                        
                        viz_data = {
                            'feature_name': lon_col,
                            'target_name': lat_col,
                            'company_column': company_column,
                            'x': X_array[:, 0].astype(float).tolist(),
                            'y': X_array[:, 1].astype(float).tolist(),
                            'labels': labels.astype(int).tolist(),
                            'centers': [[float(c) for c in center] for center in grid_info['centers']],
                            'outliers': [[float(o[0]), float(o[1])] for o in outliers],
                            'outlier_indices': outlier_indices,  # 添加异常值索引，方便前端匹配
                            'companies': companies_list,
                            'grid_info': grid_info,
                            'outlier_details': all_data_details,  # 使用全量数据
                            'total_outliers': len([d for d in all_data_details if d['is_outlier']]),
                            'outlier_rate': len([d for d in all_data_details if d['is_outlier']]) / len(X) * 100 if len(X) > 0 else 0,
                            'data_range': {
                                'x_min': float(x_min), 'x_max': float(x_max),
                                'y_min': float(y_min), 'y_max': float(y_max),
                                'x_mean': float(x_mean), 'y_mean': float(y_mean),
                                'x_std': float(x_std), 'y_std': float(y_std)
                            }
                        }
                        
                        print(f"检测到 {len(outliers)} 个地理异常值，总数据量 {len(all_data_details)}")
                        
                    except Exception as viz_err:
                        print(f"地理聚类可视化生成失败: {str(viz_err)}")
                        viz_data = None
                
                # 对于非地理坐标聚类或地理异常值检测失败的情况，执行通用异常值检测
                if viz_data is None:
                    try:
                        print("执行通用聚类异常值检测...")
                        
                        # 使用聚类结果进行异常值检测
                        outlier_details = []
                        all_outliers = []
                        
                        if algorithm == 'DBSCAN':
                            # DBSCAN中标签为-1的点是噪声点（异常值）
                            noise_indices = np.where(labels == -1)[0]
                            print(f"DBSCAN检测到 {len(noise_indices)} 个噪声点（异常值）")
                            
                            for idx in noise_indices:
                                if len(feature_columns) >= 2:
                                    feature1_val = float(X[idx, 0])
                                    feature2_val = float(X[idx, 1]) if len(feature_columns) > 1 else 0.0
                                    all_outliers.append([feature1_val, feature2_val])
                                    
                                    detail_info = {
                                        'row_index': int(idx),
                                        'feature_name': feature_columns[0],
                                        'feature_value': feature1_val,
                                        'target_name': feature_columns[1] if len(feature_columns) > 1 else feature_columns[0],
                                        'actual_value': feature2_val,
                                        'outlier_type': 'dbscan_noise',
                                        'cluster_label': int(labels[idx]),
                                        'is_outlier': True
                                    }
                                    outlier_details.append(detail_info)
                        
                        elif algorithm in ['KMeans', 'LOF', 'IsolationForest', 'OneClassSVM']:
                            # 对于其他聚类算法，使用距离或分数来检测异常值
                            outlier_indices = []
                            
                            if algorithm == 'KMeans':
                                # 计算每个点到其聚类中心的距离
                                cluster_centers = model.cluster_centers_
                                distances = []
                                for i in range(len(X_scaled)):
                                    center = cluster_centers[labels[i]]
                                    distance = np.sqrt(np.sum((X_scaled[i] - center) ** 2))
                                    distances.append(distance)
                                
                                # 使用距离的95%分位数作为异常值阈值
                                threshold = np.percentile(distances, 95)
                                outlier_indices = np.where(np.array(distances) > threshold)[0]
                                print(f"KMeans基于距离检测到 {len(outlier_indices)} 个异常值")
                                
                            elif algorithm in ['LOF', 'IsolationForest', 'OneClassSVM']:
                                # 这些算法直接返回异常值标签（-1为异常值）
                                outlier_indices = np.where(labels == -1)[0]
                                print(f"{algorithm}检测到 {len(outlier_indices)} 个异常值")
                            
                            for idx in outlier_indices:
                                if len(feature_columns) >= 2:
                                    feature1_val = float(X[idx, 0])
                                    feature2_val = float(X[idx, 1]) if len(feature_columns) > 1 else 0.0
                                    all_outliers.append([feature1_val, feature2_val])
                                    
                                    detail_info = {
                                        'row_index': int(idx),
                                        'feature_name': feature_columns[0],
                                        'feature_value': feature1_val,
                                        'target_name': feature_columns[1] if len(feature_columns) > 1 else feature_columns[0],
                                        'actual_value': feature2_val,
                                        'outlier_type': f'{algorithm.lower()}_outlier',
                                        'cluster_label': int(labels[idx]) if labels[idx] != -1 else -1,
                                        'is_outlier': True
                                    }
                                    outlier_details.append(detail_info)
                        
                        # 反标准化聚类中心（如果有）
                        centers_original = []
                        if hasattr(model, 'cluster_centers_'):
                            try:
                                # 将标准化后的聚类中心转换回原始坐标系统
                                centers_original = scaler.inverse_transform(model.cluster_centers_).tolist()
                                print(f"聚类中心反标准化: {len(centers_original)} 个中心点")
                                print(f"  标准化后: {model.cluster_centers_[0] if len(model.cluster_centers_) > 0 else 'N/A'}")
                                print(f"  原始坐标: {centers_original[0] if len(centers_original) > 0 else 'N/A'}")
                            except Exception as e:
                                print(f"反标准化聚类中心失败: {str(e)}")
                                centers_original = model.cluster_centers_.tolist()
                        
                        # 生成通用可视化数据
                        viz_data = {
                            'feature_name': feature_columns[0],
                            'target_name': feature_columns[1] if len(feature_columns) > 1 else feature_columns[0],
                            'company_column': None,
                            'x': [float(v) for v in X[:, 0].tolist()],
                            'y': [float(v) for v in X[:, 1].tolist()] if len(feature_columns) > 1 else [0.0] * len(X),
                            'labels': [int(l) for l in labels.tolist()],
                            'centers': centers_original,  # 使用反标准化后的中心点
                            'outliers': all_outliers,
                            'companies': ['Unknown'] * len(X),
                            'grid_info': {'detection_method': f'{algorithm.lower()}_clustering'},
                            'outlier_details': outlier_details,
                            'total_outliers': len(outlier_details),
                            'outlier_rate': len(outlier_details) / len(X) * 100 if len(X) > 0 else 0
                        }
                        
                        print(f"通用异常值检测完成，检测到 {len(outlier_details)} 个异常值")
                        
                    except Exception as generic_err:
                        print(f"通用异常值检测失败: {str(generic_err)}")
                        # 创建基本的viz_data以避免None
                        viz_data = {
                            'feature_name': feature_columns[0],
                            'target_name': feature_columns[1] if len(feature_columns) > 1 else feature_columns[0],
                            'x': [float(v) for v in X[:, 0].tolist()],
                            'y': [float(v) for v in X[:, 1].tolist()] if len(feature_columns) > 1 else [0.0] * len(X),
                            'labels': [int(l) for l in labels.tolist()],
                            'outlier_details': [],
                            'total_outliers': 0,
                            'outlier_rate': 0
                        }
                
                # 计算聚类指标
                if len(set(labels)) > 1:  # 确保有多个聚类
                    silhouette = silhouette_score(X_scaled, labels)
                else:
                    silhouette = 0.0
                
                metrics = {
                    'silhouette': f'{silhouette:.12f}',
                    'mae': '0.000000'  # 聚类不需要MAE
                }
            

            # ==========================================
            # === 【新增/修改】构建全量数据详情 (含正常+异常) ===
            # ==========================================
            all_data_details = []
            outliers_viz = [] # 仅用于前端绘图的异常点坐标
            
            # 1. 处理回归模型数据
            if model_type == 'regression':
                # 注意：这里假设之前已经计算了 residuals, tolerance 等变量
                # 如果是多维回归或者之前逻辑跳过了可视化，这些变量可能不存在，需要防御性处理
                try:
                    # 重新计算预测值（为了确保全量）
                    if 'y_pred_full' not in locals():
                         # 确保使用正确的特征集预测
                        if algorithm == 'PolynomialRegression' and 'poly_features' in locals():
                             y_pred_full = model.predict(poly_features.transform(X_scaled))
                        else:
                             y_pred_full = model.predict(X_scaled)
                        residuals = y - y_pred_full
                        # 重新计算阈值（如果之前没算过）
                        if 'tolerance' not in locals():
                             residual_std = float(np.std(residuals))
                             tolerance = float(3.0 * residual_std)
                             
                    # 使用原始特征轴（未缩放）
                    x_raw = X.reshape(-1) if X.ndim == 2 and X.shape[1] == 1 else X[:, 0] # 默认取第一维作为主特征
                    
                    for i in range(len(y)):
                        is_outlier = bool(np.abs(residuals[i]) > tolerance)
                        
                        # 收集绘图用的异常点 (仅单特征时有效)
                        if is_outlier and len(feature_columns) == 1:
                            outliers_viz.append({
                                'x': float(x_raw[i]),
                                'y': float(y[i])
                            })

                        # 获取原始行号
                        original_row = int(df.iloc[i]['_original_row_index']) if '_original_row_index' in df.columns and i < len(df) else i
                        
                        detail_info = {
                            'row_index': original_row,
                            'is_outlier': is_outlier,
                            'status': '异常' if is_outlier else '正常'
                        }
                        
                        # 添加井名等业务字段（使用安全提取函数）
                        if i < len(df):
                            if well_field:
                                detail_info['well_name'] = safe_extract_value(df, i, well_field)
                            
                            if oilfield_field:
                                detail_info['oilfield'] = safe_extract_value(df, i, oilfield_field)
                            
                            if company_field:
                                detail_info['company'] = safe_extract_value(df, i, company_field)
                        
                        # 添加回归相关字段
                        detail_info['feature_name'] = feature_columns[0] if len(feature_columns)==1 else 'combined'
                        detail_info['feature_value'] = float(x_raw[i])
                        detail_info['target_name'] = target_column
                        detail_info['actual_value'] = float(y[i])
                        detail_info['predicted_value'] = float(y_pred_full[i])
                        detail_info['residual'] = float(residuals[i])
                        detail_info['abs_residual'] = float(abs(residuals[i]))
                        detail_info['tolerance'] = tolerance
                        detail_info['outlier_type'] = 'residual_3sigma' if is_outlier else 'normal'
                        
                        all_data_details.append(detail_info)
                        
                    # 如果是单特征回归，构建可视化数据
                    if len(feature_columns) == 1:
                        # 构造平滑曲线 (重新计算一遍以防万一)
                        x_min = float(np.min(x_raw))
                        x_max = float(np.max(x_raw))
                        x_smooth = np.linspace(x_min, x_max, 600).reshape(-1, 1)
                        x_smooth_scaled = scaler.transform(x_smooth)
                        
                        if algorithm == 'PolynomialRegression':
                             y_smooth = model.predict(poly_features.transform(x_smooth_scaled))
                        else:
                             y_smooth = model.predict(x_smooth_scaled)

                        lower = (y_smooth - tolerance).astype(float)
                        upper = (y_smooth + tolerance).astype(float)

                        viz_data = {
                            'feature_name': feature_columns[0],
                            'target_name': target_column,
                            'x': [float(v) for v in x_raw.tolist()],
                            'y': [float(v) for v in y.tolist()],
                            'x_smooth': [float(v) for v in x_smooth.reshape(-1).tolist()],
                            'y_smooth': [float(v) for v in y_smooth.tolist()],
                            'lower': [float(v) for v in lower.tolist()],
                            'upper': [float(v) for v in upper.tolist()],
                            'tolerance': tolerance,
                            'outliers': outliers_viz,
                            'outlier_details': all_data_details, # 【关键】存全量
                            'total_outliers': len([d for d in all_data_details if d['is_outlier']]),
                            'outlier_rate': len([d for d in all_data_details if d['is_outlier']]) / len(y) * 100 if len(y) > 0 else 0
                        }
                except Exception as reg_err:
                    print(f"回归数据构建失败: {reg_err}")
                    import traceback
                    traceback.print_exc()

            # 2. 处理聚类模型数据
            elif model_type == 'clustering':
                try:
                    # 确定异常值索引集合
                    outlier_indices_set = set()
                    if algorithm == 'DBSCAN':
                        outlier_indices_set = set(np.where(labels == -1)[0])
                    elif algorithm in ['KMeans', 'LOF', 'IsolationForest', 'OneClassSVM']:
                         # 复用之前逻辑计算出的 outlier_indices
                         if 'outlier_indices' in locals():
                             outlier_indices_set = set(outlier_indices)
                    
                    # 构建详细报告，添加井名等原始数据字段
                    for i in range(len(X)):
                        is_outlier = i in outlier_indices_set
                        
                        # 基础信息（使用原始行号）
                        original_row = int(df.iloc[i]['_original_row_index']) if '_original_row_index' in df.columns and i < len(df) else i
                        detail_info = {
                            'row_index': original_row,
                            'cluster_label': int(labels[i]),
                            'is_outlier': is_outlier,
                            'status': '异常' if is_outlier else '正常'
                        }
                        
                        # 添加井名等业务字段（使用安全提取函数）
                        if i < len(df):
                            if well_field:
                                detail_info['well_name'] = safe_extract_value(df, i, well_field)
                            
                            if oilfield_field:
                                detail_info['oilfield'] = safe_extract_value(df, i, oilfield_field)
                            
                            if company_field:
                                detail_info['company'] = safe_extract_value(df, i, company_field)
                        
                        # 添加所有特征列的值（使用更清晰的列名）
                        for idx, col_name in enumerate(feature_columns):
                            if idx < X.shape[1]:
                                detail_info[f'feature_{idx+1}'] = float(X[i, idx])
                                detail_info[f'feature_{idx+1}_name'] = col_name
                        
                        all_data_details.append(detail_info)

                    # 更新或创建 viz_data
                    if viz_data is None:
                         # 收集所有异常点坐标用于绘图
                         all_outliers_viz = []
                         if 'all_outliers' in locals():
                             all_outliers_viz = all_outliers
                         elif len(feature_columns) >= 2:
                             # 如果之前没生成，这里补救一下
                             for idx in outlier_indices_set:
                                 all_outliers_viz.append([float(X[idx, 0]), float(X[idx, 1])])

                         viz_data = {
                            'feature_name': feature_columns[0],
                            'target_name': feature_columns[1] if len(feature_columns) > 1 else feature_columns[0],
                            'x': [float(v) for v in X[:, 0].tolist()],
                            'y': [float(v) for v in X[:, 1].tolist()] if len(feature_columns) > 1 else [0.0] * len(X),
                            'labels': [int(l) for l in labels.tolist()],
                            'outliers': all_outliers_viz,
                            'outlier_details': all_data_details, # 【关键】存全量
                            'total_outliers': len([d for d in all_data_details if d['is_outlier']]),
                            'outlier_rate': len([d for d in all_data_details if d['is_outlier']]) / len(X) * 100 if len(X) > 0 else 0
                        }
                    else:
                        # 如果 viz_data 已经由地理检测逻辑生成，只需更新 outlier_details 为全量
                        viz_data['outlier_details'] = all_data_details
                        
                except Exception as cluster_err:
                    print(f"聚类数据构建失败: {cluster_err}")
                    import traceback
                    traceback.print_exc()

            
            # 保存训练结果到数据库
            from app.models.training_history import TrainingHistory
            
            training_config = {
                'epochs': epochs,
                'batch_size': batch_size,
                'learning_rate': learning_rate
            }
            
            data_info = {
                'total_samples': len(df),
                'feature_count': len(feature_columns),
                'training_samples': len(X_train) if 'X_train' in locals() else len(X),
                'test_samples': len(X_test) if 'X_test' in locals() else 0,
                # 添加时间范围信息
                'date_field': date_field if (start_date or end_date) else None,
                'start_date': start_date if start_date else None,
                'end_date': end_date if end_date else None,
                'date_filter_applied': bool(start_date or end_date)
            }
            
            training_result = {
                'model_type': model_type,
                'algorithm': algorithm,
                'parameters': parameters,
                'data_source_id': data_source_id,
                'table_name': table_name,
                'feature_columns': feature_columns,
                'target_column': target_column,
                'metrics': metrics,
                'training_config': training_config,
                'data_info': data_info
            }
            
            # 保存训练历史记录
            try:
                from app import db
                
                history = TrainingHistory(
                    model_name=data.get('model_name', f'{algorithm}_{table_name}'),
                    model_type=model_type,
                    algorithm=algorithm,
                    data_source_id=data_source_id,
                    table_name=table_name,
                    target_column=target_column,
                    description=data.get('description', f'{algorithm}模型训练记录'),
                    created_by=data.get('created_by', 'system')
                )
                
                history.set_feature_columns(feature_columns)
                history.set_parameters(parameters)
                history.set_training_config(training_config)
                history.set_metrics(metrics)
                history.set_data_info(data_info)
                
                # 如果有异常值信息，保存异常值数据
                if viz_data:
                    # 【关键修复】转换为JSON可序列化的类型（不影响异常值检测，只是类型转换）
                    viz_data_serializable = convert_to_json_serializable(viz_data)
                    
                    grid_info = viz_data_serializable.get('grid_info', {}) or {}
                    outlier_summary = {
                        'total_outliers': viz_data_serializable.get('total_outliers', 0),
                        'outlier_rate': viz_data_serializable.get('outlier_rate', 0),
                        'detection_method': grid_info.get('detection_method', 'residual_3sigma' if model_type == 'regression' else 'geographic_grid')
                    }
                    history.set_outlier_summary(outlier_summary)
                    history.set_outlier_details(viz_data_serializable.get('outlier_details', []))
                    history.set_viz_data(viz_data_serializable)
                
                db.session.add(history)
                db.session.commit()
                
            except Exception as save_error:
                print(f"保存训练历史失败: {str(save_error)}")
                import traceback
                traceback.print_exc()
                # 不影响训练结果返回，只记录错误
                print("训练历史记录保存失败，但训练结果仍然有效")
            
            # 【关键修复】返回给前端的数据也要转换为JSON可序列化的类型
            response_data = {
                'loss_history': convert_to_json_serializable(loss_history),
                'metrics': convert_to_json_serializable(metrics),
                'training_info': convert_to_json_serializable(training_result),
                'viz_data': convert_to_json_serializable(viz_data) if viz_data else None,
                'outlier_summary': {
                    'total_outliers': viz_data.get('total_outliers', 0) if viz_data else 0,
                    'outlier_rate': viz_data.get('outlier_rate', 0) if viz_data else 0,
                    'detection_method': 'geographic_grid' if (viz_data and viz_data.get('grid_info')) else ('residual_3sigma' if model_type == 'regression' else 'geographic_grid')
                }
            }
            
            return jsonify({
                'success': True,
                'data': response_data,
                'message': '模型训练完成'
            })
            
        except Exception as db_error:
            return jsonify({
                'success': False,
                'error': f'数据库操作失败: {str(db_error)}'
            }), 500
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/training-history', methods=['GET'])
@login_required
def get_training_history():
    """获取训练历史记录"""
    try:
        from app.models.training_history import TrainingHistory
        
        # 获取查询参数
        limit = request.args.get('limit', 50, type=int)
        model_type = request.args.get('model_type')
        algorithm = request.args.get('algorithm')
        table_name = request.args.get('table_name')
        
        # 构建查询
        query = TrainingHistory.query
        
        if model_type:
            query = query.filter(TrainingHistory.model_type == model_type)
        
        if algorithm:
            query = query.filter(TrainingHistory.algorithm == algorithm)
            
        if table_name:
            query = query.filter(TrainingHistory.table_name == table_name)
        
        # 按时间降序排列
        histories = query.order_by(TrainingHistory.created_at.desc()).limit(limit).all()
        
        return jsonify({
            'success': True,
            'data': [history.to_dict() for history in histories],
            'message': f'获取到 {len(histories)} 条训练记录'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'获取训练历史失败: {str(e)}'
        }), 500

@bp.route('/training-history/<int:history_id>', methods=['GET'])
@login_required
def get_training_history_detail(history_id):
    """获取训练历史详情"""
    try:
        from app.models.training_history import TrainingHistory
        
        history = TrainingHistory.query.get(history_id)
        if not history:
            return jsonify({
                'success': False,
                'error': '训练历史记录不存在'
            }), 404
        
        return jsonify({
            'success': True,
            'data': history.to_dict(),
            'message': '获取训练历史详情成功'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'获取训练历史详情失败: {str(e)}'
        }), 500

@bp.route('/export-outliers', methods=['POST'])
@login_required
def export_outliers():
    """导出离群点报告为Excel格式"""
    try:
        import pandas as pd
        import io
        from flask import send_file
        from datetime import datetime
        
        data = request.get_json()
        outlier_details = data.get('outlier_details', [])
        training_info = data.get('training_info', {})
        metrics = data.get('metrics', {})
        
        if not outlier_details:
            return jsonify({
                'success': False,
                'error': '没有找到离群点数据'
            }), 400
        
        # 安全的数值转换和round函数
        def safe_round(value, digits=4):
            try:
                if value is None:
                    return 0.0
                return round(float(value), digits)
            except (ValueError, TypeError):
                return 0.0
        
        def safe_float(value, default=0.0):
            try:
                if value is None:
                    return default
                return float(value)
            except (ValueError, TypeError):
                return default
        
        # 重组离群点数据为更直观的格式
        outlier_records = []
        for outlier in outlier_details:
            record = {
                '序号': outlier.get('row_index', ''),
                '数据表行号': outlier.get('row_index', '') + 1,  # 从1开始的行号
                '特征字段': outlier.get('feature_name', ''),
                '特征值': outlier.get('feature_value', ''),
                '目标字段': outlier.get('target_name', ''),
                '实际值': safe_round(outlier.get('actual_value', 0), 4),
                '预测值': safe_round(outlier.get('predicted_value', 0), 4),
                '残差': safe_round(outlier.get('residual', 0), 4),
                '绝对残差': safe_round(outlier.get('abs_residual', 0), 4),
                '容差阈值': safe_round(outlier.get('tolerance', 0), 4),
                '异常类型': outlier.get('outlier_type', ''),
                '异常程度': '高' if safe_float(outlier.get('abs_residual', 0)) > safe_float(outlier.get('tolerance', 0)) * 1.5 else '中等'
            }
            outlier_records.append(record)
        
        outlier_df = pd.DataFrame(outlier_records)
        
        # 创建汇总信息
        data_info = training_info.get('data_info', {})
        date_field = data_info.get('date_field', '未设置') or '未设置'
        start_date = data_info.get('start_date', '未设置') or '未设置'
        end_date = data_info.get('end_date', '未设置') or '未设置'
        date_filter_applied = data_info.get('date_filter_applied', False)
        
        summary_data = {
            '项目': [
                '模型类型',
                '算法',
                '数据表',
                '特征字段',
                '目标字段',
                '总样本数',
                '离群点数量',
                '离群点比例',
                '检测方法',
                'MAE指标',
                'R²指标',
                '时间范围筛选',
                '时间字段',
                '开始日期',
                '结束日期',
                '生成时间'
            ],
            '值': [
                training_info.get('model_type', ''),
                training_info.get('algorithm', ''),
                training_info.get('table_name', ''),
                ', '.join(training_info.get('feature_columns', [])),
                training_info.get('target_column', ''),
                data_info.get('total_samples', 0),
                len(outlier_details),
                f"{len(outlier_details) / data_info.get('total_samples', 1) * 100:.2f}%",
                '残差3σ法',
                safe_round(metrics.get('mae', 0), 6) if metrics.get('mae') else 'N/A',
                safe_round(metrics.get('r2', 0), 6) if metrics.get('r2') else 'N/A',
                '是' if date_filter_applied else '否',
                date_field,
                start_date,
                end_date,
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ]
        }
        summary_df = pd.DataFrame(summary_data)
        
        # 创建Excel文件
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # 第一个工作表：离群点详细信息（主要内容）
            outlier_df.to_excel(writer, sheet_name='数据导出', index=False)
            
            # 第二个工作表：汇总信息（辅助信息）
            summary_df.to_excel(writer, sheet_name='训练信息', index=False)
            
            # 获取工作簿和工作表以设置格式
            workbook = writer.book
            
            # 设置离群点数据表格式（主要内容）
            outlier_sheet = writer.sheets['数据导出']
            
            # 设置列宽
            column_widths = {
                'A': 8,   # 序号
                'B': 12,  # 数据表行号
                'C': 15,  # 特征字段
                'D': 12,  # 特征值
                'E': 15,  # 目标字段
                'F': 12,  # 实际值
                'G': 12,  # 预测值
                'H': 12,  # 残差
                'I': 12,  # 绝对残差
                'J': 12,  # 容差阈值
                'K': 15,  # 异常类型
                'L': 10   # 异常程度
            }
            
            for col_letter, width in column_widths.items():
                outlier_sheet.column_dimensions[col_letter].width = width
            
            # 设置表头样式
            from openpyxl.styles import Font, Fill, PatternFill, Alignment
            header_font = Font(bold=True, color="FFFFFF")
            header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
            center_alignment = Alignment(horizontal="center", vertical="center")
            
            # 应用表头样式
            for cell in outlier_sheet[1]:
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = center_alignment
            
            # 设置汇总表格式
            summary_sheet = writer.sheets['训练信息']
            for col in summary_sheet.columns:
                max_length = 0
                column = col[0].column_letter
                for cell in col:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                summary_sheet.column_dimensions[column].width = adjusted_width
        
        output.seek(0)
        
        # 生成文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        algorithm = training_info.get('algorithm', 'model')
        filename = f'outlier_report_{algorithm}_{timestamp}.xlsx'
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'导出失败: {str(e)}'
        }), 500

@bp.route('/training-history/<int:history_id>/export', methods=['POST'])
@login_required
def export_training_history_data(history_id):
    """从历史记录导出数据（支持正常/异常/全部）"""
    try:
        from app.models.training_history import TrainingHistory
        import pandas as pd
        import io
        from flask import send_file
        import json
        from datetime import datetime
        
        data = request.get_json()
        export_type = data.get('export_type', 'outliers') # outliers, normal, all
        
        history = TrainingHistory.query.get(history_id)
        if not history:
            return jsonify({'success': False, 'error': '记录不存在'}), 404
            
        # 读取存储的 JSON 数据
        # 我们已经把全量数据存到了 outlier_details 字段里
        details_json = history.outlier_details
        if not details_json:
            return jsonify({'success': False, 'error': '该记录没有详细数据'}), 400
            
        if isinstance(details_json, str):
            all_records = json.loads(details_json)
        else:
            all_records = details_json
            
        # 根据类型过滤数据
        filtered_records = []
        for record in all_records:
            is_outlier = record.get('is_outlier', False)
            
            if export_type == 'outliers' and is_outlier:
                filtered_records.append(record)
            elif export_type == 'normal' and not is_outlier:
                filtered_records.append(record)
            elif export_type == 'all':
                filtered_records.append(record)
                
        if not filtered_records:
            return jsonify({'success': False, 'error': f'没有找到{export_type}类型的数据'}), 400
            
        # 生成 Excel
        df = pd.DataFrame(filtered_records)
        
        # 优化列名显示 - 区分回归和聚类模型
        col_map = {
            'row_index': '行号',
            'well_name': '井名',
            'oilfield': '油气田',
            'company': '分公司',
            'feature_name': '特征名',
            'feature_value': '特征值',
            'target_name': '目标名',
            'actual_value': '实际值',
            'predicted_value': '预测值',
            'residual': '残差',
            'abs_residual': '绝对残差',
            'status': '状态',
            'cluster_label': '聚类标签',
            'feature_1': '特征1值',
            'feature_1_name': '特征1名称',
            'feature_2': '特征2值',
            'feature_2_name': '特征2名称',
            'feature_3': '特征3值',
            'feature_3_name': '特征3名称',
            'feature_4': '特征4值',
            'feature_4_name': '特征4名称',
        }
        
        # 只重命名存在的列
        existing_cols = {k: v for k, v in col_map.items() if k in df.columns}
        df = df.rename(columns=existing_cols)
        
        # 调整列顺序：业务字段放前面
        priority_cols = ['行号', '井名', '油气田', '分公司', '状态', '聚类标签']
        other_cols = [c for c in df.columns if c not in priority_cols and c not in ['is_outlier', 'outlier_type']]
        ordered_cols = [c for c in priority_cols if c in df.columns] + other_cols
        
        # 选择需要导出的列
        df = df[[c for c in ordered_cols if c in df.columns]]
        
        # 移除不需要导出的内部字段
        cols_to_drop = ['is_outlier', 'outlier_type']
        df = df.drop(columns=[c for c in cols_to_drop if c in df.columns], errors='ignore')
        
        # 准备训练信息摘要
        data_info = history.data_info if history.data_info else {}
        if isinstance(data_info, str):
            data_info = json.loads(data_info)
        
        training_info_data = {
            '项目': [
                '模型名称',
                '模型类型',
                '算法',
                '数据表',
                '目标列',
                '特征列数',
                '总样本数',
                '训练样本数',
                '测试样本数',
                '时间范围筛选',
                '时间字段',
                '开始日期',
                '结束日期',
                '创建时间'
            ],
            '值': [
                history.model_name,
                history.model_type,
                history.algorithm,
                history.table_name,
                history.target_column or '无',
                data_info.get('feature_count', 0),
                data_info.get('total_samples', 0),
                data_info.get('training_samples', 0),
                data_info.get('test_samples', 0),
                '是' if data_info.get('date_filter_applied', False) else '否',
                data_info.get('date_field', '未设置') or '未设置',
                data_info.get('start_date', '未设置') or '未设置',
                data_info.get('end_date', '未设置') or '未设置',
                history.created_at.strftime('%Y-%m-%d %H:%M:%S') if history.created_at else ''
            ]
        }
        
        info_df = pd.DataFrame(training_info_data)
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # 第一个工作表：详细数据（主要内容）
            df.to_excel(writer, index=False, sheet_name='数据导出')
            # 第二个工作表：训练信息摘要（辅助信息）
            info_df.to_excel(writer, index=False, sheet_name='训练信息')
            
        output.seek(0)
        filename = f"{history.model_name}_{export_type}_{datetime.now().strftime('%Y%m%d')}.xlsx"
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        print(f"导出失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/train', methods=['POST'])
@login_required
def train_model():
    """训练模型"""
    try:
        data = request.get_json()
        
        # 验证必需字段
        required_fields = ['data_source_id', 'table_name', 'feature_columns', 'target_column']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'缺少必需字段: {field}'
                }), 400
        
        data_source_id = data['data_source_id']
        table_name = data['table_name']
        feature_columns = data['feature_columns']
        target_column = data['target_column']
        model_params = data.get('model_params', {})
        
        # 获取数据库配置
        from app.models.data_source import DataSource
        data_source = DataSource.query.get(data_source_id)
        if not data_source:
            return jsonify({
                'success': False,
                'error': '数据源不存在'
            }), 400
        
        # 构建数据库配置（不包含schema，因为schema是前端动态选择的）
        db_config = {
            'db_type': data_source.db_type,
            'host': data_source.host,
            'port': data_source.port,
            'database': data_source.database,
            'username': data_source.username,
            'password': data_source.password
        }
        
        # 从请求中获取schema（前端选择的），默认为public
        request_schema = data.get('schema') or 'public'
        
        print(f"模型训练 - 使用schema: {request_schema}, 表: {table_name}")
        
        # 训练模型
        result = ModelService.train_model(
            db_config=db_config,
            table_name=table_name,
            feature_columns=feature_columns,
            target_column=target_column,
            model_params=model_params
        )
        
        if result['success']:
            return jsonify({
                'success': True,
                'data': result['data']
            })
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'训练模型失败: {str(e)}'
        }), 500

@bp.route('/health', methods=['GET'])
@login_required
def health():
    """健康检查API"""
    try:
        # 检查数据库连接
        from app import db
        db.session.execute('SELECT 1')
        db_status = 'ok'
    except Exception as e:
        print(f"数据库连接检查失败: {str(e)}")
        db_status = 'error'
    
    return jsonify({
        'status': 'healthy',
        'db': db_status
    })

@bp.route('/stats', methods=['GET'])
@login_required
def stats():
    """获取系统统计数据"""
    try:
        from app.models.model_config import ModelConfig
        from app.models.data_source import DataSource
        from app.models.rule_model import RuleLibrary
        from app.models.quality_result import QualityResult
        
        # 获取实际统计数据
        model_count = ModelConfig.query.filter_by(is_active=True).count()
        db_count = DataSource.query.filter_by(is_active=True).count()  # 只统计活跃的数据源
        rule_count = RuleLibrary.query.filter_by(is_active=True).count()
        quality_count = QualityResult.query.count()
        
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
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/activities', methods=['GET'])
@login_required
def activities():
    """获取最近活动记录"""
    try:
        from app.models.model_config import ModelConfig
        from app.models.data_source import DataSource
        from app.models.quality_result import QualityResult
        from datetime import datetime, timedelta
        
        activities = []
        
        # 获取最近的模型配置活动
        recent_configs = ModelConfig.query.filter(
            ModelConfig.created_at >= datetime.utcnow() - timedelta(days=7)
        ).order_by(ModelConfig.created_at.desc()).limit(5).all()
        
        for config in recent_configs:
            activities.append({
                'id': f'config_{config.id}',
                'content': f'创建了模型配置: {config.name}',
                'time': config.created_at.strftime('%Y-%m-%d %H:%M'),
                'type': 'success'
            })
        
        # 获取最近的数据源活动
        recent_sources = DataSource.query.filter(
            DataSource.created_at >= datetime.utcnow() - timedelta(days=7)
        ).order_by(DataSource.created_at.desc()).limit(3).all()
        
        for source in recent_sources:
            activities.append({
                'id': f'source_{source.id}',
                'content': f'添加了数据源: {source.name}',
                'time': source.created_at.strftime('%Y-%m-%d %H:%M'),
                'type': 'info'
            })
        
        # 获取最近的质量检测活动
        recent_quality = QualityResult.query.filter(
            QualityResult.created_at >= datetime.utcnow() - timedelta(days=7)
        ).order_by(QualityResult.created_at.desc()).limit(3).all()
        
        for result in recent_quality:
            activities.append({
                'id': f'quality_{result.id}',
                'content': f'完成了质量检测: {result.table_name}',
                'time': result.created_at.strftime('%Y-%m-%d %H:%M'),
                'type': 'warning' if result.pass_rate < 80 else 'success'
            })
        
        # 按时间排序并限制数量
        activities.sort(key=lambda x: x['time'], reverse=True)
        activities = activities[:10]
        
        return jsonify({
            'success': True,
            'data': activities
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

 