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
            
            <!-- Schema选择 -->
            <el-form-item label="Schema" v-if="selectedDataSource">
              <el-select 
                v-model="selectedSchema" 
                placeholder="选择Schema" 
                @change="loadTables"
                filterable
                :loading="loadingSchemas"
                size="large"
                style="width: 100%"
              >
                <el-option
                  v-for="schema in schemas"
                  :key="schema"
                  :label="schema"
                  :value="schema"
                />
              </el-select>
            </el-form-item>
            
            <!-- 数据表选择 -->
            <el-form-item label="数据表" v-if="selectedSchema">
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
                  :key="table.name"
                  :label="table.description"
                  :value="table.name"
                >
                  <div class="option-content">
                    <span class="option-name">{{ table.description }}</span>
                    <span class="option-desc" v-if="table.description !== table.name">{{ table.name }}</span>
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
                  :label="`${field.description || field.name} (${field.type})`"
                  :value="field.name"
                >
                  <div class="option-content">
                    <span class="option-name">{{ field.description || field.name }}</span>
                    <span class="option-desc">{{ field.type }}<span v-if="field.description && field.description !== field.name"> | {{ field.name }}</span></span>
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
                  :label="`${field.description || field.name} (${field.type})`"
                  :value="field.name"
                >
                  <div class="option-content">
                    <span class="option-name">{{ field.description || field.name }}</span>
                    <span class="option-desc">{{ field.type }}<span v-if="field.description && field.description !== field.name"> | {{ field.name }}</span></span>
                  </div>
                </el-option>
              </el-select>
            </el-form-item>
            
            <!-- 数据筛选区域 -->
            <div class="filter-section">
              <h4 style="margin: 0 0 16px 0; color: #2c3e50; font-size: 16px;">
                <el-icon style="margin-right: 8px;"><Location /></el-icon>
                数据筛选（可选）
              </h4>
              
              <!-- 分公司字段选择 -->
              <el-form-item label="分公司字段" :required="false">
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
                    :label="field.description"
                    :value="field.name"
                  >
                    <div class="option-content">
                      <span class="option-name">{{ field.description }}</span>
                      <span class="option-desc">{{ field.type }} - 分公司字段<span v-if="field.description !== field.name"> ({{ field.name }})</span></span>
                    </div>
                  </el-option>
                </el-select>
              </el-form-item>
              
              <!-- 分公司值选择 -->
              <el-form-item v-if="selectedCompanyField" label="分公司值">
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

              <!-- 油气田字段选择 -->
              <el-form-item label="油气田字段" :required="false">
                <el-select 
                  v-model="selectedOilfieldField" 
                  placeholder="选择油气田字段（可选）"
                  filterable
                  clearable
                  :filter-method="filterFields"
                  :loading="fieldLoading"
                  :disabled="!selectedTable"
                  size="large"
                  style="width: 100%"
                  @change="onOilfieldFieldChange"
                >
                  <el-option
                    v-for="field in oilfieldFields"
                    :key="field.name"
                    :label="field.description"
                    :value="field.name"
                  >
                    <div class="option-content">
                      <span class="option-name">{{ field.description }}</span>
                      <span class="option-desc">{{ field.type }} - 油气田字段<span v-if="field.description !== field.name"> ({{ field.name }})</span></span>
                    </div>
                  </el-option>
                </el-select>
              </el-form-item>
              
              <!-- 油气田值选择 -->
              <el-form-item v-if="selectedOilfieldField" label="油气田值">
                <el-select 
                  v-model="selectedOilfieldValue" 
                  placeholder="选择要训练的油气田"
                  filterable
                  clearable
                  :loading="oilfieldValueLoading"
                  size="large"
                  style="width: 100%"
                >
                  <el-option
                    v-for="oilfield in oilfieldValues"
                    :key="oilfield"
                    :label="oilfield"
                    :value="oilfield"
                  >
                    <div class="option-content">
                      <span class="option-name">{{ oilfield }}</span>
                      <span class="option-desc">油气田</span>
                    </div>
                  </el-option>
                </el-select>
              </el-form-item>

              <!-- 井名字段选择 -->
              <el-form-item label="井名字段" :required="false">
                <el-select 
                  v-model="selectedWellField" 
                  placeholder="选择井名字段（可选）"
                  filterable
                  clearable
                  :filter-method="filterFields"
                  :loading="fieldLoading"
                  :disabled="!selectedTable"
                  size="large"
                  style="width: 100%"
                  @change="onWellFieldChange"
                >
                  <el-option
                    v-for="field in wellFields"
                    :key="field.name"
                    :label="field.description"
                    :value="field.name"
                  >
                    <div class="option-content">
                      <span class="option-name">{{ field.description }}</span>
                      <span class="option-desc">{{ field.type }} - 井名字段<span v-if="field.description !== field.name"> ({{ field.name }})</span></span>
                    </div>
                  </el-option>
                </el-select>
              </el-form-item>
              
              <!-- 井名值选择 -->
              <el-form-item v-if="selectedWellField" label="井名值">
                <el-select 
                  v-model="selectedWellValue" 
                  placeholder="选择要训练的井（可多选）"
                  filterable
                  clearable
                  :loading="wellValueLoading"
                  size="large"
                  style="width: 100%"
                  multiple
                  collapse-tags
                  collapse-tags-tooltip
                >
                  <el-option
                    v-for="well in wellValues"
                    :key="well"
                    :label="well"
                    :value="well"
                  >
                    <div class="option-content">
                      <span class="option-name">{{ well }}</span>
                      <span class="option-desc">井名</span>
                    </div>
                  </el-option>
                </el-select>
              </el-form-item>
            </div>
            
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
            
            <!-- 训练配置参数 -->
            <el-divider content-position="left">
              <el-icon style="margin-right: 4px;"><DataAnalysis /></el-icon>
              训练配置
            </el-divider>
            
            <el-alert
              title="重要提示"
              type="warning"
              :closable="false"
              show-icon
              style="margin-bottom: 16px;"
            >
              <template #default>
                <div style="font-size: 13px; line-height: 1.6;">
                  <p style="margin: 0 0 8px 0;"><strong>最大训练样本数：</strong>限制加载到内存的数据量，防止服务器内存溢出</p>
                  <p style="margin: 0;"><strong>建议值：</strong>10万（小型服务器）~ 50万（大型服务器）</p>
                </div>
              </template>
            </el-alert>
            
            <el-form-item label="最大训练样本数">
              <el-input-number
                v-model="trainingConfig.maxTrainingSamples"
                :min="1000"
                :max="1000000"
                :step="10000"
                style="width: 100%"
                size="large"
              />
              <div style="font-size: 12px; color: #909399; margin-top: 4px;">
                超过此数量将智能采样，避免内存溢出
              </div>
            </el-form-item>
            
            <el-form-item label="训练轮次 (Epochs)">
              <el-input-number
                v-model="trainingConfig.epochs"
                :min="10"
                :max="1000"
                :step="10"
                style="width: 100%"
                size="large"
              />
            </el-form-item>
            
            <el-form-item label="批次大小 (Batch Size)">
              <el-input-number
                v-model="trainingConfig.batchSize"
                :min="32"
                :max="1024"
                :step="32"
                style="width: 100%"
                size="large"
              />
            </el-form-item>
            
            <el-form-item label="学习率 (Learning Rate)">
              <el-input-number
                v-model="trainingConfig.learningRate"
                :min="0.001"
                :max="0.1"
                :step="0.001"
                :precision="3"
                style="width: 100%"
                size="large"
              />
            </el-form-item>
            
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
import { ref, shallowRef, reactive, onMounted, computed, nextTick, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useRouter } from 'vue-router'
import { TrendCharts, Connection, Setting, Cpu, DataAnalysis, View, Warning, Download, SuccessFilled, Right, Location } from '@element-plus/icons-vue'
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
    Download,
    Location
  },
  setup() {
    const router = useRouter()
    
    // 数据源相关
    const dataSources = ref([])
    const selectedDataSource = ref('')
    const schemas = ref([])
    const selectedSchema = ref('')
    const loadingSchemas = ref(false)
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
    
    // 油气田相关
    const selectedOilfieldField = ref('')
    const selectedOilfieldValue = ref('')
    const oilfieldValues = ref([])
    const oilfieldValueLoading = ref(false)
    
    // 井名相关
    const selectedWellField = ref('')
    const selectedWellValue = ref([])
    const wellValues = ref([])
    const wellValueLoading = ref(false)
    
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
      learningRate: 0.01,
      maxTrainingSamples: 100000  // 最大训练样本数，防止OOM
    })
    
    // 训练状态
    const isTraining = ref(false)
    const trainingCompleted = ref(false)
    const isSaving = ref(false)
    const vizChart = ref(null)
    const vizChartInstance = shallowRef(null)
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
    
    // 计算可能的分公司字段（基于字段描述）
    const companyFields = computed(() => {
      // 只匹配明确的公司字段，缩小范围避免误匹配
      const companyKeywords = ['公司', 'company', 'branch']
      return availableFields.value.filter(field => {
        const fieldName = field.name.toLowerCase()
        // 只匹配字段名，不匹配描述
        return companyKeywords.some(keyword => fieldName.includes(keyword.toLowerCase()))
      })
    })
    
    // 计算可能的油气田字段（基于字段描述）
    const oilfieldFields = computed(() => {
      const oilfieldKeywords = ['油田', '气田', '油气田', '区块', '工区', '油区', '气区', 'oilfield', 'gasfield', 'field', 'block', 'area']
      return availableFields.value.filter(field => {
        // 优先使用字段描述，如果没有描述则使用字段名
        const searchText = (field.description || field.name).toLowerCase()
        return oilfieldKeywords.some(keyword => searchText.includes(keyword.toLowerCase()))
      })
    })
    
    // 计算可能的井名字段（基于字段描述）
    const wellFields = computed(() => {
      // 只匹配井名/井号字段，不匹配井的其他属性字段
      return availableFields.value.filter(field => {
        // 优先使用字段描述，没有描述才用字段名
        const searchText = (field.description || field.name).toLowerCase()
        // 必须包含"井"或"well"，且包含"名"或"号"或"name"或"id"或"code"
        const hasWellPrefix = searchText.includes('井') || searchText.includes('well')
        const hasNameOrId = searchText.includes('名') || searchText.includes('号') || 
                           searchText.includes('name') || searchText.includes('id') || 
                           searchText.includes('code')
        return hasWellPrefix && hasNameOrId
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
        filteredTables.value = availableTables.value.filter(table => {
          // 如果table是对象，搜索name和description
          if (typeof table === 'object') {
            return table.name.toLowerCase().includes(query.toLowerCase()) ||
                   table.description.toLowerCase().includes(query.toLowerCase())
          }
          // 如果table是字符串（向后兼容）
          return table.toLowerCase().includes(query.toLowerCase())
        })
      }
    }
    
    const filterFields = (query) => {
      if (query === '') {
        filteredFields.value = availableFields.value
      } else {
        filteredFields.value = availableFields.value.filter(field => 
          field.name.toLowerCase().includes(query.toLowerCase()) ||
          field.type.toLowerCase().includes(query.toLowerCase()) ||
          (field.description && field.description.toLowerCase().includes(query.toLowerCase()))
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
      
      // 重置状态
      selectedSchema.value = ''
      schemas.value = []
      availableTables.value = []
      filteredTables.value = []
      selectedTable.value = ''
      availableFields.value = []
      filteredFields.value = []
      
      await loadSchemas()
    }
    
    // 加载Schema列表
    const loadSchemas = async () => {
      if (!selectedDataSource.value) return
      
      loadingSchemas.value = true
      try {
        const sourceId = selectedDataSource.value
        const response = await axios.get(`/api/database/sources/${sourceId}`)
        if (response.data.success) {
          const dataSource = response.data.data
          const schemasResponse = await axios.post('/api/database/schemas', dataSource)
          if (schemasResponse.data.success) {
            schemas.value = schemasResponse.data.data
            if (schemas.value.length > 0) {
              selectedSchema.value = schemas.value.includes('public') ? 'public' : schemas.value[0]
              await loadTables()
            }
          }
        }
      } catch (error) {
        console.error('加载Schema列表失败:', error)
        ElMessage.error('加载Schema列表失败')
      } finally {
        loadingSchemas.value = false
      }
    }
    
    // 加载表列表
    const loadTables = async () => {
      if (!selectedDataSource.value || !selectedSchema.value) return
      
      tableLoading.value = true
      try {
        const sourceId = selectedDataSource.value
        const source = dataSources.value.find(s => s.id === sourceId)
        if (source) {
          const response = await axios.post('/api/database/tables', {
            ...source,
            schema: selectedSchema.value
          })
          if (response.data.success) {
            availableTables.value = response.data.data
            filteredTables.value = availableTables.value
            selectedTable.value = ''
            availableFields.value = []
            filteredFields.value = []
          }
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
        const sourceId = selectedDataSource.value
        const source = dataSources.value.find(s => s.id === sourceId)
        if (source) {
          const response = await axios.post('/api/database/fields', {
            ...source,
            schema: selectedSchema.value,
            table_name: selectedTable.value
          })
          if (response.data.success) {
            availableFields.value = response.data.data
            filteredFields.value = availableFields.value
            selectedFeatures.value = []
            selectedTarget.value = ''
            // 重置筛选选择
            selectedCompanyField.value = ''
            selectedCompanyValue.value = ''
            companyValues.value = []
            selectedOilfieldField.value = ''
            selectedOilfieldValue.value = ''
            oilfieldValues.value = []
            selectedWellField.value = ''
            selectedWellValue.value = []
            wellValues.value = []
            await loadPreviewData()
          }
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
        const source = dataSources.value.find(s => s.id === selectedDataSource.value)
        const response = await axios.post('/api/database/distinct-values', {
          data_source_id: source.id,
          schema: selectedSchema.value,
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
    
    // 处理油气田字段变化
    const onOilfieldFieldChange = async () => {
      if (!selectedOilfieldField.value) {
        oilfieldValues.value = []
        selectedOilfieldValue.value = ''
        return
      }
      
      oilfieldValueLoading.value = true
      try {
        const source = dataSources.value.find(s => s.id === selectedDataSource.value)
        const response = await axios.post('/api/database/distinct-values', {
          data_source_id: source.id,
          schema: selectedSchema.value,
          table_name: selectedTable.value,
          field_name: selectedOilfieldField.value
        })
        
        if (response.data.success) {
          oilfieldValues.value = response.data.data.filter(value => value !== null && value !== '')
          selectedOilfieldValue.value = ''
        } else {
          ElMessage.error('加载油气田列表失败: ' + response.data.error)
        }
      } catch (error) {
        console.error('加载油气田列表失败:', error)
        ElMessage.error('加载油气田列表失败')
      } finally {
        oilfieldValueLoading.value = false
      }
    }
    
    // 处理井名字段变化
    const onWellFieldChange = async () => {
      if (!selectedWellField.value) {
        wellValues.value = []
        selectedWellValue.value = []
        return
      }
      
      wellValueLoading.value = true
      try {
        const source = dataSources.value.find(s => s.id === selectedDataSource.value)
        const response = await axios.post('/api/database/distinct-values', {
          data_source_id: source.id,
          schema: selectedSchema.value,
          table_name: selectedTable.value,
          field_name: selectedWellField.value
        })
        
        if (response.data.success) {
          wellValues.value = response.data.data.filter(value => value !== null && value !== '')
          selectedWellValue.value = []
        } else {
          ElMessage.error('加载井名列表失败: ' + response.data.error)
        }
      } catch (error) {
        console.error('加载井名列表失败:', error)
        ElMessage.error('加载井名列表失败')
      } finally {
        wellValueLoading.value = false
      }
    }
    
    // 加载预览数据
    const loadPreviewData = async () => {
      if (!selectedDataSource.value || !selectedTable.value) return
      
      try {
        const fields = [...selectedFeatures.value]
        if (selectedTarget.value) fields.push(selectedTarget.value)
        
        if (fields.length === 0) return
        
        const source = dataSources.value.find(s => s.id === selectedDataSource.value)
        if (!source) {
          console.error('未找到数据源')
          return
        }
        
        const response = await axios.post('/api/database/preview', {
          data_source_id: selectedDataSource.value,
          schema: selectedSchema.value,
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
          legend: { top: 10, left: 'center', data: [] },  // 初始化为空，等有数据时再更新
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
        console.log('=== 训练前检查 ===')
        console.log('selectedDataSource.value:', selectedDataSource.value)
        console.log('selectedSchema.value:', selectedSchema.value, '类型:', typeof selectedSchema.value)
        console.log('selectedTable.value:', selectedTable.value)
        console.log('schemas.value:', schemas.value)
        
        const trainingData = {
          data_source_id: selectedDataSource.value,
          schema: selectedSchema.value || 'public',  // 确保不发送空值
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
          max_training_samples: trainingConfig.maxTrainingSamples,  // 最大训练样本数
          // 筛选过滤参数
          company_field: selectedCompanyField.value || null,
          company_value: selectedCompanyValue.value || null,
          oilfield_field: selectedOilfieldField.value || null,
          oilfield_value: selectedOilfieldValue.value || null,
          well_field: selectedWellField.value || null,
          well_value: selectedWellValue.value && selectedWellValue.value.length > 0 ? selectedWellValue.value : null
        }
        
        console.log('=== 发送训练请求 ===')
        console.log('trainingData.schema:', trainingData.schema)
        console.log('完整trainingData:', JSON.stringify(trainingData, null, 2))
        
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
        console.log('开始绘制聚类图表，接收到的数据:', {
          hasX: !!vizData.x,
          hasY: !!vizData.y,
          xLength: vizData.x?.length || 0,
          yLength: vizData.y?.length || 0,
          outliersLength: vizData.outliers?.length || 0,
          outlierIndicesLength: vizData.outlier_indices?.length || 0
        })
        
        const x = vizData.x || []
        const y = vizData.y || []
        const labels = vizData.labels || []
        const centers = vizData.centers || []
        const outliers = vizData.outliers || []
        const outlier_indices = vizData.outlier_indices || []  // 使用索引匹配异常值
        const companies = vizData.companies || []
        const company_column = vizData.company_column
        
        // 数据验证
        if (!x || !y || x.length === 0 || y.length === 0) {
          console.error('错误: 缺少数据点 (x或y为空)')
          return
        }
        
        if (x.length !== y.length) {
          console.error(`错误: x和y数组长度不匹配 (x: ${x.length}, y: ${y.length})`)
          return
        }
        
        // 获取特征和目标名称
        const featureName = vizData.feature_name || 'X'
        const targetName = vizData.target_name || 'Y'
        
        // [新增] 1. 定义清洗算法：计算基于 IQR 的有效数据范围
        // 使用 100倍 IQR 作为阈值，仅过滤掉数量级错误的极端脏数据（如21亿），保留正常离群点
        const getValidBounds = (values) => {
          const sorted = values.filter(v => v != null && isFinite(v)).sort((a, b) => a - b)
          if (sorted.length === 0) return { min: -Infinity, max: Infinity }
          
          const q1 = sorted[Math.floor(sorted.length * 0.25)]
          const q3 = sorted[Math.floor(sorted.length * 0.75)]
          const iqr = q3 - q1
          
          // 核心策略：100倍 IQR，允许数据偏离中心极远，只杀天文数字
          const threshold = iqr * 100 
          const margin = threshold > 0 ? threshold : (Math.abs(q1) * 0.5 || 1000)

          const min = q1 - margin
          const max = q3 + margin
          
          console.log(`数据清洗范围: [${min.toFixed(2)}, ${max.toFixed(2)}], Q1=${q1}, Q3=${q3}, IQR=${iqr}`)
          return { min, max }
        }

        // 计算 X 和 Y 的有效范围
        const xBounds = getValidBounds(x)
        const yBounds = getValidBounds(y)

        // 生成颜色方案
        // 生成颜色方案（参考matplotlib风格，使用更鲜明的颜色）
        const colors = [
          '#1f77b4',  // 蓝色
          '#ff7f0e',  // 橙色  
          '#2ca02c',  // 绿色
          '#d62728',  // 红色（但离群点会用单独的红色）
          '#9467bd',  // 紫色
          '#8c564b',  // 棕色
          '#e377c2',  // 粉色
          '#7f7f7f',  // 灰色
          '#bcbd22',  // 黄绿色
          '#17becf'   // 青色
        ]
        
        // 打印接收到的关键数据
        console.log('\n=== 接收到的可视化数据 ===')
        console.log(`x 长度: ${x.length}, 前3个值:`, x.slice(0, 3))
        console.log(`y 长度: ${y.length}, 前3个值:`, y.slice(0, 3))
        console.log(`labels 长度: ${labels.length}, 前5个值:`, labels.slice(0, 5))
        console.log(`companies 长度: ${companies.length}, 前5个值:`, companies.slice(0, 5))
        console.log(`outlier_indices 长度: ${outlier_indices.length}`)
        console.log(`centers 长度: ${centers?.length || 0}`)
        console.log(`company_column:`, company_column)
        
        // 创建异常值索引集合，提高查找效率（如果提供了索引）
        const outlierIndexSet = outlier_indices.length > 0 ? new Set(outlier_indices) : null
        console.log(`outlierIndexSet 创建: ${outlierIndexSet ? outlierIndexSet.size + ' 个异常值索引' : 'null'}`)
        
        // 如果没有分公司字段，按聚类标签分组；否则按分公司分组
        const useClusterLabels = !company_column || (companies.length === 0 || companies.every(c => !c || c === 'Unknown'))
        
        // 按分组方式组织数据
        const dataGroups = {}
        let uniqueLabels = []
        let uniqueCompanies = []
        
        if (useClusterLabels) {
          // 按聚类标签分组
          uniqueLabels = [...new Set(labels)]
          uniqueLabels.forEach(label => {
            dataGroups[`聚类${label}`] = {
              normal: [],
              outliers: [],
              centers: [],
              label: label
            }
          })
          console.log('使用聚类标签分组，聚类数量:', uniqueLabels.length)
        } else {
          // 按分公司分组
          uniqueCompanies = [...new Set(companies)]
        uniqueCompanies.forEach(company => {
            dataGroups[company] = {
            normal: [],
            outliers: [],
              centers: [],
              label: null
          }
        })
          console.log('使用分公司分组，分公司数量:', uniqueCompanies.length)
        }
        
        // 确保companies数组长度匹配
        const companiesArray = companies.length === x.length ? companies : 
                              Array(x.length).fill('Unknown')
        
        // 分类数据点（使用索引匹配，O(1)时间复杂度）
        let totalNormal = 0
        let totalOutliers = 0
        let cleanedCount = 0
        let skippedInvalid = 0
        const dirtyOutliers = [] // 收集脏数据用于报告
        
        for (let i = 0; i < x.length; i++) {
          // 验证数据点有效性
          if (x[i] == null || y[i] == null || isNaN(x[i]) || isNaN(y[i])) {
            continue
          }
          
          // 脏数据清洗：跳过超出有效范围的极端值
          if (x[i] < xBounds.min || x[i] > xBounds.max || y[i] < yBounds.min || y[i] > yBounds.max) {
            cleanedCount++
            if (cleanedCount <= 5) {
               console.warn(`清洗掉极端脏数据 [${i}]: x=${x[i]}, y=${y[i]}`)
            }
            
            // 将其记录为“极端脏数据”异常点，供导出报告使用
            dirtyOutliers.push({
              row_index: i,
              feature_name: featureName,
              feature_value: x[i],
              target_name: targetName,
              actual_value: y[i],
              predicted_value: null,
              outlier_type: 'extreme_dirty_data',
              is_outlier: true,
              description: '坐标值异常(数量级错误)，已从可视化中剔除'
            })
            continue // 直接跳过这个点，不添加到图表中
          }
          
          const point = [Number(x[i]), Number(y[i])]
          
          // 确定分组键：如果没有分公司字段，使用聚类标签；否则使用分公司
          let groupKey
          if (useClusterLabels) {
            const label = labels[i] !== undefined ? labels[i] : -1
            groupKey = `聚类${label}`
          } else {
            groupKey = companiesArray[i] || 'Unknown'
          }
          
          // 确保分组存在
          if (!dataGroups[groupKey]) {
            dataGroups[groupKey] = {
              normal: [],
              outliers: [],
              centers: [],
              label: useClusterLabels ? (labels[i] !== undefined ? labels[i] : -1) : null
            }
          }
          
          // 使用索引检查是否为异常值（O(1)时间复杂度）
          const isOutlier = outlierIndexSet ? outlierIndexSet.has(i) : false
          
          if (isOutlier) {
            dataGroups[groupKey].outliers.push(point)
            totalOutliers++
          } else {
            dataGroups[groupKey].normal.push(point)
            totalNormal++
          }
        }
        
        console.log(`数据分类完成: 正常=${totalNormal}, 离群=${totalOutliers}, 清洗脏数据=${cleanedCount}`)

        // [新增] 3. 将清洗掉的脏数据合并到全局训练结果中
        if (dirtyOutliers.length > 0 && trainingResult.value) {
            if (!trainingResult.value.viz_data.outlier_details) {
                trainingResult.value.viz_data.outlier_details = []
            }
            // 合并到详情列表
            trainingResult.value.viz_data.outlier_details.push(...dirtyOutliers)
            
            // 更新统计数字
            if (outlierSummary.value) {
                outlierSummary.value.total_outliers += dirtyOutliers.length
                if (x.length > 0) {
                    outlierSummary.value.outlier_rate = (outlierSummary.value.total_outliers / x.length) * 100
                }
            }
            console.log(`已将 ${dirtyOutliers.length} 个极端脏数据添加到异常报告列表`)
        }

        console.log(`数据点分类完成: 正常=${totalNormal}, 离群=${totalOutliers}, 无效=${skippedInvalid}, 总计=${x.length}`)
        console.log('dataGroups 键:', Object.keys(dataGroups))
        console.log('dataGroups 详情:', JSON.stringify(Object.entries(dataGroups).map(([k, v]) => ({
          key: k,
          normal: v.normal.length,
          outliers: v.outliers.length,
          sampleNormal: v.normal.slice(0, 3)
        })), null, 2))
        
        // [修复] 4. 前端自动计算聚类几何中心 (解决后端中心点错位问题)
        if (useClusterLabels) {
          Object.keys(dataGroups).forEach(groupKey => {
            const group = dataGroups[groupKey]
            if (group.normal && group.normal.length > 0) {
              let sumX = 0, sumY = 0
              group.normal.forEach(p => { sumX += p[0]; sumY += p[1] })
              group.centers = [[sumX / group.normal.length, sumY / group.normal.length]]
            }
          })
        } else if (vizData.grid_info && vizData.grid_info.companies) {
           // 如果是分公司分组，使用后端返回的grid信息
           Object.entries(vizData.grid_info.companies).forEach(([key, info]) => {
            if (info.center && dataGroups[key]) dataGroups[key].centers.push(info.center)
          })
        }
        
        // 构建图表系列
        const series = []
        let colorIndex = 0
        
        console.log('开始构建图表系列，数据组:', Object.keys(dataGroups))
        console.log('数据组详情:', Object.entries(dataGroups).map(([name, data]) => ({
          name,
          normal: data.normal.length,
          outliers: data.outliers.length,
          centers: data.centers.length,
          label: data.label
        })))
        
        console.log('=== 开始构建 series，遍历 dataGroups ===')
        
        // 为每个分组添加正常数据点
        Object.entries(dataGroups).forEach(([groupKey, data]) => {
          console.log(`\n处理分组: ${groupKey}`)
          console.log(`  - normal.length: ${data.normal.length}`)
          console.log(`  - outliers.length: ${data.outliers.length}`)
          if (data.normal.length > 0) {
            // 只过滤无效数据点，不过滤坐标范围（让ECharts自动处理）
            const normalInRange = data.normal.filter(point => {
              const [px, py] = point
              // 只检查数据有效性，不检查坐标范围
              return px != null && py != null && 
                     !isNaN(px) && !isNaN(py) && 
                     isFinite(px) && isFinite(py)
            })
            
            console.log(`${groupKey} - 正常数据点: 原始=${data.normal.length}, 有效=${normalInRange.length}`)
            
            if (normalInRange.length > 0) {
              // 确定系列名称（简化命名）
              let seriesName = groupKey  // 直接使用聚类名称，如"聚类0"
              
              // 显式禁用large模式，确保所有样式生效
              const seriesItem = {
                name: seriesName,
                type: 'scatter',
                data: normalInRange,
                large: false,             // [保持] 关闭大数据优化模式
                largeThreshold: 100000,   // [新增] 调大阈值，确保不自动开启优化
                progressive: 0,           // [新增] 关闭渐进式渲染，一次性画完
                clip: false,              // [新增] 关闭裁剪，防止边缘点显示不全
                symbol: 'circle',         // 使用圆形标记
                symbolSize: 10,            // 圆点大小
                itemStyle: {
                  color: colors[colorIndex % colors.length],
                  opacity: 0.8,
                  borderWidth: 0
                },
                emphasis: {
                  itemStyle: {
                    opacity: 1.0,
                    symbolSize: 14
                  }
                }
              }

              series.push(seriesItem)
              console.log(`✓ 已添加系列: ${seriesItem.name}`)
              console.log(`  - 数据点数量: ${normalInRange.length}`)
              console.log(`  - 颜色: ${colors[colorIndex % colors.length]}`)
              console.log(`  - 前5个数据点:`, normalInRange.slice(0, 5))
            } else {
              console.warn(`✗ ${groupKey} - 没有正常数据点在有效范围内`)
              }
          } else {
            console.log(`${groupKey} - 没有正常数据点`)
          }
          
          // 添加聚类中心标记（如果存在）
          if (data.centers && data.centers.length > 0 && useClusterLabels) {
            data.centers.forEach(center => {
              if (center && center.length === 2) {
                const [cx, cy] = center
                if (cx != null && cy != null && !isNaN(cx) && !isNaN(cy) && isFinite(cx) && isFinite(cy)) {
                  series.push({
                    name: `${groupKey}中心`,
                    type: 'scatter',
                    data: [[cx, cy]],
                    symbol: 'pin',
                    symbolSize: 20,      // [修改] 改小尺寸，更精致
                    showInLegend: false, // [新增] 隐藏图例，避免图例重复导致颜色混淆
                    itemStyle: {
                      color: colors[colorIndex % colors.length],
                      borderColor: '#fff',
                      borderWidth: 1     // [修改] 边框细一点，颜色更明显
                    },
                    label: {
                      show: true,
                      formatter: `中心`,
                      position: 'top',
                      color: '#333',
                      fontSize: 12,
                      fontWeight: 'bold',
                      distance: 5        // [新增] 调整标签距离
                    },
                    tooltip: {
                      formatter: `<b>${groupKey}中心</b><br/>X: ${cx.toFixed(2)}<br/>Y: ${cy.toFixed(2)}`
                    },
                    z: 10
                  })
                  console.log(`✓ 已添加聚类中心: ${groupKey}, 坐标: [${cx.toFixed(2)}, ${cy.toFixed(2)}]`)
                }
              }
            })
          }
          
          colorIndex++
        })
        
        // 添加所有异常值作为单独系列（在正常数据点之后添加，确保离群点在上层显示）
        const allOutliers = []
        Object.values(dataGroups).forEach(data => {
          allOutliers.push(...data.outliers)
        })
        
        console.log(`\n=== 准备添加离群点系列 ===`)
        console.log(`离群点总计: ${allOutliers.length}`)
        console.log(`当前 series 数量: ${series.length}`)
        
        if (allOutliers.length > 0) {
          // 只过滤无效的异常值，不过滤坐标范围
          const validOutliers = allOutliers.filter(point => {
            const [px, py] = point
            // 只检查数据有效性，不检查坐标范围
            return px != null && py != null && 
                   !isNaN(px) && !isNaN(py) && 
                   isFinite(px) && isFinite(py)
          })
          
          console.log(`离群点过滤后: ${validOutliers.length}/${allOutliers.length} 有效`)
          
          if (validOutliers.length > 0) {
            // 显式禁用large模式，确保样式生效
            // 离群点使用红色圆点标记
            // 离群点使用红色圆点标记
            const outlierSeries = {
              name: '离群点',
              type: 'scatter',
              data: validOutliers,
              large: false,             // [保持] 关闭大数据优化模式
              largeThreshold: 100000,   // [新增] 调大阈值
              progressive: 0,           // [新增] 关闭渐进式渲染
              clip: false,              // [新增] 关闭裁剪
              symbol: 'circle',         // 使用圆形标记
              symbolSize: 12,            // 稍大一点，便于区分
              itemStyle: {
                color: '#E74C3C',       // 红色
                opacity: 0.9,
                borderWidth: 0
              },
              emphasis: {
                itemStyle: {
                  opacity: 1.0,
                  symbolSize: 16
                }
              }
            }
            series.push(outlierSeries)
            console.log(`已添加离群点系列:`, {
              name: outlierSeries.name,
              dataLength: outlierSeries.data.length,
              symbolSize: outlierSeries.symbolSize,
              sampleData: validOutliers.slice(0, 3)
            })
          } else {
            console.warn('没有有效的离群点可显示')
          }
        } else {
          console.log('没有离群点需要添加')
        }
        
        // 输出最终series统计
        console.log(`最终series统计: 总计${series.length}个系列`)
        series.forEach((s, idx) => {
          console.log(`  [${idx}] ${s.name}: ${s.data ? s.data.length : 0}个数据点`)
        })
        
        // 计算数据范围（使用分位数过滤极端异常值）
        const calculateFullRange = (values) => {
          if (!values || values.length === 0) return { min: 0, max: 100, usePercentile: false }
          
          const validValues = values.filter(v => v != null && !isNaN(v) && isFinite(v))
          if (validValues.length === 0) return { min: 0, max: 100, usePercentile: false }
          
          const min = Math.min(...validValues)
          const max = Math.max(...validValues)
          const range = max - min
          
          // 检查数据分布，如果极端值过大，使用分位数
          const sorted = [...validValues].sort((a, b) => a - b)
          const q1_idx = Math.floor(sorted.length * 0.01)  // 1%分位数
          const q99_idx = Math.floor(sorted.length * 0.99) // 99%分位数
          const q1 = sorted[q1_idx]
          const q99 = sorted[q99_idx]
          const iqr = q99 - q1
          
          // 判断是否有极端异常值：如果99%分位数范围远小于全部范围
          const usePercentile = (range > 0 && iqr > 0 && range / iqr > 10)
          
          let displayMin, displayMax
          if (usePercentile) {
            // 使用分位数范围，聚焦主要数据区域
            const margin = iqr * 0.1  // 10%边距
            displayMin = q1 - margin
            displayMax = q99 + margin
            console.log(`检测到极端值，使用1%-99%分位数。全范围: [${min.toFixed(2)}, ${max.toFixed(2)}], 显示范围: [${displayMin.toFixed(2)}, ${displayMax.toFixed(2)}]`)
          } else {
            // 使用全部数据范围
            const margin = range > 0 ? range * 0.05 : 1  // 5%边距
            displayMin = min - margin
            displayMax = max + margin
          }
          
          return {
            min: displayMin,
            max: displayMax,
            fullMin: min,
            fullMax: max,
            range: range,
            usePercentile: usePercentile,
            q1: q1,
            q99: q99
          }
        }
        
        const xRange = calculateFullRange(x)
        const yRange = calculateFullRange(y)
        
        // 调试日志
        console.log('聚类图表数据:', {
          totalPoints: x.length,
          normalPoints: Object.values(dataGroups).reduce((sum, data) => sum + data.normal.length, 0),
          outlierPoints: allOutliers.length,
          seriesCount: series.length,
          seriesNames: series.map(s => s.name),
          outlierIndices: outlier_indices.length,
          hasOutlierIndices: outlierIndexSet !== null,
          useClusterLabels: useClusterLabels,
          xRange: {
            fullMin: xRange.fullMin,
            fullMax: xRange.fullMax,
            displayMin: xRange.min,
            displayMax: xRange.max,
            usePercentile: xRange.usePercentile,
            ...(xRange.q1 !== undefined ? { q1: xRange.q1, q99: xRange.q99 } : {})
          },
          yRange: {
            fullMin: yRange.fullMin,
            fullMax: yRange.fullMax,
            displayMin: yRange.min,
            displayMax: yRange.max,
            usePercentile: yRange.usePercentile,
            ...(yRange.q1 !== undefined ? { q1: yRange.q1, q99: yRange.q99 } : {})
          },
          samplePoints: x.slice(0, 10).map((xi, i) => [xi, y[i]]),
          dataRange: vizData.data_range || null,
          // 检查有多少数据点在显示范围内
          pointsInXRange: x.filter(xi => xi >= xRange.min && xi <= xRange.max).length,
          pointsInYRange: y.filter(yi => yi >= yRange.min && yi <= yRange.max).length
        })
        
        // 如果使用了分位数，提示用户
        if (xRange.usePercentile || yRange.usePercentile) {
          console.warn('检测到数据范围异常大，已使用分位数(1%-99%)聚焦主要数据区域。极端值可能不在显示范围内。')
          console.warn(`X轴显示范围: ${xRange.min.toFixed(2)} 到 ${xRange.max.toFixed(2)} (实际范围: ${xRange.fullMin.toFixed(2)} 到 ${xRange.fullMax.toFixed(2)})`)
          console.warn(`Y轴显示范围: ${yRange.min.toFixed(2)} 到 ${yRange.max.toFixed(2)} (实际范围: ${yRange.fullMin.toFixed(2)} 到 ${yRange.fullMax.toFixed(2)})`)
        }
        
        // 如果没有系列数据，添加一个空系列以避免图表错误
        if (series.length === 0) {
          console.warn('警告: 没有数据点可显示')
          series.push({
            name: '无数据',
            type: 'scatter',
            data: [],
            symbolSize: 0
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
            formatter: (params) => {
              if (params.seriesName === '离群点') {
                return `<b style="color: #E74C3C;">离群点</b><br/>经度: ${params.value[0].toFixed(6)}<br/>纬度: ${params.value[1].toFixed(6)}`
              } else {
                return `<b>${params.seriesName}</b><br/>经度: ${params.value[0].toFixed(6)}<br/>纬度: ${params.value[1].toFixed(6)}`
              }
            },
            backgroundColor: 'rgba(255, 255, 255, 0.95)',
            borderColor: '#ccc',
            borderWidth: 1,
            textStyle: {
              color: '#333'
            }
          },
          legend: {
            data: series.map(s => s.name),
            top: 10,
            type: 'scroll',
            textStyle: {
              fontSize: 12
            }
          },
          grid: {
            left: '5%',
            right: '4%',
            bottom: '8%',
            top: '12%',
            containLabel: true
          },
          dataZoom: [
            { 
              type: 'inside',
              throttle: 50,
              filterMode: 'none'  // 不过滤数据点
            }
            // 暂时移除 slider 类型的 dataZoom，避免 getOtherAxis 错误
            // 用户可以使用鼠标滚轮进行缩放
          ],
          xAxis: {
            type: 'value',
            name: featureName,
            nameLocation: 'middle',
            nameGap: 30,
            nameTextStyle: {
              fontSize: 14,
              fontWeight: 'bold'
            },
            min: xRange.min,
            max: xRange.max,
            axisLabel: { 
              color: '#606266',
              formatter: (value) => {
                // 根据数值大小智能格式化
                if (Math.abs(value) >= 1e9) return (value / 1e9).toFixed(1) + 'B'
                if (Math.abs(value) >= 1e6) return (value / 1e6).toFixed(1) + 'M'
                if (Math.abs(value) >= 1e3) return (value / 1e3).toFixed(1) + 'K'
                return value.toFixed(2)
              }
            },
            splitLine: { 
              show: true,
              lineStyle: { 
                color: '#e0e0e0',
                type: 'solid'
              } 
            }
          },
          yAxis: {
            type: 'value',
            name: targetName,
            nameLocation: 'middle',
            nameGap: 50,
            nameTextStyle: {
              fontSize: 14,
              fontWeight: 'bold'
            },
            min: yRange.min,
            max: yRange.max,
            axisLabel: { 
              color: '#606266',
              formatter: (value) => {
                // 根据数值大小智能格式化
                if (Math.abs(value) >= 1e9) return (value / 1e9).toFixed(1) + 'B'
                if (Math.abs(value) >= 1e6) return (value / 1e6).toFixed(1) + 'M'
                if (Math.abs(value) >= 1e3) return (value / 1e3).toFixed(1) + 'K'
                return value.toFixed(2)
              }
            },
            splitLine: { 
              show: true,
              lineStyle: { 
                color: '#e0e0e0',
                type: 'solid'
              } 
            }
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
        
        // 详细调试信息
        console.log('聚类可视化图表绘制完成', {
          总数据点: x.length,
          异常值: allOutliers.length,
          分组数: useClusterLabels ? uniqueLabels.length : uniqueCompanies.length,
          分组类型: useClusterLabels ? '聚类标签' : '分公司',
          聚类中心: centers.length,
          series数量: series.length,
          series详情: series.map(s => ({
            name: s.name,
            type: s.type,
            dataLength: s.data ? s.data.length : 0,
            sampleData: s.data ? s.data.slice(0, 3) : []
          })),
          xAxis配置: option.xAxis,
          yAxis配置: option.yAxis,
          xRange: xRange,
          yRange: yRange
        })
        
        // 检查数据点是否在坐标轴范围内
        if (series.length > 0) {
          series.forEach(s => {
            if (s.data && s.data.length > 0) {
              const samplePoint = s.data[0]
              const [px, py] = samplePoint
              const inXRange = px >= (option.xAxis.min || -Infinity) && px <= (option.xAxis.max || Infinity)
              const inYRange = py >= (option.yAxis.min || -Infinity) && py <= (option.yAxis.max || Infinity)
              console.log(`${s.name}: 第一个数据点 [${px}, ${py}], X轴范围内: ${inXRange}, Y轴范围内: ${inYRange}`)
            }
          })
        }
        
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
      schemas,
      selectedSchema,
      loadingSchemas,
      availableTables,
      selectedTable,
      availableFields,
      selectedFeatures,
      selectedTarget,
      previewData,
      onDataSourceChange,
      loadSchemas,
      loadTables,
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
      
      // 油气田相关
      selectedOilfieldField,
      selectedOilfieldValue,
      oilfieldFields,
      oilfieldValues,
      oilfieldValueLoading,
      onOilfieldFieldChange,
      
      // 井名相关
      selectedWellField,
      selectedWellValue,
      wellFields,
      wellValues,
      wellValueLoading,
      onWellFieldChange,
      
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

/* 筛选区域样式 */
.filter-section {
  margin-top: 16px;
  padding: 20px;
  background: linear-gradient(135deg, rgba(52, 152, 219, 0.05) 0%, rgba(52, 152, 219, 0.02) 100%);
  border-radius: 12px;
  border: 2px solid rgba(52, 152, 219, 0.15);
  box-shadow: 0 4px 15px rgba(52, 152, 219, 0.08);
}

.filter-section h4 {
  display: flex;
  align-items: center;
  margin: 0 0 20px 0;
  color: #2c3e50;
  font-size: 16px;
  font-weight: 600;
  padding: 8px 12px;
  background: rgba(52, 152, 219, 0.08);
  border-radius: 8px;
  border-left: 4px solid #3498db;
}

.filter-section .el-form-item {
  margin-bottom: 18px;
}

.filter-section .el-form-item:last-child {
  margin-bottom: 0;
}

.filter-section .el-form-item__label {
  color: #2c3e50;
  font-weight: 600;
  font-size: 14px;
  margin-bottom: 8px;
}

.filter-section .el-select {
  width: 100%;
}

.filter-section .el-input__wrapper {
  border-radius: 8px;
  border: 2px solid #e9ecef;
  transition: all 0.3s ease;
}

.filter-section .el-input__wrapper:hover {
  border-color: #3498db;
}

.filter-section .el-input__wrapper.is-focus {
  border-color: #3498db;
  box-shadow: 0 0 0 3px rgba(52, 152, 219, 0.1);
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