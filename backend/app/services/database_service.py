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
        # 简化连接字符串，避免编码问题
        return f"postgresql://{db_config['username']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['database']}"
    
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
    def read_data_in_batches(db_config, table_name, fields=None, batch_size=10000, max_rows=None, schema='public'):
        """
        分批读取大数据集，避免内存溢出
        
        Args:
            db_config: 数据库配置
            table_name: 表名
            fields: 字段列表
            batch_size: 每批次大小
            max_rows: 最大读取行数（None表示不限制，但会智能采样）
            schema: schema名称
            
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
                    engine, table_name, fields, batch_size, max_rows, schema, logger
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
    def _read_data_in_batches_with_engine(engine, table_name, fields=None, batch_size=10000, max_rows=None, schema='public', logger=None):
        """使用指定的engine分批读取数据"""
        if logger is None:
            import logging
            logger = logging.getLogger(__name__)
        
        try:
            
            # 先获取总行数
            quoted_table_name = DatabaseService.quote_identifier(table_name)
            
            # 处理schema：以传入的schema参数为准（前端选择的），忽略db_config中的
            # 空字符串或None都视为public
            effective_schema = schema if (schema and isinstance(schema, str) and schema.strip()) else 'public'
            logger.info(f"使用schema: {effective_schema}, 表: {table_name}")
            
            # 如果schema不是public，构建完整的表引用 schema.table
            if effective_schema != 'public':
                quoted_schema = DatabaseService.quote_identifier(effective_schema)
                full_table_name = f"{quoted_schema}.{quoted_table_name}"
            else:
                full_table_name = quoted_table_name
            
            count_query = f"SELECT COUNT(*) as total FROM {full_table_name}"
            logger.info(f"执行COUNT查询: {count_query}")
            
            with engine.connect() as conn:
                result = conn.execute(text(count_query))
                total_rows = result.scalar()
                logger.info(f"表 {table_name} 总行数: {total_rows}")
            
            # 智能采样策略
            if max_rows and total_rows > max_rows:
                # 计算采样间隔
                sample_interval = total_rows // max_rows
                logger.info(f"数据量过大 ({total_rows} 行)，启用采样策略，采样间隔={sample_interval}")
                use_sampling = True
            else:
                use_sampling = False
                max_rows = total_rows
            
            # 构建查询
            if fields:
                quoted_fields = [DatabaseService.quote_identifier(field) for field in fields]
                field_list = ', '.join(quoted_fields)
                base_query = f"SELECT {field_list} FROM {full_table_name}"
            else:
                base_query = f"SELECT * FROM {full_table_name}"
            
            # 分批读取
            offset = 0
            batch_count = 0
            total_yielded = 0
            
            while offset < total_rows and (max_rows is None or total_yielded < max_rows):
                try:
                    if use_sampling:
                        # 采样模式：跳过一些行
                        query = f"{base_query} OFFSET {offset} LIMIT {batch_size}"
                        offset += batch_size * sample_interval
                    else:
                        # 正常模式：连续读取
                        query = f"{base_query} OFFSET {offset} LIMIT {batch_size}"
                        offset += batch_size
                    
                    # 读取批次数据
                    df_batch = pd.read_sql(query, engine)
                    
                    if df_batch.empty:
                        break
                    
                    batch_count += 1
                    total_yielded += len(df_batch)
                    logger.info(f"读取批次 {batch_count}: {len(df_batch)} 行 (累计: {total_yielded}/{max_rows or total_rows})")
                    
                    yield df_batch
                    
                    # 如果达到最大行数，停止
                    if max_rows and total_yielded >= max_rows:
                        logger.info(f"已达到最大行数限制: {max_rows}")
                        break
                        
                except Exception as batch_error:
                    logger.error(f"读取批次 {batch_count + 1} 失败: {str(batch_error)}")
                    raise
            
            logger.info(f"分批读取完成: 共 {batch_count} 个批次, {total_yielded} 行数据")
            
            # 确保引擎关闭
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
