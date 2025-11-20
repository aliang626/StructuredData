<template>
  <div class="rule-generate">
    <!-- 页面标题 -->
    <div class="page-header">
      <h2>规则生成</h2>
      <p>基于数据特征自动生成质量检测规则，支持多种规则类型</p>
    </div>

    <el-row :gutter="24">
      <!-- 配置面板 -->
      <el-col :span="8">
        <el-card class="config-panel" shadow="hover">
          <template #header>
            <div class="card-header">
              <div class="header-left">
                <el-icon class="header-icon"><Setting /></el-icon>
                <span class="header-title">生成配置</span>
              </div>
            </div>
          </template>
          
          <!-- 数据库选择器 -->
          <el-form :model="generateForm" label-position="top" class="config-form">
            <el-form-item label="数据源" required>
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
            <el-form-item label="Schema" required v-if="selectedDataSource">
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
            <el-form-item label="数据表" required v-if="selectedSchema">
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
            <el-form-item label="字段选择" required>
              <el-select 
                v-model="generateForm.fields" 
                multiple 
                placeholder="请选择要分析的字段"
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
              <div class="field-help">
                <el-icon><InfoFilled /></el-icon>
                <span>请选择需要生成规则的字段，支持多选</span>
              </div>
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
              
              <!-- 分公司值选择 -->
              <el-form-item v-if="selectedCompanyField" label="分公司值">
                <el-select 
                  v-model="selectedCompanyValue" 
                  placeholder="选择要分析的分公司"
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
                    :label="field.name"
                    :value="field.name"
                  >
                    <div class="option-content">
                      <span class="option-name">{{ field.name }}</span>
                      <span class="option-desc">{{ field.type }} - 油气田字段</span>
                    </div>
                  </el-option>
                </el-select>
              </el-form-item>
              
              <!-- 油气田值选择 -->
              <el-form-item v-if="selectedOilfieldField" label="油气田值">
                <el-select 
                  v-model="selectedOilfieldValue" 
                  placeholder="选择要分析的油气田"
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
                    :label="field.description || field.name"
                    :value="field.name"
                  >
                    <div class="option-content">
                      <span class="option-name">{{ field.description || field.name }}</span>
                      <span class="option-desc">{{ field.type }} | {{ field.name }}</span>
                    </div>
                  </el-option>
                </el-select>
              </el-form-item>
              
              <!-- 井名值选择 -->
              <el-form-item v-if="selectedWellField" label="井名值">
                <el-select 
                  v-model="selectedWellValue" 
                  placeholder="选择要分析的井（可多选）"
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
            
            <!-- 规则类型选择（三大类） -->
            <el-form-item label="规则类型">
              <el-select 
                v-model="generateForm.category" 
                placeholder="选择规则类型"
                style="width: 100%"
                size="large"
              >
                <el-option label="回归型（深度区间）" value="regression" />
                <el-option label="聚簇型" value="cluster" />
                <el-option label="固定范围型" value="manual" />
                <el-option label="字段比较型" value="field_comparison" />
              </el-select>
            </el-form-item>

            <!-- 回归型配置 -->
            <template v-if="generateForm.category === 'regression'">
              <el-form-item label="深度字段" required>
                <el-select v-model="generateForm.regressionDepthField" :disabled="!selectedTable" filterable clearable size="large" style="width: 100%">
                  <el-option 
                    v-for="field in availableFields" 
                    :key="field.name" 
                    :label="`${field.description || field.name} (${field.type})`" 
                    :value="field.name" 
                  />
                </el-select>
              </el-form-item>
              <el-form-item label="深度区间（米）" required>
                <el-input-number v-model="generateForm.depthInterval" :min="1" :max="1000" :step="5" size="large" style="width: 100%" />
              </el-form-item>
            </template>

            <!-- 聚簇型配置 -->
            <template v-if="generateForm.category === 'cluster'">
              <el-form-item label="聚簇方式" required>
                <el-radio-group v-model="generateForm.clusterMode">
                  <el-radio-button label="group_ranges">按分组统计范围</el-radio-button>
                  <el-radio-button label="kmeans">K-means</el-radio-button>
                </el-radio-group>
              </el-form-item>
              <template v-if="generateForm.clusterMode === 'group_ranges'">
                <el-form-item label="分组字段" required>
                  <el-select v-model="generateForm.groupByField" filterable clearable size="large" style="width: 100%">
                    <el-option v-for="field in categoricalFields" :key="field.name" :label="`${field.name} (${field.type})`" :value="field.name" />
                  </el-select>
                </el-form-item>
                <el-alert 
                  title="说明：将使用顶部已选择的字段作为统计特征" 
                  type="info" 
                  :closable="false"
                  show-icon
                  style="margin-bottom: 15px;"
                />
              </template>
              <template v-else>
                <el-form-item label="最大聚类数">
                  <el-input-number v-model="generateForm.maxClusters" :min="2" :max="10" :step="1" size="large" style="width: 100%" />
                </el-form-item>
              </template>
            </template>

            <!-- 固定范围型配置 -->
            <template v-if="generateForm.category === 'manual'">
              <div class="field-help"><el-icon><InfoFilled /></el-icon><span>为已选择字段输入固定上下界（可留空其中一个）。</span></div>
              <div v-for="fname in generateForm.fields" :key="fname" class="manual-range-row">
                <span class="manual-label">{{ fname }}</span>
                <el-input-number v-model="generateForm.manualRanges[fname].lower_bound" :controls="false" placeholder="下界" style="width: 45%" />
                <el-input-number v-model="generateForm.manualRanges[fname].upper_bound" :controls="false" placeholder="上界" style="width: 45%" />
              </div>
            </template>

            <!-- 字段比较型配置 -->
            <template v-if="generateForm.category === 'field_comparison'">
              <div class="field-help">
                <el-icon><InfoFilled /></el-icon>
                <span>字段比较规则配置将在右侧面板中显示</span>
              </div>
              <el-alert 
                title="请在右侧配置字段比较规则" 
                type="info" 
                :closable="false"
                show-icon
                style="margin-bottom: 15px;"
              />
            </template>
            
            <!-- 规则库名称 -->
            <el-form-item label="规则库名称" required>
              <el-input 
                v-model="generateForm.ruleLibraryName" 
                placeholder="输入规则库名称"
                size="large"
              />
            </el-form-item>
            
            <!-- 规则库描述 -->
            <el-form-item label="规则库描述">
              <el-input 
                v-model="generateForm.ruleLibraryDescription" 
                type="textarea" 
                :rows="3"
                placeholder="输入规则库描述"
                size="large"
              />
            </el-form-item>

            <!-- 规则版本：无版本模式已移除 -->
            
            <!-- 生成按钮 -->
            <el-form-item>
              <div class="action-buttons">
                <el-button 
                  type="primary" 
                  @click="generateRules" 
                  :loading="generating"
                  size="large"
                  style="width: 100%"
                >
                  <el-icon><Setting /></el-icon>
                  生成规则
                </el-button>
                <el-button 
                  @click="resetForm" 
                  size="large"
                  style="width: 100%; margin-top: 12px;"
                >
                  <el-icon><Refresh /></el-icon>
                  重置配置
                </el-button>
              </div>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>
      
      <!-- 右侧结果展示 -->
      <el-col :span="16">
        <!-- 字段比较规则配置 -->
        <FieldComparisonRules
          v-if="generateForm.category === 'field_comparison'"
          ref="fieldComparisonRef"
          :available-fields="availableFields"
          @rules-generated="onFieldComparisonRulesGenerated"
          style="margin-bottom: 24px;"
        />
        
        <el-card class="result-panel" shadow="hover">
          <template #header>
            <div class="card-header">
              <div class="header-left">
                <el-icon class="header-icon"><Document /></el-icon>
                <span class="header-title">生成结果</span>
              </div>
              <div class="header-actions" v-if="generatedRules.length > 0">
                <el-button size="small" @click="saveRules">
                  <el-icon><CircleCheck /></el-icon>
                  保存规则
                </el-button>
                <el-button size="small" @click="exportRules">
                  <el-icon><Download /></el-icon>
                  导出规则
                </el-button>
              </div>
            </div>
          </template>
          
          <div class="result-content">
            <!-- 生成进度 -->
            <div v-if="generating" class="generating-status">
              <div class="status-content">
                <el-icon class="status-icon"><Loading /></el-icon>
                <h3>正在生成规则...</h3>
                <p>请稍候，系统正在分析数据特征并生成相应的质量检测规则</p>
                <el-progress :percentage="generateProgress" :show-text="false" />
                <span class="progress-text">{{ generateProgress }}%</span>
              </div>
            </div>
            
            <!-- 生成结果 -->
            <div v-else-if="generatedRules.length > 0" class="rules-result">
              <div class="result-summary">
                <div class="summary-item">
                  <div class="summary-icon">
                    <el-icon><Document /></el-icon>
                  </div>
                  <div class="summary-content">
                    <span class="summary-label">生成规则</span>
                    <span class="summary-value">{{ generatedRules.length }} 条</span>
                  </div>
                </div>
                <div class="summary-item">
                  <div class="summary-icon">
                    <el-icon><Setting /></el-icon>
                  </div>
                  <div class="summary-content">
                    <span class="summary-label">涉及字段</span>
                    <span class="summary-value">{{ uniqueFields.length }} 个</span>
                  </div>
                </div>
                <div class="summary-item">
                  <div class="summary-icon">
                    <el-icon><Clock /></el-icon>
                  </div>
                  <div class="summary-content">
                    <span class="summary-label">生成时间</span>
                    <span class="summary-value">{{ generateTime }}s</span>
                  </div>
                </div>
              </div>
              
              <div class="rules-list">
                <div class="list-header">
                  <h4>规则详情</h4>
                  <el-tag type="info" size="small">{{ generatedRules.length }} 条规则</el-tag>
                </div>
                
                <div class="rules-grid">
                  <div 
                    v-for="(rule, idx) in generatedRules" 
                    :key="idx"
                    class="rule-item"
                    :class="rule.rule_type"
                  >
                    <div class="rule-header">
                      <div class="rule-info">
                        <span class="rule-name">{{ rule.name }}</span>
                        <span class="rule-field">{{ rule.field }}</span>
                      </div>
                      <el-tag :type="getRuleTypeTag(rule.rule_type)" size="small">
                        {{ getRuleTypeName(rule.rule_type) }}
                      </el-tag>
                    </div>
                    
                    <div class="rule-content">
                      <p class="rule-description">{{ rule.description }}</p>
                      <div class="rule-params">
                        <span class="param-label">参数:</span>
                        <span class="param-value">{{ formatParams(rule.params) }}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
            <!-- 空状态 -->
            <div v-else class="empty-result">
              <el-icon class="empty-icon"><Document /></el-icon>
              <p>暂无生成结果</p>
              <span>请配置生成参数并开始生成规则</span>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { 
  Download, Tools, DocumentAdd, CircleCheck, 
  Search, InfoFilled, Setting, Refresh, Clock, Document, Loading, Location
} from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import axios from 'axios'
import FieldComparisonRules from '../components/FieldComparisonRules.vue'

export default {
  name: 'RuleGenerate',
  components: {
    Download,
    Tools,
    DocumentAdd,
    CircleCheck,
    Search,
    InfoFilled,
    Setting,
    Refresh,
    Clock,
    Document,
    Loading,
    Location,
    FieldComparisonRules
  },
  setup() {
    const generating = ref(false)
    const activeAdvancedPanels = ref([])
    
    // 字段比较组件引用
    const fieldComparisonRef = ref(null)
    
    // 保存相关
    const saveDialogVisible = ref(false)
    const saving = ref(false)
    const ruleLibraries = ref([])
    const librariesLoading = ref(false)
    
    // 创建规则库相关
    const createLibraryDialogVisible = ref(false)
    const creatingLibrary = ref(false)
    
    // 数据源相关
    const dataSources = ref([])
    const selectedDataSource = ref('')
    const schemas = ref([])
    const selectedSchema = ref('')
    const loadingSchemas = ref(false)
    const availableTables = ref([])
    const selectedTable = ref('')
    const availableFields = ref([])
    const generatedRules = ref([])
    
    // 分公司筛选相关
    const selectedCompanyField = ref('')
    const selectedCompanyValue = ref('')
    const companyValues = ref([])
    const companyValueLoading = ref(false)
    
    // 油气田筛选相关
    const selectedOilfieldField = ref('')
    const selectedOilfieldValue = ref('')
    const oilfieldValues = ref([])
    const oilfieldValueLoading = ref(false)
    
    // 井名筛选相关
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
    
    const generateForm = reactive({
      // 通用
      fields: [],
      category: 'regression',
      ruleType: 'range',
      ruleLibraryName: '',
      ruleLibraryDescription: '',

      // 回归型
      regressionDepthField: '',
      depthInterval: 50,

      // 聚簇型
      clusterMode: 'group_ranges', // group_ranges | kmeans
      groupByField: '',
      maxClusters: 5,
      dbscanEps: 0.5,
      dbscanMinSamples: 5,

      // 固定范围型
      manualRanges: {}
    })
    
    const saveForm = reactive({
      libraryId: '',
      version: '',
      createdBy: '',
      description: ''
    })
    
    const createLibraryForm = reactive({
      name: '',
      description: '',
      forceReplace: false
    })


    
    const canGenerate = computed(() => {
      if (!selectedDataSource.value || !selectedTable.value || generateForm.fields.length === 0) return false
      if (generateForm.category === 'regression') {
        return !!generateForm.regressionDepthField && generateForm.depthInterval > 0
      }
      if (generateForm.category === 'cluster') {
        if (generateForm.clusterMode === 'group_ranges') {
          // 只需要分组字段，统计特征字段自动使用顶部选择的 fields
          return !!generateForm.groupByField
        }
        return generateForm.maxClusters >= 2
      }
      if (generateForm.category === 'manual') {
        // 初始化 manualRanges 的缺省
        generateForm.fields.forEach((f) => {
          if (!generateForm.manualRanges[f]) {
            generateForm.manualRanges[f] = { lower_bound: null, upper_bound: null }
          }
        })
        return true
      }
      return false
    })

    const numericFields = computed(() => {
      return availableFields.value.filter(field => 
        ['int', 'float', 'double', 'decimal', 'numeric'].includes(field.type.toLowerCase())
      )
    })
    
    // 分类型字段计算属性（用于分组字段选择）
    const categoricalFields = computed(() => {
      return availableFields.value.filter(field => {
        const type = field.type.toLowerCase()
        // 排除数值型字段，只保留字符串、文本等分类型字段
        return !['int', 'float', 'double', 'decimal', 'numeric', 'bigint', 'smallint'].includes(type)
      })
    })

    const uniqueFields = computed(() => {
      const unique = new Set();
      generatedRules.value.forEach(rule => {
        if (rule.field) {
          unique.add(rule.field);
        }
      });
      return Array.from(unique);
    });

    const generateProgress = computed(() => {
      return generating.value ? 0 : 100; // 生成完成时显示100%
    });

    const generateTime = computed(() => {
      // 模拟生成时间，实际应从后端获取
      return 5; 
    });
    
    // 分公司字段计算属性
    const companyFields = computed(() => {
      // 只匹配明确的公司字段，缩小范围避免误匹配
      const companyKeywords = ['公司', 'company', 'branch']
      return availableFields.value.filter(field => {
        const fieldName = field.name.toLowerCase()
        return companyKeywords.some(keyword => fieldName.includes(keyword.toLowerCase()))
      })
    })
    
    // 油气田字段计算属性（基于字段描述）
    const oilfieldFields = computed(() => {
      const oilfieldKeywords = ['油田', '气田', '油气田', '区块', '工区', '油区', '气区', 'oilfield', 'gasfield', 'field', 'block', 'area']
      return availableFields.value.filter(field => {
        // 优先使用字段描述，如果没有描述则使用字段名
        const searchText = (field.description || field.name).toLowerCase()
        return oilfieldKeywords.some(keyword => searchText.includes(keyword.toLowerCase()))
      })
    })
    
    // 井名字段计算属性（基于字段描述）
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
        (field.description && field.description.toLowerCase().includes(query.toLowerCase())) ||
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
            generateForm.fields = [] // 默认不选择任何字段，让用户自己选择
            generateForm.manualRanges = {}
            
            // 重置所有筛选选择
            selectedCompanyField.value = ''
            selectedCompanyValue.value = ''
            companyValues.value = []
            selectedOilfieldField.value = ''
            selectedOilfieldValue.value = ''
            oilfieldValues.value = []
            selectedWellField.value = ''
            selectedWellValue.value = []
            wellValues.value = []
          }
        }
      } catch (error) {
        console.error('加载字段失败:', error)
        ElMessage.error('加载字段失败')
      } finally {
        fieldLoading.value = false
      }
    }
    
    // 分公司字段变化处理
    const onCompanyFieldChange = async () => {
      if (!selectedCompanyField.value) {
        selectedCompanyValue.value = ''
        companyValues.value = []
        return
      }
      
      companyValueLoading.value = true
      try {
        const sourceId = selectedDataSource.value
        const response = await axios.get('/api/database/field-values', {
          params: {
            source_id: sourceId,
            schema: selectedSchema.value,
            table_name: selectedTable.value,
            field_name: selectedCompanyField.value
          }
        })
        if (response.data.success) {
          companyValues.value = response.data.data
          selectedCompanyValue.value = ''
        }
      } catch (error) {
        console.error('加载分公司值失败:', error)
        ElMessage.error('加载分公司值失败')
      } finally {
        companyValueLoading.value = false
      }
    }
    
    // 油气田字段变化处理
    const onOilfieldFieldChange = async () => {
      if (!selectedOilfieldField.value) {
        selectedOilfieldValue.value = ''
        oilfieldValues.value = []
        return
      }
      
      oilfieldValueLoading.value = true
      try {
        const sourceId = selectedDataSource.value
        const response = await axios.get('/api/database/field-values', {
          params: {
            source_id: sourceId,
            schema: selectedSchema.value,
            table_name: selectedTable.value,
            field_name: selectedOilfieldField.value
          }
        })
        if (response.data.success) {
          oilfieldValues.value = response.data.data
          selectedOilfieldValue.value = ''
        }
      } catch (error) {
        console.error('加载油气田值失败:', error)
        ElMessage.error('加载油气田值失败')
      } finally {
        oilfieldValueLoading.value = false
      }
    }
    
    // 井名字段变化处理
    const onWellFieldChange = async () => {
      if (!selectedWellField.value) {
        selectedWellValue.value = []
        wellValues.value = []
        return
      }
      
      wellValueLoading.value = true
      try {
        const sourceId = selectedDataSource.value
        const response = await axios.get('/api/database/field-values', {
          params: {
            source_id: sourceId,
            schema: selectedSchema.value,
            table_name: selectedTable.value,
            field_name: selectedWellField.value
          }
        })
        if (response.data.success) {
          wellValues.value = response.data.data
          selectedWellValue.value = []
        }
      } catch (error) {
        console.error('加载井名值失败:', error)
        ElMessage.error('加载井名值失败')
      } finally {
        wellValueLoading.value = false
      }
    }
    

    



    
    // 处理字段比较规则生成
    const onFieldComparisonRulesGenerated = (rules) => {
      console.log('接收到字段比较规则:', rules)
      generatedRules.value = rules
      ElMessage.success(`成功接收 ${rules.length} 条字段比较规则`)
    }

    const generateRules = async () => {
      if (!canGenerate.value) {
        ElMessage.warning('请完善配置信息')
        return
      }
      
      generating.value = true
      
      try {
        // 构建请求参数
        const sourceId = selectedDataSource.value
        const tableName = selectedTable.value
        
        const dbConfigResponse = await axios.get(`/api/database/sources/${sourceId}`)
        if (!dbConfigResponse.data.success) {
          throw new Error('获取数据库配置失败')
        }
        
        const requestData = {
          db_config: dbConfigResponse.data.data,
          schema: selectedSchema.value,  // 添加schema参数
          table_name: tableName,
          fields: generateForm.fields,
          rule_library_name: generateForm.ruleLibraryName,
          rule_library_description: generateForm.ruleLibraryDescription
        }
        
        // 添加筛选参数
        const filters = {}
        if (selectedCompanyField.value && selectedCompanyValue.value) {
          filters.company_filter = {
            field: selectedCompanyField.value,
            value: selectedCompanyValue.value
          }
        }
        if (selectedOilfieldField.value && selectedOilfieldValue.value) {
          filters.oilfield_filter = {
            field: selectedOilfieldField.value,
            value: selectedOilfieldValue.value
          }
        }
        if (selectedWellField.value && selectedWellValue.value && selectedWellValue.value.length > 0) {
          filters.well_filter = {
            field: selectedWellField.value,
            value: selectedWellValue.value
          }
        }
        
        // 兼容原有的branch_filter参数
        if (filters.company_filter) {
          requestData.branch_filter = filters.company_filter
        }
        
        // 添加新的筛选参数
        if (Object.keys(filters).length > 0) {
          requestData.filters = filters
        }

        // 根据三大类填充具体参数与后端 rule_type
        if (generateForm.category === 'regression') {
          requestData.rule_type = 'depth_interval'
          requestData.depth_field = generateForm.regressionDepthField
          requestData.depth_interval = generateForm.depthInterval
        } else if (generateForm.category === 'cluster') {
          if (generateForm.clusterMode === 'group_ranges') {
            requestData.rule_type = 'cluster_group_ranges'
            requestData.group_by_field = generateForm.groupByField
            // 不传 cluster_features，后端将自动使用 fields（排除分组字段）
          } else {
            requestData.rule_type = 'cluster_kmeans'
            requestData.max_clusters = generateForm.maxClusters
          }
        } else if (generateForm.category === 'manual') {
          requestData.rule_type = 'manual_range'
          requestData.manual_ranges = generateForm.manualRanges
        }
        
        // 调用统计分析API
        const response = await axios.post('/api/rules/generate-statistical', requestData)
        
        if (response.data.success) {
          generatedRules.value = response.data.data.rules
          ElMessage.success(`成功生成 ${response.data.data.rules.length} 条规则`)
        } else {
          throw new Error(response.data.error || '规则生成失败')
        }
      } catch (error) {
        ElMessage.error(`规则生成失败: ${error.message}`)
      } finally {
        generating.value = false
      }
    }

    const resetForm = () => {
      generateForm.fields = [];
      generateForm.ruleType = 'range';
      generateForm.ruleLibraryName = '';
      generateForm.ruleLibraryDescription = '';
      
      // 重置所有筛选选择
      selectedCompanyField.value = '';
      selectedCompanyValue.value = '';
      companyValues.value = [];
      selectedOilfieldField.value = '';
      selectedOilfieldValue.value = '';
      oilfieldValues.value = [];
      selectedWellField.value = '';
      selectedWellValue.value = [];
      wellValues.value = [];
      
      ElMessage.success('配置已重置');
    };

    const saveRules = async () => {
      if (generatedRules.value.length === 0) {
        ElMessage.warning('没有可保存的规则')
        return
      }
      
      // 加载规则库列表
      await loadRuleLibraries()
      // 若左侧填写了规则库名称且不存在同名库，则自动创建
      const desiredName = (generateForm.ruleLibraryName || '').trim()
      if (desiredName) {
        const exists = ruleLibraries.value.find((lib) => lib.name === desiredName)
        if (!exists) {
          try {
            const resp = await axios.post('/api/rules/libraries', {
              name: desiredName,
              description: (generateForm.ruleLibraryDescription || '').trim(),
            })
            if (resp.data?.success) {
              await loadRuleLibraries()
            }
          } catch (e) {
            console.error('自动创建规则库失败:', e)
          }
        }
      }
      
      // 设置默认值（无版本模式下，version 字段不再显示，仅用于兼容后端）
      saveForm.version = 'current'
      saveForm.createdBy = '用户'
      saveForm.description = `包含${generatedRules.value.length}条规则的当前规则`
      
      // 默认选择：优先刚创建/同名库，否则第一个
      const preferred = desiredName
        ? ruleLibraries.value.find((lib) => lib.name === desiredName)
        : null
      if (preferred) {
        saveForm.libraryId = preferred.id
      } else if (ruleLibraries.value.length > 0) {
        saveForm.libraryId = ruleLibraries.value[0].id
      }
      
      // 直接调用保存确认，跳过对话框
      await confirmSave()
    }
    
    const loadRuleLibraries = async () => {
      librariesLoading.value = true
      try {
        console.log('Loading rule libraries...')
        const response = await axios.get('/api/rules/libraries')
        console.log('Rule libraries response:', response.data)
        if (response.data.success) {
          ruleLibraries.value = response.data.data
          console.log('Loaded libraries:', ruleLibraries.value)
        } else {
          console.error('API returned error:', response.data.error)
        }
      } catch (error) {
        console.error('加载规则库失败:', error)
        ElMessage.error('加载规则库失败')
      } finally {
        librariesLoading.value = false
      }
    }
    
    const confirmSave = async () => {
      if (!saveForm.libraryId) {
        ElMessage.warning('请选择规则库')
        return
      }
      if (!saveForm.version) {
        ElMessage.warning('请输入版本号')
        return
      }
      
      saving.value = true
      try {
        // 无版本模式：调用新接口直接保存当前规则
        let response
        if (generateForm.ruleLibraryName && generateForm.ruleLibraryName.trim()) {
          response = await axios.post('/api/rules/libraries/save-by-name', {
            name: generateForm.ruleLibraryName.trim(),
            description: (generateForm.ruleLibraryDescription || '').trim(),
            rules: generatedRules.value,
            created_by: saveForm.createdBy
          })
          if (response.data?.success) {
            // 同步选择到真实库ID，便于后续再次保存
            const lib = response.data.data.library
            saveForm.libraryId = lib.id
          }
        } else {
          response = await axios.post(`/api/rules/libraries/${saveForm.libraryId}/rules`, {
            rules: generatedRules.value,
            created_by: saveForm.createdBy,
            description: saveForm.description
          })
        }
        
        if (response.data.success) {
          ElMessage.success('规则保存成功')
          saveDialogVisible.value = false
          // 重置表单
          saveForm.libraryId = ''
          saveForm.version = ''
          saveForm.createdBy = ''
          saveForm.description = ''
        }
      } catch (error) {
        console.error('保存规则失败:', error)
        ElMessage.error(error.response?.data?.error || '规则保存失败')
      } finally {
        saving.value = false
      }
    }
    
    const confirmCreateLibrary = async () => {
      if (!createLibraryForm.name.trim()) {
        ElMessage.warning('请输入规则库名称')
        return
      }
      
      // 如果勾选了强制替换，显示确认对话框
      if (createLibraryForm.forceReplace) {
        try {
          await ElMessageBox.confirm(
            `确定要删除所有名为 "${createLibraryForm.name}" 的规则库记录并创建新的吗？此操作不可恢复！`,
            '确认强制替换',
            {
              confirmButtonText: '确定',
              cancelButtonText: '取消',
              type: 'warning'
            }
          )
        } catch {
          return // 用户取消
        }
      }
      
      creatingLibrary.value = true
      try {
        const response = await axios.post('/api/rules/libraries', {
          name: createLibraryForm.name.trim(),
          description: createLibraryForm.description.trim(),
          force_replace: createLibraryForm.forceReplace
        })
        
        if (response.data.success) {
          ElMessage.success(createLibraryForm.forceReplace ? '规则库强制替换成功' : '规则库创建成功')
          createLibraryDialogVisible.value = false
          // 重置表单
          createLibraryForm.name = ''
          createLibraryForm.description = ''
          createLibraryForm.forceReplace = false
          // 重新加载规则库列表
          await loadRuleLibraries()
          // 自动选择新创建的规则库
          if (ruleLibraries.value.length > 0) {
            saveForm.libraryId = ruleLibraries.value[ruleLibraries.value.length - 1].id
          }
        }
      } catch (error) {
        console.error('创建规则库失败:', error)
        ElMessage.error(error.response?.data?.error || '创建规则库失败')
      } finally {
        creatingLibrary.value = false
      }
    }
    


    const getFieldTypeColor = (type) => {
      const colors = {
        'int': 'primary',
        'float': 'primary',
        'double': 'primary',
        'decimal': 'primary',
        'numeric': 'primary',
        'varchar': 'success',
        'text': 'success',
        'char': 'success',
        'datetime': 'warning',
        'date': 'warning',
        'timestamp': 'warning'
      }
      return colors[type.toLowerCase()] || 'info'
    }
    
    const getRuleTypeColor = (type) => {
      const colors = {
        range: 'primary',
        range_2sigma: 'primary',
        range_percentile: 'primary',
        outlier: 'danger',
        outlier_3sigma: 'danger',
        outlier_iqr: 'danger',
        outlier_zscore: 'danger',
        cluster_kmeans: 'warning',
        cluster_dbscan: 'warning',
        cluster_group_ranges: 'warning',
        manual_range: 'primary',
        distribution_check: 'success',
        frequency_analysis: 'success'
      }
      return colors[type] || 'info'
    }
    
    const getRuleTypeText = (type) => {
      const texts = {
        range: '范围检查',
        range_2sigma: '2σ范围检查',
        range_percentile: '分位数范围检查',
        outlier: '异常值检测',
        outlier_3sigma: '3σ异常值检测',
        outlier_iqr: 'IQR异常值检测',
        outlier_zscore: 'Z-score异常值检测',
        cluster_kmeans: 'K-means聚类',
        cluster_dbscan: 'DBSCAN聚类',
        cluster_group_ranges: '按分组范围',
        manual_range: '固定范围',
        distribution_check: '分布检验',
        frequency_analysis: '频率分析'
      }
      return texts[type] || type
    }

    const getRuleTypeTag = (type) => {
      const colors = {
        range: 'primary',
        range_2sigma: 'primary',
        range_percentile: 'primary',
        outlier: 'danger',
        outlier_3sigma: 'danger',
        outlier_iqr: 'danger',
        outlier_zscore: 'danger',
        cluster_kmeans: 'warning',
        cluster_dbscan: 'warning',
        cluster_group_ranges: 'warning',
        manual_range: 'primary',
        distribution_check: 'success',
        frequency_analysis: 'success'
      }
      return colors[type] || 'info';
    }

    const getRuleTypeName = (type) => {
      const texts = {
        range: '范围规则',
        range_2sigma: '2σ范围规则',
        range_percentile: '分位数范围规则',
        outlier: '异常值规则',
        outlier_3sigma: '3σ异常值规则',
        outlier_iqr: 'IQR异常值规则',
        outlier_zscore: 'Z-score异常值规则',
        cluster_kmeans: 'K-means聚类',
        cluster_dbscan: 'DBSCAN聚类',
        cluster_group_ranges: '分组范围规则',
        manual_range: '固定范围规则',
        distribution_check: '分布检验',
        frequency_analysis: '频率分析'
      }
      return texts[type] || type;
    }

    const formatParams = (params) => {
      try {
        if (!params) return '-'
        // 展示关键信息
        if (params.lower_bound !== undefined || params.upper_bound !== undefined) {
          return `范围: ${params.lower_bound ?? '-'} ~ ${params.upper_bound ?? '-'}`
        }
        if (params.intervals) {
          return `区间数: ${params.intervals.length}`
        }
        if (params.ranges && params.regex_pattern) {
          return params.regex_pattern
        }
        return JSON.stringify(params)
      } catch {
        return '-'
      }
    }






    

    
    onMounted(() => {
      loadDataSources()
    })

    // 同步手工范围表单项
    watch(() => generateForm.fields.slice(), (fields) => {
      // 添加新字段的默认项
      fields.forEach((f) => {
        if (!generateForm.manualRanges[f]) {
          generateForm.manualRanges[f] = { lower_bound: null, upper_bound: null }
        }
      })
      // 移除已删除的字段项
      Object.keys(generateForm.manualRanges).forEach((k) => {
        if (!fields.includes(k)) delete generateForm.manualRanges[k]
      })
    })
    
    return {
      generating,
      activeAdvancedPanels,
      // 字段比较相关
      fieldComparisonRef,
      onFieldComparisonRulesGenerated,
      // 数据源相关
      dataSources,
      selectedDataSource,
      schemas,
      selectedSchema,
      loadingSchemas,
      availableTables,
      selectedTable,
      availableFields,
      generatedRules,
      generateForm,
      canGenerate,
      numericFields,
      categoricalFields,
      uniqueFields,
      generateProgress,
      generateTime,
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
      loadSchemas,
      loadTables,
      
      // 保存相关
      saveDialogVisible,
      saving,
      ruleLibraries,
      librariesLoading,
      saveForm,
      
      // 创建规则库相关
      createLibraryDialogVisible,
      creatingLibrary,
      createLibraryForm,
      
      onDataSourceChange,
      onTableChange,
      onCompanyFieldChange,
      generateRules,
      saveRules,
      confirmSave,
      confirmCreateLibrary,
      getFieldTypeColor,
      getRuleTypeColor,
      getRuleTypeText,
      getRuleTypeTag,
      getRuleTypeName,
      resetForm,
      formatParams,
      exportRules: () => {
        if (generatedRules.value.length === 0) {
          ElMessage.warning('暂无规则可导出，请先生成规则');
          return;
        }
        
        try {
          // 构建导出数据
          const exportData = {
            exportTime: new Date().toLocaleString('zh-CN'),
            dataSource: dataSources.value.find(s => s.id === selectedDataSource.value)?.name || '未知',
            schema: selectedSchema.value,
            tableName: selectedTable.value,
            ruleType: generateForm.category,
            totalRules: generatedRules.value.length,
            rules: generatedRules.value.map(rule => ({
              name: rule.name,
              description: rule.description,
              ruleType: rule.rule_type,
              field: rule.field,
              params: rule.params,
              validationSql: rule.validation_sql,
              regexPattern: rule.regex_pattern
            }))
          };
          
          // 转换为JSON字符串（格式化）
          const jsonStr = JSON.stringify(exportData, null, 2);
          
          // 创建Blob
          const blob = new Blob([jsonStr], { type: 'application/json;charset=utf-8' });
          const url = URL.createObjectURL(blob);
          
          // 创建下载链接
          const link = document.createElement('a');
          link.href = url;
          
          // 生成文件名
          const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5);
          const fileName = `规则导出_${selectedTable.value}_${generateForm.category}_${timestamp}.json`;
          link.download = fileName;
          
          // 触发下载
          document.body.appendChild(link);
          link.click();
          document.body.removeChild(link);
          URL.revokeObjectURL(url);
          
          ElMessage.success(`成功导出 ${generatedRules.value.length} 条规则`);
        } catch (error) {
          console.error('导出规则失败:', error);
          ElMessage.error('导出规则失败，请重试');
        }
      },
      
      // 分公司筛选相关
      selectedCompanyField,
      selectedCompanyValue,
      companyFields,
      companyValues,
      companyValueLoading,
      
      // 油气田筛选相关
      selectedOilfieldField,
      selectedOilfieldValue,
      oilfieldFields,
      oilfieldValues,
      oilfieldValueLoading,
      onOilfieldFieldChange,
      
      // 井名筛选相关
      selectedWellField,
      selectedWellValue,
      wellFields,
      wellValues,
      wellValueLoading,
      onWellFieldChange
    }
  }
}
</script>

<style scoped>
.rule-generate {
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

.config-panel,
.result-panel {
  background: rgba(255, 255, 255, 0.95);
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  margin-bottom: 24px;
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

.header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.config-form {
  padding: 10px 0;
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

.field-help {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 8px;
  padding: 8px 12px;
  background: rgba(52, 152, 219, 0.05);
  border-radius: 6px;
  border-left: 3px solid #3498db;
  font-size: 12px;
  color: #7f8c8d;
}

.action-buttons {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 20px;
}

.action-buttons .el-button {
  border-radius: 8px;
  font-weight: 600;
  transition: all 0.3s ease;
}

.action-buttons .el-button--primary {
  background: linear-gradient(135deg, #3498db, #2980b9);
  border: none;
}

.action-buttons .el-button--primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(52, 152, 219, 0.3);
}

.result-content {
  padding: 10px 0;
}

.generating-status {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  border-radius: 12px;
  border: 2px solid #e9ecef;
  text-align: center;
}

.status-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.status-icon {
  font-size: 80px;
  color: #3498db;
  background: rgba(52, 152, 219, 0.1);
  border-radius: 50%;
  padding: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.status-content h3 {
  font-size: 24px;
  color: #2c3e50;
  margin: 0;
  font-weight: 600;
}

.status-content p {
  font-size: 16px;
  color: #7f8c8d;
  margin: 0;
  max-width: 400px;
  line-height: 1.6;
}

.progress-text {
  font-size: 16px;
  color: #3498db;
  font-weight: 600;
}

.rules-result {
  margin-top: 20px;
}

.result-summary {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  border-radius: 12px;
  padding: 24px;
  border: 2px solid #e9ecef;
  margin-bottom: 24px;
}

.summary-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  background: rgba(255, 255, 255, 0.9);
  border-radius: 10px;
  border: 2px solid #e9ecef;
  transition: all 0.3s ease;
}

.summary-item:hover {
  background: rgba(255, 255, 255, 1);
  border-color: #3498db;
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(52, 152, 219, 0.15);
}

.summary-icon {
  font-size: 32px;
  color: #3498db;
  background: rgba(52, 152, 219, 0.1);
  border-radius: 12px;
  padding: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.summary-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.summary-label {
  font-size: 14px;
  color: #7f8c8d;
  font-weight: 500;
}

.summary-value {
  font-size: 28px;
  font-weight: 700;
  color: #2c3e50;
}

.rules-list {
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  border-radius: 12px;
  padding: 24px;
  border: 2px solid #e9ecef;
}

.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 12px;
  border-bottom: 2px solid #e9ecef;
}

.list-header h4 {
  font-size: 18px;
  color: #2c3e50;
  margin: 0;
  font-weight: 600;
}

.rules-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 20px;
}

.rule-item {
  background: rgba(255, 255, 255, 0.9);
  border: 2px solid #e9ecef;
  border-radius: 12px;
  padding: 20px;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.rule-item::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  bottom: 0;
  width: 4px;
  background: #3498db;
  transition: all 0.3s ease;
}

.rule-item:hover {
  background: rgba(255, 255, 255, 1);
  border-color: #3498db;
  transform: translateX(4px);
  box-shadow: 0 8px 25px rgba(52, 152, 219, 0.15);
}

.rule-item:hover::before {
  transform: scaleY(1);
}

.rule-item.range::before {
  background: #3498db;
}

.rule-item.outlier::before {
  background: #e74c3c;
}

.rule-item.cluster::before {
  background: #f39c12;
}

.rule-item.distribution::before {
  background: #27ae60;
}

.rule-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.rule-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.rule-name {
  font-size: 16px;
  font-weight: 600;
  color: #2c3e50;
}

.rule-field {
  font-size: 14px;
  color: #7f8c8d;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
}

.rule-content {
  font-size: 14px;
  color: #606266;
  line-height: 1.6;
}

.rule-description {
  margin-bottom: 12px;
  color: #7f8c8d;
  font-style: italic;
  padding: 8px 12px;
  background: rgba(52, 152, 219, 0.05);
  border-radius: 6px;
  border-left: 3px solid #3498db;
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
  padding-bottom: 8px;
  border-bottom: 2px solid rgba(52, 152, 219, 0.1);
}

.filter-section h4 .el-icon {
  margin-right: 8px;
  color: #3498db;
  font-size: 18px;
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
}

.filter-section .el-select {
  width: 100%;
}

.filter-section .el-input__wrapper,
.filter-section .el-select .el-input__wrapper {
  border-radius: 8px;
  border: 2px solid #e9ecef;
  transition: all 0.3s ease;
}

.filter-section .el-input__wrapper:hover,
.filter-section .el-select .el-input__wrapper:hover {
  border-color: #3498db;
}

.filter-section .el-input__wrapper.is-focus,
.filter-section .el-select .el-input__wrapper.is-focus {
  border-color: #3498db;
  box-shadow: 0 0 0 3px rgba(52, 152, 219, 0.1);
}

.rule-params {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #7f8c8d;
  padding: 8px 0;
  background: rgba(52, 152, 219, 0.05);
  border-radius: 6px;
}

.param-label {
  font-weight: 600;
  color: #34495e;
}

.param-value {
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
}

.empty-result {
  text-align: center;
  padding: 60px 20px;
  color: #95a5a6;
}

.empty-icon {
  font-size: 80px;
  margin-bottom: 20px;
  color: #bdc3c7;
  opacity: 0.6;
}

.empty-result p {
  margin-bottom: 8px;
  font-size: 18px;
  font-weight: 600;
  color: #2c3e50;
}

.empty-result span {
  font-size: 14px;
  color: #7f8c8d;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .result-summary {
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  }
  
  .rules-grid {
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  }
}

@media (max-width: 768px) {
  .rule-generate {
    padding: 15px;
  }
  
  .page-header h2 {
    font-size: 24px;
  }
  
  .result-summary {
    grid-template-columns: 1fr;
  }
  
  .summary-item {
    flex-direction: column;
    text-align: center;
    gap: 12px;
  }
  
  .rules-grid {
    grid-template-columns: 1fr;
  }
  
  .rule-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
}
</style>