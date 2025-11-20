from app import db
from datetime import datetime

class LSTMAnomalyModel(db.Model):
    """LSTM异常检测模型配置"""
    __tablename__ = 'lstm_anomaly_models'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    model_path = db.Column(db.String(300), nullable=False)
    sequence_length = db.Column(db.Integer, default=20)
    input_size = db.Column(db.Integer, default=1)
    hidden_size = db.Column(db.Integer, default=64)
    num_layers = db.Column(db.Integer, default=2)
    num_classes = db.Column(db.Integer, default=2)
    dropout = db.Column(db.Float, default=0.0)
    bidirectional = db.Column(db.Boolean, default=False)
    threshold = db.Column(db.Float, default=0.5)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    model_type = db.Column(db.String(20), default='generic')  # 'wid', 'depth', 'sns', 'arc', 'generic'
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'model_path': self.model_path,
            'sequence_length': self.sequence_length,
            'input_size': self.input_size,
            'hidden_size': self.hidden_size,
            'num_layers': self.num_layers,
            'num_classes': self.num_classes,
            'dropout': self.dropout,
            'bidirectional': self.bidirectional,
            'threshold': self.threshold,
            'description': self.description,
            'model_type': self.model_type,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_active': self.is_active
        }
