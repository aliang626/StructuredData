import os
import pandas as pd
from sqlalchemy import create_engine, text
import re

def detect_and_read_csv(file_path):
    """自动检测CSV文件编码并读取"""
    encodings = ['utf-8', 'gbk', 'gb2312', 'latin-1', 'cp1252']
    
    for encoding in encodings:
        try:
            print(f"  尝试编码: {encoding}")
            df = pd.read_csv(file_path, encoding=encoding)
            print(f"  成功使用编码 {encoding} 读取文件")
            return df, encoding
        except UnicodeDecodeError:
            continue
        except Exception as e:
            print(f"  编码 {encoding} 读取失败: {str(e)}")
            continue
    
    # 如果所有编码都失败，使用错误处理模式
    try:
        print("  所有编码都失败，使用UTF-8忽略错误模式")
        df = pd.read_csv(file_path, encoding='utf-8', errors='ignore')
        return df, 'utf-8-ignore'
    except Exception as e:
        raise Exception(f"无法读取CSV文件 {file_path}: {str(e)}")

def clean_dataframe_encoding(df):
    """清理DataFrame中的编码问题"""
    print("  清理数据编码问题...")
    
    # 处理文本列的编码问题
    for col in df.select_dtypes(include=['object']).columns:
        df[col] = df[col].astype(str).apply(
            lambda x: x.encode('utf-8', errors='ignore').decode('utf-8') 
            if isinstance(x, str) and x != 'nan' else x
        )
    
    # 替换NaN值
    df = df.fillna('')
    
    return df

def import_csv_with_proper_encoding():
    """使用正确的编码导入CSV数据到PostgreSQL"""
    
    # 配置参数
    csv_folder = r'E:\cnooc'
    db_url = 'postgresql://postgres:123456@localhost:5432/CNOOC?client_encoding=utf8'
    
    print("开始CSV导入过程...")
    print(f"CSV文件夹: {csv_folder}")
    print(f"数据库连接: {db_url.replace('123456', '***')}")
    
    if not os.path.exists(csv_folder):
        print(f"错误: CSV文件夹不存在: {csv_folder}")
        return
    
    # 创建数据库连接，强制使用UTF-8编码
    engine = create_engine(
        db_url, 
        connect_args={
            'client_encoding': 'utf8',
            'options': '-c client_encoding=utf8'
        },
        pool_pre_ping=True
    )
    
    # 在导入前设置数据库编码
    print("设置数据库连接编码...")
    with engine.connect() as conn:
        conn.execute(text("SET client_encoding = 'utf8'"))
        # 检查当前编码设置
        result = conn.execute(text("SHOW client_encoding"))
        current_encoding = result.fetchone()[0]
        print(f"当前数据库客户端编码: {current_encoding}")
    
    # 获取所有CSV文件
    csv_files = [f for f in os.listdir(csv_folder) if f.lower().endswith('.csv')]
    print(f"找到 {len(csv_files)} 个CSV文件")
    
    success_count = 0
    error_count = 0
    
    # 遍历文件夹下所有csv文件
    for filename in csv_files:
        print(f"\n处理文件: {filename}")
        
        # 生成表名
        base_name = os.path.splitext(filename)[0]
        table_name = base_name
        
        # 如果有12位数字后缀，去掉
        m = re.match(r'(.+)_\d{12}$', base_name)
        if m:
            table_name = m.group(1)
        
        table_name = table_name.lower()
        file_path = os.path.join(csv_folder, filename)
        
        print(f"  文件路径: {file_path}")
        print(f"  目标表名: {table_name}")
        
        try:
            # 读取CSV文件
            df, used_encoding = detect_and_read_csv(file_path)
            print(f"  原始数据行数: {len(df)}")
            print(f"  原始数据列数: {len(df.columns)}")
            
            # 清理编码问题
            df = clean_dataframe_encoding(df)
            
            # 导入到数据库
            print(f"  导入到数据库表: {table_name}")
            df.to_sql(
                table_name, 
                engine, 
                index=False, 
                if_exists='replace',
                method='multi',  # 批量插入提高性能
                chunksize=1000   # 分批处理大文件
            )
            
            print(f"  ✓ 导入成功: {table_name} ({len(df)} 行, 使用编码: {used_encoding})")
            success_count += 1
            
        except Exception as e:
            print(f"  ✗ 导入失败: {filename}")
            print(f"    错误信息: {str(e)}")
            error_count += 1
    
    print(f"\n导入完成!")
    print(f"成功: {success_count} 个文件")
    print(f"失败: {error_count} 个文件")
    
    # 验证导入结果
    if success_count > 0:
        print("\n验证导入结果...")
        with engine.connect() as conn:
            result = conn.execute(text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'"))
            tables = [row[0] for row in result.fetchall()]
            print(f"数据库中的表数量: {len(tables)}")
            print(f"表列表: {tables[:10]}{'...' if len(tables) > 10 else ''}")

if __name__ == "__main__":
    import_csv_with_proper_encoding()