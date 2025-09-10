from app import db
from datetime import datetime
import json

class KnowledgeBase(db.Model):
    """知识库模型"""
    __tablename__ = 'knowledge_bases'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    file_path = db.Column(db.String(500))  # Excel文件路径
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    created_by = db.Column(db.String(50))
    
    # 关联知识库条目
    entries = db.relationship('KnowledgeBaseEntry', backref='knowledge_base', lazy='dynamic', cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'file_path': self.file_path,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'is_active': self.is_active,
            'created_by': self.created_by,
            'entry_count': self.entries.count()
        }

class KnowledgeBaseEntry(db.Model):
    """知识库条目模型"""
    __tablename__ = 'knowledge_base_entries'
    
    id = db.Column(db.Integer, primary_key=True)
    knowledge_base_id = db.Column(db.Integer, db.ForeignKey('knowledge_bases.id'), nullable=False)
    category = db.Column(db.String(100), nullable=False)  # 类别
    variable = db.Column(db.String(100), nullable=False)  # 变量名
    quality_description = db.Column(db.Text, nullable=False)  # 质量规范描述
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'knowledge_base_id': self.knowledge_base_id,
            'Category': self.category,
            'Variable': self.variable,
            '质量规范描述': self.quality_description,
            'created_at': self.created_at.isoformat()
        }

 