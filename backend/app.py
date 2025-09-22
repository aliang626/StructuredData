from app import create_app, db
from app.models import *

app = create_app()

@app.route('/')
def index():
    return {
        'message': '智能化地质数据处理系统API',
        'version': '1.0.0',
        'status': 'running'
    }

@app.route('/health')
def health_check():
    try:
        # 测试数据库连接
        from sqlalchemy import text
        from app import db
        db.session.execute(text('SELECT 1'))
        db.session.commit()
        return {
            'status': 'healthy',
            'db': 'ok',
            'timestamp': '2025-09-17T16:28:15+08:00'
        }
    except Exception as e:
        return {
            'status': 'unhealthy',
            'db': 'error',
            'error': str(e)
        }, 500

if __name__ == '__main__':
    with app.app_context():
        # 创建数据库表
        db.create_all()
    
    app.run(debug=True, host='0.0.0.0', port=5000) 