from app import db
from datetime import datetime
import json

class TrainingHistory(db.Model):
    """模型训练历史记录"""
    __tablename__ = 'training_history'
    
    id = db.Column(db.Integer, primary_key=True)
    model_name = db.Column(db.String(100), nullable=False)
    model_type = db.Column(db.String(50), nullable=False)  # regression/clustering
    algorithm = db.Column(db.String(50), nullable=False)
    data_source_id = db.Column(db.Integer, nullable=False)
    table_name = db.Column(db.String(100), nullable=False)
    feature_columns = db.Column(db.Text, nullable=False)  # JSON存储特征列
    target_column = db.Column(db.String(100))  # 回归模型的目标列
    
    # 训练参数
    parameters = db.Column(db.Text)  # JSON存储模型参数
    training_config = db.Column(db.Text)  # JSON存储训练配置
    
    # 训练结果
    metrics = db.Column(db.Text)  # JSON存储评估指标
    data_info = db.Column(db.Text)  # JSON存储数据信息
    
    # 异常值信息
    outlier_summary = db.Column(db.Text)  # JSON存储异常值汇总
    outlier_details = db.Column(db.Text)  # JSON存储异常值详情
    
    # 可视化数据
    viz_data = db.Column(db.Text)  # JSON存储可视化数据
    
    # 元数据
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.String(50))
    description = db.Column(db.Text)
    
    def set_feature_columns(self, columns):
        """设置特征列"""
        self.feature_columns = json.dumps(columns, ensure_ascii=False)
    
    def get_feature_columns(self):
        """获取特征列"""
        return json.loads(self.feature_columns) if self.feature_columns else []
    
    def set_parameters(self, params):
        """设置模型参数"""
        self.parameters = json.dumps(params, ensure_ascii=False)
    
    def get_parameters(self):
        """获取模型参数"""
        return json.loads(self.parameters) if self.parameters else {}
    
    def set_training_config(self, config):
        """设置训练配置"""
        self.training_config = json.dumps(config, ensure_ascii=False)
    
    def get_training_config(self):
        """获取训练配置"""
        return json.loads(self.training_config) if self.training_config else {}
    
    def set_metrics(self, metrics):
        """设置评估指标"""
        self.metrics = json.dumps(metrics, ensure_ascii=False)
    
    def get_metrics(self):
        """获取评估指标"""
        return json.loads(self.metrics) if self.metrics else {}
    
    def set_data_info(self, info):
        """设置数据信息"""
        self.data_info = json.dumps(info, ensure_ascii=False)
    
    def get_data_info(self):
        """获取数据信息"""
        return json.loads(self.data_info) if self.data_info else {}
    
    def set_outlier_summary(self, summary):
        """设置异常值汇总"""
        self.outlier_summary = json.dumps(summary, ensure_ascii=False)
    
    def get_outlier_summary(self):
        """获取异常值汇总"""
        return json.loads(self.outlier_summary) if self.outlier_summary else {}
    
    def set_outlier_details(self, details):
        """设置异常值详情"""
        self.outlier_details = json.dumps(details, ensure_ascii=False)
    
    def get_outlier_details(self):
        """获取异常值详情"""
        return json.loads(self.outlier_details) if self.outlier_details else []
    
    def set_viz_data(self, data):
        """设置可视化数据"""
        self.viz_data = json.dumps(data, ensure_ascii=False)
    
    def get_viz_data(self):
        """获取可视化数据"""
        return json.loads(self.viz_data) if self.viz_data else {}
    
    def to_dict(self):
        return {
            'id': self.id,
            'model_name': self.model_name,
            'model_type': self.model_type,
            'algorithm': self.algorithm,
            'data_source_id': self.data_source_id,
            'table_name': self.table_name,
            'feature_columns': self.get_feature_columns(),
            'target_column': self.target_column,
            'parameters': self.get_parameters(),
            'training_config': self.get_training_config(),
            'metrics': self.get_metrics(),
            'data_info': self.get_data_info(),
            'outlier_summary': self.get_outlier_summary(),
            'outlier_details': self.get_outlier_details(),
            'viz_data': self.get_viz_data(),
            'created_at': self.created_at.isoformat(),
            'created_by': self.created_by,
            'description': self.description
        }
