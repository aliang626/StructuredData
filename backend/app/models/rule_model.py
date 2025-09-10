from app import db
from datetime import datetime
import json

class RuleLibrary(db.Model):
    """规则库模型"""
    __tablename__ = 'rule_libraries'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # 关联规则版本
    versions = db.relationship('RuleVersion', backref='library', lazy='dynamic', cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'is_active': self.is_active,
            'version_count': self.versions.count()
        }

class RuleVersion(db.Model):
    """规则版本模型"""
    __tablename__ = 'rule_versions'
    
    id = db.Column(db.Integer, primary_key=True)
    library_id = db.Column(db.Integer, db.ForeignKey('rule_libraries.id'), nullable=False)
    version = db.Column(db.String(20), nullable=False)
    rules = db.Column(db.Text, nullable=False)  # JSON格式存储规则
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.String(50))
    description = db.Column(db.Text)
    
    def set_rules(self, rules_list):
        """设置规则列表"""
        self.rules = json.dumps(rules_list, ensure_ascii=False)
    
    def get_rules(self):
        """获取规则列表"""
        return json.loads(self.rules) if self.rules else []
    
    def to_dict(self):
        rules_list = self.get_rules()
        return {
            'id': self.id,
            'library_id': self.library_id,
            'version': self.version,
            'rules': rules_list,
            'rule_count': len(rules_list) if rules_list else 0,
            'created_at': self.created_at.isoformat(),
            'created_by': self.created_by,
            'description': self.description
        } 