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

    # 配置数据库 - 使用PostgreSQL
    # 读取数据库配置
    config = configparser.ConfigParser()
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'db_config.ini')
    config.read(config_path)

    # 获取PostgreSQL配置
    db_config = config['POSTGRES_DB']

    # 构建PostgreSQL连接字符串
    database_uri = f"postgresql://{db_config['username']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['database']}?client_encoding={db_config['client_encoding']}"
    app.config['SQLALCHEMY_DATABASE_URI'] = database_uri

    # 配置SQLAlchemy引擎参数
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,
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