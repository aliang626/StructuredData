<template>
  <div class="training-history-container">
    <!-- 页面标题 -->
    <div class="page-header">
      <h2>训练历史记录</h2>
      <p>查看和管理机器学习模型的训练历史，导出异常值检测报告</p>
    </div>

    <!-- 训练历史区域 -->
    <div class="history-wrapper">
        <el-card class="training-history-card">
          <template #header>
            <div class="card-header">
              <span>训练历史记录</span>
              <div>
                <el-button type="primary" size="small" @click="refreshHistory">
                  <el-icon><Refresh /></el-icon>
                  刷新
                </el-button>
              </div>
            </div>
          </template>
          
          <div class="history-content">
            <!-- 筛选器 -->
            <div class="history-filters">
              <el-row :gutter="10">
                <el-col :span="12">
                  <el-select v-model="historyFilter.model_type" placeholder="模型类型" size="small" clearable @change="refreshHistory">
                    <el-option label="回归模型" value="regression" />
                    <el-option label="聚类模型" value="clustering" />
                  </el-select>
                </el-col>
                <el-col :span="12">
                  <el-select v-model="historyFilter.algorithm" placeholder="算法" size="small" clearable @change="refreshHistory">
                    <el-option v-for="algo in allAlgorithms" :key="algo.value" :label="algo.label" :value="algo.value" />
                  </el-select>
                </el-col>
              </el-row>
            </div>
            
            <!-- 历史记录列表 -->
            <div v-if="trainingHistories.length > 0" class="history-list">
              <el-timeline class="history-timeline">
                <el-timeline-item
                  v-for="history in trainingHistories"
                  :key="history.id"
                  :timestamp="formatDate(history.created_at)"
                  placement="top"
                  type="primary"
                >
                  <el-card :body-style="{ padding: '10px' }" shadow="hover" @click="showHistoryDetail(history)" class="history-item">
                    <div class="history-header">
                      <div class="history-title">
                        <el-tag :type="getModelTypeTag(history.model_type)" size="small">
                          {{ getModelTypeName(history.model_type) }}
                        </el-tag>
                        <span class="model-name">{{ history.model_name }}</span>
                      </div>
                      <div class="history-meta">
                        <el-tag size="small">{{ getAlgorithmName(history.algorithm) }}</el-tag>
                      </div>
                    </div>
                    
                    <div class="history-info">
                      <div class="info-item">
                        <span class="label">数据表:</span>
                        <span>{{ history.table_name }}</span>
                      </div>
                      <div class="info-item">
                        <span class="label">特征数:</span>
                        <span>{{ history.feature_columns.length }}个</span>
                      </div>
                      <div v-if="history.outlier_summary && history.outlier_summary.total_outliers > 0" class="info-item outlier-info">
                        <span class="label">异常值:</span>
                        <span class="outlier-count">{{ history.outlier_summary.total_outliers }}个 ({{ history.outlier_summary.outlier_rate?.toFixed(2) }}%)</span>
                        <el-button 
                          type="text" 
                          size="small" 
                          @click.stop="quickExportOutliers(history)"
                          class="quick-export-btn"
                        >
                          <el-icon><Download /></el-icon>
                          快速导出
                        </el-button>
                      </div>
                    </div>
                  </el-card>
                </el-timeline-item>
              </el-timeline>
            </div>
            
            <div v-else class="no-history">
              <el-empty description="暂无训练历史记录" />
            </div>
          </div>
        </el-card>
    </div>
    
    <!-- 训练历史详情对话框 -->
    <el-dialog 
      v-model="historyDetailVisible" 
      title="训练历史详情" 
      width="80%" 
      :close-on-click-modal="false"
    >
      <div v-if="selectedHistory" class="history-detail">
        <!-- 基础信息 -->
        <el-descriptions title="基础信息" :column="3" border>
          <el-descriptions-item label="模型名称">{{ selectedHistory.model_name }}</el-descriptions-item>
          <el-descriptions-item label="模型类型">{{ getModelTypeName(selectedHistory.model_type) }}</el-descriptions-item>
          <el-descriptions-item label="算法">{{ getAlgorithmName(selectedHistory.algorithm) }}</el-descriptions-item>
          <el-descriptions-item label="数据表">{{ selectedHistory.table_name }}</el-descriptions-item>
          <el-descriptions-item label="训练时间">{{ formatDate(selectedHistory.created_at) }}</el-descriptions-item>
          <el-descriptions-item label="创建者">{{ selectedHistory.created_by }}</el-descriptions-item>
        </el-descriptions>
        
        <!-- 数据信息 -->
        <el-descriptions title="数据信息" :column="2" border style="margin-top: 20px;">
          <el-descriptions-item label="总样本数">{{ selectedHistory.data_info?.total_samples || 0 }}</el-descriptions-item>
          <el-descriptions-item label="特征数量">{{ selectedHistory.feature_columns?.length || 0 }}</el-descriptions-item>
          <el-descriptions-item label="训练样本">{{ selectedHistory.data_info?.training_samples || 0 }}</el-descriptions-item>
          <el-descriptions-item label="测试样本">{{ selectedHistory.data_info?.test_samples || 0 }}</el-descriptions-item>
        </el-descriptions>
        
        <!-- 特征字段 -->
        <div style="margin-top: 20px;">
          <h4>特征字段</h4>
          <el-tag v-for="feature in selectedHistory.feature_columns" :key="feature" style="margin: 2px;">
            {{ feature }}
          </el-tag>
        </div>
        
        <!-- 模型参数 -->
        <div style="margin-top: 20px;">
          <h4>模型参数</h4>
          <el-table :data="getParameterTableData(selectedHistory.parameters)" size="small" border>
            <el-table-column prop="name" label="参数名" />
            <el-table-column prop="value" label="参数值" />
          </el-table>
        </div>
        
        <!-- 评估指标 -->
        <div style="margin-top: 20px;">
          <h4>评估指标</h4>
          <el-table :data="getMetricsTableData(selectedHistory.metrics)" size="small" border>
            <el-table-column prop="name" label="指标名" />
            <el-table-column prop="value" label="指标值" />
          </el-table>
        </div>
        
        <!-- 异常值信息 -->
        <div v-if="selectedHistory.outlier_summary && selectedHistory.outlier_summary.total_outliers > 0" style="margin-top: 20px;">
          <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 15px;">
            <h4 style="margin: 0; color: #E74C3C;">
              <el-icon style="margin-right: 8px;"><Warning /></el-icon>
              异常值检测结果
            </h4>
            <el-tag type="danger" size="large">
              发现 {{ selectedHistory.outlier_summary.total_outliers }} 个异常值
            </el-tag>
          </div>
          
          <el-alert
            :title="`检测到 ${selectedHistory.outlier_summary.total_outliers} 个异常值 (占比 ${selectedHistory.outlier_summary.outlier_rate?.toFixed(2)}%)`"
            type="warning"
            :closable="false"
            style="margin-bottom: 15px;"
          >
            <template #default>
              <div style="margin-top: 8px;">
                <strong>检测方法：</strong>{{ selectedHistory.outlier_summary.detection_method === 'geographic_grid' ? '地理网格法' : '残差3σ法' }}
                <br/>
                <strong>建议：</strong>{{ selectedHistory.outlier_summary.detection_method === 'geographic_grid' ? '检查地理坐标数据的准确性，确认是否存在定位错误' : '检查异常值数据是否为测量误差或异常情况' }}
              </div>
            </template>
          </el-alert>
          
          <el-descriptions :column="3" border>
            <el-descriptions-item label="异常值数量">
              <el-tag type="danger">{{ selectedHistory.outlier_summary.total_outliers }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="异常值比例">
              <el-tag :type="selectedHistory.outlier_summary.outlier_rate > 10 ? 'danger' : selectedHistory.outlier_summary.outlier_rate > 5 ? 'warning' : 'success'">
                {{ selectedHistory.outlier_summary.outlier_rate?.toFixed(2) }}%
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="检测方法">
              <el-tag type="info">{{ selectedHistory.outlier_summary.detection_method === 'geographic_grid' ? '地理网格法' : '残差3σ法' }}</el-tag>
            </el-descriptions-item>
          </el-descriptions>
          
          <div style="margin-top: 15px; display: flex; gap: 10px;">
            <el-button type="primary" @click="exportHistoryOutliers" :loading="exportingHistoryReport">
              <el-icon><Download /></el-icon>
              导出完整异常值报告
            </el-button>
            <el-button type="success" @click="viewOutlierDetails">
              <el-icon><View /></el-icon>
              查看异常值详情
            </el-button>
          </div>
        </div>
        
        <!-- 无异常值时的提示 -->
        <div v-else style="margin-top: 20px;">
          <el-alert
            title="未检测到异常值"
            type="success"
            :closable="false"
          >
            <template #default>
              该模型训练过程中未发现明显的异常值，数据质量良好。
            </template>
          </el-alert>
        </div>
      </div>
      
      <template #footer>
        <el-button @click="historyDetailVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, onMounted, computed } from 'vue'
import { Folder, Setting, Refresh, Download, Warning, View } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

import axios from 'axios'

export default {
  name: 'ModelConfig',
  components: {
    Folder,
    Setting,
    Refresh,
    Download,
    Warning,
    View
  },
  setup() {
    const availableModels = ref({})
    const selectedModel = ref(null)
    const selectedFields = ref([])
    const previewData = ref([])
    
    // 训练历史相关
    const trainingHistories = ref([])
    const selectedHistory = ref(null)
    const historyDetailVisible = ref(false)
    const exportingHistoryReport = ref(false)
    const historyFilter = reactive({
      model_type: '',
      algorithm: '',
      table_name: ''
    })
    
    const modelForm = reactive({
      name: '',
      description: '',
      parameters: {}
    })
    
    const treeProps = {
      children: 'children',
      label: 'name'
    }
    
    // 动态获取模型树，只保留指定回归和聚类算法
    const modelTree = computed(() => {
      // 只保留需要的回归模型key
      const allowedRegression = [
        'LinearRegression',
        'PolynomialRegression',
        'RandomForestRegressor',
        'SVR',
        'XGBoostRegressor'
      ];
      // 只保留需要的聚类模型key
      const allowedClustering = [
        'DBSCAN',
        'LOF',
        'IsolationForest',
        'OneClassSVM',
        'KMeans'
      ];
      return [
        {
          id: 'regression',
          name: '回归模型',
          type: 'category',
          children: Object.entries(availableModels.value.regression || {})
            .filter(([key]) => allowedRegression.includes(key))
            .map(([key, model]) => ({
              id: key,
              name: model.name,
              type: 'model',
              ...model
            }))
        },
        {
          id: 'clustering',
          name: '聚类模型',
          type: 'category',
          children: Object.entries(availableModels.value.clustering || {})
            .filter(([key]) => allowedClustering.includes(key))
            .map(([key, model]) => ({
              id: key,
              name: model.name,
              type: 'model',
              ...model
            }))
        }
      ]
    })
    
    // 所有算法列表（用于筛选）
    const allAlgorithms = computed(() => {
      const algorithms = []
      
      // 回归算法
      const regressionAlgos = [
        { value: 'LinearRegression', label: '线性回归' },
        { value: 'PolynomialRegression', label: '多项式回归' },
        { value: 'RandomForestRegressor', label: '随机森林回归' },
        { value: 'SVR', label: '支持向量回归' },
        { value: 'XGBoostRegressor', label: 'XGBoost回归' }
      ]
      
      // 聚类算法
      const clusteringAlgos = [
        { value: 'KMeans', label: 'K均值聚类' },
        { value: 'DBSCAN', label: 'DBSCAN聚类' },
        { value: 'LOF', label: '局部异常因子' },
        { value: 'IsolationForest', label: '孤立森林' },
        { value: 'OneClassSVM', label: '单类SVM' }
      ]
      
      return [...regressionAlgos, ...clusteringAlgos]
    })
    
    // 加载可用模型
    const loadAvailableModels = async () => {
      try {
        const response = await axios.get('/api/models/available')
        if (response.data.success) {
          availableModels.value = response.data.data
        }
      } catch (error) {
        ElMessage.error('加载可用模型失败')
      }
    }
    
    
    
    // 修改 handleModelChange，记录 parentType
    const handleModelChange = (data, node) => {
      if (data.type === 'model') {
        selectedModel.value = { ...data, parentType: node.parent.data.id }
        modelForm.name = data.name
        modelForm.description = data.description
        modelForm.parameters = {}
        
        // 初始化参数默认值
        Object.entries(data.parameters).forEach(([key, param]) => {
          modelForm.parameters[key] = param.default_value
        })
      }
    }
    
    
    
    const resetParameters = () => {
      if (selectedModel.value) {
        Object.entries(selectedModel.value.parameters).forEach(([key, param]) => {
          modelForm.parameters[key] = param.default_value
        })
        ElMessage.success('参数已重置为默认值')
      }
    }
    
    // 保存时用 parentType 作为 model_type
    const saveModelConfig = async () => {
      if (!selectedModel.value) {
        ElMessage.warning('请先选择一个模型')
        return
      }
      
      if (!modelForm.name.trim()) {
        ElMessage.warning('请输入配置名称')
        return
      }
      
      try {
        const configData = {
          name: modelForm.name.trim(),
          model_type: selectedModel.value.parentType, // 正确的模型分类
          model_name: selectedModel.value.id,
          parameters: modelForm.parameters,
          description: modelForm.description || ''
        }
        
        console.log('正在保存配置:', configData)
        
        // 调用API保存配置
        const response = await axios.post('/api/models/configs', configData)
        
        if (response.data.success) {
          ElMessage.success('配置保存成功！')
          console.log('保存成功，返回数据:', response.data.data)
          
          // 清空表单
          modelForm.name = ''
          modelForm.description = ''
          modelForm.parameters = {}
          selectedModel.value = null
          
          // 可选：跳转到配置列表页面
          // this.$router.push('/model-list')
        } else {
          console.error('保存失败:', response.data.error)
          ElMessage.error(`保存失败: ${response.data.error}`)
        }
      } catch (error) {
        console.error('保存配置时发生错误:', error)
        if (error.response) {
          // 服务器返回了错误响应
          const errorMsg = error.response.data?.error || '服务器错误'
          ElMessage.error(`保存失败: ${errorMsg}`)
        } else if (error.request) {
          // 请求发送失败
          ElMessage.error('网络连接失败，请检查网络连接')
        } else {
          // 其他错误
          ElMessage.error('保存配置失败，请重试')
        }
      }
    }
    
    const refreshPreview = async () => {
      if (selectedFields.value.length === 0) {
        ElMessage.warning('请先选择字段')
        return
      }
      
      if (!selectedDataSource.value || !selectedTable.value) {
        ElMessage.warning('请先选择数据源和数据表')
        return
      }
      
      try {
        // 使用 data_source_id 获取数据预览
        const response = await axios.post('/api/database/preview', {
          data_source_id: selectedDataSource.value,
          table_name: selectedTable.value,
          fields: selectedFields.value,
          limit: 10
        })
        
        if (response.data.success) {
          previewData.value = response.data.data
          ElMessage.success('数据预览已更新')
        } else {
          throw new Error(response.data.error || '获取数据预览失败')
        }
      } catch (error) {
        console.error('获取数据预览失败:', error)
        
        // 如果API调用失败，提供备用的示例数据
        ElMessage.warning('无法连接数据源，显示示例数据')
        
        const sampleData = []
        for (let i = 0; i < 10; i++) {
          const row = {}
          selectedFields.value.forEach(field => {
            // 根据字段名生成更合理的示例数据
            if (field.toLowerCase().includes('id')) {
              row[field] = i + 1
            } else if (field.toLowerCase().includes('name')) {
              row[field] = `示例${field}_${i + 1}`
            } else if (field.toLowerCase().includes('date') || field.toLowerCase().includes('time')) {
              row[field] = new Date(Date.now() - Math.random() * 86400000 * 30).toISOString().split('T')[0]
            } else if (field.toLowerCase().includes('status')) {
              row[field] = ['正常', '异常', '待处理'][Math.floor(Math.random() * 3)]
            } else {
              // 数值型字段
              row[field] = (Math.random() * 100).toFixed(2)
            }
          })
          sampleData.push(row)
        }
        
        previewData.value = sampleData
      }
    }
    
    const removeField = (field) => {
      const index = selectedFields.value.indexOf(field)
      if (index > -1) {
        selectedFields.value.splice(index, 1)
      }
    }
    
    const getTagType = (modelType) => {
      const types = {
        regression: 'success',
        classification: 'warning',
        clustering: 'info',
        time_series: 'danger'
      }
      return types[modelType] || 'info'
    }
    
    const getModelTypeName = (modelType) => {
      const names = {
        regression: '回归',
        classification: '分类',
        clustering: '聚类',
        time_series: '时间序列'
      }
      return names[modelType] || modelType
    }
    
    // 训练历史相关函数
    const refreshHistory = async () => {
      try {
        const params = {}
        if (historyFilter.model_type) params.model_type = historyFilter.model_type
        if (historyFilter.algorithm) params.algorithm = historyFilter.algorithm
        if (historyFilter.table_name) params.table_name = historyFilter.table_name
        
        const response = await axios.get('/api/models/training-history', { params })
        if (response.data.success) {
          trainingHistories.value = response.data.data
        }
      } catch (error) {
        ElMessage.error('加载训练历史失败')
      }
    }
    
    const showHistoryDetail = (history) => {
      selectedHistory.value = history
      historyDetailVisible.value = true
    }
    
    const formatDate = (dateString) => {
      return new Date(dateString).toLocaleString('zh-CN')
    }
    
    const getModelTypeTag = (modelType) => {
      const types = {
        regression: 'success',
        clustering: 'info'
      }
      return types[modelType] || 'info'
    }
    
    const getAlgorithmName = (algorithm) => {
      const nameMap = {
        'LinearRegression': '线性回归',
        'PolynomialRegression': '多项式回归',
        'RandomForestRegressor': '随机森林回归',
        'SVR': '支持向量回归',
        'XGBoostRegressor': 'XGBoost回归',
        'KMeans': 'K均值聚类',
        'DBSCAN': 'DBSCAN聚类',
        'LOF': '局部异常因子',
        'IsolationForest': '孤立森林',
        'OneClassSVM': '单类SVM'
      }
      return nameMap[algorithm] || algorithm
    }
    
    const getParameterTableData = (parameters) => {
      if (!parameters) return []
      return Object.entries(parameters).map(([name, value]) => ({
        name,
        value: typeof value === 'object' ? JSON.stringify(value) : String(value)
      }))
    }
    
    const getMetricsTableData = (metrics) => {
      if (!metrics) return []
      const metricNames = {
        'mae': 'MAE (平均绝对误差)',
        'r2': 'R² (决定系数)',
        'silhouette': '轮廓系数'
      }
      return Object.entries(metrics).map(([name, value]) => ({
        name: metricNames[name] || name,
        value: typeof value === 'number' ? value.toFixed(6) : String(value)
      }))
    }
    
    // 快速导出异常值（从列表直接导出）
    const quickExportOutliers = async (history) => {
      if (!history.outlier_details || history.outlier_details.length === 0) {
        ElMessage.warning('该训练记录没有可导出的异常值数据')
        return
      }
      
      exportingHistoryReport.value = true
      try {
        const exportData = {
          outlier_details: history.outlier_details,
          training_info: {
            model_type: history.model_type,
            algorithm: history.algorithm,
            table_name: history.table_name,
            feature_columns: history.feature_columns,
            target_column: history.target_column,
            data_info: history.data_info
          },
          metrics: history.metrics
        }
        
        const response = await axios.post('/api/models/export-outliers', exportData, {
          responseType: 'blob'
        })
        
        const url = window.URL.createObjectURL(new Blob([response.data]))
        const link = document.createElement('a')
        link.href = url
        
        const contentDisposition = response.headers['content-disposition']
        let filename = `outlier_report_${history.algorithm}_${new Date().getTime()}.xlsx`
        if (contentDisposition) {
          const filenameMatch = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/)
          if (filenameMatch && filenameMatch[1]) {
            filename = filenameMatch[1].replace(/['"]/g, '')
          }
        }
        
        link.setAttribute('download', filename)
        document.body.appendChild(link)
        link.click()
        link.remove()
        window.URL.revokeObjectURL(url)
        
        ElMessage.success(`异常值报告已导出：${filename}`)
      } catch (error) {
        ElMessage.error('导出异常值报告失败')
      } finally {
        exportingHistoryReport.value = false
      }
    }
    
    // 从详情弹窗导出异常值
    const exportHistoryOutliers = async () => {
      if (!selectedHistory.value) {
        ElMessage.warning('请先选择训练记录')
        return
      }
      
      await quickExportOutliers(selectedHistory.value)
    }
    
    // 查看异常值详情（在控制台显示）
    const viewOutlierDetails = () => {
      if (!selectedHistory.value || !selectedHistory.value.outlier_details) {
        ElMessage.warning('没有异常值详情数据')
        return
      }
      
      console.group('🔍 异常值详细信息')
      console.log('训练记录ID:', selectedHistory.value.id)
      console.log('模型类型:', selectedHistory.value.model_type)
      console.log('算法:', selectedHistory.value.algorithm)
      console.log('异常值数量:', selectedHistory.value.outlier_details.length)
      console.table(selectedHistory.value.outlier_details)
      console.groupEnd()
      
      ElMessage.success({
        message: `异常值详情已在控制台显示，共 ${selectedHistory.value.outlier_details.length} 条记录`,
        duration: 3000
      })
    }
    
    onMounted(() => {
      loadAvailableModels()
      refreshHistory()
      // 初始化一些示例字段
      selectedFields.value = ['深度', '孔隙度', '渗透率', '含油饱和度']
    })
    
    return {
      selectedModel,
      selectedFields,
      previewData,
      modelForm,
      treeProps,
      modelTree,
      trainingHistories,
      selectedHistory,
      historyDetailVisible,
      historyFilter,
      allAlgorithms,
      handleModelChange,
      resetParameters,
      saveModelConfig,
      refreshPreview,
      removeField,
      getTagType,
      getModelTypeName,
      refreshHistory,
      showHistoryDetail,
      formatDate,
      getModelTypeTag,
      getAlgorithmName,
      getParameterTableData,
      getMetricsTableData,
      exportHistoryOutliers,
      quickExportOutliers,
      viewOutlierDetails,
      exportingHistoryReport
    }
  }
}
</script>

<style scoped>
.training-history-container {
  padding: 24px;
  background-color: #f8f9fa;
  min-height: calc(100vh - 60px);
}

.page-header {
  margin-bottom: 24px;
}

.page-header h2 {
  margin: 0 0 8px 0;
  color: #303133;
  font-size: 24px;
  font-weight: 600;
}

.page-header p {
  margin: 0;
  color: #606266;
  font-size: 14px;
}

.history-wrapper {
  max-width: 1200px;
  margin: 0 auto;
}

.training-history-card {
  min-height: 500px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}



.model-tree {
  height: 500px;
  overflow-y: auto;
}

.parameter-content {
  height: 500px;
  overflow-y: auto;
}

.parameter-input {
  width: 100%;
}

.no-model-selected {
  height: 500px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.preview-content {
  height: 500px;
  overflow-y: auto;
}

.field-selector {
  margin-bottom: 15px;
}

.field-selector h4 {
  margin-bottom: 10px;
  color: #606266;
}

.data-table {
  margin-top: 15px;
}

.no-data {
  height: 300px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.el-divider {
  margin: 20px 0;
}

/* 训练历史相关样式 */
.history-content {
  height: 500px;
  overflow-y: auto;
}

.history-filters {
  margin-bottom: 15px;
  padding-bottom: 10px;
  border-bottom: 1px solid #EBEEF5;
}

.history-list {
  height: 450px;
  overflow-y: auto;
}

.history-timeline {
  padding: 0 10px;
}

.history-item {
  cursor: pointer;
  transition: all 0.3s;
  margin-bottom: 10px;
}

.history-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}

.history-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.history-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.model-name {
  font-weight: 500;
  color: #303133;
}

.history-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.info-item {
  display: flex;
  align-items: center;
  font-size: 12px;
  color: #606266;
}

.info-item .label {
  font-weight: 500;
  margin-right: 4px;
  min-width: 50px;
}

.outlier-info {
  color: #E6A23C;
}

.outlier-count {
  font-weight: 500;
}

.quick-export-btn {
  color: #E74C3C !important;
  font-size: 12px;
  padding: 2px 6px;
  margin-left: 8px;
  border: 1px solid #E74C3C;
  border-radius: 4px;
}

.quick-export-btn:hover {
  background: #E74C3C !important;
  color: white !important;
}

.no-history {
  height: 400px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.history-detail {
  max-height: 70vh;
  overflow-y: auto;
}
</style> 