import pandas as pd
import time
from app.models.quality_result import QualityResult, QualityReport
from app.models.rule_model import RuleLibrary, RuleVersion
from app.services.database_service import DatabaseService
from app.services.rule_service import RuleService
from app import db

class QualityService:
    """质量检测服务类"""
    
    @staticmethod
    def run_quality_check(rule_library_id, version_id, db_config, table_name, fields=None, created_by=""):
        """运行质量检测"""
        start_time = time.time()
        
        try:
            # 获取规则库和版本
            library = RuleLibrary.query.get(rule_library_id)
            if not library:
                raise ValueError("规则库不存在")
            
            # 版本可选：优先用版本；否则走无版本模式（获取最新规则）
            version = None
            if version_id:
                version = RuleVersion.query.get(version_id)
            
            # 导入DatabaseService以使用数据库相关方法
            from app.services.database_service import DatabaseService
            
            # 获取数据
            engine = DatabaseService.get_connection_string(db_config, 'utf8')
            
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
                query = f"SELECT {field_list} FROM {full_table_name}"
            else:
                query = f"SELECT * FROM {full_table_name}"
            
            df = pd.read_sql(query, engine)
            total_records = len(df)
            
            # 获取规则
            if version:
                rules = version.get_rules()
            else:
                rules = RuleService.get_latest_rules(rule_library_id)
            if not rules:
                raise ValueError("该规则库暂无规则，请先在规则生成页保存规则")
            
            # 执行规则验证
            all_failed_records = set()  # 使用集合避免重复计算失败记录
            reports = []
            
            for rule in rules:
                # 验证规则并获取详细结果
                validation_result = RuleService.validate_rule_detailed(rule, df)
                
                rule_passed = validation_result.get('passed_count', 0)
                rule_failed = validation_result.get('failed_count', 0)
                failed_indices = validation_result.get('failed_indices', [])
                
                # 将失败的记录索引添加到总集合中
                all_failed_records.update(failed_indices)
                
                # 创建详细报告
                report = QualityReport(
                    rule_name=rule.get('name', ''),
                    rule_type=rule.get('rule_type', ''),
                    field_name=rule.get('field', ''),
                    passed_count=rule_passed,
                    failed_count=rule_failed
                )
                
                if rule_failed > 0:
                    error_details = validation_result.get('error_details', [])
                    report.set_error_details(error_details)
                
                reports.append(report)
            
            # 计算最终的通过和失败记录数
            failed_records = len(all_failed_records)
            passed_records = total_records - failed_records
            
            # 计算通过率
            pass_rate = (passed_records / total_records) * 100 if total_records > 0 else 0
            execution_time = time.time() - start_time
            
            # 保存结果
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
            db.session.flush()  # 获取ID
            
            # 保存详细报告
            for report in reports:
                report.result_id = result.id
                db.session.add(report)
            
            db.session.commit()
            
            return result.to_dict()
            
        except Exception as e:
            db.session.rollback()
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
                'rule_expression': getattr(report, 'rule_expression', ''),
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
            # 查找质量检测结果
            result = QualityResult.query.get(result_id)
            if not result:
                return False
            
            # 删除相关的详细报告
            QualityReport.query.filter_by(result_id=result_id).delete()
            
            # 删除主结果
            db.session.delete(result)
            db.session.commit()
            
            return True
        except Exception as e:
            print(f"删除质量检测结果失败: {e}")
            db.session.rollback()
            return False 