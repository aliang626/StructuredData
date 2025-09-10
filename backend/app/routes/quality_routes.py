from flask import Blueprint, request, jsonify
from app.services.quality_service import QualityService
from app.services.text_quality_service import TextQualityService
from app.models.quality_result import QualityResult
import traceback

bp = Blueprint('quality', __name__)

@bp.route('/check', methods=['POST'])
def run_quality_check():
    """运行质量检测"""
    try:
        data = request.get_json()
        
        # 版本号改为可选：如果不传，将在服务端自动选择该库最新版本
        required_fields = ['rule_library_id', 'db_config', 'table_name']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'缺少必需字段: {field}'
                }), 400
        
        result = QualityService.run_quality_check(
            rule_library_id=data['rule_library_id'],
            version_id=data.get('version_id'),
            db_config=data['db_config'],
            table_name=data['table_name'],
            fields=data.get('fields'),
            created_by=data.get('created_by', '')
        )
        
        return jsonify({
            'success': True,
            'data': result
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

@bp.route('/results', methods=['GET'])
def get_quality_results():
    """获取质量检测结果"""
    try:
        rule_library_id = request.args.get('rule_library_id', type=int)
        limit = request.args.get('limit', 50, type=int)
        
        results = QualityService.get_quality_results(rule_library_id, limit)
        
        return jsonify({
            'success': True,
            'data': results
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/results/<int:result_id>', methods=['GET'])
def get_quality_report(result_id):
    """获取质量检测详细报告"""
    try:
        report = QualityService.get_quality_report(result_id)
        
        return jsonify({
            'success': True,
            'data': report
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/results/<int:result_id>', methods=['DELETE'])
def delete_quality_result(result_id):
    """删除质量检测结果"""
    try:
        success = QualityService.delete_quality_result(result_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': '质量检测结果删除成功'
            })
        else:
            return jsonify({
                'success': False,
                'error': '质量检测结果不存在或删除失败'
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/compare', methods=['POST'])
def compare_quality_results():
    """比较两个质量检测结果"""
    try:
        data = request.get_json()
        
        required_fields = ['result_id_1', 'result_id_2']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'缺少必需字段: {field}'
                }), 400
        
        comparison = QualityService.compare_quality_results(
            data['result_id_1'],
            data['result_id_2']
        )
        
        return jsonify({
            'success': True,
            'data': comparison
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/batch-check', methods=['POST'])
def batch_quality_check():
    """批量质量检测"""
    try:
        data = request.get_json()
        
        # 版本号改为可选
        required_fields = ['rule_library_id', 'db_config', 'tables']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'缺少必需字段: {field}'
                }), 400
        
        results = QualityService.batch_quality_check(
            rule_library_id=data['rule_library_id'],
            version_id=data.get('version_id'),
            db_config=data['db_config'],
            tables=data['tables'],
            fields_map=data.get('fields_map'),
            created_by=data.get('created_by', '')
        )
        
        return jsonify({
            'success': True,
            'data': results
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/results/<int:result_id>/failed-records', methods=['GET'])
def get_failed_records(result_id):
    """获取质量检测失败记录的详细数据"""
    try:
        failed_records = QualityService.get_failed_records(result_id)
        
        return jsonify({
            'success': True,
            'data': failed_records
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/statistics', methods=['GET'])
def get_quality_statistics():
    """获取质量检测统计信息"""
    try:
        rule_library_id = request.args.get('rule_library_id', type=int)
        days = request.args.get('days', 30, type=int)
        
        statistics = QualityService.get_quality_statistics(rule_library_id, days)
        
        return jsonify({
            'success': True,
            'data': statistics
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/anomaly-data', methods=['GET'])
def get_anomaly_data():
    """获取异常数据"""
    try:
        result_id = request.args.get('result_id', type=int)
        limit = request.args.get('limit', 100, type=int)
        
        anomaly_data = QualityService.get_anomaly_data(result_id, limit)
        
        return jsonify({
            'success': True,
            'data': anomaly_data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/results/<int:result_id>/detail', methods=['GET'])
def get_quality_result_detail(result_id):
    """获取质量检测结果详情"""
    try:
        detail = QualityService.get_quality_report(result_id)
        
        return jsonify({
            'success': True,
            'data': detail
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/text-check', methods=['POST'])
def run_text_quality_check():
    """运行文本数据质检（基于大模型和内嵌知识库）"""
    try:
        data = request.get_json()
        
        required_fields = ['db_config', 'table_name']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'缺少必需字段: {field}'
                }), 400
        
        # 获取批处理大小参数
        batch_size = data.get('batch_size', 100)  # 默认100条
        # 验证批处理大小
        if batch_size and (batch_size < 10 or batch_size > 1000):
            return jsonify({
                'success': False,
                'error': '批处理大小必须在10-1000之间'
            }), 400
        
        # 创建文本质检服务实例
        text_service = TextQualityService(batch_size=batch_size)
        
        # 运行文本质检
        result = text_service.run_quality_check(
            db_config=data['db_config'],
            table_name=data['table_name'],
            fields=data.get('fields'),
            created_by=data.get('created_by', ''),
            field_mappings=data.get('field_mappings')  # 添加字段映射参数
        )
        
        return jsonify(result)
        
    except Exception as e:
        print(f"文本质检失败: {str(e)}")
        print(f"错误详情: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

@bp.route('/knowledge-base/preview', methods=['GET'])
def preview_embedded_knowledge_base():
    """预览Excel知识库内容"""
    try:
        # 创建文本质检服务实例
        text_service = TextQualityService()
        
        # 从Excel文件加载知识库
        knowledge_base = text_service.load_embedded_knowledge_base()
        
        # 获取搜索参数
        search_query = request.args.get('search', '').strip()
        category_filter = request.args.get('category', '').strip()
        
        # 应用搜索和过滤
        filtered_entries = knowledge_base
        if search_query:
            filtered_entries = [
                entry for entry in knowledge_base
                if (search_query.lower() in entry['Variable'].lower() or 
                    search_query.lower() in entry['质量规范描述'].lower())
            ]
        
        if category_filter:
            filtered_entries = [
                entry for entry in filtered_entries
                if category_filter.lower() in entry['Category'].lower()
            ]
        
        # 返回更多记录用于搜索
        preview_limit = min(200, len(filtered_entries))
        
        return jsonify({
            'success': True,
            'data': {
                'source': "Excel文件",
                'total_count': len(knowledge_base),
                'filtered_count': len(filtered_entries),
                'entries': filtered_entries[:preview_limit],
                'has_more': len(filtered_entries) > preview_limit
            }
        })
        
    except Exception as e:
        print(f"预览Excel知识库失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/knowledge-base/search', methods=['GET'])
def search_knowledge_base():
    """搜索知识库内容"""
    try:
        # 创建文本质检服务实例
        text_service = TextQualityService()
        
        # 从Excel文件加载知识库
        knowledge_base = text_service.load_embedded_knowledge_base()
        
        # 获取搜索参数
        search_query = request.args.get('q', '').strip()
        category_filter = request.args.get('category', '').strip()
        limit = min(int(request.args.get('limit', 50)), 200)  # 最大200条
        
        # 应用搜索和过滤
        filtered_entries = knowledge_base
        if search_query:
            filtered_entries = [
                entry for entry in knowledge_base
                if (search_query.lower() in entry['Variable'].lower() or 
                    search_query.lower() in entry['质量规范描述'].lower() or
                    search_query.lower() in entry['Category'].lower())
            ]
        
        if category_filter:
            filtered_entries = [
                entry for entry in filtered_entries
                if category_filter.lower() in entry['Category'].lower()
            ]
        
        # 返回搜索结果
        return jsonify({
            'success': True,
            'data': {
                'query': search_query,
                'category': category_filter,
                'total_count': len(knowledge_base),
                'filtered_count': len(filtered_entries),
                'results': filtered_entries[:limit],
                'has_more': len(filtered_entries) > limit
            }
        })
        
    except Exception as e:
        print(f"搜索知识库失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/knowledge-base/categories', methods=['GET'])
def get_knowledge_base_categories():
    """获取知识库的所有类别"""
    try:
        # 创建文本质检服务实例
        text_service = TextQualityService()
        
        # 从Excel文件加载知识库
        knowledge_base = text_service.load_embedded_knowledge_base()
        
        # 提取所有类别
        categories = list(set(entry['Category'] for entry in knowledge_base if entry['Category']))
        categories.sort()
        
        return jsonify({
            'success': True,
            'data': {
                'categories': categories,
                'total_count': len(categories)
            }
        })
        
    except Exception as e:
        print(f"获取知识库类别失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/knowledge-base/optimize', methods=['POST'])
def optimize_knowledge_base():
    """优化知识库结构，提高大模型识别效果"""
    try:
        from app.services.text_quality_service import TextQualityService
        
        # 创建文本质检服务实例
        text_service = TextQualityService()
        
        # 运行知识库优化
        result = text_service.optimize_knowledge_base()
        
        return jsonify(result)
        
    except Exception as e:
        print(f"知识库优化失败: {str(e)}")
        print(f"错误详情: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

@bp.route('/results/<int:result_id>/failed-data', methods=['GET'])
def get_failed_data(result_id):
    """获取质检结果中的不合格数据（分页）"""
    try:
        from flask import request
        
        # 获取分页参数
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('pageSize', 10))
        
        # 参数验证
        if page < 1:
            page = 1
        if page_size < 1 or page_size > 100:
            page_size = 10
        
        # 由于文本质检的结果可能不在数据库中，我们需要从质检服务获取
        # 这里我们返回一个模拟的不合格数据结构，实际使用时需要根据具体情况调整
        
        # 模拟不合格数据（实际应该从质检结果中获取）
        failed_data = [
            {
                'id': f'failed_{i}',
                'row': i + 1,
                'field': '井名',
                'value': f'ABC{i+1}',
                'rule': '井名格式验证',
                'message': '井名格式不符合规范',
                'result': '不合格',
                'timestamp': '2024-01-01 10:00:00'
            }
            for i in range(25)  # 模拟25条不合格数据
        ]
        
        # 计算分页
        total = len(failed_data)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        
        # 分页数据
        paginated_data = failed_data[start_idx:end_idx]
        
        return jsonify({
            'success': True,
            'data': paginated_data,
            'total': total,
            'page': page,
            'pageSize': page_size,
            'totalPages': (total + page_size - 1) // page_size,
            'hasNext': end_idx < total,
            'hasPrev': page > 1
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

