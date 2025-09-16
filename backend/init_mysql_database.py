#!/usr/bin/env python3
"""
MySQL数据库初始化脚本
创建所有必需的表结构
"""

import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.data_source import DataSource
from app.models.model_config import ModelConfig, ModelParameter
from app.models.rule_model import RuleLibrary, RuleVersion, Rule
from app.models.quality_result import QualityResult, QualityReport
from app.models.knowledge_base import KnowledgeBase
from app.models.training_history import TrainingHistory

def init_database():
    """初始化数据库"""
    try:
        print("=== MySQL数据库初始化 ===")
        
        # 创建Flask应用
        app = create_app()
        
        with app.app_context():
            print("正在创建数据库表...")
            
            # 删除所有表（如果存在）- 谨慎使用
            print("正在清理旧表...")
            db.drop_all()
            
            # 创建所有表
            print("正在创建新表...")
            db.create_all()
            
            # 验证表创建
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            
            print(f"\n✅ 成功创建 {len(tables)} 个表:")
            for table in sorted(tables):
                print(f"  - {table}")
            
            # 添加初始数据（可选）
            print("\n正在添加初始数据...")
            add_initial_data()
            
            print("\n🎉 数据库初始化完成！")
            
    except Exception as e:
        print(f"❌ 数据库初始化失败: {str(e)}")
        import traceback
        traceback.print_exc()

def add_initial_data():
    """添加初始数据"""
    try:
        # 检查是否已有数据
        if DataSource.query.first():
            print("数据库中已有数据，跳过初始数据添加")
            return
        
        # 添加示例数据源
        sample_datasource = DataSource(
            name="示例MySQL数据源",
            db_type="mysql",
            host="localhost", 
            port=3306,
            database="sample_db",
            username="sample_user",
            password="sample_password",
            status=False,
            is_active=True
        )
        db.session.add(sample_datasource)
        
        # 添加示例模型配置
        sample_model = ModelConfig(
            name="示例回归模型",
            model_type="regression",
            model_name="LinearRegression",
            description="用于数据质量预测的线性回归模型",
            is_active=True,
            status="draft"
        )
        db.session.add(sample_model)
        
        # 添加示例规则库
        sample_rule_library = RuleLibrary(
            name="基础数据质量规则",
            description="包含常用数据质量检测规则",
            is_active=True
        )
        db.session.add(sample_rule_library)
        
        # 提交事务
        db.session.commit()
        print("✅ 初始数据添加完成")
        
    except Exception as e:
        print(f"⚠️ 添加初始数据失败: {str(e)}")
        db.session.rollback()

def show_database_info():
    """显示数据库信息"""
    try:
        app = create_app()
        
        with app.app_context():
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            
            print(f"\n=== 数据库信息 ===")
            print(f"数据库引擎: {db.engine.name}")
            print(f"连接URL: {str(db.engine.url).replace(str(db.engine.url.password), '****')}")
            print(f"表数量: {len(tables)}")
            
            # 显示每个表的结构
            for table_name in sorted(tables):
                columns = inspector.get_columns(table_name)
                print(f"\n📋 表: {table_name}")
                print(f"  字段数: {len(columns)}")
                for col in columns:
                    null_str = "NULL" if col['nullable'] else "NOT NULL"
                    print(f"    - {col['name']}: {col['type']} {null_str}")
                    
    except Exception as e:
        print(f"❌ 获取数据库信息失败: {str(e)}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='MySQL数据库管理工具')
    parser.add_argument('--init', action='store_true', help='初始化数据库')
    parser.add_argument('--info', action='store_true', help='显示数据库信息')
    parser.add_argument('--test', action='store_true', help='测试数据库连接')
    
    args = parser.parse_args()
    
    if args.init:
        init_database()
    elif args.info:
        show_database_info()
    elif args.test:
        from test_mysql_connection import test_mysql_connection, test_sqlalchemy_connection
        test_mysql_connection()
        test_sqlalchemy_connection()
    else:
        print("使用帮助:")
        print("  python init_mysql_database.py --init   # 初始化数据库")
        print("  python init_mysql_database.py --info   # 显示数据库信息")
        print("  python init_mysql_database.py --test   # 测试数据库连接")
