from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os
import configparser

# 初始化扩展
db = SQLAlchemy()
migrate = Migrate()

def create_app():
    app = Flask(__name__)

    # 配置CORS
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # 配置数据库 - 使用MySQL
    # 读取数据库配置
    config = configparser.ConfigParser()
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'db_config.ini')
    config.read(config_path, encoding='utf-8')

    # 获取MySQL配置
    db_config = config['MySQL_DB']

    # 构建MySQL连接字符串（处理密码中的特殊字符）
    import urllib.parse
    username = db_config['username']
    password = urllib.parse.quote_plus(db_config['password'])  # URL编码密码中的特殊字符
    host = db_config['host']
    port = db_config['port']
    database = db_config['database']
    charset = db_config['charset']
    
    database_uri = f"mysql+pymysql://{username}:{password}@{host}:{port}/{database}?charset={charset}"
    app.config['SQLALCHEMY_DATABASE_URI'] = database_uri

    # 配置SQLAlchemy引擎参数（MySQL优化）
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,
        'pool_recycle': 3600,  # MySQL连接回收时间
        'pool_timeout': 20,    # 连接池超时
        'max_overflow': 0,     # 最大溢出连接数
        'echo': False
    }
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'your-secret-key-here'

    # 初始化扩展
    db.init_app(app)
    migrate.init_app(app, db)

    # 注册蓝图
    from .routes import model_routes, database_routes, rule_routes, quality_routes, system_routes
    app.register_blueprint(model_routes.bp, url_prefix='/api/models')
    app.register_blueprint(database_routes.bp, url_prefix='/api/database')
    app.register_blueprint(rule_routes.bp, url_prefix='/api/rules')
    app.register_blueprint(quality_routes.bp, url_prefix='/api/quality')
    app.register_blueprint(system_routes.bp, url_prefix='/api')

    return app