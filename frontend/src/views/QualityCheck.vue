<template>
  <div class="quality-check">
    <!-- 页面标题 -->
    <div class="page-header">
      <h2>质量检测</h2>
      <p>基于规则库对数据进行质量检测和分析</p>
    </div>

    <el-row :gutter="24">
      <!-- 左侧配置面板 -->
      <el-col :span="8">
        <el-card class="config-panel" shadow="hover">
          <template #header>
            <div class="card-header">
              <div class="header-left">
                <el-icon class="header-icon"><Setting /></el-icon>
                <span class="header-title">检测配置</span>
              </div>
            </div>
          </template>
          
          <!-- 规则库版本选择 -->
          <el-form :model="qualityForm" label-position="top" class="config-form">
            <el-form-item label="规则库" required>
              <el-select 
                v-model="qualityForm.ruleLibrary" 
                placeholder="选择规则库"
                @change="loadRuleVersions"
                style="width: 100%"
                size="large"
                value-key="id"
              >
                <el-option
                  v-for="library in availableRuleLibraries"
                  :key="library.id"
                  :label="library.name"
                  :value="library"
                />
              </el-select>
              <div class="field-help" v-if="availableRuleLibraries.length === 0" style="margin-top:8px;color:#909399;font-size:12px;">
                暂无包含版本的规则库，请先在“规则生成”页面保存规则为某个规则库版本。
              </div>
            </el-form-item>
            
            <!-- 无版本模式：移除显式的版本选择 -->
            
            <el-form-item label="数据源" required>
              <el-select 
                v-model="selectedDataSource" 
                placeholder="选择数据源"
                @change="onDataSourceChange"
                style="width: 100%"
                size="large"
              >
                <el-option
                  v-for="source in dataSources"
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
            
            <el-form-item label="数据表" required>
              <el-select 
                v-model="qualityForm.tableName" 
                placeholder="选择数据表"
                style="width: 100%"
                size="large"
                filterable
                remote
                :remote-method="filterTablesRemote"
                :loading="tableLoading"
              >
                <el-option
                  v-for="table in filteredTables"
                  :key="table"
                  :label="table"
                  :value="table"
                />
              </el-select>
            </el-form-item>

            <el-form-item label="字段（可多选）">
              <el-select
                v-model="qualityForm.fields"
                multiple
                collapse-tags
                placeholder="选择需要检测的字段（留空表示全表）"
                style="width: 100%"
                size="large"
                filterable
                :disabled="!qualityForm.tableName"
              >
                <el-option
                  v-for="field in availableFields"
                  :key="field.name"
                  :label="`${field.name} (${field.field_type})`"
                  :value="field.name"
                />
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
                  :disabled="!qualityForm.tableName"
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
                      <span class="option-desc">{{ field.field_type }}</span>
                    </div>
                  </el-option>
                </el-select>
              </el-form-item>
              
              <!-- 分公司值选择 -->
              <el-form-item v-if="selectedCompanyField" label="分公司值">
                <el-select 
                  v-model="selectedCompanyValue" 
                  placeholder="选择分公司值"
                  filterable
                  clearable
                  :loading="companyValueLoading"
                  size="large"
                  style="width: 100%"
                >
                  <el-option
                    v-for="value in companyValues"
                    :key="value"
                    :label="value"
                    :value="value"
                  >
                    <div class="option-name">{{ value }}</div>
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
                  :disabled="!qualityForm.tableName"
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
                      <span class="option-desc">{{ field.field_type }} - 油气田字段</span>
                    </div>
                  </el-option>
                </el-select>
              </el-form-item>
              
              <!-- 油气田值选择 -->
              <el-form-item v-if="selectedOilfieldField" label="油气田值">
                <el-select 
                  v-model="selectedOilfieldValue" 
                  placeholder="选择要检测的油气田"
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
                    <div class="option-name">{{ oilfield }}</div>
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
                  :disabled="!qualityForm.tableName"
                  size="large"
                  style="width: 100%"
                  @change="onWellFieldChange"
                >
                  <el-option
                    v-for="field in wellFields"
                    :key="field.name"
                    :label="field.name"
                    :value="field.name"
                  >
                    <div class="option-content">
                      <span class="option-name">{{ field.name }}</span>
                      <span class="option-desc">{{ field.field_type }} - 井名字段</span>
                    </div>
                  </el-option>
                </el-select>
              </el-form-item>
              
              <!-- 井名值选择 -->
              <el-form-item v-if="selectedWellField" label="井名值">
                <el-select 
                  v-model="selectedWellValue" 
                  placeholder="选择要检测的井（可多选）"
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
                    <div class="option-name">{{ well }}</div>
                  </el-option>
                </el-select>
              </el-form-item>
            </div>

            <!-- 数据上传区域 -->
            <el-form-item label="数据上传">
              <el-upload
                class="upload-demo"
                drag
                action="#"
                :auto-upload="false"
                :on-change="handleFileChange"
                :file-list="fileList"
                accept=".csv,.xlsx,.xls"
              >
                <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
                <div class="el-upload__text">
                  将文件拖到此处，或<em>点击上传</em>
                </div>
                <template #tip>
                  <div class="el-upload__tip">
                    支持 CSV、Excel 格式文件
                  </div>
                </template>
              </el-upload>
            </el-form-item>
            
            <el-form-item>
              <div class="action-buttons">
                <el-button 
                  type="primary" 
                  @click="runQualityCheck" 
                  :loading="checking"
                  size="large"
                  style="width: 100%"
                >
                  <el-icon><Check /></el-icon>
                  开始检测
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
        <el-card class="result-panel" shadow="hover">
          <template #header>
            <div class="card-header">
              <div class="header-left">
                <el-icon class="header-icon"><Setting /></el-icon>
                <span class="header-title">检测结果</span>
              </div>
              <div class="header-actions" v-if="checkResult">
                <el-button size="small" @click="exportReport">
                  <el-icon><Download /></el-icon>
                  导出失败记录
                </el-button>
              </div>
            </div>
          </template>
          
          <div class="result-content">
            <!-- 检测概览 -->
            <div v-if="checkResult" class="result-overview">
              <div class="overview-grid">
                <div class="overview-item">
                  <div class="overview-icon success">
                    <el-icon><CircleCheck /></el-icon>
                  </div>
                  <div class="overview-content">
                    <span class="overview-label">通过</span>
                    <span class="overview-value">{{ checkResult.passedCount }}</span>
                  </div>
                </div>
                <div class="overview-item">
                  <div class="overview-icon warning">
                    <el-icon><Warning /></el-icon>
                  </div>
                  <div class="overview-content">
                    <span class="overview-label">警告</span>
                    <span class="overview-value">{{ checkResult.warningCount }}</span>
                  </div>
                </div>
                <div class="overview-item">
                  <div class="overview-icon error">
                    <el-icon><CircleClose /></el-icon>
                  </div>
                  <div class="overview-content">
                    <span class="overview-label">错误</span>
                    <span class="overview-value">{{ checkResult.errorCount }}</span>
                  </div>
                </div>
                <div class="overview-item">
                  <div class="overview-icon info">
                    <el-icon><DataAnalysis /></el-icon>
                  </div>
                  <div class="overview-content">
                    <span class="overview-label">总计</span>
                    <span class="overview-value">{{ checkResult.totalCount }}</span>
                  </div>
                </div>
              </div>
            </div>
            
            <!-- 详细结果 -->
            <div v-if="checkResult && checkResult.details" class="result-details">
              <div class="details-header">
                <h4>详细检测结果</h4>
                <el-tag type="info">{{ checkResult.details.length }} 条规则</el-tag>
              </div>
              
              <div class="details-list">
                <div 
                  v-for="detail in checkResult.details" 
                  :key="detail.id"
                  class="detail-item"
                  :class="detail.status"
                >
                  <div class="detail-header">
                    <div class="detail-info">
                      <span class="detail-name">{{ detail.ruleName }}</span>
                      <span class="detail-field">{{ detail.fieldName }}</span>
                    </div>
                    <el-tag :type="getStatusType(detail.status)" size="small">
                      {{ getStatusText(detail.status) }}
                    </el-tag>
                  </div>
                  <div class="detail-content">
                    <p class="detail-description">{{ detail.description }}</p>
                    <div class="detail-stats">
                      <span>检查记录: {{ detail.checkedCount }}</span>
                      <span>异常记录: {{ detail.errorCount }}</span>
                      <span>通过率: {{ ((detail.checkedCount - detail.errorCount) / detail.checkedCount * 100).toFixed(2) }}%</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
            <!-- 空状态 -->
            <div v-else class="empty-result">
              <el-icon class="empty-icon"><DataAnalysis /></el-icon>
              <p>暂无检测结果</p>
              <span>请配置检测参数并开始检测</span>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { UploadFilled, Download, Refresh, Setting, Check, CircleCheck, Warning, CircleClose, DataAnalysis, Location } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'

export default {
  name: 'QualityCheck',
  components: {
    UploadFilled,
    Download,
    Refresh,
    Setting,
    Check,
    CircleCheck,
    Warning,
    CircleClose,
    DataAnalysis,
    Location
  },
  setup() {
    const ruleLibraries = ref([])
    const ruleVersions = ref([]) // 兼容保留，但界面不再展示
    const dataSources = ref([])
    const tables = ref([])
    const filteredTables = ref([])
    const availableFields = ref([])
    const qualityResults = ref([])
    const anomalyData = ref([])
    const anomalyFields = ref([])
    const showDetail = ref(false)
    const detailData = ref(null)
    const checking = ref(false)
    const batchChecking = ref(false)
    const checkProgress = ref(0)
    const progressText = ref('准备检测...')
    const fileList = ref([])
    const tableLoading = ref(false)
    
         // 数据源选择状态
     const selectedDataSource = ref('')
     
     // 分公司筛选相关状态
     const selectedCompanyField = ref('')
     const selectedCompanyValue = ref('')
     const companyValues = ref([])
     const companyValueLoading = ref(false)
     
     // 油气田筛选相关状态
     const selectedOilfieldField = ref('')
     const selectedOilfieldValue = ref('')
     const oilfieldValues = ref([])
     const oilfieldValueLoading = ref(false)
     
     // 井名筛选相关状态
     const selectedWellField = ref('')
     const selectedWellValue = ref([])
     const wellValues = ref([])
     const wellValueLoading = ref(false)
    
         // 无版本模式：不再过滤 version_count，全部可选
     const availableRuleLibraries = computed(() => ruleLibraries.value || [])
     
     // 分公司字段列表（常见的分公司相关字段）
     const companyFields = computed(() => {
       if (!availableFields.value || availableFields.value.length === 0) return []
       
       const companyKeywords = ['company', 'branch', 'division', 'region', 'area', 'location', '分公司', '公司', '区域', '地区']
       return availableFields.value.filter(field => 
         companyKeywords.some(keyword => 
           field.name.toLowerCase().includes(keyword.toLowerCase())
         )
       )
     })
     
     // 油气田字段计算属性
     const oilfieldFields = computed(() => {
       if (!availableFields.value || availableFields.value.length === 0) return []
       
       const oilfieldKeywords = ['field', 'oilfield', 'gasfield', '油田', '气田', '油气田', 'block', '区块', 'area', '工区', 'reserve', '储层']
       return availableFields.value.filter(field => {
         const fieldName = field.name.toLowerCase()
         return oilfieldKeywords.some(keyword => fieldName.includes(keyword.toLowerCase()))
       })
     })
     
     // 井名字段计算属性
     const wellFields = computed(() => {
       if (!availableFields.value || availableFields.value.length === 0) return []
       
       const wellKeywords = ['well', 'wellname', '井', '井名', 'wellid', 'well_id', 'well_name', 'hole', '钻井', 'borehole']
       return availableFields.value.filter(field => {
         const fieldName = field.name.toLowerCase()
         return wellKeywords.some(keyword => fieldName.includes(keyword.toLowerCase()))
       })
     })

    const qualityForm = reactive({
      ruleLibrary: null,
      ruleVersion: null,
      dataSource: null,
      tableName: '',
      fields: []
    })
    
    const canRunCheck = computed(() => {
      return qualityForm.ruleLibrary && 
             qualityForm.dataSource && 
             qualityForm.tableName
    })
    
    const canRunBatchCheck = computed(() => {
      return qualityForm.ruleLibrary && 
             qualityForm.dataSource
    })
    

    
    const totalRecords = computed(() => {
      return qualityResults.value.reduce((sum, result) => sum + result.total_records, 0)
    })
    
    const passedRecords = computed(() => {
      return qualityResults.value.reduce((sum, result) => sum + result.passed_records, 0)
    })
    
    const failedRecords = computed(() => {
      return qualityResults.value.reduce((sum, result) => sum + result.failed_records, 0)
    })
    
    const passRate = computed(() => {
      if (totalRecords.value === 0) return 0
      return Math.round((passedRecords.value / totalRecords.value) * 100)
    })
    
    // 添加 checkResult 计算属性，基于 qualityResults 
    const checkResult = computed(() => {
      if (!qualityResults.value || qualityResults.value.length === 0) {
        return null
      }
      
      const result = qualityResults.value[0]
      return {
        passedCount: result.passed_records || 0,
        warningCount: 0, // 暂时没有警告计数
        errorCount: result.failed_records || 0,
        totalCount: result.total_records || 0,
        details: [] // 暂时空数组，可以后续从报告中获取
      }
    })
    
    const loadRuleLibraries = async () => {
      try {
        const response = await axios.get('/api/rules/libraries')
        if (response.data.success) {
          ruleLibraries.value = response.data.data
          // 自动选择第一个规则库
          if (!qualityForm.ruleLibrary) {
            qualityForm.ruleLibrary = availableRuleLibraries.value[0] || null
            qualityForm.ruleVersion = null
          } else {
            // 如果列表中存在同 id 的库，用它覆盖（确保对象引用是最新项）
            const same = availableRuleLibraries.value.find(l => l.id === qualityForm.ruleLibrary.id)
            if (same) qualityForm.ruleLibrary = same
          }
        }
      } catch (error) {
        ElMessage.error('加载规则库失败')
      }
    }
    
    const loadDataSources = async () => {
      try {
        const response = await axios.get('/api/database/sources')
        if (response.data.success) {
          dataSources.value = response.data.data
          console.log('加载的数据源列表:', dataSources.value)
        }
      } catch (error) {
        ElMessage.error('加载数据源失败')
      }
    }
    
    const loadRuleVersions = async () => {
      // 无版本模式保留空函数以兼容旧流程
      ruleVersions.value = []
      qualityForm.ruleVersion = null
      return
    }
    
    // 数据源变化处理
    const onDataSourceChange = async () => {
      if (!selectedDataSource.value) return
      
      // 根据选中的ID找到对应的数据源对象
      const selectedSource = dataSources.value.find(s => s.id === selectedDataSource.value)
      if (selectedSource) {
        qualityForm.dataSource = selectedSource
        console.log('数据源选择变化:', selectedSource)
        await loadTables()
      }
    }
    
    const loadTables = async () => {
      if (!qualityForm.dataSource) return
      
      tableLoading.value = true
      try {
        const response = await axios.post('/api/database/tables', qualityForm.dataSource)
        if (response.data.success) {
          tables.value = response.data.data
          filteredTables.value = tables.value
          
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
      } catch (error) {
        ElMessage.error('加载数据表失败')
      } finally {
        tableLoading.value = false
      }
    }

    const filterTablesRemote = (query) => {
      if (!query) {
        filteredTables.value = tables.value
        return
      }
      const q = query.toLowerCase()
      filteredTables.value = tables.value.filter(t => String(t).toLowerCase().includes(q))
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
        // 获取分公司字段的唯一值
        const response = await axios.get(`/api/database/field-values`, {
          params: {
            source_id: qualityForm.dataSource.id,
            table_name: qualityForm.tableName,
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
        const response = await axios.get(`/api/database/field-values`, {
          params: {
            source_id: qualityForm.dataSource.id,
            table_name: qualityForm.tableName,
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
        const response = await axios.get(`/api/database/field-values`, {
          params: {
            source_id: qualityForm.dataSource.id,
            table_name: qualityForm.tableName,
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
    
    const loadFields = async () => {
      // 需要 selectedDataSource + tableName
      if (!qualityForm.dataSource || !qualityForm.tableName) return
      try {
        const response = await axios.get(`/api/database/fields/${qualityForm.dataSource.id}/${qualityForm.tableName}`)
        if (response.data.success) {
          availableFields.value = response.data.data
          
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
        } else {
          availableFields.value = []
        }
      } catch (error) {
        availableFields.value = []
      }
    }
    
    const resetForm = () => {
      qualityForm.ruleLibrary = null
      qualityForm.ruleVersion = null
      qualityForm.dataSource = null
      qualityForm.tableName = ''
      qualityForm.fields = []
      tables.value = []
      filteredTables.value = []
      availableFields.value = []
      qualityResults.value = []
      anomalyData.value = []
      anomalyFields.value = []
      showDetail.value = false
      detailData.value = null
      fileList.value = []
      
      // 重置数据源选择
      selectedDataSource.value = ''
      
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
    
    const handleFileChange = (file) => {
      fileList.value = [file]
      ElMessage.success('文件上传成功')
    }
    
    const runQualityCheck = async () => {
      if (!canRunCheck.value) {
        ElMessage.warning('请完善配置信息')
        return
      }
      
      checking.value = true
      checkProgress.value = 0
      progressText.value = '开始质量检测...'
      
      try {
        // 分阶段显示进度
        progressText.value = '正在连接数据源...'
        checkProgress.value = 15
        
        // 短暂延迟以显示连接状态
        await new Promise(resolve => setTimeout(resolve, 300))
        
        progressText.value = '正在加载规则...'
        checkProgress.value = 30
        
        await new Promise(resolve => setTimeout(resolve, 200))
        
        progressText.value = '正在执行质量检测...'
        checkProgress.value = 50
        
        // 构建请求参数
        const requestData = {
          rule_library_id: qualityForm.ruleLibrary.id,
          version_id: undefined,
          db_config: qualityForm.dataSource,
          table_name: qualityForm.tableName,
          fields: qualityForm.fields && qualityForm.fields.length ? qualityForm.fields : undefined
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
        
        const response = await axios.post('/api/quality/check', requestData, {
          onUploadProgress: (progressEvent) => {
            // 根据上传进度更新
            const percentCompleted = Math.round((progressEvent.loaded * 40) / progressEvent.total) + 50
            checkProgress.value = Math.min(percentCompleted, 90)
            progressText.value = '正在分析检测结果...'
          }
        })
        
        // API调用完成后更新进度
        checkProgress.value = 100
        progressText.value = '检测完成'
        
        if (response.data.success) {
          qualityResults.value = [response.data.data]
          loadAnomalyData()
          ElMessage.success('质量检测完成')
        }
      } catch (error) {
        ElMessage.error('质量检测失败')
      } finally {
        checking.value = false
        setTimeout(() => {
          checkProgress.value = 0
          progressText.value = '准备检测...'
        }, 2000)
      }
    }
    
    const batchQualityCheck = async () => {
      if (!canRunBatchCheck.value) {
        ElMessage.warning('请完善配置信息')
        return
      }
      
      batchChecking.value = true
      checkProgress.value = 0
      progressText.value = '开始批量检测...'
      
      try {
        // 构建请求参数
        const requestData = {
          rule_library_id: qualityForm.ruleLibrary.id,
          version_id: undefined,
          db_config: qualityForm.dataSource,
          tables: tables.value,
          fields_map: qualityForm.fields && qualityForm.fields.length ? { [qualityForm.tableName]: qualityForm.fields } : undefined
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
        
        const response = await axios.post('/api/quality/batch-check', requestData)
        
        if (response.data.success) {
          qualityResults.value = response.data.data
          ElMessage.success('批量质量检测完成')
        }
      } catch (error) {
        ElMessage.error('批量质量检测失败')
      } finally {
        batchChecking.value = false
        checkProgress.value = 0
        progressText.value = '准备检测...'
      }
    }
    
    const loadAnomalyData = async () => {
      try {
        const response = await axios.get('/api/quality/anomaly-data')
        if (response.data.success) {
          anomalyData.value = response.data.data.records
          anomalyFields.value = response.data.data.fields
        }
      } catch (error) {
        console.log('加载异常数据失败')
      }
    }
    
    const viewDetail = async (result) => {
      try {
        const response = await axios.get(`/api/quality/results/${result.id}/detail`)
        if (response.data.success) {
          detailData.value = response.data.data
          showDetail.value = true
        }
      } catch (error) {
        ElMessage.error('加载详情失败')
      }
    }
    
    const exportReport = async () => {
      if (!qualityResults.value || qualityResults.value.length === 0) {
        ElMessage.warning('没有检测结果可导出')
        return
      }
      
      try {
        const result = qualityResults.value[0] // 获取第一个检测结果
        const response = await axios.get(`/api/quality/results/${result.id}/failed-records`)
        
        if (response.data.success) {
          const failedRecords = response.data.data.records
          
          if (failedRecords.length === 0) {
            ElMessage.info('没有检测到失败记录')
            return
          }
          
          // 转换为CSV格式
          const csvHeaders = [
            '规则名称', '规则类型', '字段名称', '行号', '异常值', '深度', 
            '错误描述', '表名', '数据源', '检测日期'
          ]
          
          const csvRows = failedRecords.map(record => [
            record.rule_name || '',
            record.rule_type || '',
            record.field_name || '',
            record.row_number || '',
            record.value || '',
            record.depth || '',
            record.error_message || '',
            record.table_name || '',
            record.data_source || '',
            record.check_date || ''
          ])
          
          // 生成CSV内容
          const csvContent = [
            csvHeaders.join(','),
            ...csvRows.map(row => row.map(field => `"${String(field).replace(/"/g, '""')}"`).join(','))
          ].join('\n')
          
          // 添加BOM以支持中文
          const BOM = '\uFEFF'
          const csvWithBOM = BOM + csvContent
          
          // 下载CSV文件
          const dataBlob = new Blob([csvWithBOM], { type: 'text/csv;charset=utf-8' })
          const url = URL.createObjectURL(dataBlob)
          const link = document.createElement('a')
          link.href = url
          link.download = `quality_failed_records_${new Date().toISOString().slice(0, 10)}.csv`
          link.click()
          URL.revokeObjectURL(url)
          
          ElMessage.success(`已导出 ${failedRecords.length} 条失败记录`)
        } else {
          ElMessage.error('获取失败记录失败')
        }
      } catch (error) {
        console.error('导出失败记录错误:', error)
        ElMessage.error('导出失败记录失败')
      }
    }
    
    const refreshResults = () => {
      // 重新加载结果
      ElMessage.success('结果已刷新')
    }
    
    const getProgressColor = (rate) => {
      if (rate >= 90) return '#67C23A'
      if (rate >= 70) return '#E6A23C'
      return '#F56C6C'
    }
    
    const getStatusType = (status) => {
      switch(status) {
        case 'passed': return 'success'
        case 'failed': return 'danger' 
        case 'warning': return 'warning'
        default: return 'info'
      }
    }
    
    const getStatusText = (status) => {
      switch(status) {
        case 'passed': return '通过'
        case 'failed': return '失败'
        case 'warning': return '警告'
        default: return '未知'
      }
    }
    
    const isAnomalyValue = (value) => {
      // 简单的异常值判断逻辑
      return value === null || value === undefined || value === ''
    }
    
    onMounted(() => {
      loadRuleLibraries()
      loadDataSources()
      // 当选择数据表时，加载字段列表
      watch(() => qualityForm.tableName, async (val) => {
        if (val) {
          await loadFields()
        } else {
          availableFields.value = []
          qualityForm.fields = []
        }
      })
    })
    
         return {
       ruleLibraries,
       availableRuleLibraries,
       ruleVersions,
       dataSources,
       tables,
       filteredTables,
       availableFields,
       qualityResults,
       anomalyData,
       anomalyFields,
       showDetail,
       detailData,
       checking,
       batchChecking,
       checkProgress,
       progressText,
       fileList,
       tableLoading,
       qualityForm,
       canRunCheck,
       canRunBatchCheck,
       totalRecords,
       passedRecords,
       failedRecords,
       passRate,
       checkResult,
       // 数据源选择相关
       selectedDataSource,
       onDataSourceChange,
      // 分公司筛选相关
      selectedCompanyField,
      selectedCompanyValue,
      companyValues,
      companyValueLoading,
      companyFields,
      onCompanyFieldChange,
      
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
      onWellFieldChange,
       loadRuleVersions,
       loadTables,
       filterTablesRemote,
       resetForm,
       handleFileChange,
       runQualityCheck,
       batchQualityCheck,
       loadFields,
       viewDetail,
       exportReport,
       refreshResults,
       getProgressColor,
       getStatusType,
       getStatusText,
       isAnomalyValue
     }
  }
}
</script>

<style scoped>
.quality-check {
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

.result-overview {
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 24px;
  border: 2px solid #e9ecef;
}

.overview-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 20px;
}

.overview-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  background: rgba(255, 255, 255, 0.9);
  border-radius: 12px;
  border: 2px solid #e9ecef;
  transition: all 0.3s ease;
}

.overview-item:hover {
  background: rgba(255, 255, 255, 1);
  border-color: #3498db;
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(52, 152, 219, 0.15);
}

.overview-icon {
  font-size: 32px;
  background: rgba(52, 152, 219, 0.1);
  border-radius: 12px;
  padding: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.overview-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.overview-label {
  font-size: 14px;
  color: #7f8c8d;
  font-weight: 500;
}

.overview-value {
  font-size: 28px;
  font-weight: 700;
  color: #2c3e50;
}

.overview-icon.success {
  color: #27ae60;
  background: rgba(39, 174, 96, 0.1);
}

.overview-icon.warning {
  color: #f39c12;
  background: rgba(243, 156, 18, 0.1);
}

.overview-icon.error {
  color: #e74c3c;
  background: rgba(231, 76, 60, 0.1);
}

.overview-icon.info {
  color: #3498db;
  background: rgba(52, 152, 219, 0.1);
}

.result-details {
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  border-radius: 12px;
  padding: 24px;
  border: 2px solid #e9ecef;
}

.details-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 12px;
  border-bottom: 2px solid #e9ecef;
}

.details-header h4 {
  margin: 0;
  color: #2c3e50;
  font-size: 18px;
  font-weight: 600;
}

.details-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.detail-item {
  background: rgba(255, 255, 255, 0.9);
  border-radius: 12px;
  padding: 20px;
  border: 2px solid #e9ecef;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.detail-item::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  bottom: 0;
  width: 4px;
  background: #3498db;
  transition: all 0.3s ease;
}

.detail-item:hover {
  background: rgba(255, 255, 255, 1);
  border-color: #3498db;
  transform: translateX(4px);
  box-shadow: 0 8px 25px rgba(52, 152, 219, 0.15);
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.detail-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.detail-name {
  font-size: 16px;
  font-weight: 600;
  color: #2c3e50;
}

.detail-field {
  font-size: 14px;
  color: #7f8c8d;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
}

.detail-content {
  font-size: 14px;
  color: #606266;
  line-height: 1.6;
}

.detail-description {
  margin-bottom: 12px;
  font-style: italic;
  color: #7f8c8d;
  padding: 8px 12px;
  background: rgba(52, 152, 219, 0.05);
  border-radius: 6px;
  border-left: 3px solid #3498db;
}

.detail-stats {
  display: flex;
  justify-content: space-around;
  font-size: 13px;
  color: #7f8c8d;
  padding: 8px 0;
  background: rgba(52, 152, 219, 0.05);
  border-radius: 6px;
}

.detail-item.passed::before {
  background: #27ae60;
}

.detail-item.warning::before {
  background: #f39c12;
}

.detail-item.error::before {
  background: #e74c3c;
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

/* 选项内容样式 */
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

/* 响应式设计 */
@media (max-width: 1200px) {
  .overview-grid {
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  }
}

@media (max-width: 768px) {
  .quality-check {
    padding: 15px;
  }
  
  .page-header h2 {
    font-size: 24px;
  }
  
  .overview-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .overview-item {
    flex-direction: column;
    text-align: center;
    gap: 12px;
  }
  
  .detail-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
  
  .detail-stats {
    flex-direction: column;
    gap: 4px;
  }
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
</style> 