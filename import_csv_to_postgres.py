import os
import pandas as pd
from sqlalchemy import create_engine

def read_csv_auto_encoding(file_path):
    try:
        return pd.read_csv(file_path, encoding='utf-8')
    except UnicodeDecodeError:
        print(f"utf-8解码失败，尝试gbk: {file_path}")
        return pd.read_csv(file_path, encoding='gbk')

# 配置参数
csv_folder = r'E:\cnooc'
db_url = 'postgresql://postgres:123456@localhost:5432/CNOOC'

# 创建数据库连接
engine = create_engine(db_url)

# 遍历文件夹下所有csv文件
for filename in os.listdir(csv_folder):
    if filename.lower().endswith('.csv'):
        table_name = os.path.splitext(filename)[0].lower()
        file_path = os.path.join(csv_folder, filename)
        print(f'正在导入: {file_path} -> 表: {table_name}')
        try:
            df = read_csv_auto_encoding(file_path)
            df.to_sql(table_name, engine, index=False, if_exists='replace')
            print(f'导入完成: {table_name} ({len(df)} 行)')
        except Exception as e:
            print(f'导入失败: {file_path}，错误: {e}')

print('所有CSV文件已导入完成！') 