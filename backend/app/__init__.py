from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os
import configparser
import logging
from logging.handlers import RotatingFileHandler

# 初始化扩展
db = SQLAlchemy()
migrate = Migrate()

def create_app():
    app = Flask(__name__)

    # ======================= 日志配置 (新增) =======================
    # 1. 配置日志目录
    log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # 2. 定义统一格式 (去除毫秒)
    formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 3. 创建处理器
    file_handler = RotatingFileHandler(
        os.path.join(log_dir, 'app.log'), maxBytes=10*1024*1024, backupCount=10, encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)

    # 4. Flask应用日志去重
    if app.logger.hasHandlers():
        app.logger.handlers.clear()
    app.logger.propagate = False
    app.logger.addHandler(file_handler)
    app.logger.addHandler(console_handler)
    app.logger.setLevel(logging.INFO)

    # 5. SQLAlchemy日志接管 (防止重复打印)
    sql_logger = logging.getLogger('sqlalchemy.engine')
    if sql_logger.hasHandlers():
        sql_logger.handlers.clear()
    sql_logger.propagate = False
    sql_logger.addHandler(file_handler)
    sql_logger.addHandler(console_handler)
    sql_logger.setLevel(logging.WARNING)
    # =============================================================

    # 配置CORS
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # 配置数据库
    # 读取数据库配置
    config = configparser.ConfigParser()
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'db_config.ini')
    config.read(config_path, encoding='utf-8')

    # ========== MySQL 配置 (当前使用) ==========
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
        'echo': False          # [修改] 关闭默认打印，交由上面配置的logger处理，防止重复
    }

    # ========== PostgreSQL 配置 (已注释，保留备用) ==========
    # 获取PostgreSQL配置
    # db_config = config['POSTGRES_DB']

    # # 构建PostgreSQL连接字符串（处理密码中的特殊字符）
    # import urllib.parse
    # username = db_config['username']
    # password = urllib.parse.quote_plus(db_config['password'])  # URL编码密码中的特殊字符
    # host = db_config['host']
    # port = db_config['port']
    # database = db_config['database']
    # client_encoding = db_config.get('client_encoding', 'utf8')
    
    # database_uri = f"postgresql://{username}:{password}@{host}:{port}/{database}?client_encoding={client_encoding}"
    # app.config['SQLALCHEMY_DATABASE_URI'] = database_uri

    # # 配置SQLAlchemy引擎参数（PostgreSQL优化）
    # app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    #     'pool_pre_ping': True,
    #     'pool_recycle': 1800,  # PostgreSQL连接回收时间
    #     'pool_timeout': 20,    # 连接池超时
    #     'max_overflow': 0,     # 最大溢出连接数
    #     'echo': False
    # }
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'your-secret-key-here'

    # 初始化扩展
    db.init_app(app)
    migrate.init_app(app, db)


    # 注册蓝图
    # 1. 在这里添加 lstm_anomaly_routes
    from .routes import model_routes, database_routes, rule_routes, quality_routes, system_routes, lstm_anomaly_routes
    
    app.register_blueprint(model_routes.bp, url_prefix='/api/models')
    app.register_blueprint(database_routes.bp, url_prefix='/api/database')
    app.register_blueprint(rule_routes.bp, url_prefix='/api/rules')
    app.register_blueprint(quality_routes.bp, url_prefix='/api/quality')
    app.register_blueprint(system_routes.bp, url_prefix='/api')
    
    # 2. 注册新的蓝图，前缀设置为 /api/lstm-anomaly
    app.register_blueprint(lstm_anomaly_routes.bp, url_prefix='/api/lstm-anomaly')

    return app