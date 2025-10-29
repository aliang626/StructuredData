import pandas as pd
import numpy as np
from scipy import stats
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans, DBSCAN
from app.models.rule_model import RuleLibrary, RuleVersion
from app.services.database_service import DatabaseService
from app import db
import json
import warnings
from datetime import datetime
warnings.filterwarnings('ignore')

class RuleService:
    """规则服务类 - 基于统计分析的规则生成"""
    
    @staticmethod
    def generate_rules_from_data(db_config, table_name, fields, rule_type='range', depth_field=None, depth_interval=10, cluster_params=None, outlier_params=None, group_by_field=None, cluster_features=None, manual_ranges=None):
        """从数据生成规则
        
        Args:
            db_config: 数据库配置
            table_name: 表名
            fields: 字段列表
            rule_type: 规则类型，默认为'range'
            depth_field: 深度字段名（用于回归型数据分析）
            depth_interval: 深度区间大小（米）
        """
        
        # 如果是手工固定范围型，直接返回对应规则
        if rule_type == 'manual_range' and manual_ranges:
            rules = []
            try:
                for field in fields:
                    bounds = manual_ranges.get(field)
                    if not bounds:
                        continue
                    lower_bound = bounds.get('lower_bound')
                    upper_bound = bounds.get('upper_bound')
                    # 构建SQL和正则表达式
                    sql_conditions = []
                    lower_val = float(lower_bound) if lower_bound is not None else None
                    upper_val = float(upper_bound) if upper_bound is not None else None
                    
                    if lower_val is not None and upper_val is not None:
                        regex_pattern = f'(?=.*{field}.*(?:[0-9]*\\.?[0-9]+)).*({lower_val:.2f}|{upper_val:.2f}|(?:[0-9]*\\.?[0-9]+))'
                        sql_conditions.append(f'{field} >= {lower_val} AND {field} <= {upper_val}')
                    elif lower_val is not None:
                        regex_pattern = f'(?=.*{field}.*(?:[0-9]*\\.?[0-9]+)).*(?!({lower_val:.2f}|(?:[0-9]*\\.?[0-9]+)))'
                        sql_conditions.append(f'{field} >= {lower_val}')
                    elif upper_val is not None:
                        regex_pattern = f'(?=.*{field}.*(?:[0-9]*\\.?[0-9]+)).*(?!({upper_val:.2f}|(?:[0-9]*\\.?[0-9]+)))'
                        sql_conditions.append(f'{field} <= {upper_val}')
                    else:
                        regex_pattern = f'{field}_manual_range_pattern'
                        sql_conditions.append(f'{field} IS NOT NULL')
                    
                    validation_sql = f'SELECT * FROM {{table}} WHERE {" AND ".join(sql_conditions)}' if sql_conditions else f'SELECT * FROM {{table}} WHERE {field} IS NOT NULL'
                    
                    rule = {
                        'rule_type': 'range',
                        'field': field,
                        'name': f'{field}_manual_range',
                        'description': f'{field}字段固定范围检查',
                        'params': {
                            'method': 'manual',
                            'lower_bound': lower_val,
                            'upper_bound': upper_val
                        },
                        'regex_pattern': regex_pattern,
                        'validation_sql': validation_sql
                    }
                    rules.append(rule)
            except Exception as e:
                print(f"生成手工范围规则失败: {str(e)}")
            return rules

        # 获取完整数据用于高级分析
        try:
            connection_string = DatabaseService.get_connection_string(db_config, 'utf8')
            engine = DatabaseService.create_engine(connection_string)
            
            # 构建查询字段列表
            query_fields = fields.copy()
            if depth_field and depth_field not in query_fields:
                query_fields.append(depth_field)
            
            # 使用引号包装表名和字段名
            quoted_table_name = DatabaseService.quote_identifier(table_name)
            quoted_fields = [DatabaseService.quote_identifier(field) for field in query_fields]
            field_list = ', '.join(quoted_fields)
            query = f"SELECT {field_list} FROM {quoted_table_name}"
            df = pd.read_sql(query, engine)
            
        except Exception as e:
            # 如果无法获取完整数据，回退到基础统计信息
            statistics = DatabaseService.get_data_statistics(db_config, table_name, fields)
            return RuleService._generate_basic_rules(statistics, fields, rule_type)
        
        rules = []

        # 特殊：聚簇分组范围（例如按照分公司对经纬度/数值特征做范围统计）
        if rule_type == 'cluster_group_ranges' and group_by_field:
            try:
                # 如果没有显式指定特征，则使用传入 fields 作为特征
                features = cluster_features if cluster_features else [f for f in fields if f != group_by_field]

                # 需要的列：分组字段 + 特征字段
                required_cols = [group_by_field] + features
                df_required = df[required_cols].dropna()
                if not df_required.empty:
                    rules.extend(RuleService._generate_group_ranges_rules(df_required, group_by_field, features))
                return rules
            except Exception as e:
                print(f"生成分组范围规则失败: {str(e)}")
                return rules
        
        for field in fields:
            if field not in df.columns:
                continue
            
            field_data = df[field].dropna()
            if field_data.empty:
                continue
            
            # 判断数据类型
            is_numeric = pd.api.types.is_numeric_dtype(field_data)
            
            if is_numeric:
                # 数值型字段处理
                rules.extend(RuleService._generate_numeric_rules(
                    df, field, field_data, rule_type, depth_field, depth_interval
                ))
            else:
                # 分类型字段处理
                rules.extend(RuleService._generate_categorical_rules(
                    df, field, field_data, rule_type
                ))
        
        return rules
    
    @staticmethod
    def _generate_numeric_rules(df, field, field_data, rule_type, depth_field=None, depth_interval=10):
        """生成数值型字段规则"""
        rules = []
        
        # 1. 基础范围规则（基于全局统计）
        if rule_type == 'range':
            # 基础范围规则
            mean_val = field_data.mean()
            std_val = field_data.std()
            
            if std_val > 0:
                lower_bound = float(mean_val - 2 * std_val)
                upper_bound = float(mean_val + 2 * std_val)
                rule = {
                    'rule_type': 'range',
                    'field': field,
                    'name': f'{field}_range_check',
                    'description': f'{field}字段范围检查',
                    'params': {
                        'method': 'basic',
                        'mean': float(mean_val),
                        'std': float(std_val),
                        'lower_bound': lower_bound,
                        'upper_bound': upper_bound
                    },
                    'regex_pattern': f'(?=.*{field}.*(?:[0-9]*\\.?[0-9]+)).*({lower_bound:.2f}|{upper_bound:.2f}|(?:[0-9]*\\.?[0-9]+))',
                    'validation_sql': f'SELECT * FROM {{table}} WHERE {field} >= {lower_bound} AND {field} <= {upper_bound}'
                }
                rules.append(rule)
        elif rule_type == 'range_2sigma':
            # 2σ范围规则
            mean_val = field_data.mean()
            std_val = field_data.std()
            
            if std_val > 0:
                lower_bound = float(mean_val - 2 * std_val)
                upper_bound = float(mean_val + 2 * std_val)
                rule = {
                    'rule_type': 'range_2sigma',
                    'field': field,
                    'name': f'{field}_range_2sigma',
                    'description': f'{field}字段范围检查（均值±2σ）',
                    'params': {
                        'method': '2sigma',
                        'mean': float(mean_val),
                        'std': float(std_val),
                        'lower_bound': lower_bound,
                        'upper_bound': upper_bound
                    },
                    'regex_pattern': f'(?=.*{field}.*(?:[0-9]*\\.?[0-9]+)).*({lower_bound:.2f}|{upper_bound:.2f}|(?:[0-9]*\\.?[0-9]+))',
                    'validation_sql': f'SELECT * FROM {{table}} WHERE {field} >= {lower_bound} AND {field} <= {upper_bound}'
                }
                rules.append(rule)
        elif rule_type == 'range_percentile':
            # 百分位数范围规则
            q25 = field_data.quantile(0.25)
            q75 = field_data.quantile(0.75)
            lower_bound = float(q25)
            upper_bound = float(q75)
            rule = {
                'rule_type': 'range_percentile',
                'field': field,
                'name': f'{field}_range_percentile',
                'description': f'{field}字段范围检查（25%-75%分位数）',
                'params': {
                    'method': 'percentile',
                    'q25': float(q25),
                    'q75': float(q75),
                    'lower_bound': lower_bound,
                    'upper_bound': upper_bound
                },
                'regex_pattern': f'(?=.*{field}.*(?:[0-9]*\\.?[0-9]+)).*({lower_bound:.2f}|{upper_bound:.2f}|(?:[0-9]*\\.?[0-9]+))',
                'validation_sql': f'SELECT * FROM {{table}} WHERE {field} >= {lower_bound} AND {field} <= {upper_bound}'
            }
            rules.append(rule)
        
        # 2. 深度区间统计规则（回归型数据处理）
        elif rule_type == 'depth_interval':
            if depth_field and depth_field in df.columns:
                rules.extend(RuleService._generate_depth_interval_rules(
                    df, field, depth_field, depth_interval
                ))
        
        # 3. 异常值检测规则
        elif rule_type.startswith('outlier'):
            rules.extend(RuleService._generate_outlier_rules(field, field_data, rule_type))
        
        # 4. 聚簇分析规则
        elif rule_type.startswith('cluster'):
            rules.extend(RuleService._generate_cluster_rules(field, field_data, rule_type))
        
        return rules
    
    @staticmethod
    def _generate_depth_interval_rules(df, field, depth_field, depth_interval):
        """生成深度区间统计规则"""
        rules = []
        
        try:
            import logging
            logger = logging.getLogger(__name__)
            
            # 按深度区间分组
            df_clean = df[[depth_field, field]].dropna()
            logger.info(f"深度区间分析: 字段={field}, 深度字段={depth_field}, 清洗后数据量={len(df_clean)}")
            
            if df_clean.empty or len(df_clean) == 0:
                logger.warning(f"深度区间分析: 无有效数据")
                return rules
            
            # 创建深度区间
            min_depth = df_clean[depth_field].min()
            max_depth = df_clean[depth_field].max()
            logger.info(f"深度范围: {min_depth} - {max_depth}, 区间大小: {depth_interval}米")
            
            # 生成区间边界
            intervals = []
            current_depth = min_depth
            while current_depth < max_depth:
                intervals.append((current_depth, current_depth + depth_interval))
                current_depth += depth_interval
            
            logger.info(f"生成了 {len(intervals)} 个深度区间")
            
            interval_stats = []
            for start_depth, end_depth in intervals:
                interval_data = df_clean[
                    (df_clean[depth_field] >= start_depth) & 
                    (df_clean[depth_field] < end_depth)
                ][field]
                
                if not interval_data.empty and len(interval_data) > 0:
                    stats_info = {
                        'depth_range': f"{start_depth}-{end_depth}m",
                        'start_depth': float(start_depth),
                        'end_depth': float(end_depth),
                        'count': int(len(interval_data)),
                        'mean': float(interval_data.mean()),
                        'std': float(interval_data.std()),
                        'min': float(interval_data.min()),
                        'max': float(interval_data.max()),
                        'q05': float(interval_data.quantile(0.05)),
                        'q25': float(interval_data.quantile(0.25)),
                        'q75': float(interval_data.quantile(0.75)),
                        'q95': float(interval_data.quantile(0.95))
                    }
                    interval_stats.append(stats_info)
            
            logger.info(f"成功统计了 {len(interval_stats)} 个有效深度区间")
            
            if interval_stats:
                # 生成每个深度区间的正则表达式和SQL
                ranges_regex = []
                ranges_sql = []
                for stats in interval_stats:
                    start_depth = stats['start_depth']
                    end_depth = stats['end_depth']
                    mean_val = stats['mean']
                    std_val = stats['std']
                    
                    # 为每个区间生成范围规则
                    if std_val > 0:
                        lower_bound = mean_val - 2 * std_val
                        upper_bound = mean_val + 2 * std_val
                        ranges_regex.append(f'({depth_field}:{start_depth}-{end_depth},{field}:{lower_bound:.2f}-{upper_bound:.2f})')
                        ranges_sql.append(f'({depth_field} >= {start_depth} AND {depth_field} < {end_depth} AND {field} >= {lower_bound} AND {field} <= {upper_bound})')
                
                regex_pattern = '|'.join(ranges_regex) if ranges_regex else f'{field}_depth_interval_pattern'
                validation_sql = f'SELECT * FROM {{table}} WHERE {" OR ".join(ranges_sql)}' if ranges_sql else f'SELECT * FROM {{table}} WHERE {depth_field} IS NOT NULL AND {field} IS NOT NULL'
                
                rule = {
                    'rule_type': 'depth_interval_stats',
                    'field': field,
                    'name': f'{field}_depth_interval_stats',
                    'description': f'{field}字段按深度区间统计分析（每{depth_interval}米）',
                    'params': {
                        'depth_field': depth_field,
                        'interval_size': depth_interval,
                        'intervals': interval_stats
                    },
                    'regex_pattern': regex_pattern,
                    'validation_sql': validation_sql
                }
                rules.append(rule)
                logger.info(f"成功生成深度区间规则: {rule['name']}")
        
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"生成深度区间规则失败: {str(e)}", exc_info=True)
            print(f"生成深度区间规则失败: {str(e)}")
        
        return rules
    
    @staticmethod
    def _generate_outlier_rules(field, field_data, rule_type='outlier'):
        """生成异常值检测规则"""
        rules = []
        
        try:
            mean_val = field_data.mean()
            std_val = field_data.std()
            
            if rule_type == 'outlier' or rule_type == 'outlier_3sigma':
                # 3σ异常值检测
                if std_val > 0:
                    lower_bound = float(mean_val - 3 * std_val)
                    upper_bound = float(mean_val + 3 * std_val)
                    rule = {
                        'rule_type': 'outlier_3sigma',
                        'field': field,
                        'name': f'{field}_outlier_3sigma',
                        'description': f'{field}字段异常值检测（3σ原则）',
                        'params': {
                            'method': '3sigma',
                            'mean': float(mean_val),
                            'std': float(std_val),
                            'lower_bound': lower_bound,
                            'upper_bound': upper_bound
                        },
                        'regex_pattern': f'(?=.*{field}.*(?:[0-9]*\\.?[0-9]+)).*(?!({lower_bound:.2f}|{upper_bound:.2f}|(?:[0-9]*\\.?[0-9]+)))',
                        'validation_sql': f'SELECT * FROM {{table}} WHERE {field} < {lower_bound} OR {field} > {upper_bound}'
                    }
                    rules.append(rule)
            
            elif rule_type == 'outlier_iqr':
                # IQR异常值检测
                q25 = field_data.quantile(0.25)
                q75 = field_data.quantile(0.75)
                iqr = q75 - q25
                
                if iqr > 0:
                    lower_bound = float(q25 - 1.5 * iqr)
                    upper_bound = float(q75 + 1.5 * iqr)
                    rule = {
                        'rule_type': 'outlier_iqr',
                        'field': field,
                        'name': f'{field}_outlier_iqr',
                        'description': f'{field}字段异常值检测（IQR方法）',
                        'params': {
                            'method': 'iqr',
                            'q25': float(q25),
                            'q75': float(q75),
                            'iqr': float(iqr),
                            'lower_bound': lower_bound,
                            'upper_bound': upper_bound
                        },
                        'regex_pattern': f'(?=.*{field}.*(?:[0-9]*\\.?[0-9]+)).*(?!({lower_bound:.2f}|{upper_bound:.2f}|(?:[0-9]*\\.?[0-9]+)))',
                        'validation_sql': f'SELECT * FROM {{table}} WHERE {field} < {lower_bound} OR {field} > {upper_bound}'
                    }
                    rules.append(rule)
            
            elif rule_type == 'outlier_zscore':
                # Z-score异常值检测
                if std_val > 0:
                    lower_bound = float(mean_val - 2.5 * std_val)
                    upper_bound = float(mean_val + 2.5 * std_val)
                    rule = {
                        'rule_type': 'outlier_zscore',
                        'field': field,
                        'name': f'{field}_outlier_zscore',
                        'description': f'{field}字段异常值检测（Z-score方法）',
                        'params': {
                            'method': 'zscore',
                            'mean': float(mean_val),
                            'std': float(std_val),
                            'threshold': 2.5,  # Z-score阈值
                            'lower_bound': lower_bound,
                            'upper_bound': upper_bound
                        },
                        'regex_pattern': f'(?=.*{field}.*(?:[0-9]*\\.?[0-9]+)).*(?!({lower_bound:.2f}|{upper_bound:.2f}|(?:[0-9]*\\.?[0-9]+)))',
                        'validation_sql': f'SELECT * FROM {{table}} WHERE {field} < {lower_bound} OR {field} > {upper_bound}'
                    }
                    rules.append(rule)
        
        except Exception as e:
            print(f"生成异常值检测规则失败: {str(e)}")
        
        return rules
    
    @staticmethod
    def _generate_cluster_rules(field, field_data, rule_type='cluster'):
        """生成聚簇分析规则"""
        rules = []
        
        try:
            if len(field_data) < 10:  # 数据量太少，不适合聚类
                return rules
            
            # 数据预处理
            data_array = field_data.values.reshape(-1, 1)
            scaler = StandardScaler()
            data_scaled = scaler.fit_transform(data_array)
            
            if rule_type == 'cluster' or rule_type == 'cluster_kmeans':
                # K-means聚类分析
                optimal_k = min(5, len(field_data) // 3)  # 自动确定聚类数
                if optimal_k >= 2:
                    kmeans = KMeans(n_clusters=optimal_k, random_state=42, n_init=10)
                    cluster_labels = kmeans.fit_predict(data_scaled)
                    
                    # 计算每个聚类的统计信息
                    clusters_info = []
                    for i in range(optimal_k):
                        cluster_data = field_data[cluster_labels == i]
                        if not cluster_data.empty:
                            cluster_info = {
                                'cluster_id': int(i),
                                'count': int(len(cluster_data)),
                                'mean': float(cluster_data.mean()),
                                'std': float(cluster_data.std()),
                                'min': float(cluster_data.min()),
                                'max': float(cluster_data.max()),
                                'center': float(scaler.inverse_transform(kmeans.cluster_centers_[i].reshape(1, -1))[0][0])
                            }
                            clusters_info.append(cluster_info)
                    
                    # 生成聚类的正则表达式和SQL
                    cluster_ranges = []
                    for cluster in clusters_info:
                        center = cluster['center']
                        std = cluster['std']
                        if std > 0:
                            lower = center - 2 * std
                            upper = center + 2 * std
                            cluster_ranges.append(f'({field} >= {lower:.2f} AND {field} <= {upper:.2f})')
                    
                    regex_pattern = f'{field}_cluster_kmeans_pattern'
                    validation_sql = f'SELECT * FROM {{table}} WHERE {" OR ".join(cluster_ranges)}' if cluster_ranges else f'SELECT * FROM {{table}} WHERE {field} IS NOT NULL'
                    
                    rule = {
                        'rule_type': 'cluster_kmeans',
                        'field': field,
                        'name': f'{field}_cluster_kmeans',
                        'description': f'{field}字段K-means聚类分析（{optimal_k}个聚类）',
                        'params': {
                            'method': 'kmeans',
                            'n_clusters': optimal_k,
                            'clusters': clusters_info
                        },
                        'regex_pattern': regex_pattern,
                        'validation_sql': validation_sql
                    }
                    rules.append(rule)
            
            elif rule_type == 'cluster_dbscan':
                # DBSCAN密度聚类（用于异常值检测）
                if len(field_data) >= 20:  # DBSCAN需要更多数据
                    dbscan = DBSCAN(eps=0.5, min_samples=5)
                    cluster_labels = dbscan.fit_predict(data_scaled)
                    
                    # 统计噪声点（异常值）
                    noise_points = field_data[cluster_labels == -1]
                    normal_points = field_data[cluster_labels != -1]
                    
                    if not noise_points.empty:
                        # 生成DBSCAN规则的正则表达式和SQL（基于正常点的范围）
                        if not normal_points.empty:
                            normal_min = normal_points.min()
                            normal_max = normal_points.max()
                            regex_pattern = f'(?=.*{field}.*(?:[0-9]*\\.?[0-9]+)).*({normal_min:.2f}|{normal_max:.2f}|(?:[0-9]*\\.?[0-9]+))'
                            validation_sql = f'SELECT * FROM {{table}} WHERE {field} >= {normal_min} AND {field} <= {normal_max}'
                        else:
                            regex_pattern = f'{field}_dbscan_pattern'
                            validation_sql = f'SELECT * FROM {{table}} WHERE {field} IS NOT NULL'
                        
                        rule = {
                            'rule_type': 'cluster_dbscan',
                            'field': field,
                            'name': f'{field}_cluster_dbscan',
                            'description': f'{field}字段DBSCAN密度聚类异常检测',
                            'params': {
                                'method': 'dbscan',
                                'eps': 0.5,
                                'min_samples': 5,
                                'noise_count': int(len(noise_points)),
                                'normal_count': int(len(normal_points)),
                                'noise_ratio': float(len(noise_points) / len(field_data))
                            },
                            'regex_pattern': regex_pattern,
                            'validation_sql': validation_sql
                        }
                        rules.append(rule)
        
        except Exception as e:
            print(f"生成聚簇分析规则失败: {str(e)}")
        
        return rules

    @staticmethod
    def _generate_group_ranges_rules(df, group_field, features):
        """按分组字段统计多个特征的最小/最大范围，生成范围规则。

        返回的每条规则对应一个分组（例如分公司），params 中包含各特征的范围，
        同时尽量生成易读字符串 regex_pattern 以便前端展示。
        """
        rules = []
        try:
            grouped = df.groupby(group_field)
            for group_value, sub_df in grouped:
                ranges = {}
                for feat in features:
                    # 仅对数值型特征统计范围
                    if pd.api.types.is_numeric_dtype(sub_df[feat]):
                        ranges[feat] = {
                            'min': float(sub_df[feat].min()),
                            'max': float(sub_df[feat].max())
                        }
                # 生成可读模式串（如果包含常见的经纬度字段名则拼接中文样式）
                regex_parts = []
                if 'Latitude' in ranges and 'Longitude' in ranges:
                    lat = ranges['Latitude']
                    lon = ranges['Longitude']
                    regex_parts.append(f"纬度 {lat['min']:.4f}-{lat['max']:.4f}")
                    regex_parts.append(f"经度 {lon['min']:.4f}-{lon['max']:.4f}")
                else:
                    for feat, r in ranges.items():
                        regex_parts.append(f"{feat} {r['min']:.4f}-{r['max']:.4f}")

                rule = {
                    'rule_type': 'cluster_group_ranges',
                    'field': group_field,
                    'name': f"{group_field}_{group_value}_group_ranges",
                    'description': f"{group_field}={group_value} 的特征范围统计",
                    'params': {
                        'group': str(group_value),
                        'ranges': ranges,
                        'regex_pattern': '，'.join(regex_parts)
                    }
                }
                rules.append(rule)
        except Exception as e:
            print(f"生成分组范围规则失败: {str(e)}")
        return rules
    
    @staticmethod
    def _generate_categorical_rules(df, field, field_data, rule_type):
        """生成分类型字段规则"""
        rules = []
        
        try:
            # 值分布分析
            value_counts = field_data.value_counts()
            total_count = len(field_data)
            
            # 频率分析规则
            if rule_type == 'frequency_analysis':
                frequency_stats = []
                for value, count in value_counts.items():
                    frequency_stats.append({
                        'value': str(value),
                        'count': int(count),
                        'frequency': float(count / total_count)
                    })
                
                # 生成基于频率的正则表达式和SQL
                value_patterns = [str(item['value']) for item in frequency_stats]
                regex_pattern = f'(?=.*{field}.*).*({"|".join(value_patterns)})'
                # 修复f-string嵌套引号问题
                quoted_values = [f"'{v}'" for v in value_patterns]
                validation_sql = f'SELECT * FROM {{table}} WHERE {field} IN ({", ".join(quoted_values)})'
                
                rule = {
                    'rule_type': 'frequency_analysis',
                    'field': field,
                    'name': f'{field}_frequency_analysis',
                    'description': f'{field}字段频率分析',
                    'params': {
                        'total_count': total_count,
                        'unique_count': len(value_counts),
                        'value_distribution': frequency_stats
                    },
                    'regex_pattern': regex_pattern,
                    'validation_sql': validation_sql
                }
                rules.append(rule)
        
        except Exception as e:
            print(f"生成分类型字段规则失败: {str(e)}")
        
        return rules
    
    @staticmethod
    def _generate_basic_rules(statistics, fields, rule_type):
        """生成基础规则（当无法获取完整数据时的回退方案）"""
        rules = []
        
        for field in fields:
            if field not in statistics:
                continue
                
            stats = statistics[field]
            
            # 生成范围规则
            if rule_type.startswith('range') and stats.get('min') is not None and stats.get('max') is not None:
                min_val = stats['min']
                max_val = stats['max']
                rule = {
                    'rule_type': 'range',
                    'field': field,
                    'name': f'{field}_range_check',
                    'description': f'{field}字段范围检查',
                    'params': {
                        'min': min_val,
                        'max': max_val
                    },
                    'regex_pattern': f'(?=.*{field}.*(?:[0-9]*\\.?[0-9]+)).*({min_val:.2f}|{max_val:.2f}|(?:[0-9]*\\.?[0-9]+))',
                    'validation_sql': f'SELECT * FROM {{table}} WHERE {field} >= {min_val} AND {field} <= {max_val}'
                }
                rules.append(rule)
            
            # 生成异常值检测规则（基于3σ原则）
            if rule_type.startswith('outlier') and stats.get('mean') is not None and stats.get('std') is not None:
                mean = stats['mean']
                std = stats['std']
                if std > 0:
                    rule = {
                        'rule_type': 'outlier',
                        'field': field,
                        'name': f'{field}_outlier_check',
                        'description': f'{field}字段异常值检查（3σ原则）',
                        'params': {
                            'method': '3sigma',
                            'lower_bound': mean - 3 * std,
                            'upper_bound': mean + 3 * std
                        }
                    }
                    rules.append(rule)
        
        return rules
    
    @staticmethod
    def generate_advanced_rules(db_config, table_name, fields, model_config_id=None, advanced_params=None):
        """生成高级规则（基于机器学习模型和统计分析）"""
        try:
            # 获取数据
            connection_string = DatabaseService.get_connection_string(db_config, 'utf8')
            engine = DatabaseService.create_engine(connection_string)
            
            # 使用引号包装表名和字段名
            quoted_table_name = DatabaseService.quote_identifier(table_name)
            quoted_fields = [DatabaseService.quote_identifier(field) for field in fields]
            field_list = ', '.join(quoted_fields)
            df = pd.read_sql(f"SELECT {field_list} FROM {quoted_table_name}", engine)
            
            rules = []
            
            # 数值型字段的分布检验
            numeric_fields = df.select_dtypes(include=[np.number]).columns.tolist()
            for field in numeric_fields:
                if field in fields:
                    # 正态性检验
                    if len(df[field].dropna()) > 3:
                        _, p_value = stats.normaltest(df[field].dropna())
                        rule = {
                            'rule_type': 'distribution_check',
                            'field': field,
                            'name': f'{field}_distribution_check',
                            'description': f'{field}字段分布检验',
                            'params': {
                                'expected_distribution': 'normal',
                                'p_value': float(p_value),
                                'is_normal': p_value >= 0.05
                            }
                        }
                        rules.append(rule)
            
            # 相关性分析
            if len(numeric_fields) > 1:
                correlation_matrix = df[numeric_fields].corr()
                high_corr_pairs = []
                
                for i in range(len(numeric_fields)):
                    for j in range(i+1, len(numeric_fields)):
                        corr_value = correlation_matrix.iloc[i, j]
                        if abs(corr_value) > 0.8:  # 高相关性阈值
                            high_corr_pairs.append({
                                'field1': numeric_fields[i],
                                'field2': numeric_fields[j],
                                'correlation': float(corr_value)
                            })
                
                if high_corr_pairs:
                    rule = {
                        'rule_type': 'correlation_check',
                        'field': 'multiple',
                        'name': 'high_correlation_check',
                        'description': '高相关性字段检查',
                        'params': {
                            'correlation_threshold': 0.8,
                            'high_corr_pairs': high_corr_pairs
                        }
                    }
                    rules.append(rule)
            
            return rules
            
        except Exception as e:
            raise Exception(f"生成高级规则失败: {str(e)}")
    
    @staticmethod
    def create_rule_library(name, description="", force_replace=False):
        """创建规则库
        
        Args:
            name: 规则库名称
            description: 规则库描述
            force_replace: 是否强制替换已存在的规则库（包括已删除的）
        """
        # 检查是否已存在相同名称的规则库（包括已删除的）
        existing_library = RuleLibrary.query.filter_by(name=name).first()
        
        if existing_library:
            if existing_library.is_active and not force_replace:
                # 如果已存在且为活跃状态，且不强制替换，抛出异常
                raise Exception(f"规则库名称 '{name}' 已存在")
            elif not existing_library.is_active and not force_replace:
                # 如果存在但已删除，且不强制替换，恢复它
                existing_library.is_active = True
                existing_library.description = description
                existing_library.updated_at = datetime.utcnow()
                db.session.commit()
                return existing_library
            else:
                # 强制替换：删除旧记录（包括关联的版本）
                print(f"强制替换规则库 '{name}'，删除旧记录 ID: {existing_library.id}")
                db.session.delete(existing_library)
                db.session.commit()
        
        # 创建新的规则库
        library = RuleLibrary(
            name=name,
            description=description
        )
        
        db.session.add(library)
        db.session.commit()
        return library

    @staticmethod
    def get_or_create_library(name: str, description: str = ""):
        """按名称获取活跃库，不存在则创建并返回"""
        library = RuleLibrary.query.filter_by(name=name, is_active=True).first()
        if library:
            return library
        return RuleService.create_rule_library(name=name, description=description, force_replace=False)
    
    @staticmethod
    def save_rule_version(library_id, version, rules, created_by="", description=""):
        """保存规则版本"""
        rule_version = RuleVersion(
            library_id=library_id,
            version=version,
            created_by=created_by,
            description=description
        )
        
        rule_version.set_rules(rules)
        db.session.add(rule_version)
        db.session.commit()
        return rule_version

    @staticmethod
    def save_current_rules(library_id, rules, created_by="", description=""):
        """保存当前规则（无版本模式）。
        实现为：清空该库已有版本，仅保留一个名为 'current' 的版本以持久化规则。
        前端不展示版本，后端仅作为存储实现。
        """
        # 删除该库的旧版本
        RuleVersion.query.filter_by(library_id=library_id).delete()
        db.session.commit()

        # 保存为固定版本名 'current'
        return RuleService.save_rule_version(
            library_id=library_id,
            version='current',
            rules=rules,
            created_by=created_by,
            description=description or '当前规则（无版本模式）'
        )
    
    @staticmethod
    def get_rule_libraries():
        """获取所有规则库"""
        libraries = RuleLibrary.query.filter_by(is_active=True).all()
        return [library.to_dict() for library in libraries]
    

    
    @staticmethod
    def get_rule_versions(library_id):
        """获取规则库的所有版本"""
        versions = RuleVersion.query.filter_by(library_id=library_id).order_by(RuleVersion.created_at.desc()).all()
        if versions is None:
            return []
        return [version.to_dict() for version in versions]

    @staticmethod
    def get_latest_rules(library_id):
        """获取规则库的最新一份规则（无版本模式用于直接查看/检测）。"""
        version = (
            RuleVersion.query.filter_by(library_id=library_id)
            .order_by(RuleVersion.created_at.desc())
            .first()
        )
        if not version:
            return []
        return version.get_rules() or []
    
    @staticmethod
    def validate_rule(rule, data):
        """验证单个规则"""
        field = rule['field']
        rule_type = rule['rule_type']
        params = rule['params']
        
        if field not in data.columns:
            return False, f"字段 {field} 不存在"
        
        # 范围检查规则
        if rule_type in ['range', 'range_2sigma', 'range_percentile']:
            return RuleService._validate_range_rule(rule, data)
        
        # 异常值检测规则
        elif rule_type in ['outlier', 'outlier_3sigma', 'outlier_iqr', 'outlier_zscore']:
            return RuleService._validate_outlier_rule(rule, data)
        
        # 聚类规则
        elif rule_type in ['cluster_kmeans', 'cluster_dbscan']:
            return RuleService._validate_cluster_rule(rule, data)
        
        # 深度区间规则
        elif rule_type == 'depth_interval_stats':
            return RuleService._validate_depth_interval_rule(rule, data)
        
        else:
            return False, f"不支持的规则类型: {rule_type}"
    
    @staticmethod
    def _validate_range_rule(rule, data):
        """验证范围规则"""
        field = rule['field']
        params = rule['params']
        
        lower_bound = params.get('lower_bound')
        upper_bound = params.get('upper_bound')
        field_data = data[field].dropna()
        
        if lower_bound is not None and field_data.min() < lower_bound:
            return False, f"字段 {field} 存在小于下界 {lower_bound} 的数据"
        if upper_bound is not None and field_data.max() > upper_bound:
            return False, f"字段 {field} 存在大于上界 {upper_bound} 的数据"
        
        return True, "通过"
    
    @staticmethod
    def _validate_outlier_rule(rule, data):
        """验证异常值规则"""
        field = rule['field']
        params = rule['params']
        method = params.get('method')
        
        field_data = data[field].dropna()
        outliers = []
        
        if method in ['3sigma', 'zscore']:
            lower_bound = params.get('lower_bound')
            upper_bound = params.get('upper_bound')
            outliers = field_data[(field_data < lower_bound) | (field_data > upper_bound)]
        
        elif method == 'iqr':
            lower_bound = params.get('lower_bound')
            upper_bound = params.get('upper_bound')
            outliers = field_data[(field_data < lower_bound) | (field_data > upper_bound)]
        
        if not outliers.empty:
            return False, f"字段 {field} 存在 {len(outliers)} 个异常值"
        
        return True, "通过"
    
    @staticmethod
    def _validate_cluster_rule(rule, data):
        """验证聚类规则"""
        # 聚类规则主要用于数据分析，不作为严格的验证规则
        return True, "聚类分析完成"
    
    @staticmethod
    def _validate_depth_interval_rule(rule, data):
        """验证深度区间规则"""
        field = rule['field']
        params = rule['params']
        depth_field = params.get('depth_field')
        intervals = params.get('intervals', [])
        
        if not depth_field or depth_field not in data.columns:
            return False, f"深度字段 {depth_field} 不存在"
        
        if not intervals:
            return False, "深度区间统计信息为空"
        
        # 检查数据是否在任何区间的统计范围内
        valid_count = 0
        for _, row in data.iterrows():
            if pd.isna(row[field]) or pd.isna(row[depth_field]):
                continue
                
            depth_value = row[depth_field]
            field_value = row[field]
            
            # 查找匹配的深度区间
            for interval in intervals:
                start_depth = interval['start_depth']
                end_depth = interval['end_depth']
                
                if start_depth <= depth_value < end_depth:
                    # 检查字段值是否在该区间的合理范围内（均值±2σ）
                    mean_val = interval['mean']
                    std_val = interval['std']
                    
                    if std_val > 0:
                        lower_bound = mean_val - 2 * std_val
                        upper_bound = mean_val + 2 * std_val
                        
                        if lower_bound <= field_value <= upper_bound:
                            valid_count += 1
                    break
        
        total_count = len(data.dropna(subset=[field, depth_field]))
        if total_count == 0:
            return True, "无有效数据用于深度区间验证"
            
        pass_rate = valid_count / total_count
        return pass_rate > 0.8, f"深度区间验证通过率: {pass_rate:.2%}"
    
    @staticmethod
    def validate_rule_detailed(rule, data):
        """详细验证单个规则，返回详细结果"""
        field = rule['field']
        rule_type = rule['rule_type']
        params = rule['params']
        
        if field not in data.columns:
            return {
                'passed_count': 0,
                'failed_count': len(data),
                'failed_indices': list(range(len(data))),
                'error_details': [{'message': f"字段 {field} 不存在"}]
            }
        
        failed_indices = []
        error_details = []
        
        # 范围检查规则详细验证
        if rule_type in ['range', 'range_2sigma', 'range_percentile']:
            failed_indices, error_details = RuleService._validate_range_rule_detailed(rule, data)
        
        # 异常值检测规则详细验证
        elif rule_type in ['outlier', 'outlier_3sigma', 'outlier_iqr', 'outlier_zscore']:
            failed_indices, error_details = RuleService._validate_outlier_rule_detailed(rule, data)
        
        # 深度区间规则详细验证
        elif rule_type == 'depth_interval_stats':
            failed_indices, error_details = RuleService._validate_depth_interval_rule_detailed(rule, data)
        
        # 频率分析规则详细验证
        elif rule_type == 'frequency_analysis':
            failed_indices, error_details = RuleService._validate_frequency_rule_detailed(rule, data)
        
        passed_count = len(data) - len(failed_indices)
        failed_count = len(failed_indices)
        
        return {
            'passed_count': passed_count,
            'failed_count': failed_count,
            'failed_indices': failed_indices,
            'error_details': error_details
        }
    
    @staticmethod
    def _validate_range_rule_detailed(rule, data):
        """详细验证范围规则"""
        field = rule['field']
        params = rule['params']
        
        lower_bound = params.get('lower_bound')
        upper_bound = params.get('upper_bound')
        
        failed_indices = []
        error_details = []
        
        for idx, value in enumerate(data[field]):
            if pd.isna(value):
                continue
                
            if lower_bound is not None and value < lower_bound:
                failed_indices.append(idx)
                error_details.append({
                    'row': idx,
                    'value': value,
                    'message': f"值 {value} 小于下界 {lower_bound}"
                })
            elif upper_bound is not None and value > upper_bound:
                failed_indices.append(idx)
                error_details.append({
                    'row': idx,
                    'value': value,
                    'message': f"值 {value} 大于上界 {upper_bound}"
                })
        
        return failed_indices, error_details
    
    @staticmethod
    def _validate_outlier_rule_detailed(rule, data):
        """详细验证异常值规则"""
        field = rule['field']
        params = rule['params']
        method = params.get('method')
        
        lower_bound = params.get('lower_bound')
        upper_bound = params.get('upper_bound')
        
        failed_indices = []
        error_details = []
        
        for idx, value in enumerate(data[field]):
            if pd.isna(value):
                continue
                
            if value < lower_bound or value > upper_bound:
                failed_indices.append(idx)
                error_details.append({
                    'row': idx,
                    'value': value,
                    'message': f"字段 {field} 值 {value} 为异常值（{method}方法）"
                })
        
        return failed_indices, error_details
    
    @staticmethod
    def _get_geological_parameter_bounds(field_name, interval_stats):
        """根据地质参数特性确定合理的统计边界"""
        
        # 地质参数的物理约束
        geological_constraints = {
            'porosity': {'min': 0.0, 'max': 50.0, 'method': 'percentile'},           # 孔隙度 0%-50%
            'effe_porosity': {'min': 0.0, 'max': 50.0, 'method': 'percentile'},     # 有效孔隙度
            'permeability': {'min': 0.0, 'max': None, 'method': 'log_percentile'},  # 渗透率，对数分布
            'density': {'min': 1.0, 'max': 4.0, 'method': 'percentile'},           # 密度 1-4 g/cm³
            'resistivity': {'min': 0.0, 'max': None, 'method': 'log_percentile'},  # 电阻率，对数分布
            'gamma_ray': {'min': 0.0, 'max': 300.0, 'method': 'percentile'},       # 自然伽马 0-300 API
        }
        
        # 检查字段名是否包含已知的地质参数关键词
        field_lower = field_name.lower()
        constraints = None
        
        for param_key, param_constraints in geological_constraints.items():
            if param_key in field_lower:
                constraints = param_constraints
                break
        
        # 如果没有找到特定约束，使用默认的百分位数方法
        if constraints is None:
            constraints = {'min': None, 'max': None, 'method': 'percentile'}
        
        # 根据统计方法计算边界
        method = constraints['method']
        
        if method == 'percentile':
            # 使用5%-95%分位数，更稳健
            if 'q05' in interval_stats and 'q95' in interval_stats:
                lower_bound = interval_stats['q05']
                upper_bound = interval_stats['q95']
            else:
                # 如果没有计算分位数，使用四分位距方法
                q25 = interval_stats.get('q25', interval_stats.get('mean', 0))
                q75 = interval_stats.get('q75', interval_stats.get('mean', 0))
                iqr = q75 - q25
                lower_bound = q25 - 1.5 * iqr
                upper_bound = q75 + 1.5 * iqr
        
        elif method == 'log_percentile':
            # 对数正态分布，适用于渗透率等参数
            mean_val = interval_stats.get('mean', 1.0)
            std_val = interval_stats.get('std', 0.5)
            
            if mean_val > 0 and std_val > 0:
                # 使用对数正态分布的特性
                log_mean = np.log(mean_val)
                log_std = std_val / mean_val  # 变异系数近似
                
                lower_bound = np.exp(log_mean - 2 * log_std)
                upper_bound = np.exp(log_mean + 2 * log_std)
            else:
                lower_bound = 0.0
                upper_bound = mean_val * 3 if mean_val > 0 else 100.0
        
        else:
            # 默认使用改进的均值±标准差方法
            mean_val = interval_stats.get('mean', 0)
            std_val = interval_stats.get('std', 0)
            
            lower_bound = mean_val - 1.5 * std_val  # 减少到1.5σ
            upper_bound = mean_val + 1.5 * std_val
        
        # 应用物理约束
        if constraints['min'] is not None:
            lower_bound = max(lower_bound, constraints['min'])
        
        if constraints['max'] is not None:
            upper_bound = min(upper_bound, constraints['max'])
        
        # 确保下界不为负值（对于大多数地质参数）
        if constraints['min'] is None and lower_bound < 0:
            lower_bound = 0.0
        
        return lower_bound, upper_bound, method

    @staticmethod
    def _validate_depth_interval_rule_detailed(rule, data):
        """详细验证深度区间规则（改进的统计方法）"""
        field = rule['field']
        params = rule['params']
        depth_field = params.get('depth_field')
        intervals = params.get('intervals', [])
        
        failed_indices = []
        error_details = []
        
        if not depth_field or depth_field not in data.columns:
            # 如果深度字段不存在，所有记录都标记为失败
            for idx in range(len(data)):
                failed_indices.append(idx)
                error_details.append({
                    'row': idx,
                    'message': f"深度字段 {depth_field} 不存在"
                })
            return failed_indices, error_details
        
        if not intervals:
            # 如果没有区间信息，所有记录都标记为失败
            for idx in range(len(data)):
                failed_indices.append(idx)
                error_details.append({
                    'row': idx,
                    'message': "深度区间统计信息为空"
                })
            return failed_indices, error_details
        
        for idx, row in data.iterrows():
            if pd.isna(row[field]) or pd.isna(row[depth_field]):
                continue
                
            depth_value = row[depth_field]
            field_value = row[field]
            found_valid_interval = False
            
            # 查找匹配的深度区间
            for interval in intervals:
                start_depth = interval['start_depth']
                end_depth = interval['end_depth']
                
                if start_depth <= depth_value < end_depth:
                    # 使用改进的统计方法确定边界
                    lower_bound, upper_bound, method = RuleService._get_geological_parameter_bounds(field, interval)
                    
                    if lower_bound <= field_value <= upper_bound:
                        found_valid_interval = True
                    else:
                        failed_indices.append(idx)
                        error_details.append({
                            'row': idx,
                            'depth': depth_value,
                            'value': field_value,
                            'message': f"在深度{start_depth}-{end_depth}m区间内，{field}值{field_value}超出合理范围[{lower_bound:.2f}, {upper_bound:.2f}]（使用{method}方法）"
                        })
                    break
            
            if not found_valid_interval and not any(start <= depth_value < end for start, end in [(i['start_depth'], i['end_depth']) for i in intervals]):
                failed_indices.append(idx)
                error_details.append({
                    'row': idx,
                    'depth': depth_value,
                    'value': field_value,
                    'message': f"深度值{depth_value}不在任何统计区间范围内"
                })
        
        return failed_indices, error_details
    
    @staticmethod
    def _validate_frequency_rule_detailed(rule, data):
        """详细验证频率分析规则"""
        field = rule['field']
        params = rule['params']
        value_distribution = params.get('value_distribution', [])
        
        failed_indices = []
        error_details = []
        
        if not value_distribution:
            # 如果没有频率分布信息，所有记录都标记为失败
            for idx in range(len(data)):
                failed_indices.append(idx)
                error_details.append({
                    'row': idx,
                    'message': "频率分析信息为空"
                })
            return failed_indices, error_details
        
        # 获取期望的值列表
        expected_values = [item['value'] for item in value_distribution]
        
        for idx, value in enumerate(data[field]):
            if pd.isna(value):
                continue
            
            if str(value) not in expected_values:
                failed_indices.append(idx)
                error_details.append({
                    'row': idx,
                    'value': value,
                    'message': f"值 '{value}' 不在期望的值列表中: {expected_values}"
                })
        
        return failed_indices, error_details