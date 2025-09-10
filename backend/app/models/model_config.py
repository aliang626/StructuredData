from app import db
from datetime import datetime
import json

class ModelConfig(db.Model):
    """模型配置模型"""
    __tablename__ = 'model_configs'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    model_type = db.Column(db.String(50), nullable=False)  # regression/clustering
    model_name = db.Column(db.String(50), nullable=False)  # LinearRegression/SVR/RandomForest等
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)  # 启用/禁用状态
    status = db.Column(db.String(20), default='draft')  # 工作流状态：draft, active, training, deployed, archived
    
    # 关联参数
    parameters = db.relationship('ModelParameter', backref='config', lazy='dynamic', cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'model_type': self.model_type,
            'model_name': self.model_name,
            'description': self.description,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'is_active': self.is_active,
            'status': self.status,
            'parameters': [param.to_dict() for param in self.parameters]
        }

class ModelParameter(db.Model):
    """模型参数模型"""
    __tablename__ = 'model_parameters'
    
    id = db.Column(db.Integer, primary_key=True)
    config_id = db.Column(db.Integer, db.ForeignKey('model_configs.id'), nullable=False)
    param_name = db.Column(db.String(50), nullable=False)
    param_value = db.Column(db.String(200))
    param_type = db.Column(db.String(20), nullable=False)  # int/float/string/bool
    description = db.Column(db.Text)
    min_value = db.Column(db.Float)
    max_value = db.Column(db.Float)
    default_value = db.Column(db.String(200))
    
    def to_dict(self):
        return {
            'id': self.id,
            'config_id': self.config_id,
            'param_name': self.param_name,
            'param_value': self.param_value,
            'param_type': self.param_type,
            'description': self.description,
            'min_value': self.min_value,
            'max_value': self.max_value,
            'default_value': self.default_value
        } 