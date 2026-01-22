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
        # 基础 URL
        base_url = f"postgresql://{db_config['username']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['database']}"
        
        # [核心修复] 将 client_encoding 显式拼接到 URL 中
        if encoding:
            pg_encoding = encoding
            # 映射常用编码名称到 PostgreSQL 支持的标准名称
            if encoding.lower() in ['utf-8', 'utf8']:
                pg_encoding = 'UTF8'
            elif encoding.lower() in ['gbk', 'gb18030']:
                pg_encoding = 'GBK'
            elif encoding.lower() in ['latin1', 'latin-1']:
                pg_encoding = 'LATIN1'
            
            # 拼接参数，确保驱动层识别
            return f"{base_url}?client_encoding={pg_encoding}"
            
        return base_url

    @staticmethod
    def create_engine(connection_string, **kwargs):
        """创建数据库引擎 - 使用NullPool避免连接池复用问题"""
        from sqlalchemy.pool import NullPool
        default_args = {
            'poolclass': NullPool,  # 关键修复：使用NullPool，每次创建新连接，用完立即关闭
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
    def get_schemas(db_config):
        """获取数据库所有schema列表"""
        try:
            encodings = ['utf8', 'gbk', 'latin1']
            last_error = None
            
            for enc in encodings:
                try:
                    connection_string = DatabaseService.get_connection_string(db_config, enc)
                    engine = create_engine(
                        connection_string, 
                        connect_args={'client_encoding': enc},
                        pool_pre_ping=True,
                        echo=False
                    )
                    
                    with engine.connect() as conn:
                        try:
                            conn.execute(text(f"SET client_encoding = '{enc}'"))
                        except Exception as enc_error:
                            print(f"设置编码 {enc} 失败，使用默认编码: {str(enc_error)}")
                        
                        # 查询所有schema
                        query = """
                        SELECT schema_name
                        FROM information_schema.schemata
                        WHERE schema_name NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
                        ORDER BY schema_name
                        """
                        
                        result = conn.execute(text(query))
                        schemas = [row[0] for row in result.fetchall()]
                        
                        print(f"成功使用编码 {enc} 获取到 {len(schemas)} 个schema")
                        return schemas
                        
                except Exception as e:
                    print(f"编码 {enc} 失败: {str(e)}")
                    last_error = e
                    continue
            
            # 如果所有编码都失败，返回默认的public schema
            print(f"所有编码尝试失败，返回默认schema。最后错误: {last_error}")
            return ['public']
            
        except Exception as e:
            print(f"获取schema列表失败: {str(e)}")
            # 返回默认schema而不是抛出异常
            return ['public']
    
    @staticmethod
    def get_tables(db_config):
        """获取数据库表列表（包含描述），自动尝试多种编码"""
        try:
            encodings = ['utf8', 'gbk', 'latin1']
            last_error = None
            
            # 获取schema，默认为public
            schema = db_config.get('schema', 'public')
            
            for enc in encodings:
                try:
                    connection_string = DatabaseService.get_connection_string(db_config, enc)
                    engine = create_engine(
                        connection_string, 
                        connect_args={'client_encoding': enc},
                        pool_pre_ping=True,
                        echo=False
                    )
                    
                    with engine.connect() as conn:
                        try:
                            conn.execute(text(f"SET client_encoding = '{enc}'"))
                        except Exception as enc_error:
                            print(f"设置编码 {enc} 失败，使用默认编码: {str(enc_error)}")
                        
                        # 查询表名和描述，使用动态schema
                        query = """
                        SELECT 
                            c.relname as table_name,
                            COALESCE(d.description, '') as table_description
                        FROM pg_class c
                        LEFT JOIN pg_description d ON c.oid = d.objoid AND d.objsubid = 0
                        WHERE c.relkind = 'r' 
                        AND c.relnamespace = (SELECT oid FROM pg_namespace WHERE nspname = :schema)
                        ORDER BY c.relname
                        """
                        
                        result = conn.execute(text(query), {'schema': schema})
                        tables = []
                        for row in result.fetchall():
                            tables.append({
                                'name': row[0],
                                'description': row[1] if row[1] else row[0]  # 如果没有描述，使用表名
                            })
                        
                        print(f"成功使用编码 {enc} 从schema '{schema}' 获取到 {len(tables)} 个表（含描述）")
                        return tables
                        
                except Exception as e:
                    print(f"编码 {enc} 失败: {str(e)}")
                    last_error = e
                    continue
            
            raise Exception(f"所有编码尝试失败，最后错误: {last_error}")
            
        except Exception as e:
            print(f"获取表列表失败: {str(e)}")
            raise e
    
    @staticmethod
    def get_table_fields(db_config, table_name):
        """获取表字段信息（包含描述）"""
        try:
            # 尝试多种编码获取字段信息
            encodings = ['utf8', 'gbk', 'latin1']
            last_error = None
            
            # 获取schema，默认为public
            schema = db_config.get('schema', 'public')
            
            for enc in encodings:
                try:
                    connection_string = DatabaseService.get_connection_string(db_config, enc)
                    engine = create_engine(connection_string, connect_args={'client_encoding': enc})
                    
                    with engine.connect() as conn:
                        conn.execute(text(f"SET client_encoding = '{enc}'"))
                        
                        # 查询字段名、类型和描述，使用动态schema
                        query = """
                        SELECT 
                            a.attname as column_name,
                            pg_catalog.format_type(a.atttypid, a.atttypmod) as data_type,
                            a.attnotnull as not_null,
                            COALESCE(pg_catalog.col_description(c.oid, a.attnum), '') as column_description
                        FROM pg_catalog.pg_attribute a
                        JOIN pg_catalog.pg_class c ON a.attrelid = c.oid
                        JOIN pg_catalog.pg_namespace n ON c.relnamespace = n.oid
                        WHERE c.relname = :table_name
                        AND n.nspname = :schema
                        AND a.attnum > 0
                        AND NOT a.attisdropped
                        ORDER BY a.attnum
                        """
                        
                        result = conn.execute(text(query), {'table_name': table_name, 'schema': schema})
                        
                        fields = []
                        for row in result.fetchall():
                            field = {
                                'name': row[0],
                                'type': row[1],
                                'nullable': not row[2],
                                'description': row[3] if row[3] else row[0],  # 如果没有描述，使用字段名
                                'primary_key': False,
                                'default': None
                            }
                            fields.append(field)
                        
                        print(f"成功使用编码 {enc} 从schema '{schema}' 获取到 {len(fields)} 个字段（含描述）")
                        return fields
                        
                except Exception as e:
                    last_error = e
                    print(f"使用编码 {enc} 获取字段失败: {str(e)}")
                    continue
            
            raise last_error
            
        except Exception as e:
            raise Exception(f"获取表字段失败: {str(e)}")
    
    @staticmethod
    def read_data_in_batches(db_config, table_name, fields=None, batch_size=10000, max_rows=None, schema='public', filters=None, start_date=None, end_date=None, date_column='update_date'):
        """
        分批读取大数据集，避免内存溢出
        
        Args:
            db_config: 数据库配置
            table_name: 表名
            fields: 字段列表
            batch_size: 每批次大小
            max_rows: 最大读取行数（None表示不限制，但会智能采样）
            schema: schema名称
            filters: 字段过滤条件字典 {field_name: value}
            start_date: 开始日期（格式：YYYY-MM-DD），筛选date_column >= start_date
            end_date: 结束日期（格式：YYYY-MM-DD），筛选date_column <= end_date
            date_column: 用于时间范围筛选的列名，默认为'update_date'
            
        Returns:
            generator: 返回DataFrame批次的生成器
        """
        import logging
        logger = logging.getLogger(__name__)
        
        # 尝试多种编码
        encodings = ['utf8', 'gbk']
        last_error = None
        
        for encoding in encodings:
            try:
                logger.info(f"尝试使用编码 {encoding} 分批读取数据: 表={table_name}, 批次大小={batch_size}, 最大行数={max_rows}")
                
                connection_string = DatabaseService.get_connection_string(db_config, encoding)
                engine = DatabaseService.create_engine(connection_string)
                
                # 设置数据库客户端编码
                try:
                    with engine.connect() as test_conn:
                        if encoding == 'utf8':
                            test_conn.execute(text("SET client_encoding = 'UTF8'"))
                        elif encoding == 'gbk':
                            test_conn.execute(text("SET client_encoding = 'GBK'"))
                        logger.info(f"成功设置数据库客户端编码为 {encoding}")
                except Exception as enc_error:
                    logger.warning(f"设置编码 {encoding} 失败，使用默认编码: {str(enc_error)}")
                
                # 尝试读取第一批数据验证编码是否正确
                # 创建生成器并尝试获取第一个批次
                gen = DatabaseService._read_data_in_batches_with_engine(
                    engine, table_name, fields, batch_size, max_rows, schema, logger, filters, start_date, end_date, date_column
                )
                
                # 测试第一个批次，验证编码
                try:
                    first_batch = next(gen)
                    # 如果成功，先yield第一个批次，然后yield剩余的
                    def yield_all():
                        yield first_batch
                        for batch in gen:
                            yield batch
                    return yield_all()
                except StopIteration:
                    # 如果没有数据，返回空生成器
                    return iter([])
                
            except UnicodeDecodeError as e:
                last_error = f"'{encoding}' codec can't decode: {str(e)}"
                logger.warning(f"编码 {encoding} 失败: {last_error}")
                try:
                    engine.dispose()
                except:
                    pass
                continue
            except Exception as e:
                last_error = str(e)
                logger.error(f"使用编码 {encoding} 读取数据失败: {last_error}")
                try:
                    engine.dispose()
                except:
                    pass
                # 如果不是编码问题，直接抛出异常
                if 'decode' not in str(e).lower() and 'codec' not in str(e).lower():
                    raise
                continue
        
        # 所有编码都失败
        raise Exception(f"所有编码尝试失败，最后错误: {last_error}")
    
    @staticmethod
    def _read_data_in_batches_with_engine(engine, table_name, fields=None, batch_size=10000, max_rows=None, schema='public', logger=None, filters=None, start_date=None, end_date=None, date_column='update_date'):
        """使用指定的engine分批读取数据"""
        if logger is None:
            import logging
            logger = logging.getLogger(__name__)
        
        try:
            quoted_table_name = DatabaseService.quote_identifier(table_name)
            effective_schema = schema if (schema and isinstance(schema, str) and schema.strip()) else 'public'
            
            if effective_schema != 'public':
                quoted_schema = DatabaseService.quote_identifier(effective_schema)
                full_table_name = f"{quoted_schema}.{quoted_table_name}"
            else:
                full_table_name = quoted_table_name
            
            # --- 构建过滤条件 ---
            where_clause = ""
            conditions = []
            
            # 处理字段过滤条件
            if filters and isinstance(filters, dict):
                for f_name, f_val in filters.items():
                    if f_name and f_val is not None:
                        q_field = DatabaseService.quote_identifier(f_name)
                        # 简单防注入处理
                        safe_val = str(f_val).replace("'", "''") 
                        conditions.append(f"{q_field} = '{safe_val}'")
            
            # 处理时间范围过滤条件
            if start_date or end_date:
                quoted_date_column = DatabaseService.quote_identifier(date_column)
                if start_date:
                    # 简单防注入处理
                    safe_start_date = str(start_date).replace("'", "''")
                    conditions.append(f"{quoted_date_column} >= '{safe_start_date}'")
                    logger.info(f"添加开始日期过滤: {quoted_date_column} >= '{safe_start_date}'")
                if end_date:
                    # 简单防注入处理
                    safe_end_date = str(end_date).replace("'", "''")
                    conditions.append(f"{quoted_date_column} <= '{safe_end_date}'")
                    logger.info(f"添加结束日期过滤: {quoted_date_column} <= '{safe_end_date}'")
            
            if conditions:
                where_clause = "WHERE " + " AND ".join(conditions)
            # -------------------

            # [优化] 移除 SELECT COUNT(*) 查询，直接按需读取
            # 旧逻辑：先Count再采样(Sampling)，会导致大表卡死且不符合"限制数据量"的直觉
            # 新逻辑：直接 LIMIT 方式分批读取前 N 条 (Sequential Reading)
            
            if fields:
                quoted_fields = [DatabaseService.quote_identifier(field) for field in fields]
                field_list = ', '.join(quoted_fields)
                base_query = f"SELECT {field_list} FROM {full_table_name} {where_clause}"
            else:
                base_query = f"SELECT * FROM {full_table_name} {where_clause}"
            
            offset = 0
            total_yielded = 0
            
            # 循环读取直到达到 max_rows 或数据读完
            while max_rows is None or total_yielded < max_rows:
                try:
                    # 计算当前批次需要读取的条数
                    current_limit = batch_size
                    if max_rows is not None:
                        remaining = max_rows - total_yielded
                        if remaining < batch_size:
                            current_limit = remaining
                    
                    # 直接使用 LIMIT OFFSET 进行分批读取
                    query = f"{base_query} LIMIT {current_limit} OFFSET {offset}"
                    
                    df_batch = pd.read_sql(query, engine)
                    
                    if df_batch.empty:
                        break
                    
                    rows_fetched = len(df_batch)
                    total_yielded += rows_fetched
                    offset += rows_fetched
                    
                    yield df_batch
                    
                    # 如果读取到的数据少于请求的限制，说明数据已经读完了
                    if rows_fetched < current_limit:
                        break
                        
                except Exception as batch_error:
                    logger.error(f"读取批次失败: {str(batch_error)}")
                    raise
            
            logger.info(f"分批读取完成，共读取 {total_yielded} 行")
            engine.dispose()
            
        except Exception as e:
            logger.error(f"分批读取数据失败: {str(e)}")
            raise Exception(f"分批读取数据失败: {str(e)}")
    
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
                        
                        # 构建完整的表名（包含schema）
                        schema = db_config.get('schema', 'public')
                        if schema and schema != 'public':
                            quoted_schema = DatabaseService.quote_identifier(schema)
                            full_table_name = f"{quoted_schema}.{quoted_table_name}"
                        else:
                            full_table_name = quoted_table_name
                        
                        if fields:
                            quoted_fields = [DatabaseService.quote_identifier(field) for field in fields]
                            field_list = ', '.join(quoted_fields)
                            if limit is None:
                                query = f"SELECT {field_list} FROM {full_table_name}"
                            else:
                                query = f"SELECT {field_list} FROM {full_table_name} LIMIT {limit}"
                        else:
                            if limit is None:
                                query = f"SELECT * FROM {full_table_name}"
                            else:
                                query = f"SELECT * FROM {full_table_name} LIMIT {limit}"
                        
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
                        
                        # 构建完整的表名（包含schema）
                        schema = db_config.get('schema', 'public')
                        if schema and schema != 'public':
                            quoted_schema = DatabaseService.quote_identifier(schema)
                            full_table_name = f"{quoted_schema}.{quoted_table_name}"
                        else:
                            full_table_name = quoted_table_name
                        
                        quoted_fields = [DatabaseService.quote_identifier(field) for field in fields]
                        field_list = ', '.join(quoted_fields)
                        query = f"SELECT {field_list} FROM {full_table_name}"
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
                        
                        # 构建完整的表名（包含schema）
                        schema = db_config.get('schema', 'public')
                        if schema and schema != 'public':
                            quoted_schema = DatabaseService.quote_identifier(schema)
                            full_table_name = f"{quoted_schema}.{quoted_table_name}"
                        else:
                            full_table_name = quoted_table_name
                        
                        # 构建查询语句获取不同值
                        query = f"SELECT DISTINCT {quoted_field_name} FROM {full_table_name} WHERE {quoted_field_name} IS NOT NULL ORDER BY {quoted_field_name} LIMIT {limit}"
                        
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
                        
                        # 构建完整的表名（包含schema）
                        schema = db_config.get('schema', 'public')
                        if schema and schema != 'public':
                            quoted_schema = DatabaseService.quote_identifier(schema)
                            full_table_name = f"{quoted_schema}.{quoted_table_name}"
                        else:
                            full_table_name = quoted_table_name
                        
                        # 构建字段列表
                        if fields:
                            quoted_fields = [DatabaseService.quote_identifier(field) for field in fields]
                            field_list = ', '.join(quoted_fields)
                        else:
                            field_list = '*'
                        
                        # 构建基本查询
                        query = f"SELECT {field_list} FROM {full_table_name}"
                        
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
    
    @staticmethod
    def get_tag_data(db_config, table_name, tag_code, tag_field_name='tag_code', limit=300, start_time=None, end_time=None, date_field='tag_time'):
        """获取TAG数据（用于生产数据质检的趋势图）
        
        强制实施数据量限制，保护生产环境数据库
        
        Args:
            db_config: 数据库配置
            table_name: 表名
            tag_code: TAG代码/字段值
            tag_field_name: TAG字段名（默认'tag_code'，支持动态字段）
            limit: 数据量限制（最大300）
            start_time: 开始时间（可选，格式：YYYY-MM-DD HH:MM:SS）
            end_time: 结束时间（可选，格式：YYYY-MM-DD HH:MM:SS）
            date_field: 时间字段名（默认'tag_time'）
        
        Returns:
            list: TAG数据列表，每条记录包含 tag_code, tag_time, tag_value
        """
        try:
            # 强制限制（防御性编程）
            # [优化] 确保 limit 是有效的整数，如果为None则默认为2000
            if limit is None:
                limit = 2000
            else:
                limit = min(int(limit), 2000)

            print(f"🔒 查询TAG数据: {tag_field_name}={tag_code}, limit={limit}")
            
            # 获取数据库连接
            connection_string = DatabaseService.get_connection_string(db_config, 'utf8')
            engine = DatabaseService.create_engine(connection_string)
            
            # 构建表名
            schema = db_config.get('schema', 'public')
            quoted_table = DatabaseService.quote_identifier(table_name)
            if schema and schema != 'public':
                quoted_schema = DatabaseService.quote_identifier(schema)
                full_table = f"{quoted_schema}.{quoted_table}"
            else:
                full_table = quoted_table
            
            # 引用字段名
            quoted_tag_field = DatabaseService.quote_identifier(tag_field_name)
            quoted_date_field = DatabaseService.quote_identifier(date_field)
            
            # 构建WHERE子句
            where_clauses = [f"{quoted_tag_field} = '{tag_code}'"]
            
            if start_time:
                where_clauses.append(f"{quoted_date_field} >= '{start_time}'")
            if end_time:
                where_clauses.append(f"{quoted_date_field} <= '{end_time}'")
            
            where_clause = " AND ".join(where_clauses)
            
            # 构建查询（使用倒序索引，获取最新数据）
            # 将选中的字段别名为 tag_code 以保持接口一致性
            query = f"""
                SELECT {quoted_tag_field} as tag_code, {quoted_date_field} as tag_time, tag_value
                FROM {full_table}
                WHERE {where_clause}
                ORDER BY {quoted_date_field} DESC
                LIMIT {limit}
            """
            
            print(f"执行查询: {query}")
            
            # 执行查询
            with engine.connect() as conn:
                df = pd.read_sql(text(query), conn)
            
            # 按时间正序排列（前端展示需要）
            df = df.sort_values('tag_time')
            
            print(f"✅ 成功获取 {len(df)} 条TAG数据")
            
            # 转换为字典列表
            return df.to_dict('records')
            
        except Exception as e:
            print(f"❌ 获取TAG数据失败: {str(e)}")
            import traceback
            traceback.print_exc()
            raise Exception(f"获取TAG数据失败: {str(e)}")
    
    @staticmethod
    def detect_anomalies(db_config, table_name, tag_code, tag_field_name='tag_code',
                        gap_thres=60, win_sec=300, z_win=50, z_thres=2.0,
                        limit=10000, start_time=None, end_time=None, date_field='tag_time'):
        """检测生产数据异常（数据丢失、断流、数值异常）
        
        强制实施数据量限制，保护生产环境数据库
        
        Args:
            db_config: 数据库配置
            table_name: 表名
            tag_code: TAG代码/字段值
            tag_field_name: TAG字段名（默认'tag_code'，支持动态字段）
            gap_thres: 数据丢失阈值（秒），默认60秒
            win_sec: 断流检测窗口（秒），默认300秒（5分钟）
            z_win: Z-Score窗口大小，默认50
            z_win: Z-Score阈值，默认2.0
            limit: 数据量限制（最大50000）
            start_time: 开始时间（可选）
            end_time: 结束时间（可选）
            date_field: 时间字段名（默认'tag_time'）
        
        Returns:
            dict: 包含 anomalies_list（异常列表） 和 chart_data（图表数据）
        """
        import numpy as np
        from datetime import datetime
        
        try:
            # 强制限制（防御性编程）
            MAX_LIMIT = 50000

            if limit is None:
                limit = MAX_LIMIT
                print(f"⚠️  前端请求全量数据，强制限制为 {MAX_LIMIT} 条以保护数据库")
            else:
                limit = min(int(limit), MAX_LIMIT)

            print(f"🔒 异常检测: {tag_field_name}={tag_code}, limit={limit}, "
                  f"gap_thres={gap_thres}s, win_sec={win_sec}s, z_win={z_win}, z_thres={z_thres}")
            
            # 1. 获取数据（使用更大的limit用于分析）
            tag_data = DatabaseService.get_tag_data(
                db_config, table_name, tag_code, tag_field_name,
                limit=limit,
                start_time=start_time,
                end_time=end_time,
                date_field=date_field
            )
            
            if not tag_data or len(tag_data) == 0:
                print("⚠️  未查询到数据")
                return {
                    'anomalies_list': [],
                    'chart_data': []
                }
            
            print(f"📊 开始分析 {len(tag_data)} 条数据...")
            
            # 2. 数据准备
            df = pd.DataFrame(tag_data)
            df['tag_time'] = pd.to_datetime(df['tag_time'])
            df = df.sort_values('tag_time').reset_index(drop=True)
            df['tag_value'] = pd.to_numeric(df['tag_value'], errors='coerce')
            
            anomalies = []
            
            # 3. 检测数据丢失（时间间隔超过阈值）
            print("🔍 检测数据丢失...")
            for i in range(1, len(df)):
                time_gap = (df.iloc[i]['tag_time'] - df.iloc[i-1]['tag_time']).total_seconds()
                if time_gap > gap_thres:
                    anomalies.append({
                        'code': tag_code,
                        'type': '数据丢失',
                        'timestamp': df.iloc[i]['tag_time'].strftime('%Y-%m-%d %H:%M:%S'),
                        'value': None,
                        'details': f'数据缺失 {int(time_gap)} 秒（阈值={gap_thres}秒）',
                        # 'row_index': i + 1,
                        'time_range': [
                            df.iloc[i-1]['tag_time'].strftime('%Y-%m-%d %H:%M:%S'),
                            df.iloc[i]['tag_time'].strftime('%Y-%m-%d %H:%M:%S')
                        ]
                    })
            
            # 4. 检测数据断流（窗口内数据点过少）
            print("🔍 检测数据断流...")
            # 将win_sec转换为数据点数量估算
            if len(df) >= 2:
                avg_interval = (df.iloc[-1]['tag_time'] - df.iloc[0]['tag_time']).total_seconds() / len(df)
                expected_points_in_window = max(int(win_sec / avg_interval), 1) if avg_interval > 0 else 1
                
                # 使用滚动窗口检测
                if len(df) >= expected_points_in_window:
                    df['rolling_count'] = df['tag_value'].rolling(
                        window=expected_points_in_window, 
                        min_periods=1
                    ).count()
                    
                    # 断流判断：窗口内有效数据点少于期望值的50%
                    zero_flow_threshold = expected_points_in_window * 0.5
                    zero_flow = df[df['rolling_count'] < zero_flow_threshold]
                    
                    for idx, row in zero_flow.iterrows():
                        anomalies.append({
                            'code': tag_code,
                            'type': '数据断流',
                            'timestamp': row['tag_time'].strftime('%Y-%m-%d %H:%M:%S'),
                            'value': float(row['tag_value']) if not pd.isna(row['tag_value']) else None,
                            'details': f'窗口内数据点数 {int(row["rolling_count"])} < 期望值 {int(zero_flow_threshold)}'
                            # 'row_index': idx + 1,
                        })
            
            # 5. 检测数值异常（Z-Score方法）
            print("🔍 检测数值异常...")
            df_clean = df.dropna(subset=['tag_value'])
            
            if len(df_clean) >= z_win:
                # 计算滚动统计量
                df_clean['rolling_mean'] = df_clean['tag_value'].rolling(
                    window=z_win, 
                    min_periods=1
                ).mean()
                df_clean['rolling_std'] = df_clean['tag_value'].rolling(
                    window=z_win, 
                    min_periods=1
                ).std()
                
                # 计算Z-Score（避免除以0）
                df_clean['z_score'] = np.abs(
                    (df_clean['tag_value'] - df_clean['rolling_mean']) / 
                    (df_clean['rolling_std'] + 1e-10)
                )
                
                # 找出异常值
                outliers = df_clean[df_clean['z_score'] > z_thres]
                
                for idx, row in outliers.iterrows():
                    anomalies.append({
                        'code': tag_code,
                        'type': '数据异常',
                        'timestamp': row['tag_time'].strftime('%Y-%m-%d %H:%M:%S'),
                        'value': float(row['tag_value']),
                        'details': f'Z-Score = {row["z_score"]:.2f} (阈值={z_thres})'
                        # 'row_index': idx + 1,
                    })
            
            # 6. 生成图表数据
            print("📈 生成图表数据...")
            chart_data = []
            anomaly_timestamps = {a['timestamp']: a['type'] for a in anomalies}
            
            for idx, row in df.iterrows():
                timestamp_str = row['tag_time'].strftime('%Y-%m-%d %H:%M:%S')
                chart_data.append({
                    'tag_time': timestamp_str,
                    'tag_value': float(row['tag_value']) if not pd.isna(row['tag_value']) else None,
                    'anomaly_type': anomaly_timestamps.get(timestamp_str)
                })
            
            print(f"✅ 异常检测完成: 发现 {len(anomalies)} 个异常")
            print(f"   - 数据丢失: {sum(1 for a in anomalies if a['type'] == '数据丢失')} 个")
            print(f"   - 数据断流: {sum(1 for a in anomalies if a['type'] == '数据断流')} 个")
            print(f"   - 数值异常: {sum(1 for a in anomalies if a['type'] == '数据异常')} 个")
            
            return {
                'anomalies_list': anomalies,
                'chart_data': chart_data
            }
            
        except Exception as e:
            print(f"❌ 异常检测失败: {str(e)}")
            import traceback
            traceback.print_exc()
            raise Exception(f"异常检测失败: {str(e)}")
    
    @staticmethod
    def get_well_parameter_sequence(db_config, table_name, well_id, parameter, 
                                     limit=10000, start_date=None, end_date=None, date_field=None):
        """获取井参数序列数据（用于LSTM异常检测）
        
        强制实施数据量限制，保护生产环境数据库
        
        Args:
            db_config: 数据库配置
            table_name: 表名
            well_id: 井ID
            parameter: 参数名称（字段名）
            limit: 数据量限制（最大50000）
            start_date: 开始日期（可选）
            end_date: 结束日期（可选）
            date_field: 用于时间筛选的字段名（可选，如果不提供则自动检测）
        
        Returns:
            list: 参数序列数据，每条记录包含 value, date_time_index 等字段
        """
        try:
            # 强制限制（防御性编程）
            MAX_LIMIT = 50000
            # [优化] 处理 limit=None 的情况
            if limit is None:
                limit = MAX_LIMIT
            else:
                limit = min(int(limit), MAX_LIMIT)
            print(f"🔒 查询井参数序列: well_id={well_id}, parameter={parameter}, limit={limit}")
            
            # 获取数据库连接
            connection_string = DatabaseService.get_connection_string(db_config, 'utf8')
            engine = DatabaseService.create_engine(connection_string)
            
            # 构建表名
            schema = db_config.get('schema', 'public')
            quoted_table = DatabaseService.quote_identifier(table_name)
            if schema and schema != 'public':
                quoted_schema = DatabaseService.quote_identifier(schema)
                full_table = f"{quoted_schema}.{quoted_table}"
            else:
                full_table = quoted_table
            
            # 构建字段名
            quoted_wid = DatabaseService.quote_identifier('wid')
            quoted_param = DatabaseService.quote_identifier(parameter)
            
            # 确定时间字段
            if date_field:
                # 用户指定了时间字段，直接使用
                time_field = date_field
                print(f"✅ 使用用户指定的时间字段: {time_field}")
            else:
                # 尝试自动找时间字段（常见的字段名）
                time_field_candidates = ['date_time_index', 'datetime', 'timestamp', 'time', 'date', 'update_date']
                time_field = None
                
                # 查询表结构找时间字段
                with engine.connect() as conn:
                    # 先检查表中有哪些字段
                    inspect_query = f"""
                        SELECT column_name 
                        FROM information_schema.columns 
                        WHERE table_name = '{table_name}'
                        AND table_schema = '{schema}'
                    """
                    df_columns = pd.read_sql(text(inspect_query), conn)
                    available_columns = df_columns['column_name'].tolist()
                    
                    # 找到第一个匹配的时间字段
                    for candidate in time_field_candidates:
                        if candidate in available_columns:
                            time_field = candidate
                            break
                    
                    if not time_field:
                        # 如果找不到时间字段，使用第一个看起来像日期的字段
                        for col in available_columns:
                            if any(keyword in col.lower() for keyword in ['date', 'time']):
                                time_field = col
                                break
                
                if not time_field:
                    time_field = 'date_time_index'  # 默认字段名
                    print(f"⚠️  未找到明确的时间字段，使用默认值: {time_field}")
            
            quoted_time = DatabaseService.quote_identifier(time_field)
            
            # 构建WHERE子句
            where_clauses = [f"{quoted_wid} = '{well_id}'"]
            
            if start_date:
                where_clauses.append(f"{quoted_time} >= '{start_date}'")
            if end_date:
                where_clauses.append(f"{quoted_time} <= '{end_date}'")
            
            where_clause = " AND ".join(where_clauses)
            
            # 构建查询（获取最新数据，按时间倒序）
            query = f"""
                SELECT {quoted_param} as value, {quoted_time} as date_time_index
                FROM {full_table}
                WHERE {where_clause}
                ORDER BY {quoted_time} DESC
                LIMIT {limit}
            """
            
            print(f"执行查询: {query}")
            
            # 执行查询
            with engine.connect() as conn:
                df = pd.read_sql(text(query), conn)
            
            # 按时间正序排列（模型需要）
            df = df.sort_values('date_time_index')
            
            print(f"✅ 成功获取 {len(df)} 条井参数数据")
            
            # 转换为字典列表
            return df.to_dict('records')
            
        except Exception as e:
            print(f"❌ 获取井参数序列失败: {str(e)}")
            import traceback
            traceback.print_exc()
            raise Exception(f"获取井参数序列失败: {str(e)}")
    
    # @staticmethod
    # def generate_anomaly_excel(anomalies, metadata):
    #     """生成异常检测Excel报告（通用）"""
    #     try:
    #         import io
    #         import pandas as pd
            
    #         if not anomalies:
    #             raise ValueError("没有异常数据可导出")
                
    #         # 转换为DataFrame
    #         df = pd.DataFrame(anomalies)
            
    #         # 统一列名映射
    #         column_mapping = {
    #             'row_index': '行号',       # [新增] 映射行号
    #             'field_name': '数据库字段',
    #             # DrillingData 字段
    #             'parameter': '参数名称',
    #             'rawValue': '异常数值',
    #             'unit': '单位',
    #             'type': '异常类型',
    #             'timestamp': '时间戳',
    #             # ProductData 字段
    #             'code': '点位代码',
    #             'value': '异常数值',
    #             'details': '详细描述',
    #             'time_range': '影响时段'
    #         }
            
    #         # 重命名
    #         df = df.rename(columns=column_mapping)
            
    #         # [修改] 调整列顺序，将“行号”放在最前面
    #         desired_order = [
    #             '行号', '数据库字段', '参数名称', '点位代码', 
    #             '异常数值', '单位', '异常类型', 
    #             '时间戳', '详细描述', '影响时段'
    #         ]
            
    #         # 重新排列列顺序
    #         existing_cols = [c for c in desired_order if c in df.columns]
    #         other_cols = [c for c in df.columns if c not in existing_cols]
    #         df = df[existing_cols + other_cols]
            
    #         # 创建 Excel
    #         output = io.BytesIO()
    #         with pd.ExcelWriter(output, engine='openpyxl') as writer:
    #             df.to_excel(writer, index=False, sheet_name='异常明细')
                
    #             if metadata:
    #                 meta_rows = []
    #                 for k, v in metadata.items():
    #                     meta_rows.append({'配置项': k, '内容': str(v)})
    #                 meta_df = pd.DataFrame(meta_rows)
    #                 meta_df.to_excel(writer, index=False, sheet_name='检测环境配置')
    #                 worksheet = writer.sheets['检测环境配置']
    #                 worksheet.column_dimensions['A'].width = 20
    #                 worksheet.column_dimensions['B'].width = 50
            
    #         output.seek(0)
    #         return output
            
    #     except Exception as e:
    #         raise Exception(f"生成Excel报告失败: {str(e)}")