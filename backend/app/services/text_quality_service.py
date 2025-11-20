# coding: utf-8
import pandas as pd
import os
import time
import asyncio
import re
from app.services.llm_client import LLMClient
from app.services.database_service import DatabaseService
from app.models.quality_result import QualityResult, QualityReport
from app import db

class TextQualityService:
    """文本数据质检服务"""
    
    def __init__(self, batch_size=100):
        self.llm_client = LLMClient()
        self.batch_size = min(batch_size, 1000)  # 批处理大小，默认100条，最大1000条
        self._max_retries = 3  # 最大重试次数
        self._retry_delay = 1.0  # 重试延迟（秒）
        
        # 井名正则表达式模式
        self.well_name_pattern = re.compile(
            r'^(?P<oil_field>[A-Z]+\d+(?:-\d+)*)-(?P<wellhead_area>[A-Z])(?P<well_number>\d+)(?P<well_marker>(?:H\d*|M\d*(?:[a-z]\d*)?|P\d+|S\d+)?)$'
        )
        
        # 加载区块代号白名单（来自 backend/block_info.csv 的“代号”列）
        self.block_code_whitelist = self._load_block_codes()
        print(f"加载区块代号白名单完成，数量: {len(self.block_code_whitelist)}")
    
    def _load_block_codes(self):
        """从 CSV 加载区块代号白名单（列名：代号）"""
        try:
            # 计算 CSV 路径：从当前文件到 backend 目录
            backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
            csv_path = os.path.join(backend_dir, 'block_info.csv')
            if not os.path.exists(csv_path):
                print(f"未找到区块代号文件: {csv_path}")
                return set()
            df = pd.read_csv(csv_path, dtype=str)
            if '代号' not in df.columns:
                print("CSV中未找到‘代号’列")
                return set()
            codes = set(str(x).strip().upper() for x in df['代号'].dropna().tolist() if str(x).strip())
            return codes
        except Exception as e:
            print(f"加载区块代号白名单失败: {e}")
            return set()
    
    def _is_well_name_field(self, kb_field_name):
        """判断字段是否为井名字段"""
        # 检查知识库字段名是否为井名
        return kb_field_name == '井名'
    
    def _validate_well_name(self, well_name):
        """使用正则表达式验证井名格式；若前缀字母在区块代号白名单内，直接放行"""
        if not well_name or pd.isna(well_name):
            return False, "井名为空"
        
        well_name_str = str(well_name).strip().upper()
        if not well_name_str:
            return False, "井名为空字符串"
        
        # 1) 白名单前缀快速放行：提取最前面的连续大写字母作为前缀
        prefix_match = re.match(r'^([A-Z]+)', well_name_str)
        if prefix_match:
            prefix = prefix_match.group(1)
            if prefix in self.block_code_whitelist:
                return True, f"白名单代号: {prefix}，直接放行"
        
        # 2) 正则格式校验
        match = self.well_name_pattern.match(well_name_str)
        if match:
            oil_field = match.group('oil_field')
            wellhead_area = match.group('wellhead_area')
            well_number = match.group('well_number')
            well_marker = match.group('well_marker') or ''
            
            explanation = f"油田:{oil_field}, 井区:{wellhead_area}, 井号:{well_number}"
            if well_marker:
                explanation += f", 标记:{well_marker}"
            
            return True, explanation
        else:
            return False, f"井名格式不符合规范: {well_name_str}"
    
    def _preprocess_well_name_fields(self, all_check_items):
        """预处理井名字段，使用正则表达式验证"""
        well_name_results = []
        remaining_items = []
        
        for item in all_check_items:
            field_name = item['field_name']
            kb_field_name = item['kb_field_name']
            field_value = item['field_value']
            record_idx = item['record_idx']
            
            # 判断是否为井名字段（通过知识库字段名判断）
            if self._is_well_name_field(kb_field_name):
                print(f"检测到井名字段: {field_name} -> {kb_field_name}")
                
                # 使用正则表达式验证
                is_valid, explanation = self._validate_well_name(field_value)
                
                well_name_results.append({
                    '记录编号': record_idx,
                    '原字段': field_name,
                    '映射字段': kb_field_name,
                    '变量': kb_field_name,
                    '值': str(field_value),
                    '类别': item['category'],
                    '结果': '合格' if is_valid else '不合格',
                    '说明': explanation,
                    '规范': item['quality_spec'],
                    '验证方式': '正则表达式'
                })
                
                print(f"井名正则验证完成: 记录{record_idx} {field_name} -> {'合格' if is_valid else '不合格'}")
            else:
                remaining_items.append(item)
        
        print(f"井名预处理完成: 正则验证 {len(well_name_results)} 个，待大模型检查 {len(remaining_items)} 个")
        return well_name_results, remaining_items
    
    def set_batch_size(self, batch_size):
        """设置批处理大小"""
        if batch_size > 0 and batch_size <= 1000:
            self.batch_size = batch_size
            print(f"批处理大小已设置为: {self.batch_size}")
        elif batch_size > 1000:
            self.batch_size = 1000
            print(f"批处理大小超过最大限制，已设置为: {self.batch_size}")
        else:
            print("批处理大小必须大于0且不超过1000")
    
    def get_batch_size(self):
        """获取当前批处理大小"""
        return self.batch_size
    
    def load_embedded_knowledge_base(self):
        """加载内嵌的知识库文件（保留兼容性）"""
        try:

            base_dir = os.path.dirname(os.path.dirname(__file__))  # 从 services 到 app
            base_dir = os.path.dirname(base_dir)  # 从 app 到 backend
            kb_path = os.path.join(base_dir, '文本型知识库.xlsx')
            
            print(f"加载知识库文件: {kb_path}")
            
            if not os.path.exists(kb_path):
                raise FileNotFoundError(f"知识库文件未找到: {kb_path}")
            
            # 读取Excel文件
            df = pd.read_excel(kb_path)
            
            # 转换为字典格式
            knowledge_base = []
            for _, row in df.iterrows():
                knowledge_base.append({
                    'Variable': str(row.get('Variable', '')),
                    'Category': str(row.get('Category', '')),
                    '质量规范描述': str(row.get('质量规范描述', ''))
                })
            
            print(f"成功加载知识库，包含 {len(knowledge_base)} 条记录")
            return knowledge_base
        
        except Exception as e:
            print(f"加载知识库失败: {str(e)}")
            raise e
    
    def _create_batch_prompt(self, batch_data, field_mapping_info, kb_map):
        prompt_parts = []
        
        # 系统角色定义 - 强调逻辑规则执行
        prompt_parts.append("你是一个专业的数据质量检查专家，具有丰富的石油勘探开发数据质检经验。")
        prompt_parts.append("你的任务是：根据提供的结构化质检规则（IF-THEN逻辑），严格判断每个数据字段是否合格。")
        prompt_parts.append("【核心原则】规则就是法律，必须100%严格执行，不得有任何主观判断或偏离。")
        prompt_parts.append("")
        
        # 规则语言说明 - 教会大模型理解IF-THEN逻辑
        prompt_parts.append("【规则语言理解指南】")
        prompt_parts.append("质检规则采用IF-THEN结构化逻辑，你必须严格按照逻辑执行：")
        prompt_parts.append("")
        prompt_parts.append("1. 逻辑函数解释：")
        prompt_parts.append("   - `is_null_or_blank(字段)` = 字段为空、null、None、NaN或仅包含空格")
        prompt_parts.append("   - `字段 NOT IN {值1、值2}` = 字段值不在枚举列表中")
        prompt_parts.append("   - `NOT (大于等于X并且小于等于Y)` = 数值不在[X,Y]范围内")
        prompt_parts.append("   - `filename_match_pattern(字段, '模式')` = 文件名不符合指定命名规范")
        prompt_parts.append("")
        prompt_parts.append("2. 逻辑执行规则：")
        prompt_parts.append("   - IF条件为真 → THEN标记错误 → 判定为【不合格】")
        prompt_parts.append("   - IF条件为假 → 不触发错误 → 该条规则通过")
        prompt_parts.append("   - 多条规则：只要任意一条IF条件为真，就判定【不合格】")
        prompt_parts.append("   - 所有规则都不触发错误，才判定【合格】")
        prompt_parts.append("")
        prompt_parts.append("3. 特别注意事项：")
        prompt_parts.append("   - 数值范围：必须精确比较，包括单位（MPa、kPa、℃等）")
        prompt_parts.append("   - 枚举值：必须完全匹配，区分大小写和标点符号")
        prompt_parts.append("   - 空值判断：null、None、NaN、空字符串、纯空格都视为空值")
        prompt_parts.append("")
        
        # 输出格式要求
        prompt_parts.append("【输出格式要求】绝对不得更改")
        prompt_parts.append("格式：记录{编号}|{字段名}|{结果}|{详细说明}")
        prompt_parts.append("")
        prompt_parts.append("说明：")
        prompt_parts.append("- 记录编号：纯数字（1, 2, 3...）")
        prompt_parts.append("- 字段名：使用提供的中文字段名")
        prompt_parts.append("- 结果：只能是'合格'或'不合格'（无其他表述）")
        prompt_parts.append("- 详细说明：触发的具体规则或通过原因（10-30字）")
        prompt_parts.append("")
        
        # 执行步骤 - 清晰的判断流程
        prompt_parts.append("【质检执行步骤】")
        prompt_parts.append("对每条数据，按以下步骤严格执行：")
        prompt_parts.append("")
        prompt_parts.append("步骤1：读取该字段的所有IF-THEN规则")
        prompt_parts.append("步骤2：逐条检查每个IF条件是否为真")
        prompt_parts.append("   - 如果IF条件为真 → 触发THEN中的错误 → 记录错误信息")
        prompt_parts.append("步骤3：汇总判断结果")
        prompt_parts.append("   - 任意规则触发错误 → 判定【不合格】，说明具体触发了哪条规则")
        prompt_parts.append("   - 所有规则都未触发 → 判定【合格】，说明符合所有规则要求")
        prompt_parts.append("")
        
        # 示例 - 基于IF-THEN规则的实际示例
        prompt_parts.append("【输出示例】完全按照此格式")
        prompt_parts.append("")
        prompt_parts.append("示例1：空值检查")
        prompt_parts.append("规则：IF is_null_or_blank(井名) THEN 标记错误('字段【井名】不能为空')")
        prompt_parts.append("数据：井名=''")
        prompt_parts.append("输出：记录1|井名|不合格|字段不能为空")
        prompt_parts.append("")
        prompt_parts.append("示例2：枚举检查")
        prompt_parts.append("规则：IF 是否为防爆设备 NOT IN {是、否} THEN 标记错误('取值必须为：是、否')")
        prompt_parts.append("数据：是否为防爆设备='未知'")
        prompt_parts.append("输出：记录1|是否为防爆设备|不合格|取值不在枚举{是、否}中")
        prompt_parts.append("")
        prompt_parts.append("示例3：数值范围检查")
        prompt_parts.append("规则：IF NOT (大于等于0MPa并且小于等于100MPa) THEN 标记错误('不满足范围')")
        prompt_parts.append("数据：操作压力=150MPa")
        prompt_parts.append("输出：记录1|操作压力|不合格|150MPa超出0-100MPa范围")
        prompt_parts.append("")
        prompt_parts.append("示例4：全部通过")
        prompt_parts.append("规则：IF is_null_or_blank(报告编号) THEN 标记错误('字段不能为空')")
        prompt_parts.append("数据：报告编号='RPT-2025-001'")
        prompt_parts.append("输出：记录1|报告编号|合格|符合所有规则要求")
        prompt_parts.append("")
        
        # 检查数据 - 结构化展示
        prompt_parts.append("=" * 60)
        prompt_parts.append("【待检查数据】")
        prompt_parts.append("=" * 60)
        prompt_parts.append("")
        for item in batch_data:
            record_idx = item['record_idx']
            field_name = item['field_name']
            field_value = item['field_value']
            kb_field_name = item['kb_field_name']
            quality_spec = item['quality_spec']
            category = item['category']
            
            # 清晰的结构化展示
            prompt_parts.append(f"【记录{record_idx}】")
            prompt_parts.append(f"字段名称：{kb_field_name}")
            prompt_parts.append(f"字段值：{field_value}")
            prompt_parts.append(f"字段类别：{category}")
            prompt_parts.append(f"质检规则：")
            # 将多行规则分行显示，提高可读性
            if quality_spec:
                spec_lines = quality_spec.strip().split(';')
                for i, line in enumerate(spec_lines, 1):
                    if line.strip():
                        prompt_parts.append(f"  规则{i}）{line.strip()}")
            prompt_parts.append("")
        
        # 最终指令
        prompt_parts.append("【执行要求】必须100%遵守")
        prompt_parts.append("")
        prompt_parts.append("1. 规则执行原则：")
        prompt_parts.append("   ✓ IF-THEN规则是唯一判断依据，不得使用常识或经验判断")
        prompt_parts.append("   ✓ 规则中的每个逻辑条件都必须精确计算，不得近似或模糊判断")
        prompt_parts.append("   ✓ 空值(null/None/NaN/空字符串/纯空格)必须通过is_null_or_blank()判断")
        prompt_parts.append("   ✓ 枚举值必须完全匹配（包括中文标点、大小写）")
        prompt_parts.append("   ✓ 数值范围必须包括单位判断（MPa≠kPa≠KPa）")
        prompt_parts.append("")
        prompt_parts.append("2. 输出格式原则：")
        prompt_parts.append("   ✓ 每条记录单独一行：记录编号|字段名|结果|详细说明")
        prompt_parts.append("   ✓ 结果只能是'合格'或'不合格'（无第三种表述）")
        prompt_parts.append("   ✓ 详细说明必须指出具体触发的规则或通过的原因")
        prompt_parts.append("   ✓ 不得输出任何额外的解释、总结、标题、分隔线")
        prompt_parts.append("")
        prompt_parts.append("3. 特殊情况处理：")
        prompt_parts.append("   ✓ 一个字段有多条规则：任意一条触发即判定不合格")
        prompt_parts.append("   ✓ 规则包含多个OR条件：只要满足一个即通过该规则")
        prompt_parts.append("   ✓ 规则包含AND条件：必须全部满足才通过该规则")
        prompt_parts.append("")
        prompt_parts.append("现在开始执行质检，输出结果：")
        
        return "\n".join(prompt_parts)
    
    def _parse_batch_response(self, response_content, batch_data):
        """解析批处理的响应结果 - 改进版本"""
        results = []
        lines = response_content.strip().split('\n')
        
        # 调试信息
        print(f"解析批处理响应，共 {len(lines)} 行，{len(batch_data)} 个检查项")
        print(f"响应内容前200字符: {response_content[:200]}...")
        
        for item in batch_data:
            record_idx = item['record_idx']
            field_name = item['field_name']
            field_value = item['field_value']
            kb_field_name = item['kb_field_name']
            quality_spec = item['quality_spec']
            category = item['category']
            
            # 尝试从响应中查找对应的结果
            result_found = False
            is_passed = True  # 默认假设合格
            explanation = "未找到对应结果，默认标记为合格"
            
            # 方法1: 精确匹配记录编号和字段名
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                # 检查是否包含记录编号和字段名（处理不同的格式）
                if (f"记录{record_idx}" in line and (f"字段'{kb_field_name}'" in line or f"字段\"{kb_field_name}\"" in line)) or \
                   (str(record_idx) in line and kb_field_name in line):
                    print(f"找到匹配行: {line}")
                    
                    # 解析结果
                    if "|" in line:
                        parts = line.split("|")
                        if len(parts) >= 3:
                            result = parts[2].strip()
                            explanation = parts[3].strip() if len(parts) > 3 else ""
                            is_passed = "不合格" not in result and "不符合" not in result
                            result_found = True
                            print(f"记录{record_idx} 解析结果: {result} -> {'合格' if is_passed else '不合格'}")
                            break
                    else:
                        # 如果没有分隔符，尝试直接判断
                        is_passed = "不合格" not in line and "不符合" not in line
                        explanation = line
                        result_found = True
                        print(f"记录{record_idx} 直接判断: {'合格' if is_passed else '不合格'}")
                        break
            
            # 方法2: 如果精确匹配失败，尝试模糊匹配
            if not result_found:
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                        
                    # 检查是否包含记录编号（更宽松的匹配）
                    if f"记录{record_idx}" in line or str(record_idx) in line:
                        print(f"模糊匹配找到行: {line}")
                        
                        if "|" in line:
                            parts = line.split("|")
                            if len(parts) >= 3:
                                result = parts[2].strip()
                                explanation = parts[3].strip() if len(parts) > 3 else ""
                                is_passed = "不合格" not in result and "不符合" not in result
                                result_found = True
                                print(f"记录{record_idx} 模糊解析结果: {result} -> {'合格' if is_passed else '不合格'}")
                                break
                        else:
                            # 直接判断
                            is_passed = "不合格" not in line and "不符合" not in line
                            explanation = line
                            result_found = True
                            print(f"记录{record_idx} 模糊直接判断: {'合格' if is_passed else '不合格'}")
                            break
            
            # 方法3: 如果仍然找不到，进行智能推断
            if not result_found:
                print(f"记录{record_idx} 未找到对应结果，进行智能推断...")
                
                # 检查整个响应中是否有关于这个记录的信息
                record_mentioned = False
                for line in lines:
                    if f"记录{record_idx}" in line or str(record_idx) in line:
                        record_mentioned = True
                        break
                
                if record_mentioned:
                    # 如果记录被提到但结果不明确，标记为需要人工检查
                    is_passed = False
                    explanation = "记录被提到但结果不明确，需要人工检查"
                else:
                    # 如果记录完全没有被提到，可能是大模型遗漏了，标记为合格
                    is_passed = True
                    explanation = "记录未被大模型处理，默认标记为合格"
            
            results.append({
                '记录编号': record_idx,
                '原字段': field_name,
                '映射字段': kb_field_name,
                '变量': kb_field_name,
                '值': str(field_value),
                '类别': category,
                '结果': '合格' if is_passed else '不合格',
                '说明': explanation,
                '规范': quality_spec
            })
        
        # 统计解析结果
        passed_count = sum(1 for r in results if r['结果'] == '合格')
        failed_count = sum(1 for r in results if r['结果'] == '不合格')
        print(f"批处理解析完成: 合格 {passed_count} 个，不合格 {failed_count} 个")
        
        return results
    
    def _call_llm_with_retry(self, prompt, batch_idx, total_batches):
        """带重试机制的LLM调用"""
        for attempt in range(self._max_retries):
            try:
                print(f"[批次 {batch_idx}/{total_batches}] 调用大模型API，检查字段值... (尝试 {attempt + 1}/{self._max_retries})")
                
                # 优先使用简化版方法
                response_content = self.llm_client.generate_sync_simple(prompt)
                
                if response_content and response_content.strip():
                    return response_content
                
                # 如果简化版返回空结果，尝试备用方法
                print(f"[批次 {batch_idx}/{total_batches}] 简化版返回空结果，尝试备用方法...")
                response_content = self.llm_client.generate_sync(prompt)
                
                if response_content and response_content.strip():
                    return response_content
                
                # 如果两种方法都返回空结果，等待后重试
                if attempt < self._max_retries - 1:
                    print(f"[批次 {batch_idx}/{total_batches}] 两种方法都返回空结果，等待 {self._retry_delay} 秒后重试...")
                    time.sleep(self._retry_delay)
                    continue
                    
            except Exception as e:
                error_msg = str(e)
                print(f"[批次 {batch_idx}/{total_batches}] 尝试 {attempt + 1} 失败: {error_msg}")
                
                # 如果是事件循环相关错误，增加延迟
                if "Event loop is closed" in error_msg or "asyncio" in error_msg.lower():
                    delay = self._retry_delay * (attempt + 1)  # 递增延迟
                    print(f"[批次 {batch_idx}/{total_batches}] 检测到事件循环错误，等待 {delay} 秒后重试...")
                    time.sleep(delay)
                
                # 最后一次尝试失败，返回默认结果
                if attempt == self._max_retries - 1:
                    print(f"[批次 {batch_idx}/{total_batches}] 所有重试都失败，使用默认处理")
                    return "所有记录均合格"
                
                # 等待后重试
                time.sleep(self._retry_delay)
        
        # 所有重试都失败，返回默认结果
        return "所有记录均合格"

    def _cleanup_event_loop(self):
        """清理事件循环，防止Event loop is closed错误"""
        try:
            import asyncio
            # 清理可能存在的旧循环
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.stop()
                if not loop.is_closed():
                    loop.close()
            except:
                pass
        except:
            pass

    def run_quality_check(self, db_config, table_name, fields=None, created_by="", knowledge_base_id=None, field_mappings=None, limit=None):
        """运行文本质检（批处理版本）
        
        Args:
            db_config: 数据库配置
            table_name: 表名
            fields: 字段列表
            created_by: 创建者
            knowledge_base_id: 知识库ID（保留但不使用）
            field_mappings: 字段映射字典
            limit: 数据量限制，None表示不限制
        """
        start_time = time.time()
        debug_logs = []  # 收集调试信息
        
        try:
            debug_logs.append("开始执行文本数据质检（批处理模式）...")
            
            # 1. 加载知识库数据 - 从Excel文件读取
            try:
                debug_logs.append("从Excel文件加载知识库...")
                knowledge_base = self.load_embedded_knowledge_base()
                debug_logs.append(f"成功从Excel文件加载知识库，包含 {len(knowledge_base)} 条记录")
                
                # 显示前几条知识库记录用于调试
                for i, item in enumerate(knowledge_base[:3]):
                    debug_logs.append(f"知识库记录 {i+1}: Variable='{item['Variable']}', Category='{item['Category']}'")
                    
            except Exception as kb_error:
                debug_logs.append(f"加载知识库失败: {str(kb_error)}")
                return {
                    'success': False,
                    'error': f'加载知识库失败: {str(kb_error)}',
                    'debug_logs': debug_logs
                }
            
            # 2. 从数据库读取数据进行质检
            limit_info = f"（限制 {limit} 条）" if limit else "（全量数据）"
            debug_logs.append(f"从数据库读取数据{limit_info}...")
            try:
                data_records = DatabaseService.preview_data_with_filter(
                    db_config=db_config, 
                    table_name=table_name, 
                    fields=fields,
                    limit=limit,  # 使用传入的limit参数
                    company_field=None,
                    company_value=None
                )
                
                if not data_records:
                    debug_logs.append("数据库查询结果为空")
                    return {
                        'success': False,
                        'error': '没有找到数据',
                        'debug_logs': debug_logs
                    }
                
                debug_logs.append(f"获取到 {len(data_records)} 条记录")
                
                # 显示第一条记录的字段名用于调试
                if data_records:
                    first_record = data_records[0]
                    field_names = list(first_record.keys())
                    debug_logs.append(f"数据字段: {field_names}")
                    
            except Exception as db_error:
                debug_logs.append(f"数据库查询失败: {str(db_error)}")
                return {
                    'success': False,
                    'error': f'数据库查询失败: {str(db_error)}',
                    'debug_logs': debug_logs
                }
            
            # 3. 创建知识库字段映射
            kb_map = {item['Variable']: item for item in knowledge_base if item['Variable']}
            debug_logs.append(f"知识库字段映射: {list(kb_map.keys())}")
            
            # 4. 处理字段映射（英文字段名 -> 中文描述）
            if field_mappings:
                debug_logs.append(f"使用字段映射: {field_mappings}")
            else:
                debug_logs.append("未提供字段映射，将尝试直接匹配")
            
            # 检查字段匹配情况
            if data_records:
                data_fields = set(data_records[0].keys())
                kb_fields = set(kb_map.keys())
                
                # 如果有字段映射，检查映射后的匹配情况
                if field_mappings:
                    mapped_matches = []
                    for eng_field in data_fields:
                        if eng_field in field_mappings:
                            chinese_desc = field_mappings[eng_field]
                            if chinese_desc in kb_map:
                                mapped_matches.append(f"{eng_field} -> {chinese_desc}")
                    debug_logs.append(f"字段映射匹配: {mapped_matches}")
                    if not mapped_matches:
                        debug_logs.append("字段映射后仍无法匹配知识库规则")
                else:
                    # 直接匹配
                    matched_fields = data_fields.intersection(kb_fields)
                    debug_logs.append(f"直接匹配的字段: {list(matched_fields)}")
                    if not matched_fields:
                        debug_logs.append("没有找到匹配的字段！数据库字段与知识库变量不匹配")
            
            # 5. 预处理字段映射信息
            field_mapping_info = {}
            if field_mappings:
                for eng_field, chn_desc in field_mappings.items():
                    if eng_field in data_records[0].keys() and chn_desc in kb_map:
                        field_mapping_info[eng_field] = {
                            'chinese_name': chn_desc,
                            'kb_entry': kb_map[chn_desc]
                        }
                        debug_logs.append(f"字段映射配置: {eng_field} -> {chn_desc}")
            
            # 6. 收集所有需要质检的数据项
            all_check_items = []
            for record_idx, record in enumerate(data_records, 1):
                for field_name, field_value in record.items():
                    # 确定要使用的知识库字段名
                    kb_field_name = field_name  # 默认使用原字段名
                    kb_entry = None
                    
                    # 如果有字段映射，使用预处理的映射信息
                    if field_name in field_mapping_info:
                        kb_field_name = field_mapping_info[field_name]['chinese_name']
                        kb_entry = field_mapping_info[field_name]['kb_entry']
                    
                    # 检查字段是否在知识库中（优先使用预处理的映射信息）
                    if kb_entry or kb_field_name in kb_map:
                        if not kb_entry:
                            kb_entry = kb_map[kb_field_name]
                            
                        quality_spec = kb_entry['质量规范描述']
                        category = kb_entry['Category']
                        
                        all_check_items.append({
                            'record_idx': record_idx,
                            'field_name': field_name,
                            'field_value': field_value,
                            'kb_field_name': kb_field_name,
                            'quality_spec': quality_spec,
                            'category': category
                        })
            
            debug_logs.append(f"📋 将处理 {len(all_check_items)} 个字段值，使用批处理模式（每{self.batch_size}条）")
            debug_logs.append("--- 开始执行批处理质检 ---")
            
            # 7. 预处理井名字段（使用正则表达式，不调用大模型）
            debug_logs.append("🔍 开始预处理井名字段...")
            well_name_results, remaining_items = self._preprocess_well_name_fields(all_check_items)
            quality_results = well_name_results.copy()  # 先保存井名验证结果
            
            debug_logs.append(f"✅ 井名预处理完成: 正则验证 {len(well_name_results)} 个，待大模型检查 {len(remaining_items)} 个")
            
            # 8. 批处理质检（只处理非井名字段）
            if remaining_items:
                total_batches = (len(remaining_items) + self.batch_size - 1) // self.batch_size
                
                for batch_idx in range(total_batches):
                    start_idx = batch_idx * self.batch_size
                    end_idx = min(start_idx + self.batch_size, len(remaining_items))
                    batch_items = remaining_items[start_idx:end_idx]
                    
                    debug_logs.append(f"处理批次 {batch_idx + 1}/{total_batches}，包含 {len(batch_items)} 个检查项")
                    
                    # 创建批处理的prompt
                    batch_prompt = self._create_batch_prompt(batch_items, field_mapping_info, kb_map)
                    
                    # 调用大模型进行批处理质检（带重试机制）
                    response_content = self._call_llm_with_retry(batch_prompt, batch_idx + 1, total_batches)
                    
                    # 解析批处理结果
                    batch_results = self._parse_batch_response(response_content, batch_items)
                    quality_results.extend(batch_results)
                    
                    print(f"[批次 {batch_idx + 1}/{total_batches}] 完成，解析到 {len(batch_results)} 个结果")
                    
                    # 批次间延迟，避免API调用过于频繁
                    if batch_idx < total_batches - 1:
                        time.sleep(0.5)
            else:
                debug_logs.append("✅ 所有字段都是井名字段，无需调用大模型")
                total_batches = 0
            
            # 9. 输出处理完成信息
            debug_logs.append(f"✅ 批处理质检完成！共处理 {len(quality_results)} 个字段值")
            debug_logs.append("--- 质检结果统计 ---")
            
            # 10. 计算统计信息
            total_count = len(quality_results)
            passed_count = sum(1 for r in quality_results if r['结果'] == '合格')
            failed_count = sum(1 for r in quality_results if r['结果'] == '不合格')
            error_count = sum(1 for r in quality_results if r['结果'] == '检查失败')
            pass_rate = (passed_count / total_count * 100) if total_count > 0 else 0
            execution_time = time.time() - start_time
            
            # 统计井名验证结果
            well_name_count = len(well_name_results)
            well_name_passed = sum(1 for r in well_name_results if r['结果'] == '合格')
            well_name_failed = sum(1 for r in well_name_results if r['结果'] == '不合格')
            
            print(f"\n=== 批处理质检完成 ===")
            print(f"总检查项: {total_count}")
            print(f"井名正则验证: {well_name_count} 个 (合格: {well_name_passed}, 不合格: {well_name_failed})")
            print(f"大模型检查: {len(remaining_items)} 个")
            print(f"合格: {passed_count}")
            print(f"不合格: {failed_count}")
            print(f"检查失败: {error_count}")
            print(f"合格率: {pass_rate:.2f}%")
            print(f"执行时间: {execution_time:.2f}秒")
            print(f"批处理数: {total_batches}")
            
            # 11. 保存结果到数据库
            result_id = self._save_quality_results(
                quality_results, 
                db_config, 
                table_name, 
                created_by,
                passed_count,
                failed_count,
                pass_rate,
                execution_time
            )
            
            # 12. 最终清理事件循环
            print("质检完成，执行最终清理...")
            self._cleanup_event_loop()
            
            return {
                'success': True,
                'data': {
                    'id': result_id,
                    'results': quality_results,
                    'total_records': total_count,
                    'passed_records': passed_count,
                    'failed_records': failed_count,
                    'pass_rate': round(pass_rate, 2),
                    'execution_time': round(execution_time, 2),
                    'total_batches': total_batches,
                    'batch_size': self.batch_size,
                    'reports': self._generate_reports(quality_results),
                    'debug_logs': debug_logs  # 添加调试日志
                }
            }
            
        except Exception as e:
            debug_logs.append(f"质检流程失败: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'debug_logs': debug_logs
            }
    
    def _generate_reports(self, quality_results):
        """生成报告格式"""
        reports = {}
        
        # 按字段分组统计
        for result in quality_results:
            field_name = result['变量']
            if field_name not in reports:
                reports[field_name] = {
                    'rule_name': f"文本质检-{field_name}",
                    'rule_type': 'text_quality',
                    'field_name': field_name,
                    'passed_count': 0,
                    'failed_count': 0,
                    'error_details': []
                }
            
            if result['结果'] == '合格':
                reports[field_name]['passed_count'] += 1
            else:
                reports[field_name]['failed_count'] += 1
                reports[field_name]['error_details'].append({
                    'row': result['记录编号'],
                    'value': result['值'],
                    'message': result['说明']
                })
        
        return list(reports.values())
    
    def _save_quality_results(self, results, db_config, table_name, created_by, 
                             passed_count, failed_count, pass_rate, execution_time):
        """保存质检结果到数据库"""
        try:
            # 保存主结果
            result = QualityResult(
                rule_library_id=None,  # 文本质检不使用规则库
                data_source=db_config.get('name', 'unknown'),
                table_name=table_name,
                total_records=len(results),
                passed_records=passed_count,
                failed_records=failed_count,
                pass_rate=pass_rate,
                execution_time=execution_time,
                created_by=created_by,
                check_type='text_llm'  # 标记为文本LLM检查
            )
            
            db.session.add(result)
            db.session.flush()
            
            # 保存详细报告
            for item in results:
                report = QualityReport(
                    result_id=result.id,
                    rule_name=f"文本质检-{item['变量']}",
                    rule_type='text_quality_check',
                    field_name=item['变量'],
                    passed_count=1 if item['结果'] == '合格' else 0,
                    failed_count=1 if item['结果'] == '不合格' else 0
                )
                
                if item['结果'] != '合格':
                    error_details = [{
                        'record': item['记录编号'],
                        'value': item['值'],
                        'message': item['说明'],
                        'standard': item['规范']
                    }]
                    report.set_error_details(error_details)
                
                db.session.add(report)
            
            db.session.commit()
            print(f"质检结果已保存到数据库，结果ID: {result.id}")
            return result.id
            
        except Exception as e:
            db.session.rollback()
            print(f"保存质检结果失败: {str(e)}")
            return None

    def optimize_knowledge_base(self):
        """优化知识库结构，提高大模型识别效果"""
        try:
            # 获取知识库文件路径
            base_dir = os.path.dirname(os.path.dirname(__file__))
            base_dir = os.path.dirname(base_dir)
            kb_path = os.path.join(base_dir, '文本型知识库.xlsx')
            
            if not os.path.exists(kb_path):
                raise FileNotFoundError(f"知识库文件未找到: {kb_path}")
            
            # 读取Excel文件
            df = pd.read_excel(kb_path)
            
            # 优化建议
            optimization_suggestions = []
            
            # 1. 检查字段完整性
            required_columns = ['Variable', 'Category', '质量规范描述']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                optimization_suggestions.append(f"缺少必需列: {missing_columns}")
            
            # 2. 检查数据质量
            if 'Variable' in df.columns:
                # 检查变量名是否规范
                invalid_variables = []
                for idx, var in enumerate(df['Variable']):
                    if pd.isna(var) or str(var).strip() == '':
                        invalid_variables.append(f"第{idx+1}行: 变量名为空")
                    elif len(str(var)) > 50:
                        invalid_variables.append(f"第{idx+1}行: 变量名过长({len(str(var))}字符)")
                
                if invalid_variables:
                    optimization_suggestions.extend(invalid_variables)
            
            # 3. 检查类别标准化
            if 'Category' in df.columns:
                valid_categories = ['数值型', '文本型', '日期型', '枚举型', '布尔型']
                invalid_categories = []
                for idx, cat in enumerate(df['Category']):
                    if pd.isna(cat) or str(cat).strip() == '':
                        invalid_categories.append(f"第{idx+1}行: 类别为空")
                    elif str(cat) not in valid_categories:
                        invalid_categories.append(f"第{idx+1}行: 类别'{cat}'不在标准类别中")
                
                if invalid_categories:
                    optimization_suggestions.extend(invalid_categories)
            
            # 4. 检查质量规范描述
            if '质量规范描述' in df.columns:
                poor_descriptions = []
                for idx, desc in enumerate(df['质量规范描述']):
                    if pd.isna(desc) or str(desc).strip() == '':
                        poor_descriptions.append(f"第{idx+1}行: 质量规范描述为空")
                    elif len(str(desc)) < 10:
                        poor_descriptions.append(f"第{idx+1}行: 质量规范描述过短({len(str(desc))}字符)")
                    elif len(str(desc)) > 500:
                        poor_descriptions.append(f"第{idx+1}行: 质量规范描述过长({len(str(desc))}字符)")
                
                if poor_descriptions:
                    optimization_suggestions.extend(poor_descriptions)
            
            # 5. 生成优化后的知识库
            if optimization_suggestions:
                print("发现知识库问题，建议优化:")
                for suggestion in optimization_suggestions:
                    print(f"  - {suggestion}")
                
                # 创建优化后的知识库
                optimized_df = self._create_optimized_knowledge_base(df)
                
                # 保存优化后的知识库
                optimized_path = os.path.join(base_dir, '文本型知识库_优化版.xlsx')
                optimized_df.to_excel(optimized_path, index=False)
                print(f"优化后的知识库已保存到: {optimized_path}")
                
                return {
                    'success': True,
                    'message': '知识库优化完成',
                    'issues_found': len(optimization_suggestions),
                    'suggestions': optimization_suggestions,
                    'optimized_file': '文本型知识库_优化版.xlsx'
                }
            else:
                return {
                    'success': True,
                    'message': '知识库结构良好，无需优化',
                    'issues_found': 0,
                    'suggestions': []
                }
                
        except Exception as e:
            print(f"知识库优化失败: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _create_optimized_knowledge_base(self, original_df):
        """创建优化后的知识库"""
        optimized_data = []
        
        for idx, row in original_df.iterrows():
            # 标准化变量名
            variable = str(row.get('Variable', '')).strip()
            if not variable:
                variable = f"未命名变量_{idx+1}"
            
            # 标准化类别
            category = str(row.get('Category', '')).strip()
            if not category or category not in ['数值型', '文本型', '日期型', '枚举型', '布尔型']:
                category = '文本型'  # 默认类别
            
            # 优化质量规范描述
            description = str(row.get('质量规范描述', '')).strip()
            if not description:
                description = f"{category}字段，需要符合基本格式要求"
            elif len(description) < 10:
                description = f"{description}，需要符合{category}字段的基本规范"
            elif len(description) > 500:
                description = description[:497] + "..."
            
            # 添加新的优化字段
            optimized_row = {
                'Variable': variable,
                'Category': category,
                '质量规范描述': description,
                '数据类型': self._infer_data_type(category),
                '验证规则': self._generate_validation_rule(category, description),
                '示例值': self._generate_example_value(category),
                '错误提示': self._generate_error_message(category, description)
            }
            
            optimized_data.append(optimized_row)
        
        return pd.DataFrame(optimized_data)
    
    def _infer_data_type(self, category):
        """根据类别推断数据类型"""
        type_mapping = {
            '数值型': 'float/int',
            '文本型': 'string',
            '日期型': 'datetime',
            '枚举型': 'string',
            '布尔型': 'boolean'
        }
        return type_mapping.get(category, 'string')
    
    def _generate_validation_rule(self, category, description):
        """生成验证规则"""
        if category == '数值型':
            return "必须是有效数值，不能为空"
        elif category == '日期型':
            return "必须是有效日期格式(YYYY-MM-DD或YYYY/MM/DD)"
        elif category == '文本型':
            return "不能为空，长度不超过1000字符"
        elif category == '枚举型':
            return "必须在允许值范围内"
        elif category == '布尔型':
            return "必须是true/false或0/1"
        else:
            return "符合基本格式要求"
    
    def _generate_example_value(self, category):
        """生成示例值"""
        example_mapping = {
            '数值型': '123.45',
            '文本型': '示例文本',
            '日期型': '2024-01-01',
            '枚举型': '选项A',
            '布尔型': 'true'
        }
        return example_mapping.get(category, '示例值')
    
    def _generate_error_message(self, category, description):
        """生成错误提示信息"""
        if category == '数值型':
            return f"字段值必须是有效数值: {description}"
        elif category == '日期型':
            return f"字段值必须是有效日期格式: {description}"
        elif category == '文本型':
            return f"字段值不符合文本规范: {description}"
        elif category == '枚举型':
            return f"字段值不在允许范围内: {description}"
        elif category == '布尔型':
            return f"字段值必须是布尔类型: {description}"
        else:
            return f"字段值不符合规范: {description}"
