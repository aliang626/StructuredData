from app import db
from datetime import datetime
import json

class QualityResult(db.Model):
    """质量检测结果模型"""
    __tablename__ = 'quality_results'
    
    id = db.Column(db.Integer, primary_key=True)
    rule_library_id = db.Column(db.Integer, db.ForeignKey('rule_libraries.id'), nullable=True)  # 允许为空，支持LLM检查
    data_source = db.Column(db.String(100), nullable=False)
    table_name = db.Column(db.String(100), nullable=False)
    total_records = db.Column(db.Integer, nullable=False)
    passed_records = db.Column(db.Integer, nullable=False)
    failed_records = db.Column(db.Integer, nullable=False)
    pass_rate = db.Column(db.Float, nullable=False)
    execution_time = db.Column(db.Float)  # 执行时间（秒）
    check_type = db.Column(db.String(20), default='rule')  # rule/llm 检查类型
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.String(50))
    
    # 关联详细报告
    reports = db.relationship('QualityReport', backref='result', lazy='dynamic', cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'rule_library_id': self.rule_library_id,
            'data_source': self.data_source,
            'table_name': self.table_name,
            'total_records': self.total_records,
            'passed_records': self.passed_records,
            'failed_records': self.failed_records,
            'pass_rate': self.pass_rate,
            'execution_time': self.execution_time,
            'check_type': self.check_type,
            'created_at': self.created_at.isoformat(),
            'created_by': self.created_by
        }

class QualityReport(db.Model):
    """质量检测详细报告模型"""
    __tablename__ = 'quality_reports'
    
    id = db.Column(db.Integer, primary_key=True)
    result_id = db.Column(db.Integer, db.ForeignKey('quality_results.id'), nullable=False)
    rule_name = db.Column(db.String(100), nullable=False)
    rule_type = db.Column(db.String(50), nullable=False)  # range/pattern/null_check等
    field_name = db.Column(db.String(100), nullable=False)
    passed_count = db.Column(db.Integer, nullable=False)
    failed_count = db.Column(db.Integer, nullable=False)
    error_details = db.Column(db.Text)  # JSON格式存储错误详情
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_error_details(self, details):
        """设置错误详情"""
        self.error_details = json.dumps(details, ensure_ascii=False)
    
    def get_error_details(self):
        """获取错误详情"""
        return json.loads(self.error_details) if self.error_details else []
    
    def to_dict(self):
        return {
            'id': self.id,
            'result_id': self.result_id,
            'rule_name': self.rule_name,
            'rule_type': self.rule_type,
            'field_name': self.field_name,
            'passed_count': self.passed_count,
            'failed_count': self.failed_count,
            'error_details': self.get_error_details(),
            'created_at': self.created_at.isoformat()
        } 