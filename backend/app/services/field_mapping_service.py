# coding: utf-8
import pandas as pd
import os
import re
from difflib import SequenceMatcher

class FieldMappingService:
    """字段映射服务 - 处理英文字段名与中文数据项的映射关系"""
    
    def __init__(self):
        self.field_mappings = {}
        self.load_field_mappings()
    
    def load_field_mappings(self):
        """从Excel文件加载字段映射关系"""
        try:
            # 获取Excel文件路径
            base_dir = os.path.dirname(os.path.dirname(__file__))  # 从 services 到 app
            base_dir = os.path.dirname(base_dir)  # 从 app 到 backend
            excel_path = os.path.join(base_dir, '业务数据规范数据项.xlsx')
            
            if not os.path.exists(excel_path):
                print(f"字段映射文件未找到: {excel_path}")
                return
            
            # 读取Excel文件
            df = pd.read_excel(excel_path)
            print(f"成功加载字段映射文件，包含 {len(df)} 条记录")
            
            # 检查列名
            print(f"Excel文件列名: {df.columns.tolist()}")
            
            # 假设列名为：英文代码、数据项名称
            # 如果列名不同，需要根据实际情况调整
            english_code_col = None
            chinese_name_col = None
            
            # 自动识别列名
            for col in df.columns:
                if '英文' in col or '代码' in col or 'code' in col.lower():
                    english_code_col = col
                elif '名称' in col or 'name' in col.lower():
                    chinese_name_col = col
            
            if not english_code_col or not chinese_name_col:
                print("无法识别英文代码列或中文名称列")
                print(f"可用列名: {df.columns.tolist()}")
                return
            
            print(f"使用列: 英文代码='{english_code_col}', 中文名称='{chinese_name_col}'")
            
            # 构建映射关系
            for _, row in df.iterrows():
                english_code = str(row.get(english_code_col, '')).strip()
                chinese_name = str(row.get(chinese_name_col, '')).strip()
                
                if english_code and chinese_name and english_code != 'nan' and chinese_name != 'nan':
                    # 存储原始映射
                    self.field_mappings[english_code] = chinese_name
                    
                    # 存储小写映射（用于模糊匹配）
                    self.field_mappings[english_code.lower()] = chinese_name
                    
                    # 存储去除下划线的映射
                    clean_code = english_code.replace('_', '').replace('-', '')
                    if clean_code != english_code:
                        self.field_mappings[clean_code] = chinese_name
                        self.field_mappings[clean_code.lower()] = chinese_name
            
            print(f"成功加载 {len(self.field_mappings)} 个字段映射")
            
        except Exception as e:
            print(f"加载字段映射失败: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def get_chinese_name(self, english_field, use_fuzzy_match=True):
        """获取字段的中文名称
        
        Args:
            english_field: 英文字段名
            use_fuzzy_match: 是否使用模糊匹配
            
        Returns:
            str: 中文名称，如果未找到则返回原英文字段名
        """
        if not english_field:
            return english_field
        
        # 1. 精确匹配
        if english_field in self.field_mappings:
            return self.field_mappings[english_field]
        
        # 2. 小写匹配
        if english_field.lower() in self.field_mappings:
            return self.field_mappings[english_field.lower()]
        
        # 3. 去除下划线后匹配
        clean_field = english_field.replace('_', '').replace('-', '')
        if clean_field in self.field_mappings:
            return self.field_mappings[clean_field]
        if clean_field.lower() in self.field_mappings:
            return self.field_mappings[clean_field.lower()]
        
        # 4. 模糊匹配（如果启用）
        if use_fuzzy_match:
            best_match = self._fuzzy_match(english_field)
            if best_match:
                return best_match
        
        # 5. 返回原字段名
        return english_field
    
    def _fuzzy_match(self, english_field, threshold=0.6):
        """模糊匹配字段名
        
        Args:
            english_field: 英文字段名
            threshold: 相似度阈值
            
        Returns:
            str: 最佳匹配的中文名称，如果没有达到阈值则返回None
        """
        if not english_field:
            return None
        
        best_match = None
        best_score = 0
        
        # 遍历所有英文代码
        for code in self.field_mappings.keys():
            # 跳过已经处理过的映射
            if code in self.field_mappings and self.field_mappings[code] != code:
                continue
            
            # 计算相似度
            score = self._calculate_similarity(english_field, code)
            if score > best_score and score >= threshold:
                best_score = score
                best_match = self.field_mappings[code]
        
        return best_match
    
    def _calculate_similarity(self, str1, str2):
        """计算两个字符串的相似度
        
        Args:
            str1: 字符串1
            str2: 字符串2
            
        Returns:
            float: 相似度分数 (0-1)
        """
        if not str1 or not str2:
            return 0.0
        
        # 转换为小写进行比较
        s1 = str1.lower()
        s2 = str2.lower()
        
        # 使用SequenceMatcher计算相似度
        similarity = SequenceMatcher(None, s1, s2).ratio()
        
        # 额外加分：如果包含相同的单词
        words1 = set(re.findall(r'\w+', s1))
        words2 = set(re.findall(r'\w+', s2))
        
        if words1 and words2:
            word_overlap = len(words1.intersection(words2)) / len(words1.union(words2))
            # 综合相似度：字符串相似度 * 0.7 + 单词重叠度 * 0.3
            final_similarity = similarity * 0.7 + word_overlap * 0.3
            return final_similarity
        
        return similarity
    
    def get_all_mappings(self):
        """获取所有字段映射关系"""
        return self.field_mappings.copy()
    
    def search_fields(self, query, limit=20):
        """搜索字段映射
        
        Args:
            query: 搜索查询（支持中英文）
            limit: 返回结果数量限制
            
        Returns:
            list: 匹配的字段映射列表
        """
        if not query:
            return []
        
        results = []
        query_lower = query.lower()
        
        for english_code, chinese_name in self.field_mappings.items():
            # 跳过已经处理过的映射
            if english_code in self.field_mappings and self.field_mappings[english_code] != english_code:
                continue
            
            # 检查是否匹配
            if (query_lower in english_code.lower() or 
                query_lower in chinese_name.lower() or
                english_code.lower() in query_lower or
                chinese_name.lower() in query_lower):
                
                results.append({
                    'english_code': english_code,
                    'chinese_name': chinese_name
                })
                
                if len(results) >= limit:
                    break
        
        return results
    
    def get_field_info(self, english_field):
        """获取字段的详细信息
        
        Args:
            english_field: 英文字段名
            
        Returns:
            dict: 字段信息，包含英文代码、中文名称、相似字段等
        """
        chinese_name = self.get_chinese_name(english_field)
        
        # 查找相似字段
        similar_fields = []
        if english_field:
            for code in self.field_mappings.keys():
                if code != english_field and self._calculate_similarity(english_field, code) > 0.5:
                    similar_fields.append({
                        'english_code': code,
                        'chinese_name': self.field_mappings[code]
                    })
        
        return {
            'english_field': english_field,
            'chinese_name': chinese_name,
            'is_mapped': chinese_name != english_field,
            'similar_fields': similar_fields[:5]  # 最多返回5个相似字段
        }

    def get_rule_name_translation(self, rule_name):
        """获取规则名称的中文翻译
        
        Args:
            rule_name: 英文规则名称
            
        Returns:
            str: 中文规则名称描述
        """
        if not rule_name:
            return rule_name
        
        # 解析规则名称，提取关键信息
        # 例如: effe_porosity_depth_interval_stats -> 有效孔隙度深度区间统计分析
        
        # 1. 尝试直接匹配
        if rule_name in self.field_mappings:
            return self.field_mappings[rule_name]
        
        # 2. 解析规则名称结构
        parts = rule_name.split('_')
        if len(parts) >= 2:
            # 提取主要字段名（通常是前几个部分）
            main_field = '_'.join(parts[:2])  # 例如: effe_porosity
            rule_type = '_'.join(parts[2:])   # 例如: depth_interval_stats
            
            # 获取字段的中文名称
            field_chinese = self.get_chinese_name(main_field, use_fuzzy_match=False)
            
            # 获取规则类型的中文描述
            type_chinese = self._translate_rule_type(rule_type)
            
            if field_chinese != main_field and type_chinese:
                return f"{field_chinese}{type_chinese}"
            elif field_chinese != main_field:
                return f"{field_chinese}规则"
            elif type_chinese:
                return f"{main_field}{type_chinese}"
        
        # 3. 模糊匹配整个规则名称
        best_match = self._fuzzy_match(rule_name, threshold=0.5)
        if best_match:
            return best_match
        
        # 4. 返回原名称
        return rule_name
    
    def _translate_rule_type(self, rule_type):
        """翻译规则类型
        
        Args:
            rule_type: 英文规则类型
            
        Returns:
            str: 中文规则类型描述
        """
        if not rule_type:
            return ""
        
        # 规则类型映射表
        type_mappings = {
            'depth_interval_stats': '按深度区间统计分析',
            'depth_interval': '深度区间',
            'stats': '统计分析',
            'range_check': '范围检查',
            'outlier_detection': '异常值检测',
            'quality_check': '质量检查',
            'validation': '数据验证',
            'consistency': '一致性检查',
            'completeness': '完整性检查',
            'accuracy': '准确性检查',
            'timeliness': '时效性检查',
            'uniqueness': '唯一性检查',
            'format_check': '格式检查',
            'length_check': '长度检查',
            'pattern_check': '模式检查',
            'reference_check': '引用完整性检查',
            'cross_field': '跨字段检查',
            'business_rule': '业务规则检查',
            'threshold': '阈值检查',
            'trend': '趋势分析',
            'anomaly': '异常检测',
            'clustering': '聚类分析',
            'regression': '回归分析',
            'classification': '分类分析'
        }
        
        # 1. 精确匹配
        if rule_type in type_mappings:
            return type_mappings[rule_type]
        
        # 2. 部分匹配
        for key, value in type_mappings.items():
            if key in rule_type or rule_type in key:
                return value
        
        # 3. 模糊匹配
        best_match = None
        best_score = 0
        
        for key, value in type_mappings.items():
            score = self._calculate_similarity(rule_type, key)
            if score > best_score and score >= 0.4:
                best_score = score
                best_match = value
        
        if best_match:
            return best_match
        
        # 4. 返回默认描述
        return "规则"
    
    def get_rule_type_translation(self, rule_type):
        """获取规则类型的中文翻译
        
        Args:
            rule_type: 英文规则类型
            
        Returns:
            str: 中文规则类型描述
        """
        return self._translate_rule_type(rule_type)
