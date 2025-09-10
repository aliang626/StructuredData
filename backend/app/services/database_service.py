import pandas as pd
import psycopg2
from sqlalchemy import create_engine, text, inspect
from app.models.data_source import DataSource, TableField
from app import db
import configparser
import os
import pandas as pd
from sqlalchemy import create_engine
import re
from pathlib import Path

def read_sql_auto_encoding(query, engine):
    """自动处理编码的SQL读取函数"""
    try:
        print("尝试使用默认编码读取数据...")
        df = pd.read_sql(query, engine)
        print("成功使用默认编码读取数据")
        return df
    except UnicodeDecodeError as e:
        print(f"默认编码解码失败: {str(e)}")
        # 如果默认编码失败，尝试重新创建引擎并使用不同编码
        return None
    except Exception as e:
        print(f"读取数据失败: {str(e)}")
        print(f"错误类型: {type(e).__name__}")
        print(f"错误详情: {str(e)}")
        return None

def try_get_tables_with_encodings(db_config, encodings=['utf8', 'gbk', 'latin1']):
    """尝试多种编码获取表列表，针对CSV导入的混合编码数据"""
    last_error = None
    
    for enc in encodings:
        try:
            # 使用DatabaseService的连接字符串方法
            connection_string = DatabaseService.get_connection_string(db_config, enc)
            
            # 创建引擎时添加编码参数
            engine = create_engine(
                connection_string, 
                connect_args={
                    'client_encoding': enc
                },
                pool_pre_ping=True,
                echo=False
            )
            
            # 使用连接测试并设置编码
            with engine.connect() as conn:
                # 显式设置客户端编码，避免连接字符串中的编码问题
                try:
                    conn.execute(text(f"SET client_encoding = '{enc}'"))
                except Exception as enc_error:
                    print(f"设置编码 {enc} 失败，使用默认编码: {str(enc_error)}")
                    # 如果设置编码失败，继续使用默认编码
                
                # 获取表列表 - 这里可能出现编码错误
                inspector = inspect(engine)
                
                # 尝试获取表名，如果出现编码错误则捕获
                try:
                    tables = inspector.get_table_names()
                    print(f"成功使用编码 {enc} 获取到 {len(tables)} 个表")
                    return tables
                except UnicodeDecodeError as unicode_error:
                    print(f"编码 {enc} 在获取表名时出现Unicode错误: {unicode_error}")
                    # 尝试直接SQL查询作为备选方案
                    try:
                        result = conn.execute(text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'"))
                        tables = [row[0] for row in result.fetchall()]
                        print(f"使用直接SQL查询成功获取到 {len(tables)} 个表")
                        return tables
                    except Exception as sql_error:
                        print(f"直接SQL查询也失败: {sql_error}")
                        raise unicode_error
                
        except Exception as e:
            print(f"编码 {enc} 失败: {str(e)}")
            last_error = e
            continue
    
    raise Exception(f"所有编码尝试失败，最后错误: {last_error}")

def read_csv_auto_encoding(file_path):
    """自动检测CSV文件编码并读取"""
    encodings = ['utf-8', 'gbk', 'latin-1']
    
    for encoding in encodings:
        try:
            return pd.read_csv(file_path, encoding=encoding)
        except UnicodeDecodeError:
            continue
    
    # 如果所有编码都失败，使用错误处理模式
    try:
        return pd.read_csv(file_path, encoding='utf-8', errors='ignore')
    except Exception as e:
        raise Exception(f"无法读取CSV文件 {file_path}: {str(e)}")

class DatabaseService:
    """数据库服务类"""
    
    @staticmethod
    def quote_identifier(identifier):
        """为PostgreSQL标识符添加双引号，处理大小写敏感问题"""
        if identifier is None:
            return None
        # 如果标识符包含大写字母、特殊字符或空格，则添加引号
        if (any(c.isupper() for c in identifier) or 
            any(c in identifier for c in [' ', '(', ')', '°', '-', '.']) or
            identifier != identifier.lower()):
            return f'"{identifier}"'
        return identifier
    
    @staticmethod
    def get_connection_string(db_config, encoding='utf8'):
        """获取数据库连接字符串，支持指定编码"""
        # 简化连接字符串，避免编码问题
        return f"postgresql://{db_config['username']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['database']}"
    
    @staticmethod
    def create_engine(connection_string, **kwargs):
        """创建数据库引擎"""
        default_args = {
            'pool_pre_ping': True,
            'echo': False
        }
        default_args.update(kwargs)
        return create_engine(connection_string, **default_args)
    
    @staticmethod
    def test_connection(db_config):
        """测试数据库连接"""
        try:
            conn = psycopg2.connect(
                host=db_config['host'],
                port=int(db_config['port']),
                user=db_config['username'],
                password=db_config['password'],
                database=db_config['database'],
                client_encoding='utf8'
            )
            conn.close()
            return True
        except Exception as e:
            print(f"数据库连接测试失败: {str(e)}")
            return False
    
    @staticmethod
    def get_tables(db_config):
        """获取数据库表列表，自动尝试多种编码"""
        try:
            return try_get_tables_with_encodings(db_config)
        except Exception as e:
            print(f"获取表列表失败: {str(e)}")
            raise e
    
    @staticmethod
    def get_table_fields(db_config, table_name):
        """获取表字段信息"""
        try:
            # 尝试多种编码获取字段信息
            encodings = ['utf8', 'gbk', 'latin1']
            last_error = None
            
            for enc in encodings:
                try:
                    connection_string = DatabaseService.get_connection_string(db_config, enc)
                    engine = create_engine(connection_string, connect_args={'client_encoding': enc})
                    
                    with engine.connect() as conn:
                        conn.execute(text(f"SET client_encoding = '{enc}'"))
                        inspector = inspect(engine)
                        columns = inspector.get_columns(table_name)
                        
                        fields = []
                        for column in columns:
                            field = {
                                'name': column['name'],
                                'type': str(column['type']),
                                'nullable': column['nullable'],
                                'primary_key': column.get('primary_key', False),
                                'default': column.get('default')
                            }
                            fields.append(field)
                        return fields
                        
                except Exception as e:
                    last_error = e
                    continue
            
            raise last_error
            
        except Exception as e:
            raise Exception(f"获取表字段失败: {str(e)}")
    
    @staticmethod
    def preview_data(db_config, table_name, fields=None, limit=100):
        """预览数据"""
        # 保证try/except结构正确
        try:
            print("测试基本数据库连接...")
            if not DatabaseService.test_connection(db_config):
                raise Exception("无法连接到数据库，请检查数据库配置")
            print("基本数据库连接正常")
            
            # 只使用支持中文的编码，移除latin-1
            encodings = ['utf8', 'gbk']
            last_error = None
            
            for enc in encodings:
                try:
                    print(f"尝试使用编码 {enc} 预览数据...")
                    connection_string = DatabaseService.get_connection_string(db_config, enc)
                    
                    # 简化连接参数，避免编码冲突
                    engine = create_engine(
                        connection_string, 
                        pool_pre_ping=True,
                        echo=False
                    )
                    
                    with engine.connect() as conn:
                        # 设置数据库客户端编码
                        try:
                            if enc == 'utf8':
                                conn.execute(text("SET client_encoding = 'UTF8'"))
                            elif enc == 'gbk':
                                conn.execute(text("SET client_encoding = 'GBK'"))
                        except Exception as enc_error:
                            print(f"设置编码 {enc} 失败，使用默认编码: {str(enc_error)}")
                        
                        # 使用引号包装表名和字段名
                        quoted_table_name = DatabaseService.quote_identifier(table_name)
                        
                        if fields:
                            quoted_fields = [DatabaseService.quote_identifier(field) for field in fields]
                            field_list = ', '.join(quoted_fields)
                            if limit is None:
                                query = f"SELECT {field_list} FROM {quoted_table_name}"
                            else:
                                query = f"SELECT {field_list} FROM {quoted_table_name} LIMIT {limit}"
                        else:
                            if limit is None:
                                query = f"SELECT * FROM {quoted_table_name}"
                            else:
                                query = f"SELECT * FROM {quoted_table_name} LIMIT {limit}"
                        
                        print(f"执行查询: {query}")
                        
                        # 先测试连接是否正常
                        try:
                            test_result = conn.execute(text("SELECT 1"))
                            test_result.fetchone()
                            print("数据库连接正常")
                        except Exception as conn_error:
                            print(f"数据库连接测试失败: {str(conn_error)}")
                            raise conn_error
                        
                        # 测试表是否存在（使用不区分大小写的查询）
                        try:
                            table_check = conn.execute(text(f"SELECT EXISTS (SELECT FROM information_schema.tables WHERE LOWER(table_name) = LOWER('{table_name}'))"))
                            table_exists = table_check.fetchone()[0]
                            if not table_exists:
                                raise Exception(f"表 {table_name} 不存在")
                            print(f"表 {table_name} 存在")
                        except Exception as table_error:
                            print(f"表检查失败: {str(table_error)}")
                            raise table_error
                        
                        # 直接使用pandas读取，不传递encoding参数
                        df = pd.read_sql(query, engine)
                        
                        if df is not None and len(df) > 0:
                            print(f"成功获取 {len(df)} 行数据")
                            
                            # 改进中文字符处理
                            for col in df.select_dtypes(include=['object']).columns:
                                df[col] = df[col].astype(str).apply(
                                    lambda x: x if x == 'nan' else (
                                        x.encode('utf-8', errors='replace').decode('utf-8') 
                                        if isinstance(x, str) else str(x)
                                    )
                                )
                            
                            return df.to_dict('records')
                        elif df is not None:
                            print("查询结果为空")
                            return []
                        else:
                            print(f"编码 {enc} 读取失败，尝试下一个编码")
                            continue
                            
                except Exception as e:
                    print(f"编码 {enc} 预览数据失败: {str(e)}")
                    last_error = e
                    continue
            
            if last_error:
                raise Exception(f"所有编码尝试都失败了，最后错误: {str(last_error)}")
            else:
                raise Exception("所有编码尝试都失败了，但没有捕获到具体错误")
                
        except Exception as e:
            raise Exception(f"预览数据失败: {str(e)}")

    @staticmethod
    def get_data_statistics(db_config, table_name, fields):
        """获取数据统计信息"""
        try:
            print("测试基本数据库连接...")
            if not DatabaseService.test_connection(db_config):
                raise Exception("无法连接到数据库，请检查数据库配置")
            print("基本数据库连接正常")
            
            # 只使用支持中文的编码，移除latin-1
            encodings = ['utf8', 'gbk']
            last_error = None
            
            for enc in encodings:
                try:
                    print(f"尝试使用编码 {enc} 获取统计信息...")
                    connection_string = DatabaseService.get_connection_string(db_config, enc)
                    
                    # 简化连接参数，避免编码冲突
                    engine = create_engine(
                        connection_string, 
                        pool_pre_ping=True,
                        echo=False
                    )
                    
                    with engine.connect() as conn:
                        # 设置数据库客户端编码
                        try:
                            if enc == 'utf8':
                                conn.execute(text("SET client_encoding = 'UTF8'"))
                            elif enc == 'gbk':
                                conn.execute(text("SET client_encoding = 'GBK'"))
                        except Exception as enc_error:
                            print(f"设置编码 {enc} 失败，使用默认编码: {str(enc_error)}")
                        
                        # 使用引号包装表名和字段名
                        quoted_table_name = DatabaseService.quote_identifier(table_name)
                        quoted_fields = [DatabaseService.quote_identifier(field) for field in fields]
                        field_list = ', '.join(quoted_fields)
                        query = f"SELECT {field_list} FROM {quoted_table_name}"
                        print(f"执行统计查询: {query}")
                        
                        # 直接使用pandas读取，不传递encoding参数
                        df = pd.read_sql(query, engine)
                        
                        if df is not None and len(df) > 0:
                            print(f"成功获取 {len(df)} 行数据用于统计")
                            
                            # 改进中文字符处理
                            for col in df.select_dtypes(include=['object']).columns:
                                df[col] = df[col].astype(str).apply(
                                    lambda x: x if x == 'nan' else (
                                        x.encode('utf-8', errors='replace').decode('utf-8') 
                                        if isinstance(x, str) else str(x)
                                    )
                                )
                            
                            statistics = {}
                            for field in fields:
                                if field in df.columns:
                                    statistics[field] = {
                                        'count': int(df[field].count()),
                                        'mean': float(df[field].mean()) if pd.api.types.is_numeric_dtype(df[field]) else None,
                                        'std': float(df[field].std()) if pd.api.types.is_numeric_dtype(df[field]) else None,
                                        'min': float(df[field].min()) if pd.api.types.is_numeric_dtype(df[field]) else None,
                                        'max': float(df[field].max()) if pd.api.types.is_numeric_dtype(df[field]) else None
                                    }
                                else:
                                    statistics[field] = {
                                        'count': 0,
                                        'mean': None,
                                        'std': None,
                                        'min': None,
                                        'max': None
                                    }
                            return statistics
                        elif df is not None:
                            print("查询结果为空，返回空统计信息")
                            return {field: {'count': 0, 'mean': None, 'std': None, 'min': None, 'max': None} for field in fields}
                        else:
                            print(f"编码 {enc} 读取失败，尝试下一个编码")
                            continue
                            
                except Exception as e:
                    print(f"编码 {enc} 获取统计信息失败: {str(e)}")
                    last_error = e
                    continue
            
            if last_error:
                raise Exception(f"所有编码尝试都失败了，最后错误: {str(last_error)}")
            else:
                raise Exception("所有编码尝试都失败了，但没有捕获到具体错误")
                
        except Exception as e:
            raise Exception(f"获取统计信息失败: {str(e)}")
    
    @staticmethod
    def save_data_source(name, db_type, host, port, database, username, password, status=False):
        data_source = DataSource(
            name=name,
            db_type=db_type,
            host=host,
            port=port,
            database=database,
            username=username,
            password=password,
            status=status
        )
        db.session.add(data_source)
        db.session.commit()
        return data_source
    
    @staticmethod
    def get_data_sources():
        """获取所有数据源"""
        try:
            print("开始获取数据源列表...")
            # 只返回活跃的数据源，这样更符合业务逻辑
            sources = DataSource.query.filter_by(is_active=True).all()
            print(f"成功获取 {len(sources)} 个活跃数据源")
            
            result = []
            for source in sources:
                try:
                    source_dict = source.to_dict()
                    result.append(source_dict)
                except Exception as e:
                    print(f"转换数据源 {source.id} 失败: {str(e)}")
                    # 如果转换失败，跳过这个数据源
                    continue
            
            print(f"成功转换 {len(result)} 个数据源")
            return result
            
        except Exception as e:
            print(f"获取数据源失败: {str(e)}")
            print(f"错误类型: {type(e).__name__}")
            raise Exception(f"获取数据源失败: {str(e)}")
    
    @staticmethod
    def load_cnooc_config():
        """加载CNOOC数据库配置"""
        try:
            config = configparser.ConfigParser()
            config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'config', 'db_config.ini')
            config.read(config_path)
            
            if 'POSTGRES_DB' in config:
                db_config = config['POSTGRES_DB']
                return {
                    'host': db_config['host'],
                    'port': int(db_config['port']),
                    'database': db_config['database'],
                    'username': db_config['username'],
                    'password': db_config['password'],
                    'client_encoding': db_config.get('client_encoding', 'utf8'),
                    'db_type': 'postgresql'
                }
            else:
                raise Exception("配置文件中未找到POSTGRES_DB配置")
        except Exception as e:
            raise Exception(f"加载CNOOC配置失败: {str(e)}")
    
    @staticmethod
    def get_distinct_values(db_config, table_name, field_name, limit=1000):
        """获取指定字段的不同值"""
        try:
            print(f"获取字段 {field_name} 在表 {table_name} 中的不同值...")
            
            # 测试数据库连接
            if not DatabaseService.test_connection(db_config):
                raise Exception("无法连接到数据库，请检查数据库配置")
            
            # 支持中文的编码
            encodings = ['utf8', 'gbk']
            last_error = None
            
            for enc in encodings:
                try:
                    print(f"尝试使用编码 {enc} 获取不同值...")
                    connection_string = DatabaseService.get_connection_string(db_config, enc)
                    
                    engine = create_engine(
                        connection_string, 
                        pool_pre_ping=True,
                        echo=False
                    )
                    
                    with engine.connect() as conn:
                        # 设置数据库客户端编码
                        try:
                            if enc == 'utf8':
                                conn.execute(text("SET client_encoding = 'UTF8'"))
                            elif enc == 'gbk':
                                conn.execute(text("SET client_encoding = 'GBK'"))
                        except Exception as enc_error:
                            print(f"设置编码 {enc} 失败，使用默认编码: {str(enc_error)}")
                        
                        # 使用引号包装表名和字段名
                        quoted_table_name = DatabaseService.quote_identifier(table_name)
                        quoted_field_name = DatabaseService.quote_identifier(field_name)
                        
                        # 构建查询语句获取不同值
                        query = f"SELECT DISTINCT {quoted_field_name} FROM {quoted_table_name} WHERE {quoted_field_name} IS NOT NULL ORDER BY {quoted_field_name} LIMIT {limit}"
                        
                        print(f"执行查询: {query}")
                        result = conn.execute(text(query))
                        
                        # 获取所有不同值
                        distinct_values = [row[0] for row in result.fetchall()]
                        
                        print(f"成功获取 {len(distinct_values)} 个不同值，使用编码: {enc}")
                        return distinct_values
                        
                except Exception as e:
                    last_error = e
                    print(f"使用编码 {enc} 获取不同值失败: {str(e)}")
                    continue
            
            # 所有编码都失败了
            raise Exception(f"所有编码尝试都失败了，最后错误: {str(last_error)}")
            
        except Exception as e:
            print(f"获取字段不同值失败: {str(e)}")
            raise Exception(f"获取字段不同值失败: {str(e)}")
    
    @staticmethod
    def preview_data_with_filter(db_config, table_name, fields=None, limit=100, company_field=None, company_value=None):
        """预览数据（支持分公司过滤）"""
        try:
            print(f"预览数据: 表={table_name}, 字段={fields}, 分公司字段={company_field}, 分公司值={company_value}")
            
            # 测试数据库连接
            if not DatabaseService.test_connection(db_config):
                raise Exception("无法连接到数据库，请检查数据库配置")
            
            # 支持中文的编码
            encodings = ['utf8', 'gbk']
            last_error = None
            
            for enc in encodings:
                try:
                    print(f"尝试使用编码 {enc} 预览数据...")
                    connection_string = DatabaseService.get_connection_string(db_config, enc)
                    
                    engine = create_engine(
                        connection_string, 
                        pool_pre_ping=True,
                        echo=False
                    )
                    
                    with engine.connect() as conn:
                        # 设置数据库客户端编码
                        try:
                            if enc == 'utf8':
                                conn.execute(text("SET client_encoding = 'UTF8'"))
                            elif enc == 'gbk':
                                conn.execute(text("SET client_encoding = 'GBK'"))
                        except Exception as enc_error:
                            print(f"设置编码 {enc} 失败，使用默认编码: {str(enc_error)}")
                        
                        # 使用引号包装表名和字段名
                        quoted_table_name = DatabaseService.quote_identifier(table_name)
                        
                        # 构建字段列表
                        if fields:
                            quoted_fields = [DatabaseService.quote_identifier(field) for field in fields]
                            field_list = ', '.join(quoted_fields)
                        else:
                            field_list = '*'
                        
                        # 构建基本查询
                        query = f"SELECT {field_list} FROM {quoted_table_name}"
                        
                        # 添加分公司过滤条件
                        if company_field and company_value:
                            quoted_company_field = DatabaseService.quote_identifier(company_field)
                            # 使用参数化查询防止SQL注入，同时处理字符串转义
                            escaped_value = company_value.replace("'", "''")  # SQL字符串转义
                            query += f" WHERE {quoted_company_field} = '{escaped_value}'"
                        
                        # 添加限制
                        if limit is not None:
                            query += f" LIMIT {limit}"
                        
                        print(f"执行查询: {query}")
                        
                        # 使用pandas读取数据
                        df = pd.read_sql(query, conn)
                        
                        print(f"成功获取 {len(df)} 行数据，使用编码: {enc}")
                        return df.to_dict('records')
                        
                except Exception as e:
                    last_error = e
                    print(f"使用编码 {enc} 预览数据失败: {str(e)}")
                    continue
            
            # 所有编码都失败了
            raise Exception(f"所有编码尝试都失败了，最后错误: {str(last_error)}")
            
        except Exception as e:
            print(f"预览数据失败: {str(e)}")
            raise Exception(f"预览数据失败: {str(e)}")
