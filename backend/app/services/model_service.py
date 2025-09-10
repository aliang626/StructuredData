import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from sklearn.svm import SVR
from sklearn.ensemble import RandomForestRegressor, IsolationForest
from sklearn.cluster import DBSCAN, KMeans
from sklearn.neighbors import LocalOutlierFactor
from sklearn.svm import OneClassSVM
from sklearn.pipeline import Pipeline
import xgboost as xgb
from app.models.model_config import ModelConfig, ModelParameter
from app import db

class ModelService:
    """模型服务类"""
    @staticmethod
    def get_available_models():
        """获取可用模型列表"""
        regression_models = {
            'LinearRegression': {
                'name': '线性回归',
                'description': '基础线性回归模型',
                'parameters': {
                    'fit_intercept': {'type': 'bool', 'default': True, 'description': '是否计算截距'}
                }
            },
            'PolynomialRegression': {
                'name': '多项式回归',
                'description': '多项式特征回归',
                'parameters': {
                    'degree': {'type': 'int', 'default': 2, 'min': 2, 'max': 10, 'description': '多项式次数'},
                    'fit_intercept': {'type': 'bool', 'default': True, 'description': '是否计算截距'}
                }
            },
            'RandomForestRegressor': {
                'name': '随机森林回归',
                'description': '集成学习的回归模型',
                'parameters': {
                    'n_estimators': {'type': 'int', 'default': 100, 'min': 10, 'max': 1000, 'description': '树的数量'},
                    'max_depth': {'type': 'int', 'default': 10, 'min': 1, 'max': 50, 'description': '最大深度'}
                }
            },
            'SVR': {
                'name': '支持向量回归',
                'description': '支持向量机回归',
                'parameters': {
                    'kernel': {'type': 'string', 'default': 'rbf', 'options': ['rbf', 'linear', 'poly'], 'description': '核函数类型'},
                    'C': {'type': 'float', 'default': 1.0, 'min': 0.01, 'max': 100.0, 'description': '惩罚系数'},
                    'epsilon': {'type': 'float', 'default': 0.1, 'min': 0.01, 'max': 1.0, 'description': 'epsilon参数'},
                    'gamma': {'type': 'string', 'default': 'scale', 'options': ['scale', 'auto'], 'description': '核函数系数'}
                }
            },
            'XGBoostRegressor': {
                'name': 'XGBoost回归',
                'description': '基于XGBoost的回归模型',
                'parameters': {
                    'n_estimators': {'type': 'int', 'default': 100, 'min': 10, 'max': 1000, 'description': '树的数量'},
                    'max_depth': {'type': 'int', 'default': 6, 'min': 1, 'max': 20, 'description': '最大深度'},
                    'learning_rate': {'type': 'float', 'default': 0.1, 'min': 0.01, 'max': 1.0, 'description': '学习率'}
                }
            }
        }
        clustering_models = {
            'DBSCAN': {
                'name': 'DBSCAN聚类',
                'description': '基于密度的聚类算法',
                'parameters': {
                    'eps': {'type': 'float', 'default': 0.5, 'min': 0.1, 'max': 10.0, 'description': '邻域半径'},
                    'min_samples': {'type': 'int', 'default': 5, 'min': 1, 'max': 100, 'description': '最小样本数'}
                }
            },
            'LOF': {
                'name': 'LOF聚类',
                'description': '局部离群因子聚类算法',
                'parameters': {
                    'n_neighbors': {'type': 'int', 'default': 20, 'min': 1, 'max': 100, 'description': '邻居数'},
                    'contamination': {'type': 'float', 'default': 0.1, 'min': 0.01, 'max': 0.5, 'description': '异常比例'},
                    'algorithm': {'type': 'string', 'default': 'auto', 'options': ['auto', 'ball_tree', 'kd_tree', 'brute'], 'description': '算法类型'},
                    'leaf_size': {'type': 'int', 'default': 30, 'min': 10, 'max': 100, 'description': '叶子大小'}
                }
            },
            'IsolationForest': {
                'name': '孤立森林',
                'description': '基于树的异常检测聚类',
                'parameters': {
                    'n_estimators': {'type': 'int', 'default': 100, 'min': 10, 'max': 500, 'description': '树的数量'},
                    'contamination': {'type': 'float', 'default': 0.1, 'min': 0.01, 'max': 0.5, 'description': '异常比例'},
                    'max_samples': {'type': 'string', 'default': 'auto', 'description': '最大样本数'},
                    'random_state': {'type': 'int', 'default': 42, 'description': '随机种子'}
                }
            },
            'OneClassSVM': {
                'name': '单类SVM',
                'description': '单类支持向量机异常检测',
                'parameters': {
                    'kernel': {'type': 'string', 'default': 'rbf', 'options': ['rbf', 'linear', 'poly', 'sigmoid'], 'description': '核函数类型'},
                    'nu': {'type': 'float', 'default': 0.1, 'min': 0.01, 'max': 1.0, 'description': '异常比例参数'},
                    'gamma': {'type': 'string', 'default': 'scale', 'options': ['scale', 'auto'], 'description': '核函数系数'},
                    'degree': {'type': 'int', 'default': 3, 'min': 1, 'max': 10, 'description': '多项式核的度数'}
                }
            },
            'KMeans': {
                'name': 'K-means聚类',
                'description': '经典K均值聚类算法',
                'parameters': {
                    'n_clusters': {'type': 'int', 'default': 3, 'min': 2, 'max': 20, 'description': '聚类数量'},
                    'max_iter': {'type': 'int', 'default': 300, 'min': 100, 'max': 1000, 'description': '最大迭代次数'}
                }
            }
        }
        return {
            'regression': regression_models,
            'clustering': clustering_models
        }
    
    @staticmethod
    def create_model_config(name, model_type, model_name, parameters, description=""):
        """创建模型配置"""
        print(f"ModelService.create_model_config 被调用")
        print(f"参数: name={name}, model_type={model_type}, model_name={model_name}")
        print(f"parameters={parameters}, description={description}")
        
        try:
            config = ModelConfig(
                name=name,
                model_type=model_type,
                model_name=model_name,
                description=description
            )
            
            print("创建ModelConfig对象成功，准备添加到数据库...")
            db.session.add(config)
            db.session.flush()  # 获取ID
            print(f"ModelConfig已添加到会话，获得ID: {config.id}")
            
            # 添加参数
            print(f"开始添加 {len(parameters)} 个参数...")
            for param_name, param_value in parameters.items():
                # 根据参数值类型确定正确的参数类型
                param_type = ModelService._determine_param_type(param_value)
                
                param = ModelParameter(
                    config_id=config.id,
                    param_name=param_name,
                    param_value=str(param_value),
                    param_type=param_type
                )
                db.session.add(param)
                print(f"添加参数: {param_name} = {param_value}")
            
            print("提交数据库事务...")
            db.session.commit()
            print("模型配置创建成功！")
            return config
            
        except Exception as e:
            print(f"创建模型配置时发生数据库错误: {str(e)}")
            db.session.rollback()
            raise e
    
    @staticmethod
    def get_model_configs():
        """获取所有模型配置"""
        print("ModelService.get_model_configs 被调用")
        try:
            print("查询数据库中的活跃模型配置...")
            configs = ModelConfig.query.filter_by(is_active=True).all()
            print(f"从数据库查询到 {len(configs)} 个活跃配置")
            
            if configs:
                print("配置详情:")
                for config in configs:
                    print(f"  - ID: {config.id}, 名称: {config.name}, 类型: {config.model_type}")
            else:
                print("数据库中没有找到活跃的模型配置")
                # 检查是否有非活跃的配置
                all_configs = ModelConfig.query.all()
                print(f"数据库中总共有 {len(all_configs)} 个配置（包括非活跃的）")
            
            result = [config.to_dict() for config in configs]
            print(f"转换为字典格式，返回 {len(result)} 个配置")
            return result
            
        except Exception as e:
            print(f"获取模型配置时发生数据库错误: {str(e)}")
            raise e
    
    @staticmethod
    def train_model(config_id, X, y=None):
        """训练模型"""
        config = ModelConfig.query.get(config_id)
        if not config:
            raise ValueError("模型配置不存在")
        
        # 获取参数
        params = {}
        for param in config.parameters:
            value = param.param_value
            if param.param_type == 'int':
                value = int(value)
            elif param.param_type == 'float':
                value = float(value)
            elif param.param_type == 'bool':
                value = value.lower() == 'true'
            params[param.param_name] = value
        
        # 创建模型
        model = ModelService._create_model_instance(config.model_name, params)
        
        # 训练模型
        if config.model_type == 'regression':
            if y is None:
                raise ValueError("回归模型需要目标变量y")
            model.fit(X, y)
        else:  # clustering
            model.fit(X)
        
        return model
    
    @staticmethod
    def _create_model_instance(model_name, params):
        """创建模型实例"""
        if model_name == 'LinearRegression':
            return LinearRegression(**params)
        elif model_name == 'PolynomialRegression':
            # 创建多项式回归管道
            degree = params.pop('degree', 2)
            fit_intercept = params.pop('fit_intercept', True)
            poly_features = PolynomialFeatures(degree=degree, include_bias=fit_intercept)
            linear_reg = LinearRegression(fit_intercept=False)  # 因为PolynomialFeatures已经包含了偏置项
            return Pipeline([
                ('poly', poly_features),
                ('linear', linear_reg)
            ])
        elif model_name == 'RandomForestRegressor':
            return RandomForestRegressor(**params)
        elif model_name == 'SVR':
            # 处理SVR的特殊参数
            if 'gamma' in params and params['gamma'] in ['scale', 'auto']:
                params['gamma'] = params['gamma']
            return SVR(**params)
        elif model_name == 'XGBoostRegressor':
            return xgb.XGBRegressor(**params)
        elif model_name == 'DBSCAN':
            return DBSCAN(**params)
        elif model_name == 'KMeans':
            return KMeans(**params)
        elif model_name == 'LOF':
            # 处理LOF的特殊参数
            if 'algorithm' in params:
                params['algorithm'] = params['algorithm']
            if 'leaf_size' in params:
                params['leaf_size'] = int(params['leaf_size'])
            return LocalOutlierFactor(**params)
        elif model_name == 'IsolationForest':
            # 处理孤立森林的特殊参数
            if 'max_samples' in params and params['max_samples'] == 'auto':
                params['max_samples'] = 'auto'
            if 'random_state' in params:
                params['random_state'] = int(params['random_state'])
            return IsolationForest(**params)
        elif model_name == 'OneClassSVM':
            # 处理单类SVM的特殊参数
            if 'gamma' in params and params['gamma'] in ['scale', 'auto']:
                params['gamma'] = params['gamma']
            if 'degree' in params:
                params['degree'] = int(params['degree'])
            return OneClassSVM(**params)
        else:
            raise ValueError(f"不支持的模型类型: {model_name}")
    
    @staticmethod
    def _determine_param_type(value):
        """根据参数值确定参数类型"""
        if isinstance(value, bool):
            return 'bool'
        elif isinstance(value, int):
            return 'int'
        elif isinstance(value, float):
            return 'float'
        elif isinstance(value, str):
            # 尝试解析字符串类型
            if value.lower() in ['true', 'false']:
                return 'bool'
            try:
                int(value)
                return 'int'
            except ValueError:
                try:
                    float(value)
                    return 'float'
                except ValueError:
                    return 'string'
        else:
            return 'string' 