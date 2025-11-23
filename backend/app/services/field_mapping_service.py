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
            
            # 自动识别列名
            english_code_col = None
            chinese_name_col = None
            
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
            count = 0
            for _, row in df.iterrows():
                english_code = str(row.get(english_code_col, '')).strip()
                chinese_name = str(row.get(chinese_name_col, '')).strip()
                
                if english_code and chinese_name and english_code != 'nan' and chinese_name != 'nan':
                    # 1. 存储原始映射 (例如: BIT_NO -> 钻头编号)
                    self.field_mappings[english_code] = chinese_name
                    
                    # 2. 存储小写映射 (例如: bit_no -> 钻头编号)
                    # 这样数据库里的 bit_no 就能匹配到了
                    if english_code.lower() != english_code:
                        self.field_mappings[english_code.lower()] = chinese_name
                    
                    # 3. 存储去除下划线的映射 (例如: bitno -> 钻头编号)
                    clean_code = english_code.replace('_', '').replace('-', '')
                    if clean_code != english_code:
                        self.field_mappings[clean_code] = chinese_name
                        self.field_mappings[clean_code.lower()] = chinese_name
                    
                    count += 1
            
            print(f"成功处理 {count} 条原始记录，生成 {len(self.field_mappings)} 个映射条目（含变体）")
            
        except Exception as e:
            print(f"加载字段映射失败: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def get_chinese_name(self, english_field, use_fuzzy_match=True):
        """获取字段的中文名称"""
        if not english_field:
            return english_field
        
        # 1. 精确匹配 (BIT_NO)
        if english_field in self.field_mappings:
            return self.field_mappings[english_field]
        
        # 2. 小写匹配 (bit_no)
        if english_field.lower() in self.field_mappings:
            return self.field_mappings[english_field.lower()]
        
        # 3. 去除下划线后匹配 (bitno)
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
        """模糊匹配字段名"""
        if not english_field:
            return None
        
        best_match = None
        best_score = 0
        
        # 遍历所有已知的英文代码
        for code in self.field_mappings.keys():
            # 排除掉那些 value 等于 key 的情况（虽然现在逻辑里应该没有这种情况了，但为了保险）
            if self.field_mappings[code] == code:
                continue
            
            # 计算相似度
            score = self._calculate_similarity(english_field, code)
            if score > best_score and score >= threshold:
                best_score = score
                best_match = self.field_mappings[code]
        
        return best_match
    
    def _calculate_similarity(self, str1, str2):
        """计算两个字符串的相似度"""
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
        """
        搜索字段映射
        修复说明：
        1. 移除了之前的过滤逻辑，确保只要Excel里有就能搜到
        2. 增加了去重逻辑，避免 BIT_NO 和 bit_no 同时显示
        """
        if not query:
            return []
        
        results = []
        query_lower = query.lower()
        
        # 用于去重：记录已经添加到结果集的中文名+英文名组合
        # 我们倾向于展示原始的大写形式（如果存在）
        seen_combinations = set()
        
        # 先收集所有匹配项
        matches = []
        for english_code, chinese_name in self.field_mappings.items():
            # 匹配逻辑：搜英文或搜中文
            if (query_lower in english_code.lower() or 
                query_lower in chinese_name.lower()):
                matches.append((english_code, chinese_name))
        
        # 排序优化：优先显示完全匹配的，或者英文代码较短的
        matches.sort(key=lambda x: (len(x[0]), x[0]))
        
        for english_code, chinese_name in matches:
            # 构造唯一键，例如 "BIT_NO|钻头编号"
            # 我们希望 BIT_NO 和 bit_no 视为同一个，优先展示大写
            upper_code = english_code.upper()
            combo_key = f"{upper_code}|{chinese_name}"
            
            if combo_key in seen_combinations:
                continue
                
            results.append({
                'english_code': english_code,
                'chinese_name': chinese_name
            })
            seen_combinations.add(combo_key)
            
            if len(results) >= limit:
                break
        
        return results
    
    def get_field_info(self, english_field):
        """获取字段的详细信息"""
        chinese_name = self.get_chinese_name(english_field)
        
        # 查找相似字段
        similar_fields = []
        if english_field:
            seen_similar = set()
            for code in self.field_mappings.keys():
                if code != english_field and self._calculate_similarity(english_field, code) > 0.5:
                    name = self.field_mappings[code]
                    # 简单的去重
                    if name not in seen_similar:
                        similar_fields.append({
                            'english_code': code,
                            'chinese_name': name
                        })
                        seen_similar.add(name)
        
        return {
            'english_field': english_field,
            'chinese_name': chinese_name,
            'is_mapped': chinese_name != english_field,
            'similar_fields': similar_fields[:5]  # 最多返回5个相似字段
        }

    def get_rule_name_translation(self, rule_name):
        """获取规则名称的中文翻译"""
        if not rule_name:
            return rule_name
        
        # 1. 尝试直接匹配
        if rule_name in self.field_mappings:
            return self.field_mappings[rule_name]
        
        # 2. 解析规则名称结构
        parts = rule_name.split('_')
        if len(parts) >= 2:
            main_field = '_'.join(parts[:2])
            rule_type = '_'.join(parts[2:])
            
            field_chinese = self.get_chinese_name(main_field, use_fuzzy_match=False)
            type_chinese = self._translate_rule_type(rule_type)
            
            if field_chinese != main_field and type_chinese:
                return f"{field_chinese}{type_chinese}"
            elif field_chinese != main_field:
                return f"{field_chinese}规则"
            elif type_chinese:
                return f"{main_field}{type_chinese}"
        
        # 3. 模糊匹配
        best_match = self._fuzzy_match(rule_name, threshold=0.5)
        if best_match:
            return best_match
        
        return rule_name
    
    def _translate_rule_type(self, rule_type):
        """翻译规则类型"""
        if not rule_type:
            return ""
        
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
        
        if rule_type in type_mappings:
            return type_mappings[rule_type]
            
        for key, value in type_mappings.items():
            if key in rule_type or rule_type in key:
                return value
                
        return "规则"
    
    def get_rule_type_translation(self, rule_type):
        return self._translate_rule_type(rule_type)