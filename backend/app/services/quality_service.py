import pandas as pd
import time
import os
import psycopg2
from sqlalchemy import text
from app.models.quality_result import QualityResult, QualityReport
from app.models.rule_model import RuleLibrary, RuleVersion
from app.models.data_source import DataSource
from app.services.database_service import DatabaseService
from app.services.rule_service import RuleService
from app import db

class QualityService:
    """质量检测服务类"""
    
    # 定义报告存储目录
    REPORT_DIR = os.path.join(os.getcwd(), 'reports', 'quality')
    
    @staticmethod
    def ensure_report_dir():
        """确保报告目录存在"""
        if not os.path.exists(QualityService.REPORT_DIR):
            os.makedirs(QualityService.REPORT_DIR)

    @staticmethod
    def run_quality_check(rule_library_id, version_id, db_config, table_name, fields=None, created_by="", limit=None):
        """运行质量检测（并自动保存全量报告）"""
        start_time = time.time()
        
        try:
            # 获取规则库和版本
            library = RuleLibrary.query.get(rule_library_id)
            if not library:
                raise ValueError("规则库不存在")
            
            version = None
            if version_id:
                version = RuleVersion.query.get(version_id)
            
            # 1. 获取真实密码（解决前端传 ****** 的问题）
            real_password = db_config.get('password')
            if not real_password or real_password == '******':
                source_id = db_config.get('id')
                if source_id:
                    ds = DataSource.query.get(source_id)
                    if ds:
                        real_password = ds.password
                    else:
                        raise ValueError(f"找不到ID为 {source_id} 的数据源")
                else:
                    raise ValueError("未提供数据源ID且密码被掩码，无法连接数据库")

            # 2. 准备数据读取
            # 构建查询语句
            quoted_table_name = DatabaseService.quote_identifier(table_name)
            schema = db_config.get('schema', 'public')
            target_schema = schema if schema else 'public'
            quoted_schema = DatabaseService.quote_identifier(target_schema)
            full_table_name = f"{quoted_schema}.{quoted_table_name}"
            
            if fields:
                quoted_fields = [DatabaseService.quote_identifier(field) for field in fields]
                field_list = ', '.join(quoted_fields)
                query = f"SELECT {field_list} FROM {full_table_name}"
            else:
                query = f"SELECT * FROM {full_table_name}"
            
            if limit is not None and int(limit) > 0:
                query += f" LIMIT {int(limit)}"
            
            # 3. 执行数据读取（多编码重试机制）
            # 使用 psycopg2 直连，避开 SQLAlchemy 的复杂封装，确保编码设置生效
            encodings = ['utf8', 'gbk', 'latin1']
            df = None
            used_encoding = None
            last_error = None
            
            print(f"开始读取数据，表: {full_table_name}, 限制: {limit}")
            
            for enc in encodings:
                conn = None
                try:
                    # 映射 Postgres 编码名称
                    pg_enc = 'LATIN1' if enc == 'latin1' else ('GBK' if enc.lower() == 'gbk' else 'UTF8')
                    
                    conn = psycopg2.connect(
                        host=db_config['host'],
                        port=int(db_config['port']),
                        database=db_config['database'],
                        user=db_config['username'],
                        password=real_password,
                        client_encoding=pg_enc
                    )
                    
                    # 双重保险：执行 SET 命令
                    with conn.cursor() as cursor:
                        cursor.execute(f"SET client_encoding TO '{pg_enc}'")
                    
                    # 读取数据
                    df = pd.read_sql(query, conn)
                    
                    print(f"检测阶段：成功使用编码 {enc} 读取到 {len(df)} 行数据")
                    used_encoding = enc
                    break
                except Exception as e:
                    print(f"检测阶段：编码 {enc} 读取失败: {str(e)}")
                    last_error = e
                    continue
                finally:
                    if conn:
                        conn.close()
            
            if df is None:
                raise Exception(f"无法读取数据，已尝试编码 {encodings}。错误: {str(last_error)}")

            # 4. 数据清洗
            # 如果使用了 latin1 兜底，尝试修复乱码
            if used_encoding == 'latin1':
                print("正在尝试修复 Latin1 乱码...")
                for col in df.select_dtypes(include=['object']).columns:
                    new_vals = []
                    for val in df[col]:
                        if isinstance(val, str):
                            try:
                                # 尝试还原为 UTF-8
                                new_vals.append(val.encode('latin1').decode('utf-8'))
                            except:
                                try:
                                    # 尝试还原为 GBK
                                    new_vals.append(val.encode('latin1').decode('gbk'))
                                except:
                                    # 无法修复，保留原样或替换
                                    new_vals.append(val.encode('latin1').decode('utf-8', errors='replace'))
                        else:
                            new_vals.append(val)
                    df[col] = new_vals

            # 填充空值，避免后续处理报错
            df = df.fillna(0)
            
            total_records = len(df)
            
            # 5. 获取规则并执行验证
            if version:
                rules = version.get_rules()
            else:
                rules = RuleService.get_latest_rules(rule_library_id)
            
            all_failed_records = set()
            reports = []
            
            # 记录每行的错误信息 {row_index: [errors]}
            row_errors = {i: [] for i in range(total_records)}
            
            for rule in rules:
                validation_result = RuleService.validate_rule_detailed(rule, df)
                
                rule_passed = validation_result.get('passed_count', 0)
                rule_failed = validation_result.get('failed_count', 0)
                failed_indices = validation_result.get('failed_indices', [])
                error_details = validation_result.get('error_details', [])
                
                # 记录总的失败行
                all_failed_records.update(failed_indices)
                
                # 将详细错误填入对应行
                rule_name = rule.get('name', rule.get('rule_type', '未知规则'))
                for err in error_details:
                    idx = err.get('row')
                    msg = err.get('message', '验证失败')
                    if idx is not None:
                        try:
                            idx = int(idx)
                            if idx in row_errors:
                                row_errors[idx].append(f"[{rule_name}] {msg}")
                        except:
                            pass
                
                # 创建详细报告对象
                report = QualityReport(
                    rule_name=rule.get('name', ''),
                    rule_type=rule.get('rule_type', ''),
                    field_name=rule.get('field', ''),
                    passed_count=rule_passed,
                    failed_count=rule_failed
                )
                if rule_failed > 0:
                    report.set_error_details(error_details)
                reports.append(report)
            
            # 6. 计算统计结果
            failed_records = len(all_failed_records)
            passed_records = total_records - failed_records
            pass_rate = (passed_records / total_records) * 100 if total_records > 0 else 0
            execution_time = time.time() - start_time
            
            # 7. 保存结果记录
            result = QualityResult(
                rule_library_id=rule_library_id,
                data_source=db_config.get('name', 'unknown'),
                table_name=table_name,
                total_records=total_records,
                passed_records=passed_records,
                failed_records=failed_records,
                pass_rate=pass_rate,
                execution_time=execution_time,
                created_by=created_by
            )
            
            db.session.add(result)
            db.session.flush()  # 获取 result.id
            
            # 8. 生成全量 Excel 报告并保存到本地
            try:
                QualityService.ensure_report_dir()
                
                # 准备导出数据
                export_df = df.copy()
                
                # 插入质检状态列
                export_df.insert(0, '异常详情', export_df.index.map(lambda x: ' ; '.join(row_errors[x]) if row_errors[x] else ''))
                export_df.insert(0, '质检状态', export_df.index.map(lambda x: '异常' if x in all_failed_records else '正常'))
                
                # 生成文件名
                filename = f"quality_report_{result.id}_{int(time.time())}.xlsx"
                file_path = os.path.join(QualityService.REPORT_DIR, filename)
                
                # 保存为 Excel
                export_df.to_excel(file_path, index=False)
                
                # 更新数据库中的文件路径
                result.report_file_path = file_path
                print(f"全量报告已生成并保存: {file_path}")
                
            except Exception as file_error:
                print(f"生成全量报告文件失败: {str(file_error)}")
                # 不阻断主流程，仅打印错误
            
            # 保存详细报告数据
            for report in reports:
                report.result_id = result.id
                db.session.add(report)
            
            db.session.commit()
            
            return result.to_dict()
            
        except Exception as e:
            db.session.rollback()
            import traceback
            traceback.print_exc()
            raise Exception(f"质量检测失败: {str(e)}")
    
    @staticmethod
    def get_quality_results(rule_library_id=None, limit=50):
        """获取质量检测结果"""
        query = QualityResult.query
        
        if rule_library_id:
            query = query.filter_by(rule_library_id=rule_library_id)
        
        results = query.order_by(QualityResult.created_at.desc()).limit(limit).all()
        return [result.to_dict() for result in results]
    
    @staticmethod
    def get_quality_report(result_id):
        """获取质量检测详细报告"""
        result = QualityResult.query.get(result_id)
        if not result:
            raise ValueError("质量检测结果不存在")
        
        reports = QualityReport.query.filter_by(result_id=result_id).all()
        
        # 构建前端期望的数据结构
        rule_results = []
        for report in reports:
            rule_result = {
                'rule_name': report.rule_name,
                'rule_type': report.rule_type,
                'field_name': report.field_name,
                'passed_count': report.passed_count,
                'failed_count': report.failed_count,
                'pass_rate': round((report.passed_count / (report.passed_count + report.failed_count)) * 100, 2) if (report.passed_count + report.failed_count) > 0 else 0,
                'error_details': report.get_error_details(),
                'created_at': report.created_at.strftime('%Y-%m-%d %H:%M:%S') if report.created_at else '',
                'status': 'failed' if report.failed_count > 0 else 'passed'
            }
            rule_results.append(rule_result)
        
        # 构建完整的报告详情
        report_detail = {
            'id': result.id,
            'table_name': result.table_name,
            'data_source': result.data_source,
            'rule_library_name': getattr(result, 'rule_library_name', ''),
            'version': getattr(result, 'version', ''),
            'total_records': result.total_records,
            'passed_records': result.passed_records,
            'failed_records': result.failed_records,
            'pass_rate': result.pass_rate,
            'execution_time': result.execution_time,
            'created_at': result.created_at.strftime('%Y-%m-%d %H:%M:%S') if result.created_at else '',
            'created_by': result.created_by,
            'check_type': result.check_type,
            'rule_results': rule_results,
            'report_file_path': result.report_file_path,
            'summary': {
                'total_rules': len(reports),
                'passed_rules': len([r for r in reports if r.failed_count == 0]),
                'failed_rules': len([r for r in reports if r.failed_count > 0]),
                'avg_rule_pass_rate': round(sum([r['pass_rate'] for r in rule_results]) / len(rule_results), 2) if rule_results else 0
            }
        }
        
        return report_detail
    
    @staticmethod
    def compare_quality_results(result_id_1, result_id_2):
        """比较两个质量检测结果"""
        result_1 = QualityResult.query.get(result_id_1)
        result_2 = QualityResult.query.get(result_id_2)
        
        if not result_1 or not result_2:
            raise ValueError("质量检测结果不存在")
        
        # 获取详细报告
        reports_1 = QualityReport.query.filter_by(result_id=result_id_1).all()
        reports_2 = QualityReport.query.filter_by(result_id=result_id_2).all()
        
        # 比较结果
        comparison = {
            'result_1': result_1.to_dict(),
            'result_2': result_2.to_dict(),
            'differences': {
                'pass_rate_diff': result_2.pass_rate - result_1.pass_rate,
                'passed_records_diff': result_2.passed_records - result_1.passed_records,
                'failed_records_diff': result_2.failed_records - result_1.failed_records,
                'execution_time_diff': result_2.execution_time - result_1.execution_time
            },
            'reports_1': [report.to_dict() for report in reports_1],
            'reports_2': [report.to_dict() for report in reports_2]
        }
        
        return comparison
    
    @staticmethod
    def get_failed_records(result_id):
        """获取质量检测失败记录的详细数据"""
        result = QualityResult.query.get(result_id)
        if not result:
            raise ValueError("质量检测结果不存在")
        
        reports = QualityReport.query.filter_by(result_id=result_id).all()
        
        failed_records = []
        for report in reports:
            if report.failed_count > 0:
                error_details = report.get_error_details()
                for error in error_details:
                    failed_record = {
                        'rule_name': report.rule_name,
                        'rule_type': report.rule_type,
                        'field_name': report.field_name,
                        'row_number': error.get('row', ''),
                        'value': error.get('value', ''),
                        'depth': error.get('depth', ''),
                        'error_message': error.get('message', ''),
                        'table_name': result.table_name,
                        'data_source': result.data_source,
                        'check_date': result.created_at.strftime('%Y-%m-%d %H:%M:%S')
                    }
                    failed_records.append(failed_record)
        
        return {
            'total_failed_records': len(failed_records),
            'records': failed_records,
            'summary': {
                'result_id': result_id,
                'table_name': result.table_name,
                'data_source': result.data_source,
                'total_records': result.total_records,
                'failed_records': result.failed_records,
                'pass_rate': result.pass_rate,
                'check_date': result.created_at.strftime('%Y-%m-%d %H:%M:%S')
            }
        }
    
    @staticmethod
    def batch_quality_check(rule_library_id, version_id, db_config, tables, fields_map=None, created_by=""):
        """批量质量检测"""
        results = []
        
        for table_name in tables:
            try:
                fields = fields_map.get(table_name) if fields_map else None
                result = QualityService.run_quality_check(
                    rule_library_id, version_id, db_config, table_name, fields, created_by
                )
                results.append(result)
            except Exception as e:
                # 记录错误但继续处理其他表
                results.append({
                    'table_name': table_name,
                    'error': str(e),
                    'status': 'failed'
                })
        
        return results
    
    @staticmethod
    def get_quality_statistics(rule_library_id=None, days=30):
        """获取质量检测统计信息"""
        from datetime import datetime, timedelta
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        query = QualityResult.query.filter(QualityResult.created_at >= start_date)
        
        if rule_library_id:
            query = query.filter_by(rule_library_id=rule_library_id)
        
        results = query.all()
        
        if not results:
            return {
                'total_checks': 0,
                'avg_pass_rate': 0,
                'avg_execution_time': 0,
                'total_records_checked': 0
            }
        
        total_checks = len(results)
        avg_pass_rate = sum(r.pass_rate for r in results) / total_checks
        avg_execution_time = sum(r.execution_time for r in results) / total_checks
        total_records_checked = sum(r.total_records for r in results)
        
        return {
            'total_checks': total_checks,
            'avg_pass_rate': avg_pass_rate,
            'avg_execution_time': avg_execution_time,
            'total_records_checked': total_records_checked
        }
    
    @staticmethod
    def get_anomaly_data(result_id=None, limit=100):
        """获取异常数据"""
        try:
            if result_id:
                # 获取特定结果的异常数据
                result = QualityResult.query.get(result_id)
                if not result:
                    raise ValueError("质量检测结果不存在")
                
                # 获取失败的报告
                failed_reports = QualityReport.query.filter_by(
                    result_id=result_id
                ).filter(QualityReport.failed_count > 0).all()
                
                if not failed_reports:
                    return {'records': [], 'fields': []}
                
                # 从数据源配置获取实际的数据库连接信息
                from app.models.data_source import DataSource
                
                # 尝试通过数据源名称找到对应的数据源配置
                data_source = DataSource.query.filter_by(name=result.data_source).first()
                if not data_source:
                    # 如果找不到数据源，抛出异常
                    raise ValueError(f"找不到数据源配置: {result.data_source}")
                
                db_config = {
                    'db_type': data_source.db_type,
                    'host': data_source.host,
                    'port': data_source.port,
                    'database': data_source.database,
                    'schema': getattr(data_source, 'schema', 'public'),
                    'username': data_source.username,
                    'password': data_source.password
                }
                
                engine = DatabaseService.get_connection_string(db_config, 'utf8')
                
                # 构建查询，获取包含异常的记录
                fields = [report.field_name for report in failed_reports]
                unique_fields = list(set(fields))
                
                if unique_fields:
                    # 使用引号包装表名和字段名
                    quoted_table_name = DatabaseService.quote_identifier(result.table_name)
                    
                    # 构建完整的表名（包含schema）
                    schema = db_config.get('schema', 'public')
                    if schema and schema != 'public':
                        quoted_schema = DatabaseService.quote_identifier(schema)
                        full_table_name = f"{quoted_schema}.{quoted_table_name}"
                    else:
                        full_table_name = quoted_table_name
                    
                    quoted_fields = [DatabaseService.quote_identifier(field) for field in unique_fields]
                    field_list = ', '.join(quoted_fields)
                    query = f"SELECT {field_list} FROM {full_table_name} LIMIT {limit}"
                    df = pd.read_sql(query, engine)
                    
                    # 简单的异常检测：空值、重复值等
                    anomaly_records = []
                    for _, row in df.iterrows():
                        is_anomaly = False
                        for field in unique_fields:
                            if pd.isna(row[field]) or row[field] == '' or row[field] is None:
                                is_anomaly = True
                                break
                        
                        if is_anomaly:
                            anomaly_records.append(row.to_dict())
                    
                    return {
                        'records': anomaly_records[:limit],
                        'fields': unique_fields
                    }
            
            return {'records': [], 'fields': []}
            
        except Exception as e:
            # 记录错误并返回空结果
            print(f"获取异常数据失败: {str(e)}")
            return {
                'records': [],
                'fields': [],
                'error': f"获取异常数据失败: {str(e)}"
            }

    @staticmethod
    def delete_quality_result(result_id):
        """删除质量检测结果"""
        try:
            result = QualityResult.query.get(result_id)
            if not result: return False
            
            # 删除关联的物理文件
            if result.report_file_path and os.path.exists(result.report_file_path):
                try:
                    os.remove(result.report_file_path)
                except Exception as e:
                    print(f"删除报告文件失败: {e}")
                    
            QualityReport.query.filter_by(result_id=result_id).delete()
            db.session.delete(result)
            db.session.commit()
            return True
        except Exception as e:
            print(f"删除质量检测结果失败: {e}")
            db.session.rollback()
            return False

    @staticmethod
    def export_all_quality_data(result_id, schema=None):
        """导出全量数据（直接返回预生成的文件路径）"""
        try:
            result = QualityResult.query.get(result_id)
            if not result:
                raise ValueError("质量检测结果不存在")
            
            # 1. 优先检查是否有预生成的文件
            if result.report_file_path and os.path.exists(result.report_file_path):
                print(f"使用预生成的全量报告: {result.report_file_path}")
                return result.report_file_path
            
            # 2. 如果没有文件，提示用户重新运行
            # 这是因为旧数据的实时查询极其不稳定（如前所述的编码问题）
            raise ValueError("该记录未生成全量报告文件（可能是旧版本数据），请点击界面上的“开始检测”按钮重新运行一次即可生成。")
            
        except Exception as e:
            raise Exception(f"导出失败: {str(e)}")