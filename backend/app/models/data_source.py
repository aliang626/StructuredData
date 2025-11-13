from app import db
from datetime import datetime

class DataSource(db.Model):
    """数据源模型"""
    __tablename__ = 'data_sources'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    db_type = db.Column(db.String(20), nullable=False)  # mysql/postgresql
    host = db.Column(db.String(100), nullable=False)
    port = db.Column(db.Integer, nullable=False)
    database = db.Column(db.String(100), nullable=False)
    schema = db.Column(db.String(100), default='public')  # schema名称，默认为public
    username = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(200), nullable=False)
    status = db.Column(db.Boolean, default=False)  # 新增字段，表示连接状态
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    def to_dict(self, include_password=False):
        """
        转换为字典
        :param include_password: 是否包含密码（默认False，不包含密码）
        """
        result = {
            'id': self.id,
            'name': self.name,
            'db_type': self.db_type,
            'host': self.host,
            'port': self.port,
            'database': self.database,
            'schema': self.schema if hasattr(self, 'schema') else 'public',  # 兼容旧数据
            'username': self.username,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'is_active': self.is_active
        }
        
        # 只在明确需要时才返回密码（用于内部操作，如编辑数据源）
        # 对外API默认不返回密码，增强安全性
        if include_password:
            result['password'] = self.password
        else:
            # 返回密码掩码，让前端知道密码已设置
            result['password'] = '******' if self.password else ''
        
        return result

class TableField(db.Model):
    """表字段模型"""
    __tablename__ = 'table_fields'
    
    id = db.Column(db.Integer, primary_key=True)
    table_name = db.Column(db.String(100), nullable=False)
    field_name = db.Column(db.String(100), nullable=False)
    field_type = db.Column(db.String(50), nullable=False)
    field_length = db.Column(db.Integer)
    is_nullable = db.Column(db.Boolean, default=True)
    is_primary_key = db.Column(db.Boolean, default=False)
    default_value = db.Column(db.String(200))
    description = db.Column(db.Text)
    
    def to_dict(self):
        return {
            'id': self.id,
            'table_name': self.table_name,
            'field_name': self.field_name,
            'field_type': self.field_type,
            'field_length': self.field_length,
            'is_nullable': self.is_nullable,
            'is_primary_key': self.is_primary_key,
            'default_value': self.default_value,
            'description': self.description
        } 