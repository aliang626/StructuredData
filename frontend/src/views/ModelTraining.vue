<template>
  <div class="model-training-container">
    <!-- 页面标题 -->
    <div class="page-header">
      <h2>模型训练</h2>
      <p>配置和训练机器学习模型，支持回归和聚类算法</p>
    </div>
    
    <el-row :gutter="24" class="main-content">
      <!-- 左侧：数据选择 + 模型配置 -->
      <el-col :span="10">
        <el-card class="data-selection-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <div class="header-left">
                <el-icon class="header-icon"><Connection /></el-icon>
                <span class="header-title">数据选择</span>
              </div>
            </div>
          </template>
          
          <div class="data-selection-content">
            <!-- 数据源选择 -->
            <el-form-item label="数据源">
              <el-select 
                v-model="selectedDataSource" 
                placeholder="选择数据源" 
                @change="onDataSourceChange"
                filterable
                clearable
                :filter-method="filterDataSources"
                :loading="dataSourceLoading"
                size="large"
                style="width: 100%"
              >
                <el-option
                  v-for="source in filteredDataSources"
                  :key="source.id"
                  :label="source.name"
                  :value="source.id"
                >
                  <div class="option-content">
                    <span class="option-name">{{ source.name }}</span>
                    <span class="option-desc">{{ source.host }}:{{ source.port }}/{{ source.database }}</span>
                  </div>
                </el-option>
              </el-select>
            </el-form-item>
            
            <!-- 数据表选择 -->
            <el-form-item label="数据表">
              <el-select 
                v-model="selectedTable" 
                placeholder="选择数据表" 
                @change="onTableChange"
                filterable
                clearable
                :filter-method="filterTables"
                :loading="tableLoading"
                :disabled="!selectedDataSource"
                size="large"
                style="width: 100%"
              >
                <el-option
                  v-for="table in filteredTables"
                  :key="table"
                  :label="table"
                  :value="table"
                >
                  <div class="option-content">
                    <span class="option-name">{{ table }}</span>
                    <span class="option-desc">数据表</span>
                  </div>
                </el-option>
              </el-select>
            </el-form-item>
            
            <!-- 字段选择 -->
            <el-form-item label="特征字段">
              <el-select 
                v-model="selectedFeatures" 
                multiple 
                placeholder="选择特征字段"
                style="width: 100%"
                filterable
                clearable
                :filter-method="filterFields"
                :loading="fieldLoading"
                :disabled="!selectedTable"
                size="large"
              >
                <el-option
                  v-for="field in filteredFields"
                  :key="field.name"
                  :label="field.name"
                  :value="field.name"
                >
                  <div class="option-content">
                    <span class="option-name">{{ field.name }}</span>
                    <span class="option-desc">{{ field.type }}</span>
                  </div>
                </el-option>
              </el-select>
            </el-form-item>
            
            <!-- 目标字段（仅回归模型） -->
            <el-form-item v-if="modelConfig.modelType === 'regression'" label="目标字段">
              <el-select 
                v-model="selectedTarget" 
                placeholder="选择目标字段"
                filterable
                clearable
                :filter-method="filterFields"
                :loading="fieldLoading"
                :disabled="!selectedTable"
                size="large"
                style="width: 100%"
              >
                <el-option
                  v-for="field in filteredFields"
                  :key="field.name"
                  :label="field.name"
                  :value="field.name"
                >
                  <div class="option-content">
                    <span class="option-name">{{ field.name }}</span>
                    <span class="option-desc">{{ field.type }}</span>
                  </div>
                </el-option>
              </el-select>
            </el-form-item>
            
            <!-- 分公司字段选择（可选） -->
            <el-form-item label="分公司筛选" :required="false">
              <el-select 
                v-model="selectedCompanyField" 
                placeholder="选择分公司字段（可选）"
                filterable
                clearable
                :filter-method="filterFields"
                :loading="fieldLoading"
                :disabled="!selectedTable"
                size="large"
                style="width: 100%"
                @change="onCompanyFieldChange"
              >
                <el-option
                  v-for="field in companyFields"
                  :key="field.name"
                  :label="field.name"
                  :value="field.name"
                >
                  <div class="option-content">
                    <span class="option-name">{{ field.name }}</span>
                    <span class="option-desc">{{ field.type }} - 分公司字段</span>
                  </div>
                </el-option>
              </el-select>
            </el-form-item>
            
            <!-- 分公司值选择（当选择了分公司字段时显示） -->
            <el-form-item v-if="selectedCompanyField" label="分公司">
              <el-select 
                v-model="selectedCompanyValue" 
                placeholder="选择要训练的分公司"
                filterable
                clearable
                :loading="companyValueLoading"
                size="large"
                style="width: 100%"
              >
                <el-option
                  v-for="company in companyValues"
                  :key="company"
                  :label="company"
                  :value="company"
                >
                  <div class="option-content">
                    <span class="option-name">{{ company }}</span>
                    <span class="option-desc">分公司</span>
                  </div>
                </el-option>
              </el-select>
            </el-form-item>
            
            <!-- 数据预览已移除 -->
          </div>
        </el-card>
        <!-- 模型配置 -->
        <el-card class="config-card" shadow="hover" style="margin-top: 16px;">
          <template #header>
            <div class="card-header">
              <div class="header-left">
                <el-icon class="header-icon"><Setting /></el-icon>
                <span class="header-title">模型配置</span>
              </div>
            </div>
          </template>
          
          <div class="config-content">
            <!-- 模型类型选择 -->
            <el-form-item label="模型类型">
              <el-select v-model="modelConfig.modelType" placeholder="选择模型类型" @change="onModelTypeChange" size="large" style="width: 100%">
                <el-option label="回归模型" value="regression" />
                <el-option label="聚类模型" value="clustering" />
              </el-select>
            </el-form-item>
            
            <!-- 具体模型选择 -->
            <el-form-item label="算法选择">
              <el-select v-model="modelConfig.algorithm" placeholder="选择算法" size="large" style="width: 100%">
                <el-option
                  v-for="algo in availableAlgorithms"
                  :key="algo.value"
                  :label="algo.label"
                  :value="algo.value"
                />
              </el-select>
            </el-form-item>
            
            <!-- 模型名称 -->
            <el-form-item label="模型名称">
              <el-input v-model="modelConfig.modelName" placeholder="输入模型名称" size="large" />
            </el-form-item>
            
            <!-- 模型描述 -->
            <el-form-item label="模型描述">
              <el-input 
                v-model="modelConfig.description" 
                type="textarea"
                :rows="2"
                placeholder="输入模型描述" 
                size="large"
              />
            </el-form-item>
            
            <!-- 动态参数配置 -->
            <div v-if="algorithmParams.length > 0">
              <el-divider content-position="left">算法参数</el-divider>
              <el-form-item
                v-for="param in algorithmParams"
                :key="param.name"
                :label="param.label"
              >
                <el-input-number
                  v-if="param.type === 'number'"
                  v-model="modelConfig.parameters[param.name]"
                  :min="param.min"
                  :max="param.max"
                  :step="param.step"
                  style="width: 100%"
                  size="large"
                />
                <el-select
                  v-else-if="param.type === 'select'"
                  v-model="modelConfig.parameters[param.name]"
                  style="width: 100%"
                  size="large"
                >
                  <el-option
                    v-for="option in param.options"
                    :key="option.value"
                    :label="option.label"
                    :value="option.value"
                  />
                </el-select>
                <el-switch
                  v-else-if="param.type === 'boolean'"
                  v-model="modelConfig.parameters[param.name]"
                />
              </el-form-item>
            </div>
            
            <!-- 训练按钮 -->
            <div class="training-controls">
              <el-button 
                type="primary" 
                size="large" 
                @click="startTraining"
                :loading="isTraining"
                :disabled="!canStartTraining"
                class="start-training-btn"
              >
                {{ isTraining ? '训练中...' : '开始训练' }}
              </el-button>
              
              <!-- 保存模型按钮 -->
              <el-button 
                v-if="trainingCompleted"
                type="success" 
                size="large" 
                @click="saveTrainedModel"
                :loading="isSaving"
                class="save-model-btn"
              >
                {{ isSaving ? '保存中...' : '保存模型' }}
              </el-button>
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- 右侧：拟合可视化（放大） -->
      <el-col :span="14">
        <el-card class="chart-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <div class="header-left">
                <el-icon class="header-icon"><TrendCharts /></el-icon>
                <span class="header-title">{{ chartTitle }}</span>
              </div>
            </div>
          </template>
          
          <div class="chart-container large">
            <div ref="vizChart" class="viz-chart"></div>
            
            <!-- 指标显示 -->
            <div class="metrics-display" v-if="trainingCompleted">
              <div class="metrics-grid">
                <div class="metric-item">
                  <div class="metric-icon">
                    <el-icon><TrendCharts /></el-icon>
                  </div>
                  <div class="metric-content">
                    <span class="metric-label">MAE</span>
                    <span class="metric-value">{{ metrics.mae }}</span>
                  </div>
                </div>
                <div class="metric-item" v-if="modelConfig.modelType === 'regression'">
                  <div class="metric-icon">
                    <el-icon><TrendCharts /></el-icon>
                  </div>
                  <div class="metric-content">
                    <span class="metric-label">R²</span>
                    <span class="metric-value">{{ metrics.r2 }}</span>
                  </div>
                </div>
                <!-- 离群点汇总 -->
                <div class="metric-item" v-if="outlierSummary && outlierSummary.total_outliers > 0">
                  <div class="metric-icon outlier-icon">
                    <el-icon><Warning /></el-icon>
                  </div>
                  <div class="metric-content">
                    <span class="metric-label">离群点</span>
                    <span class="metric-value">{{ outlierSummary.total_outliers }}个 ({{ outlierSummary.outlier_rate.toFixed(2) }}%)</span>
                  </div>
                </div>
              </div>
              
              <!-- 训练结果保存提示 -->
              <div class="report-actions" v-if="trainingResult && (modelConfig.modelType === 'regression' || modelConfig.modelType === 'clustering')">
                <div class="save-success-info">
                  <el-icon class="save-icon"><SuccessFilled /></el-icon>
                  <div class="save-content">
                    <div class="save-title">训练结果已保存</div>
                    <div class="save-description">
                      {{ modelConfig.modelType === 'clustering' ? '聚类分析' : '异常值检测' }}结果已保存到配置管理，
                      可在<strong>配置管理 → 训练历史</strong>中查看和导出详细报告
                    </div>
                  </div>
                </div>
                <div class="report-info">
                  <el-tag v-if="outlierSummary && outlierSummary.detection_method" type="success">
                    检测方法：{{ outlierSummary.detection_method }}
                  </el-tag>
                  <span v-if="outlierSummary && outlierSummary.total_outliers > 0" class="outlier-count">
                    共发现 {{ outlierSummary.total_outliers }} 个{{ modelConfig.modelType === 'clustering' ? '异常点' : '离群点' }}
                  </span>
                  <el-button 
                    type="text" 
                    @click="goToConfigManagement"
                    class="goto-config-btn"
                  >
                    <el-icon><Right /></el-icon>
                    前往配置管理查看
                  </el-button>
                </div>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script>
import { ref, reactive, onMounted, computed, nextTick, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useRouter } from 'vue-router'
import { TrendCharts, Connection, Setting, Cpu, DataAnalysis, View, Warning, Download, SuccessFilled, Right } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import axios from 'axios'

export default {
  name: 'ModelTraining',
  components: {
    TrendCharts,
    Connection,
    Setting,
    Cpu,
    DataAnalysis,
    View,
    Warning,
    Download
  },
  setup() {
    const router = useRouter()
    
    // 数据源相关
    const dataSources = ref([])
    const selectedDataSource = ref('')
    const availableTables = ref([])
    const selectedTable = ref('')
    const availableFields = ref([])
    const selectedFeatures = ref([])
    const selectedTarget = ref('')
    const previewData = ref([])
    
    // 分公司相关
    const selectedCompanyField = ref('')
    const selectedCompanyValue = ref('')
    const companyValues = ref([])
    const companyValueLoading = ref(false)
    
    // 搜索过滤相关
    const filteredDataSources = ref([])
    const filteredTables = ref([])
    const filteredFields = ref([])
    
    // 加载状态
    const dataSourceLoading = ref(false)
    const tableLoading = ref(false)
    const fieldLoading = ref(false)
    
    // 模型配置
    const modelConfig = reactive({
      modelType: 'regression',
      algorithm: '',
      modelName: '',
      description: '',
      parameters: {}
    })
    
    // 训练配置
    const trainingConfig = reactive({
      epochs: 100,
      batchSize: 256,
      learningRate: 0.01
    })
    
    // 训练状态
    const isTraining = ref(false)
    const trainingCompleted = ref(false)
    const isSaving = ref(false)
    const vizChart = ref(null)
    const vizChartInstance = ref(null)
    const vizChartVisible = ref(true)
    const chartTitle = ref('拟合可视化')
    
    // 算法中文名映射
    const algorithmNameMap = {
      'LinearRegression': '线性回归',
      'PolynomialRegression': '多项式回归',
      'RandomForestRegressor': '随机森林回归',
      'SVR': '支持向量回归',
      'XGBoostRegressor': 'XGBoost回归',
      'KMeans': 'K均值聚类',
      'DBSCAN': 'DBSCAN聚类',
      'LOF': '局部离群因子',
      'IsolationForest': '孤立森林',
      'OneClassSVM': '单类支持向量机'
    }
    
    // 指标数据
    const metrics = reactive({
      mae: '0.000000',
      r2: '0.000000',
      silhouette: '0.000000'
    })
    
    // 训练结果和离群点数据
    const trainingResult = ref(null)
    const outlierSummary = ref(null)
    const exportingReport = ref(false)
    
    // 算法选项
    const algorithmOptions = {
      regression: [
        { label: '线性回归', value: 'LinearRegression' },
        { label: '多项式回归', value: 'PolynomialRegression' },
        { label: '随机森林回归', value: 'RandomForestRegressor' },
        { label: '支持向量回归', value: 'SVR' },
        { label: 'XGBoost回归', value: 'XGBoostRegressor' }
      ],
      clustering: [
        { label: 'K均值聚类', value: 'KMeans' },
        { label: 'DBSCAN聚类', value: 'DBSCAN' },
        { label: '局部离群因子', value: 'LOF' },
        { label: '孤立森林', value: 'IsolationForest' },
        { label: '单类支持向量机', value: 'OneClassSVM' }
      ]
    }
    
    // 参数配置
    const parameterConfigs = {
      LinearRegression: [],
      PolynomialRegression: [
        { name: 'degree', label: '多项式次数', type: 'number', min: 2, max: 10, step: 1, default: 2 },
        { name: 'fit_intercept', label: '计算截距', type: 'boolean', default: true }
      ],
      RandomForestRegressor: [
        { name: 'n_estimators', label: '树的数量', type: 'number', min: 10, max: 1000, step: 10, default: 100 },
        { name: 'max_depth', label: '最大深度', type: 'number', min: 1, max: 50, step: 1, default: 10 }
      ],
      SVR: [
        { name: 'kernel', label: '核函数类型', type: 'select', options: [
          { label: 'RBF核', value: 'rbf' },
          { label: '线性核', value: 'linear' },
          { label: '多项式核', value: 'poly' }
        ], default: 'rbf' },
        { name: 'C', label: '惩罚系数', type: 'number', min: 0.01, max: 100.0, step: 0.01, default: 1.0 },
        { name: 'epsilon', label: 'Epsilon参数', type: 'number', min: 0.01, max: 1.0, step: 0.01, default: 0.1 },
        { name: 'gamma', label: '核函数系数', type: 'select', options: [
          { label: 'Scale', value: 'scale' },
          { label: 'Auto', value: 'auto' }
        ], default: 'scale' }
      ],
      XGBoostRegressor: [
        { name: 'n_estimators', label: '迭代次数', type: 'number', min: 10, max: 1000, step: 10, default: 100 },
        { name: 'learning_rate', label: '学习率', type: 'number', min: 0.01, max: 1, step: 0.01, default: 0.1 },
        { name: 'max_depth', label: '最大深度', type: 'number', min: 1, max: 20, step: 1, default: 6 }
      ],
      KMeans: [
        { name: 'n_clusters', label: '聚类数量', type: 'number', min: 2, max: 20, step: 1, default: 3 },
        { name: 'max_iter', label: '最大迭代次数', type: 'number', min: 100, max: 1000, step: 50, default: 300 }
      ],
      DBSCAN: [
        { name: 'eps', label: 'Epsilon', type: 'number', min: 0.1, max: 5, step: 0.1, default: 0.5 },
        { name: 'min_samples', label: '最小样本数', type: 'number', min: 1, max: 20, step: 1, default: 5 }
      ],
      LOF: [
        { name: 'n_neighbors', label: '邻居数', type: 'number', min: 1, max: 100, step: 1, default: 20 },
        { name: 'contamination', label: '异常比例', type: 'number', min: 0.01, max: 0.5, step: 0.01, default: 0.1 },
        { name: 'algorithm', label: '算法类型', type: 'select', options: [
          { label: '自动', value: 'auto' },
          { label: 'Ball Tree', value: 'ball_tree' },
          { label: 'KD Tree', value: 'kd_tree' },
          { label: '暴力搜索', value: 'brute' }
        ], default: 'auto' },
        { name: 'leaf_size', label: '叶子大小', type: 'number', min: 10, max: 100, step: 5, default: 30 }
      ],
      IsolationForest: [
        { name: 'n_estimators', label: '树的数量', type: 'number', min: 10, max: 500, step: 10, default: 100 },
        { name: 'contamination', label: '异常比例', type: 'number', min: 0.01, max: 0.5, step: 0.01, default: 0.1 },
        { name: 'max_samples', label: '最大样本数', type: 'string', default: 'auto' },
        { name: 'random_state', label: '随机种子', type: 'number', min: 1, max: 1000, step: 1, default: 42 }
      ],
      OneClassSVM: [
        { name: 'kernel', label: '核函数类型', type: 'select', options: [
          { label: 'RBF核', value: 'rbf' },
          { label: '线性核', value: 'linear' },
          { label: '多项式核', value: 'poly' },
          { label: 'Sigmoid核', value: 'sigmoid' }
        ], default: 'rbf' },
        { name: 'nu', label: '异常比例参数', type: 'number', min: 0.01, max: 1.0, step: 0.01, default: 0.1 },
        { name: 'gamma', label: '核函数系数', type: 'select', options: [
          { label: 'Scale', value: 'scale' },
          { label: 'Auto', value: 'auto' }
        ], default: 'scale' },
        { name: 'degree', label: '多项式核度数', type: 'number', min: 1, max: 10, step: 1, default: 3 }
      ]
    }
    
    // 计算属性
    const availableAlgorithms = computed(() => {
      return algorithmOptions[modelConfig.modelType] || []
    })
    
    const algorithmParams = computed(() => {
      return parameterConfigs[modelConfig.algorithm] || []
    })
    
    const canStartTraining = computed(() => {
      return selectedDataSource.value && 
             selectedTable.value && 
             selectedFeatures.value.length > 0 &&
             modelConfig.algorithm &&
             modelConfig.modelName &&
             (modelConfig.modelType !== 'regression' || selectedTarget.value) &&
             !isTraining.value
    })
    
    // 计算可能的分公司字段
    const companyFields = computed(() => {
      const companyKeywords = ['company', 'branch', '分公司', '公司', 'dept', '部门', 'org', '组织', 'unit', '单位']
      return availableFields.value.filter(field => {
        const fieldName = field.name.toLowerCase()
        return companyKeywords.some(keyword => fieldName.includes(keyword.toLowerCase()))
      })
    })
    
    // 监听算法变化，初始化参数
    watch(() => modelConfig.algorithm, (newAlgorithm) => {
      if (newAlgorithm) {
        const params = parameterConfigs[newAlgorithm] || []
        modelConfig.parameters = {}
        params.forEach(param => {
          modelConfig.parameters[param.name] = param.default
        })
      }
    })
    
    // 过滤方法
    const filterDataSources = (query) => {
      if (query === '') {
        filteredDataSources.value = dataSources.value
      } else {
        filteredDataSources.value = dataSources.value.filter(source => 
          source.name.toLowerCase().includes(query.toLowerCase()) ||
          source.host.toLowerCase().includes(query.toLowerCase()) ||
          source.database.toLowerCase().includes(query.toLowerCase())
        )
      }
    }
    
    const filterTables = (query) => {
      if (query === '') {
        filteredTables.value = availableTables.value
      } else {
        filteredTables.value = availableTables.value.filter(table => 
          table.toLowerCase().includes(query.toLowerCase())
        )
      }
    }
    
    const filterFields = (query) => {
      if (query === '') {
        filteredFields.value = availableFields.value
      } else {
        filteredFields.value = availableFields.value.filter(field => 
          field.name.toLowerCase().includes(query.toLowerCase()) ||
          field.type.toLowerCase().includes(query.toLowerCase())
        )
      }
    }
    
    // 加载数据源
    const loadDataSources = async () => {
      dataSourceLoading.value = true
      try {
        const response = await axios.get('/api/database/sources')
        if (response.data.success) {
          dataSources.value = response.data.data
          filteredDataSources.value = dataSources.value
        }
      } catch (error) {
        console.error('加载数据源失败:', error)
        ElMessage.error('加载数据源失败')
      } finally {
        dataSourceLoading.value = false
      }
    }
    
    // 数据源变化处理
    const onDataSourceChange = async () => {
      if (!selectedDataSource.value) return
      
      tableLoading.value = true
      try {
        const response = await axios.get(`/api/database/tables/${selectedDataSource.value}`)
        if (response.data.success) {
          availableTables.value = response.data.data
          filteredTables.value = availableTables.value
          selectedTable.value = ''
          availableFields.value = []
          filteredFields.value = []
        }
      } catch (error) {
        console.error('加载数据表失败:', error)
        ElMessage.error('加载数据表失败')
      } finally {
        tableLoading.value = false
      }
    }
    
    // 数据表变化处理
    const onTableChange = async () => {
      if (!selectedTable.value) return
      
      fieldLoading.value = true
      try {
        const response = await axios.get(`/api/database/fields/${selectedDataSource.value}/${selectedTable.value}`)
        if (response.data.success) {
          availableFields.value = response.data.data
          filteredFields.value = availableFields.value
          selectedFeatures.value = []
          selectedTarget.value = ''
          // 重置分公司选择
          selectedCompanyField.value = ''
          selectedCompanyValue.value = ''
          companyValues.value = []
          await loadPreviewData()
        }
      } catch (error) {
        console.error('加载字段失败:', error)
        ElMessage.error('加载字段失败')
      } finally {
        fieldLoading.value = false
      }
    }
    
    // 模型类型变化处理
    const onModelTypeChange = () => {
      modelConfig.algorithm = ''
      modelConfig.parameters = {}
      selectedTarget.value = ''
    }
    
    // 处理分公司字段变化
    const onCompanyFieldChange = async () => {
      if (!selectedCompanyField.value) {
        companyValues.value = []
        selectedCompanyValue.value = ''
        return
      }
      
      companyValueLoading.value = true
      try {
        const response = await axios.post('/api/database/distinct-values', {
          data_source_id: selectedDataSource.value,
          table_name: selectedTable.value,
          field_name: selectedCompanyField.value
        })
        
        if (response.data.success) {
          companyValues.value = response.data.data.filter(value => value !== null && value !== '')
          selectedCompanyValue.value = ''
        } else {
          ElMessage.error('加载分公司列表失败: ' + response.data.error)
        }
      } catch (error) {
        console.error('加载分公司列表失败:', error)
        ElMessage.error('加载分公司列表失败')
      } finally {
        companyValueLoading.value = false
      }
    }
    
    // 加载预览数据
    const loadPreviewData = async () => {
      if (!selectedDataSource.value || !selectedTable.value) return
      
      try {
        const fields = [...selectedFeatures.value]
        if (selectedTarget.value) fields.push(selectedTarget.value)
        
        if (fields.length === 0) return
        
        const response = await axios.post('/api/database/preview', {
          data_source_id: selectedDataSource.value,
          table_name: selectedTable.value,
          fields: fields,
          limit: 10
        })
        
        if (response.data.success) {
          previewData.value = response.data.data
        }
      } catch (error) {
        console.error('加载预览数据失败:', error)
      }
    }
    
    // 监听字段选择变化
    watch([selectedFeatures, selectedTarget], loadPreviewData)
    
    // 初始化图表
    // 移除loss曲线初始化，统一使用拟合可视化图表

    // 初始化可视化图表（散点+拟合曲线+区间）
    const initVizChart = () => {
      try {
        if (!vizChart.value) {
          console.warn('vizChart DOM element not ready')
          return
        }
        
        // 检查DOM元素是否已挂载到页面
        if (!vizChart.value.offsetParent && vizChart.value.offsetHeight === 0) {
          console.warn('vizChart DOM element not visible, retrying...')
          setTimeout(initVizChart, 100)
          return
        }
        
        // 如果已有实例，先销毁避免重复绑定
        if (vizChartInstance.value) {
          try {
            vizChartInstance.value.dispose()
          } catch (error) {
            console.warn('Error disposing chart instance:', error)
          }
          vizChartInstance.value = null
        }
        
        // 安全地初始化ECharts实例
        vizChartInstance.value = echarts.init(vizChart.value, null, {
          renderer: 'canvas',
          useDirtyRect: false
        })
        
        // 设置初始的空白图表配置
        const option = {
          tooltip: { 
            trigger: 'item',
            formatter: function(params) {
              if (params.seriesName === '异常值') {
                return `异常值<br/>${params.data[0].toFixed(2)}, ${params.data[1].toFixed(2)}<br/>超出容许范围`
              } else if (params.seriesName === '实际数据') {
                return `实际数据<br/>${params.data[0].toFixed(2)}, ${params.data[1].toFixed(2)}`
              } else if (params.seriesName.includes('拟合曲线')) {
                return `拟合值<br/>${params.data[0].toFixed(2)}, ${params.data[1].toFixed(2)}`
              }
              return `${params.seriesName}<br/>${params.data[0].toFixed(2)}, ${params.data[1].toFixed(2)}`
            }
          },
          grid: { left: 60, right: 30, top: 60, bottom: 100 },
          xAxis: {
            type: 'value', name: 'X', nameGap: 22,
            axisLine: { lineStyle: { color: '#C0C4CC' } },
            axisLabel: { color: '#606266' },
            splitLine: { lineStyle: { color: '#F2F6FC' } }
          },
          yAxis: {
            type: 'value', name: 'Y', nameGap: 22,
            axisLine: { lineStyle: { color: '#C0C4CC' } },
            axisLabel: { color: '#606266' },
            splitLine: { lineStyle: { color: '#F2F6FC' } }
          },
          dataZoom: [
            { type: 'inside', throttle: 50 },
            { type: 'slider', bottom: 20, height: 20 }
          ],
          legend: { top: 10, left: 'center', data: ['实际孔隙度', '拟合曲线', '容许范围', '异常值'] },
          series: []
        }
        
        // 安全地设置初始配置
        try {
          vizChartInstance.value.setOption(option)
          console.log('Chart option set successfully')
        } catch (error) {
          console.error('Error setting chart option:', error)
        }
        
        console.log('ECharts instance initialized successfully')
      } catch (error) {
        console.error('Error initializing ECharts:', error)
        vizChartInstance.value = null
      }
    }
    
    // 开始训练
    const startTraining = async () => {
      if (!canStartTraining.value) {
        ElMessage.warning('请完善训练配置')
        return
      }
      
      isTraining.value = true
      trainingCompleted.value = false
      vizChartVisible.value = true
      chartTitle.value = '拟合可视化'
      ElMessage.info('开始训练模型...')
      
      try {
        const trainingData = {
          data_source_id: selectedDataSource.value,
          table_name: selectedTable.value,
          feature_columns: selectedFeatures.value,
          target_column: selectedTarget.value,
          model_type: modelConfig.modelType,
          algorithm: modelConfig.algorithm,
          parameters: modelConfig.parameters,
          model_name: modelConfig.modelName,
          description: modelConfig.description,
          // 添加训练配置参数
          use_full_data: true,  // 默认使用全量数据
          epochs: trainingConfig.epochs,
          batch_size: trainingConfig.batchSize,
          learning_rate: trainingConfig.learningRate,
          // 分公司过滤参数
          company_field: selectedCompanyField.value || null,
          company_value: selectedCompanyValue.value || null
        }
        
        // 调用实际的训练API
        const response = await axios.post('/api/models/train-realtime', trainingData)
        
        if (response.data.success) {
          // 可视化数据
          const metricsData = response.data.data.metrics || {}
          const vizData = response.data.data.viz_data || null
          
          // 更新指标
          metrics.mae = metricsData.mae || '0.000000'
          metrics.r2 = metricsData.r2 || '0.000000'
          metrics.silhouette = metricsData.silhouette || '0.000000'
          
          // 保存训练结果和离群点信息
          trainingResult.value = response.data.data
          outlierSummary.value = response.data.data.outlier_summary || null
          
          // 训练结果保存成功提示
          if (outlierSummary.value && outlierSummary.value.total_outliers > 0) {
            ElMessage.success({
              message: `训练完成！检测到 ${outlierSummary.value.total_outliers} 个异常值，结果已保存到配置管理`,
              duration: 3000
            })
          } else {
            ElMessage.success('训练完成！结果已保存到配置管理')
          }
          
          // 绘制可视化图（若返回vizData）
          if (vizData) {
            await nextTick()
            vizChartVisible.value = true
            
            // 等待DOM更新后再初始化图表
            await nextTick()
            
            // 安全地初始化图表
            if (!vizChartInstance.value) {
              initVizChart()
            }
            
            // 如果初始化失败，重试一次
            if (!vizChartInstance.value && vizChart.value) {
              setTimeout(() => {
                try {
                  vizChartInstance.value = echarts.init(vizChart.value, null, {
                    renderer: 'canvas',
                    useDirtyRect: false
                  })
                  console.log('Chart initialized on retry')
                } catch (error) {
                  console.error('Chart initialization retry failed:', error)
                }
              }, 200)
            }
            
            // 根据模型类型决定绘制方式
            if (modelConfig.modelType === 'clustering') {
              chartTitle.value = '聚类分布可视化'
              // 延迟执行聚类图表绘制，确保实例已准备好
              setTimeout(() => {
                if (vizChartInstance.value) {
                  drawClusteringChart(vizData)
                } else {
                  console.warn('Chart instance not ready for clustering visualization')
                }
              }, 300)
            } else {
              chartTitle.value = '拟合可视化'
              
              const x = vizData.x || []
              const y = vizData.y || []
              const xs = vizData.x_smooth || []
              const ys = vizData.y_smooth || []
              const lower = vizData.lower || []
              const upper = vizData.upper || []
              const outliers = vizData.outliers || []

            // 对容许范围进行合理约束（特别是地质参数）
            const targetName = vizData.target_name || 'Y'
            const isGeologicalParam = /porosity|permeability|gamma_ray|density/i.test(targetName)
            
            // 为地质参数设置合理的边界
            const constrainedLower = lower.map(val => {
              if (isGeologicalParam && val < 0) {
                return 0  // 地质参数不能为负值
              }
              return val
            })
            
            const constrainedUpper = upper.map((val, i) => {
              if (isGeologicalParam) {
                if (targetName.toLowerCase().includes('porosity') && val > 50) {
                  return 50  // 孔隙度通常不超过50%
                }
                if (targetName.toLowerCase().includes('gamma_ray') && val > 300) {
                  return 300  // 自然伽马通常不超过300 API
                }
              }
              return val
            })
            
            // 重新计算异常值，使用约束后的边界
            const validOutliers = []
            outliers.forEach(outlier => {
              // 找到对应的x位置在smooth数据中的索引
              const closestIndex = xs.reduce((prev, curr, index) => {
                return Math.abs(curr - outlier.x) < Math.abs(xs[prev] - outlier.x) ? index : prev
              }, 0)
              
              // 检查是否真的在约束后的容许范围外
              const lowerBound = constrainedLower[closestIndex]
              const upperBound = constrainedUpper[closestIndex]
              
              if (outlier.y < lowerBound || outlier.y > upperBound) {
                validOutliers.push(outlier)
              }
            })
            
            // 计算合理的Y轴范围
            const allYValues = [...y, ...ys, ...constrainedLower, ...constrainedUpper]
            const yMin = Math.max(Math.min(...allYValues) - 2, isGeologicalParam ? 0 : Math.min(...allYValues) - 2)
            const yMax = Math.max(...allYValues) + 2
            
            const option = {
              grid: { left: 60, right: 30, top: 60, bottom: 100 },
              dataZoom: [
                { type: 'inside', throttle: 50 },
                { type: 'slider', bottom: 20, height: 20 }
              ],
              xAxis: { 
                type: 'value', 
                min: Math.min(...x) - 1, 
                max: Math.max(...x) + 1, 
                name: vizData.feature_name || 'X',
                axisLine: { lineStyle: { color: '#C0C4CC' } },
                axisLabel: { color: '#606266' },
                splitLine: { lineStyle: { color: '#F2F6FC' } }
              },
              yAxis: { 
                type: 'value', 
                min: yMin, 
                max: yMax, 
                name: vizData.target_name || 'Y',
                axisLine: { lineStyle: { color: '#C0C4CC' } },
                axisLabel: { color: '#606266' },
                splitLine: { lineStyle: { color: '#F2F6FC' } }
              },
              legend: { 
                data: [
                  {name: '实际孔隙度', icon: 'circle', textStyle: {color: '#3498DB'}},
                  {name: `${algorithmNameMap[modelConfig.algorithm] || modelConfig.algorithm}拟合曲线`, icon: 'line', textStyle: {color: '#E74C3C'}},
                  {name: '容许范围', icon: 'rect', textStyle: {color: '#228B22'}},
                  {name: '异常值', icon: 'path://M-6,-6 L6,6 M6,-6 L-6,6', textStyle: {color: '#E74C3C'}}
                ],
                top: 10,
                left: 'center',
                textStyle: {
                  fontSize: 12
                },
                itemWidth: 20,
                itemHeight: 12
              },
              series: [
                {
                  name: '容许范围',
                  type: 'line',
                  data: xs.map((xi, i) => [xi, constrainedUpper[i]]),
                  lineStyle: { opacity: 0 },
                  stack: 'confidence-band',
                  symbol: 'none',
                  areaStyle: {
                    color: 'rgba(34, 139, 34, 0.4)'
                  }
                },
                {
                  name: '容许范围下界',
                  type: 'line',
                  data: xs.map((xi, i) => [xi, constrainedLower[i]]),
                  lineStyle: { opacity: 0 },
                  stack: 'confidence-band',
                  symbol: 'none',
                  areaStyle: {
                    color: 'rgba(255, 255, 255, 0.8)'
                  },
                  showInLegend: false
                },
                {
                  name: `${algorithmNameMap[modelConfig.algorithm] || modelConfig.algorithm}拟合曲线`,
                  type: 'line',
                  smooth: true,
                  symbol: 'none',
                  lineStyle: { color: '#E74C3C', width: 2 },
                  data: xs.map((xi, i) => [xi, ys[i]])
                },
                {
                  name: '实际孔隙度',
                  type: 'scatter',
                  symbolSize: 4,
                  itemStyle: { 
                    color: '#3498DB', 
                    opacity: 1.0,
                    borderColor: '#2980B9',
                    borderWidth: 0.5
                  },
                  data: x.map((xi, i) => [xi, y[i]])
                },
                {
                  name: '异常值',
                  type: 'scatter',
                  symbol: 'path://M-6,-6 L6,6 M6,-6 L-6,6',
                  symbolSize: 12,
                  itemStyle: { 
                    color: '#E74C3C',
                    borderColor: '#E74C3C',
                    borderWidth: 2
                  },
                  data: validOutliers.map(o => [o.x, o.y])
                }
              ]
            }
            
            // 安全地设置图表选项
            const setChartOption = () => {
              if (vizChartInstance.value) {
                try {
                  vizChartInstance.value.setOption(option, true)
                  vizChartInstance.value.resize()
                  console.log('Regression chart rendered successfully')
                } catch (error) {
                  console.error('Error setting chart option:', error)
                }
              } else {
                console.warn('Chart instance not ready for regression visualization')
              }
            }
            
            // 延迟执行以确保图表实例准备就绪
            setTimeout(setChartOption, 300)
            } // 回归可视化的结束括号
          }

          trainingCompleted.value = true
          ElMessage.success('模型训练完成！')
        } else {
          throw new Error(response.data.error || '训练失败')
        }
      } catch (error) {
        console.error('训练失败:', error)
        ElMessage.error(`模型训练失败: ${error.message}`)
      } finally {
        isTraining.value = false
      }
    }
    
    // 聚类可视化绘制函数
    const drawClusteringChart = (vizData) => {
      try {
        const x = vizData.x || []
        const y = vizData.y || []
        const labels = vizData.labels || []
        const centers = vizData.centers || []
        const outliers = vizData.outliers || []
        const companies = vizData.companies || []
        const company_column = vizData.company_column
        
        // 获取特征和目标名称
        const featureName = vizData.feature_name || 'X'
        const targetName = vizData.target_name || 'Y'
        
        // 生成颜色方案
        const colors = ['#5470C6', '#91CC75', '#FAC858', '#EE6666', '#73C0DE', '#3BA272', '#FC8452', '#9A60B4', '#EA7CCC']
        
        // 按分公司分组数据
        const companyGroups = {}
        const uniqueCompanies = [...new Set(companies)]
        
        // 初始化分公司组
        uniqueCompanies.forEach(company => {
          companyGroups[company] = {
            normal: [],
            outliers: [],
            centers: []
          }
        })
        
        // 分类数据点
        for (let i = 0; i < x.length; i++) {
          const point = [x[i], y[i]]
          const company = companies[i] || 'Unknown'
          
          // 检查是否为异常值
          const isOutlier = outliers.some(outlier => 
            Math.abs(outlier[0] - x[i]) < 0.0001 && Math.abs(outlier[1] - y[i]) < 0.0001
          )
          
          if (isOutlier) {
            companyGroups[company].outliers.push(point)
          } else {
            companyGroups[company].normal.push(point)
          }
        }
        
        // 分配中心点给分公司
        if (vizData.grid_info && vizData.grid_info.companies) {
          Object.entries(vizData.grid_info.companies).forEach(([company, info]) => {
            if (info.center && companyGroups[company]) {
              companyGroups[company].centers.push(info.center)
            }
          })
        }
        
        // 构建图表系列
        const series = []
        let colorIndex = 0
        
        // 为每个分公司添加正常数据点
        Object.entries(companyGroups).forEach(([company, data]) => {
          if (data.normal.length > 0) {
            series.push({
              name: `${company} - 数据点`,
              type: 'scatter',
              data: data.normal,
              symbolSize: 6,
              itemStyle: {
                color: colors[colorIndex % colors.length],
                opacity: 0.7
              }
            })
          }
          
          // 添加聚类中心
          if (data.centers.length > 0) {
            series.push({
              name: `${company} - 聚类中心`,
              type: 'scatter',
              data: data.centers,
              symbol: 'diamond',
              symbolSize: 12,
              itemStyle: {
                color: colors[colorIndex % colors.length],
                borderColor: '#000',
                borderWidth: 2
              }
            })
          }
          
          colorIndex++
        })
        
        // 添加所有异常值作为单独系列
        const allOutliers = []
        Object.values(companyGroups).forEach(data => {
          allOutliers.push(...data.outliers)
        })
        
        if (allOutliers.length > 0) {
          series.push({
            name: '离群点',
            type: 'scatter',
            data: allOutliers,
            symbol: 'path://M-6,-6 L6,6 M6,-6 L-6,6',
            symbolSize: 10,
            itemStyle: {
              color: '#E74C3C',
              borderColor: '#C0392B',
              borderWidth: 2
            }
          })
        }
        
        // 图表配置
        const option = {
          title: {
            text: company_column ? `${company_column} 经纬度分布` : '地理坐标聚类分布',
            left: 'center',
            textStyle: {
              fontSize: 16,
              fontWeight: 'bold'
            }
          },
          tooltip: {
            trigger: 'item',
            formatter: function(params) {
              const [lon, lat] = params.data
              const company = params.seriesName.split(' - ')[0]
              const type = params.seriesName.includes('聚类中心') ? '聚类中心' : 
                          params.seriesName.includes('离群点') ? '离群点' : '数据点'
              
              return `${company}<br/>
                      类型: ${type}<br/>
                      ${featureName}: ${lon.toFixed(4)}<br/>
                      ${targetName}: ${lat.toFixed(4)}`
            }
          },
          legend: {
            data: series.map(s => s.name),
            top: 30,
            type: 'scroll'
          },
          grid: {
            left: '10%',
            right: '10%',
            bottom: '20%',
            top: '20%'
          },
          dataZoom: [
            { type: 'inside', throttle: 50 },
            { type: 'slider', bottom: 20, height: 20 }
          ],
          xAxis: {
            type: 'value',
            name: featureName,
            nameLocation: 'middle',
            nameGap: 30,
            axisLabel: { color: '#606266' },
            splitLine: { lineStyle: { color: '#F2F6FC' } }
          },
          yAxis: {
            type: 'value',
            name: targetName,
            nameLocation: 'middle',
            nameGap: 50,
            axisLabel: { color: '#606266' },
            splitLine: { lineStyle: { color: '#F2F6FC' } }
          },
          series: series
        }
        
        // 应用图表配置
        if (vizChartInstance.value) {
          try {
            vizChartInstance.value.setOption(option, true)
            vizChartInstance.value.resize()
            console.log('Clustering chart rendered successfully')
          } catch (error) {
            console.error('Error rendering clustering chart:', error)
          }
        } else {
          console.warn('Chart instance not available for clustering visualization')
          // 尝试重新初始化
          setTimeout(() => {
            if (!vizChartInstance.value && vizChart.value) {
              try {
                vizChartInstance.value = echarts.init(vizChart.value, null, {
                  renderer: 'canvas',
                  useDirtyRect: false
                })
                if (vizChartInstance.value) {
                  vizChartInstance.value.setOption(option, true)
                  vizChartInstance.value.resize()
                  console.log('Clustering chart rendered after retry')
                }
              } catch (error) {
                console.error('Failed to initialize chart for clustering:', error)
              }
            }
          }, 100)
        }
        
        console.log('聚类可视化图表绘制完成', {
          总数据点: x.length,
          异常值: allOutliers.length,
          分公司数: uniqueCompanies.length,
          聚类中心: centers.length
        })
        
      } catch (error) {
        console.error('聚类可视化绘制失败:', error)
        ElMessage.error('聚类可视化绘制失败')
      }
    }
    
    // 跳转到配置管理
    const goToConfigManagement = () => {
      router.push('/model-config')
      ElMessage.success('跳转到配置管理页面')
    }
    
    // 移除loss曲线动画逻辑
    
    // 导出离群点报告
    const exportOutlierReport = async () => {
      if (!trainingResult.value) {
        ElMessage.warning('没有可导出的训练结果数据')
        return
      }
      
      const vizData = trainingResult.value.viz_data
      let outlierDetails = []
      
      // 检查多种可能的异常值数据源
      if (vizData && vizData.outlier_details && vizData.outlier_details.length > 0) {
        outlierDetails = vizData.outlier_details
      } else if (outlierSummary.value && outlierSummary.value.total_outliers > 0) {
        // 如果没有详细的outlier_details，但有outlierSummary，创建基础的异常值记录
        ElMessage.warning('异常值详细信息不完整，将导出基础报告')
        outlierDetails = [{
          row_index: 0,
          feature_name: trainingResult.value.training_info?.feature_columns?.[0] || 'unknown',
          feature_value: 0,
          target_name: trainingResult.value.training_info?.target_column || 'unknown',
          actual_value: 0,
          predicted_value: 0,
          residual: 0,
          abs_residual: 0,
          tolerance: 0,
          outlier_type: 'detected',
          is_outlier: true
        }]
      } else {
        ElMessage.warning('未检测到离群点数据')
        return
      }
      
      exportingReport.value = true
      
      try {
        const exportData = {
          outlier_details: outlierDetails,
          training_info: trainingResult.value.training_info,
          metrics: trainingResult.value.metrics
        }
        
        const response = await axios.post('/api/model/export-outliers', exportData, {
          responseType: 'blob' // 重要：设置响应类型为blob
        })
        
        // 创建下载链接
        const url = window.URL.createObjectURL(new Blob([response.data]))
        const link = document.createElement('a')
        link.href = url
        
        // 从响应头获取文件名，如果没有则使用默认名称
        const contentDisposition = response.headers['content-disposition']
        let filename = 'outlier_report.xlsx'
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
        
        ElMessage.success(`离群点报告已导出：${filename}`)
        
      } catch (error) {
        console.error('导出失败:', error)
        ElMessage.error('导出离群点报告失败')
      } finally {
        exportingReport.value = false
      }
    }
    
    // 保存训练完成的模型
    const saveTrainedModel = async () => {
      if (!trainingCompleted.value) {
        ElMessage.warning('请先完成模型训练')
        return
      }
      
      if (!modelConfig.modelName.trim()) {
        ElMessage.warning('请输入模型名称')
        return
      }
      
      isSaving.value = true
      
      try {
        // 准备保存的数据
        const saveData = {
          name: modelConfig.modelName,
          model_type: modelConfig.modelType,
          model_name: modelConfig.algorithm,
          parameters: modelConfig.parameters,
          description: modelConfig.description || `训练完成的${modelConfig.algorithm}模型`,
          status: 'trained',
          data_source_id: selectedDataSource.value,
          table_name: selectedTable.value,
          feature_columns: selectedFeatures.value,
          target_column: selectedTarget.value
        }
        
        // 调用后端API保存模型配置
        const response = await axios.post('/api/models/configs', saveData)
        
        if (response.data.success) {
          ElMessage.success('模型保存成功！')
          
          // 询问用户是否跳转到模型列表
          try {
            await ElMessageBox.confirm(
              '模型已成功保存到配置库中，是否跳转到模型列表查看？',
              '保存成功',
              {
                confirmButtonText: '查看模型列表',
                cancelButtonText: '继续训练',
                type: 'success'
              }
            )
            
            // 用户选择跳转
            router.push('/model-list')
          } catch {
            // 用户选择继续训练，不做任何操作
          }
        } else {
          throw new Error(response.data.error || '保存失败')
        }
      } catch (error) {
        console.error('保存模型失败:', error)
        ElMessage.error(`保存模型失败: ${error.message}`)
      } finally {
        isSaving.value = false
      }
    }
    
    onMounted(async () => {
      try {
        await loadDataSources()
        await nextTick()
        
        // 延迟初始化图表，确保DOM完全渲染
        setTimeout(() => {
          if (vizChart.value) {
            console.log('Initializing chart on mount')
            initVizChart()
          } else {
            console.warn('Chart container not found on mount')
          }
        }, 500)
      } catch (error) {
        console.error('Error in onMounted:', error)
      }
    })
    
    return {
      // 数据源相关
      dataSources,
      selectedDataSource,
      availableTables,
      selectedTable,
      availableFields,
      selectedFeatures,
      selectedTarget,
      previewData,
      onDataSourceChange,
      onTableChange,
      
      // 搜索过滤相关
      filteredDataSources,
      filteredTables,
      filteredFields,
      filterDataSources,
      filterTables,
      filterFields,
      
      // 加载状态
      dataSourceLoading,
      tableLoading,
      fieldLoading,
      
      // 分公司相关
      selectedCompanyField,
      selectedCompanyValue,
      companyFields,
      companyValues,
      companyValueLoading,
      onCompanyFieldChange,
      
      // 模型配置
      modelConfig,
      availableAlgorithms,
      algorithmParams,
      onModelTypeChange,
      
      // 训练相关
      isTraining,
      trainingCompleted,
      isSaving,
      canStartTraining,
      startTraining,
      saveTrainedModel,
      
      // 图表相关
      vizChart,
      chartTitle,
      metrics,
      
      // 训练配置
      trainingConfig,
      
      // 算法映射
      algorithmNameMap,
      trainingResult,
      outlierSummary,
      exportOutlierReport,
      exportingReport,
      goToConfigManagement
    }
  }
}
</script>

<style scoped>
.model-training-container {
  padding: 20px;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  min-height: calc(100vh - 60px);
}

.page-header {
  text-align: center;
  margin-bottom: 30px;
  background: rgba(255, 255, 255, 0.9);
  padding: 20px;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
}

.page-header h2 {
  margin-bottom: 8px;
  color: #2c3e50;
  font-size: 28px;
  font-weight: 600;
}

.page-header p {
  color: #7f8c8d;
  font-size: 16px;
  margin: 0;
}

.main-content {
  margin-top: 20px;
}

.data-selection-card,
.chart-card,
.config-card {
  background: rgba(255, 255, 255, 0.95);
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  margin-bottom: 24px;
  min-height: 600px;
  display: flex;
  flex-direction: column;
}

/* 收起数据选择卡片的空白高度 */
.data-selection-card {
  min-height: auto;
}
.data-selection-card .data-selection-content {
  flex: 0 0 auto;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-icon {
  font-size: 24px;
  color: #3498db;
  background: linear-gradient(135deg, #3498db, #2980b9);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.header-title {
  font-size: 20px;
  font-weight: 600;
  color: #2c3e50;
}

.data-selection-content,
.config-content {
  padding: 10px 0;
  flex: 1;
  display: flex;
  flex-direction: column;
}

.el-form-item {
  margin-bottom: 20px;
}

.el-form-item label {
  font-size: 14px;
  color: #2c3e50;
  font-weight: 600;
  margin-bottom: 8px;
}

.el-input__wrapper,
.el-select .el-input__wrapper {
  border-radius: 8px;
  border: 2px solid #e9ecef;
  transition: all 0.3s ease;
}

.el-input__wrapper:hover,
.el-select .el-input__wrapper:hover {
  border-color: #3498db;
}

.el-input__wrapper.is-focus,
.el-select .el-input__wrapper.is-focus {
  border-color: #3498db;
  box-shadow: 0 0 0 3px rgba(52, 152, 219, 0.1);
}

.option-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.option-name {
  font-weight: 500;
  color: #303133;
}

.option-desc {
  font-size: 12px;
  color: #909399;
}

.preview-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
  padding: 12px 16px;
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  border-radius: 10px;
  border: 2px solid #e9ecef;
}

.preview-icon {
  font-size: 20px;
  color: #3498db;
}

.preview-title {
  font-weight: 600;
  color: #2c3e50;
  font-size: 16px;
}

.preview-table-container {
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid #e9ecef;
}

  .chart-container {
  flex: 1;
  display: flex;
  flex-direction: column;
    min-height: 600px;
}

.viz-chart {
    flex: 1;
    min-height: 600px;
    height: 600px;
}

.metrics-display {
  margin-top: 20px;
  flex: 1;
  min-height: 120px;
  overflow-y: auto;
}

.metrics-grid {
  display: flex;
  flex-direction: column;
  gap: 12px;
  width: 100%;
}

.metric-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  border-radius: 10px;
  border: 2px solid #e9ecef;
  transition: all 0.3s ease;
  min-height: 60px;
}

.metric-item:hover {
  background: linear-gradient(135deg, #ecf5ff 0%, #e1f0ff 100%);
  border-color: #3498db;
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(52, 152, 219, 0.15);
}

.metric-icon {
  font-size: 24px;
  color: #3498db;
  background: rgba(52, 152, 219, 0.1);
  border-radius: 8px;
  padding: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.metric-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.metric-label {
  font-size: 14px;
  font-weight: 600;
  color: #2c3e50;
}

.metric-value {
  font-size: 16px;
  color: #3498db;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-weight: 700;
  word-break: break-all;
  line-height: 1.2;
}

.training-status {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
}

.status-placeholder {
  text-align: center;
  color: #95a5a6;
  padding: 40px 20px;
}

.status-icon {
  font-size: 60px;
}

.outlier-icon {
  color: #E74C3C !important;
  background: rgba(231, 76, 60, 0.1) !important;
}

.report-actions {
  margin-top: 20px;
  padding: 16px;
  background: linear-gradient(135deg, #e8f5e8 0%, #c8e6c9 100%);
  border-radius: 12px;
  border: 2px solid #4caf50;
  box-shadow: 0 4px 15px rgba(76, 175, 80, 0.2);
}

.save-success-info {
  display: flex;
  align-items: flex-start;
  margin-bottom: 12px;
}

.save-icon {
  color: #4caf50;
  font-size: 24px;
  margin-right: 12px;
  margin-top: 2px;
}

.save-content {
  flex: 1;
}

.save-title {
  font-size: 16px;
  font-weight: 600;
  color: #2e7d32;
  margin-bottom: 4px;
}

.save-description {
  font-size: 14px;
  color: #388e3c;
  line-height: 1.5;
}

.goto-config-btn {
  color: #4caf50 !important;
  font-weight: 500;
  padding: 4px 8px;
  margin-left: 8px;
}

.goto-config-btn:hover {
  color: #2e7d32 !important;
  background: rgba(76, 175, 80, 0.1);
}

.report-info {
  margin-top: 12px;
  display: flex;
  align-items: center;
  gap: 12px;
}

.outlier-count {
  font-size: 14px;
  color: #e67e22;
  font-weight: 600;
}

.status-placeholder p {
  font-size: 16px;
  margin: 0;
}

.training-controls {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #e9ecef;
}

.training-controls .el-button {
  width: 100%;
  margin-bottom: 12px;
  border-radius: 8px;
  font-weight: 600;
  transition: all 0.3s ease;
}

.training-controls .el-button--primary {
  background: linear-gradient(135deg, #3498db, #2980b9);
  border: none;
}

.training-controls .el-button--primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(52, 152, 219, 0.3);
}

.training-controls .el-button--success {
  background: linear-gradient(135deg, #27ae60, #2ecc71);
  border: none;
}

.training-controls .el-button--success:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(39, 174, 96, 0.3);
}

.training-controls .el-button--danger {
  background: linear-gradient(135deg, #e74c3c, #c0392b);
  border: none;
}

.training-controls .el-button--danger:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(231, 76, 60, 0.3);
}

.config-tip {
  font-size: 12px;
  color: #7f8c8d;
  margin-top: 4px;
  line-height: 1.4;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .metrics-grid {
    grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  }
}

@media (max-width: 768px) {
  .model-training-container {
    padding: 15px;
  }
  
  .page-header h2 {
    font-size: 24px;
  }
  
  .main-content .el-col {
    margin-bottom: 20px;
  }
  
  .metrics-grid {
    grid-template-columns: 1fr;
  }
  
  .metric-item {
    flex-direction: column;
    text-align: center;
    gap: 8px;
  }
}
</style>