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
    return {
        'status': 'healthy',
        'timestamp': '2024-01-01T00:00:00Z'
    }

if __name__ == '__main__':
    with app.app_context():
        # 创建数据库表
        db.create_all()
    
    app.run(debug=True, host='0.0.0.0', port=5000) 