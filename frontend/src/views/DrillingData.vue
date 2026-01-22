<template>
  <div class="model-container">
    <!-- 拆分后的模板区域 -->
    <el-row :gutter="20" style="margin-bottom: 20px;">
      <!-- 左侧钻井数据DrillingData质量检查卡片 (80%) -->
      <el-col :span="19">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>钻井实时数据质量检查</span>
            </div>
          </template>
          <div class="drilling-data-content">
            <p>实时监控钻井数据质量，自动检测异常数据点，确保数据采集的准确性和完整性。</p>
            <div class="data-quality-stats">
              <el-row :gutter="10">
                <el-col :span="8">
                  <div class="stat-card">
                    <div class="stat-value">{{ overviewStats[0].value }}%</div>
                    <div class="stat-label">{{ overviewStats[0].label }}</div>
                  </div>
                </el-col>
                <el-col :span="8">
                  <div class="stat-card">
                    <div class="stat-value">{{ overviewStats[1].value }}</div>
                    <div class="stat-label">{{ overviewStats[1].label }}</div>
                  </div>
                </el-col>
                <el-col :span="8">
                  <div class="stat-card">
                    <div class="stat-value">{{ overviewStats[2].value }}%</div>
                    <div class="stat-label">{{ overviewStats[2].label }}</div>
                  </div>
                </el-col>
              </el-row>
            </div>
            <el-progress :percentage="dataQualityScore" status="success" :show-text="false"/>
            <div class="progress-labels">
              <span>数据质量评分</span>
              <span>{{ dataQualityScore }}/100</span>
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- 右侧异常检测模型卡片 (20%) -->
      <el-col :span="5">
        <el-card class="anomaly-model-card">
          <template #header>
            <div class="card-header">
              <span>异常检测模型</span>
            </div>
          </template>
          <div class="model-display">
            <div class="model-icon">
              <el-icon size="40">
                <Cpu/>
              </el-icon>
            </div>
            <div class="model-name">LSTM</div>
            <div class="model-desc">长短期记忆网络</div>
            <el-tag type="danger" size="small">时间序列</el-tag>
            <div class="model-status">
              <el-tag type="success" size="small">运行中</el-tag>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20">
      <!-- 异常检测结果区 -->
      <el-col :span="6">
        <el-card class="anomaly-results-card">
          <template #header>
            <div class="card-header">
              <span>异常检测结果</span>
              <div>
                <el-button type="success" size="small" @click="exportReport" :disabled="anomalyData.length === 0" style="margin-right: 10px;">
                  <el-icon style="margin-right: 5px;"><Download /></el-icon>
                  导出报告
                </el-button>
                <el-button type="primary" size="small" @click="runAnomalyDetection" :loading="isDetecting">
                  开始检测
                </el-button>
              </div>
            </div>
          </template>
          <el-table :data="anomalyData" style="width: 100%" height="500">
            <el-table-column prop="rawValue" label="异常数据" width="180">
              <template #default="scope">
                <div class="anomaly-value">
                  <div class="label">{{ scope.row.parameter }}：</div>
                  <div class="value">{{ scope.row.rawValue }} <span class="unit">{{ scope.row.unit }}</span></div>
                </div>
              </template>
            </el-table-column>
            <el-table-column prop="type" label="异常类型" width="120">
              <template #default="scope">
                <el-tag :type="getTagType(scope.row.type)" size="small">{{ scope.row.type }}</el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>

      <!-- 参数配置区 -->
      <el-col :span="10">
        <el-card class="parameter-panel-card">
          <template #header>
            <div class="card-header">
              <span>{{ selectedModel?.name || 'LSTM' }}</span>
              <div>
                <el-button type="primary" @click="resetParameters" :disabled="!selectedModel">
                  重置参数
                </el-button>
                <el-button type="success" @click="saveModelConfig" :disabled="!selectedModel">
                  保存配置
                </el-button>
              </div>
            </div>
          </template>

          <div v-if="selectedModel" class="parameter-content">
            <el-alert
                :title="selectedModel.description"
                type="info"
                :closable="false"
                style="margin-bottom: 20px;"
            />

            <!-- 配置名称单独一行 -->
            <el-row class="config-section">
              <el-col :span="24">
                <div class="config-item">
                  <div class="config-label">配置名称</div>
                  <el-input v-model="modelForm.name" placeholder="异常模型检测"/>
                </div>
              </el-col>
            </el-row>

            <!-- 数据源配置 -->
            <el-divider content-position="left">数据源配置</el-divider>
            <div class="config-section">
              <el-row :gutter="20">
                <el-col :span="24">
                  <!-- ================== 新增的数据源下拉框 ================== -->
                  <div class="config-item">
                    <div class="config-label">数据源</div>
                    <el-select
                        v-model="selectedSourceId"
                        placeholder="请选择数据源"
                        :loading="loadingSources"
                        filterable
                        style="width: 100%;"
                    >
                      <el-option
                          v-for="source in dataSources"
                          :key="source.id"
                          :label="source.name"
                          :value="source.id"
                      />
                    </el-select>
                  </div>

                  <div class="config-item" style="margin-top: 15px;">
                    <div class="config-label">Schema</div>
                    <el-select
                        v-model="selectedSchema"
                        placeholder="请先选择数据源"
                        :loading="loadingSchemas"
                        :disabled="!selectedSourceId"
                        filterable
                        style="width: 100%;"
                    >
                      <el-option
                          v-for="schema in schemas"
                          :key="schema"
                          :label="schema"
                          :value="schema"
                      />
                    </el-select>
                  </div>

                  <div class="config-item" style="margin-top: 15px;">
                    <div class="config-label">数据表 (模型参数)</div>
                    <el-select
                        v-model="modelForm.dataTable"
                        placeholder="请先选择Schema"
                        :loading="loadingTables"
                        :disabled="!selectedSchema"
                        filterable
                        style="width: 100%;"
                    >
                      <el-option
                          v-for="table in dataTables"
                          :key="table.value"
                          :label="table.label"
                          :value="table.value"
                      />
                    </el-select>
                  </div>

                  <div class="config-item" style="margin-top: 15px;">
                    <div class="config-label">井名字段选择</div>
                    <el-select
                        v-model="selectedWellField"
                        placeholder="请先选择数据表"
                        :disabled="!modelForm.dataTable"
                        filterable
                        clearable
                        style="width: 100%;"
                    >
                      <el-option
                          v-for="field in wellFields"
                          :key="field.name"
                          :label="field.description || field.name"
                          :value="field.name"
                      >
                        <div class="option-content">
                          <span class="option-name">{{ field.description || field.name }}</span>
                          <span class="option-desc">{{ field.type }}<span v-if="field.description && field.description !== field.name"> | {{ field.name }}</span></span>
                        </div>
                      </el-option>
                    </el-select>
                  </div>

                  <div class="config-item" style="margin-top: 15px;">
                    <div class="config-label">井选取</div>
                    <el-select
                        v-model="modelForm.selectedWell"
                        placeholder="请先选择井名字段"
                        :loading="loadingWells"
                        :disabled="!selectedWellField"
                        filterable
                        style="width: 100%;"
                    >
                      <el-option
                          v-for="well in wellOptions"
                          :key="well.value"
                          :label="well.label"
                          :value="well.value"
                      />
                    </el-select>
                  </div>

                  <div class="config-item" style="margin-top: 15px;">
                    <div class="config-label">数据项参数选择</div>
                    <el-select
                        v-model="modelForm.dataParam"
                        placeholder="请先选择数据表"
                        :loading="loadingParams"
                        :disabled="!modelForm.dataTable"
                        filterable
                        style="width: 100%;"
                    >
                      <el-option
                          v-for="param in dataParams"
                          :key="param.value"
                          :label="param.label"
                          :value="param.value"
                      />
                    </el-select>
                  </div>
                  
                  <!-- 数据量限制选项 -->
                  <div class="config-item" style="margin-top: 15px;">
                    <div class="config-label">
                      数据量限制
                      <el-tooltip content="建议：数据量过大时选择限制以提升性能" placement="top">
                        <el-icon style="margin-left: 5px;"><QuestionFilled /></el-icon>
                      </el-tooltip>
                    </div>
                    <el-select
                        v-model="modelForm.dataLimit"
                        placeholder="选择数据量限制"
                        style="width: 100%;"
                    >
                      <el-option label="最近 1,000 条（快速）" :value="1000" />
                      <el-option label="最近 5,000 条（推荐）" :value="5000" />
                      <el-option label="最近 10,000 条" :value="10000" />
                      <el-option label="最近 50,000 条" :value="50000" />
                      <el-option label="全部数据（可能较慢）" :value="null" />
                    </el-select>
                  </div>
                  
                  <!-- 时间范围筛选（可选） -->
                  <el-divider content-position="left" style="margin-top: 20px;">
                    时间范围筛选（可选）
                  </el-divider>
                  
                  <!-- 时间字段选择 -->
                  <div class="config-item">
                    <div class="config-label">
                      时间字段
                      <el-tooltip content="选择用于时间筛选的字段，默认为update_date" placement="top">
                        <el-icon style="margin-left: 5px;"><QuestionFilled /></el-icon>
                      </el-tooltip>
                    </div>
                    <el-select
                        v-model="modelForm.dateField"
                        placeholder="选择时间字段"
                        :disabled="!modelForm.dataTable"
                        filterable
                        clearable
                        style="width: 100%;"
                    >
                      <el-option
                          v-for="field in dateFields"
                          :key="field.name"
                          :label="field.description || field.name"
                          :value="field.name"
                      >
                        <div class="option-content">
                          <span class="option-name">{{ field.description || field.name }}</span>
                          <span class="option-desc">{{ field.type }}<span v-if="field.description && field.description !== field.name"> | {{ field.name }}</span></span>
                        </div>
                      </el-option>
                    </el-select>
                  </div>
                  
                  <div class="config-item" style="margin-top: 15px;">
                    <div class="config-label">
                      开始时间
                      <el-tooltip content="留空表示不限制开始时间" placement="top">
                        <el-icon style="margin-left: 5px;"><QuestionFilled /></el-icon>
                      </el-tooltip>
                    </div>
                    <el-date-picker
                        v-model="modelForm.startDate"
                        type="datetime"
                        placeholder="选择开始时间"
                        style="width: 100%;"
                        format="YYYY-MM-DD HH:mm:ss"
                        value-format="YYYY-MM-DD HH:mm:ss"
                        :clearable="true"
                    />
                  </div>
                  
                  <div class="config-item" style="margin-top: 15px;">
                    <div class="config-label">
                      结束时间
                      <el-tooltip content="留空表示不限制结束时间" placement="top">
                        <el-icon style="margin-left: 5px;"><QuestionFilled /></el-icon>
                      </el-tooltip>
                    </div>
                    <el-date-picker
                        v-model="modelForm.endDate"
                        type="datetime"
                        placeholder="选择结束时间"
                        style="width: 100%;"
                        format="YYYY-MM-DD HH:mm:ss"
                        value-format="YYYY-MM-DD HH:mm:ss"
                        :clearable="true"
                    />
                  </div>
                  
                  <!-- 快捷时间范围选择 -->
                  <div class="config-item" style="margin-top: 15px;">
                    <div class="config-label">快捷选择</div>
                    <el-row :gutter="8">
                      <el-col :span="8">
                        <el-button size="small" @click="setTimeRange('today')" style="width: 100%;">今天</el-button>
                      </el-col>
                      <el-col :span="8">
                        <el-button size="small" @click="setTimeRange('week')" style="width: 100%;">近7天</el-button>
                      </el-col>
                      <el-col :span="8">
                        <el-button size="small" @click="setTimeRange('month')" style="width: 100%;">近30天</el-button>
                      </el-col>
                    </el-row>
                  </div>
                </el-col>
              </el-row>
            </div>
          </div>

          <div v-else class="no-model-selected">
            <el-empty description="请选择一个模型进行配置"/>
          </div>
        </el-card>
      </el-col>

      <!-- 数据预览区 -->
      <el-col :span="8">
        <el-card class="data-preview-card">
          <template #header>
            <div class="card-header">
              <span>数据预览</span>
            </div>
          </template>

          <div class="preview-content">
            <div class="data-table">
              <el-table :data="previewData" style="width: 100%" height="300" size="small" v-loading="loadingPreview">
                <el-table-column
                    v-for="column in previewColumns"
                    :key="column.prop"
                    :prop="column.prop"
                    :label="column.label"
                    :width="column.width"
                />
              </el-table>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import {ref, reactive, computed, onMounted, watch} from 'vue'
import {Cpu, QuestionFilled, Download} from '@element-plus/icons-vue'
import {ElMessage} from 'element-plus'
// --- MODIFICATION: Import the configured api instance, not the raw axios library ---
import api, { apiService } from '@/utils/api.js'


// --- MODIFICATION: API constants are no longer needed as apiService handles URLs ---
// const API_DATABASE_URL = '/api/database';
// const API_LSTM_URL = '/api/lstm-anomaly';

// --- 新增: 数据源状态 ---
const dataSources = ref([]);
const selectedSourceId = ref(null);
const loadingSources = ref(false);
const schemas = ref([]);
const selectedSchema = ref('');
const loadingSchemas = ref(false);

// --- 统计和模型数据 ---
const overviewStats = ref([
  {label: '数据完整率', value: 0},
  {label: '今日异常点', value: 0},
  {label: '错误率', value: 0}
]);
const dataQualityScore = ref(0);
const selectedModel = ref({
  id: 'lstm',
  name: 'LSTM',
  type: 'model',
  description: '长短期记忆网络模型，适用于时间序列数据',
});

// --- 核心状态 ---
const dataTables = ref([]);
const availableFields = ref([]);  // 存储当前表的所有字段
const selectedWellField = ref('');  // 用户选择的井名字段
const wellOptions = ref([]);
const dataParams = ref([]);
const previewData = ref([]);
const previewColumns = ref([]);
const anomalyData = ref([]);

// --- 加载状态 ---
const loadingTables = ref(false);
const loadingWells = ref(false);
const loadingParams = ref(false);
const loadingPreview = ref(false);
const isDetecting = ref(false);

// --- 计算属性 ---
// 智能匹配井名字段
// 智能匹配井名字段
const wellFields = computed(() => {
  return availableFields.value.filter(field => {
    const name = field.name.toLowerCase();
    const desc = (field.description || '').toLowerCase();
    
    // 1. 直接放行常见的井名字段名 (如 wid, jh, well_id 等)
    if (['wid', 'jh', 'well_id', 'wellid', 'well_name'].includes(name)) return true;

    // 2. 原有的模糊匹配逻辑
    const searchText = (desc || name);
    const hasWellPrefix = searchText.includes('井') || searchText.includes('well');
    const hasNameOrId = searchText.includes('名') || searchText.includes('号') || 
                       searchText.includes('name') || searchText.includes('id') || 
                       searchText.includes('code');
    
    return hasWellPrefix && hasNameOrId;
  })
});

// 计算可能的日期字段（基于字段类型）
const dateFields = computed(() => {
  // 筛选日期/时间类型的字段
  return availableFields.value.filter(field => {
    const fieldType = (field.type || '').toLowerCase()
    const fieldName = (field.name || '').toLowerCase()
    const fieldDesc = (field.description || '').toLowerCase()
    
    // 匹配常见的日期时间类型
    const isDateType = fieldType.includes('date') || 
                      fieldType.includes('time') || 
                      fieldType.includes('timestamp') ||
                      fieldName.includes('date') ||
                      fieldName.includes('time') ||
                      fieldDesc.includes('日期') ||
                      fieldDesc.includes('时间')
    
    return isDateType
  })
})

// --- 表单数据 ---
const modelForm = reactive({
  name: '异常模型检测',
  dataTable: '',
  selectedWell: '',
  dataParam: '',
  dataLimit: 5000,  // 默认5000条（推荐）
  dateField: 'update_date',  // 默认时间字段
  startDate: null,  // 开始时间（可选）
  endDate: null,    // 结束时间（可选）
  description: '',
});

// --- API 调用函数 (已重构) ---

// 1. 获取所有可用数据源
const fetchDataSources = async () => {
  loadingSources.value = true;
  try {
    // --- MODIFICATION: Use apiService ---
    const response = await apiService.database.getSources();
    if (response.data.success) {
      dataSources.value = response.data.data;
      if (dataSources.value.length > 0) {
        selectedSourceId.value = dataSources.value[0].id; // 自动选择第一个
      }
    } else {
      ElMessage.error(`获取数据源列表失败: ${response.data.error}`);
    }
  } catch (error) {
    // The interceptor in api.js will handle showing the ElMessage
    console.error(`请求数据源列表时出错: ${error.message}`);
  } finally {
    loadingSources.value = false;
  }
};

// 2. 获取Schema列表
const loadSchemas = async () => {
  if (!selectedSourceId.value) return;
  
  // 重置后续选择
  selectedSchema.value = '';
  dataTables.value = [];
  modelForm.dataTable = '';
  modelForm.selectedWell = '';
  modelForm.dataParam = '';
  wellOptions.value = [];
  dataParams.value = [];
  previewData.value = [];
  
  loadingSchemas.value = true;
  try {
    const selectedSource = dataSources.value.find(s => s.id === selectedSourceId.value);
    if (!selectedSource) return;
    
    const response = await api.post('/api/database/schemas', selectedSource);
    if (response.data.success) {
      schemas.value = response.data.data;
      // 默认选择 public 或第一个
      if (schemas.value.length > 0) {
        selectedSchema.value = schemas.value.includes('public') ? 'public' : schemas.value[0];
      }
    } else {
      ElMessage.error(`获取Schema列表失败: ${response.data.error}`);
    }
  } catch (error) {
    console.error(`请求Schema列表时出错: ${error.message}`);
  } finally {
    loadingSchemas.value = false;
  }
};

// 3. 根据 source_id 和 schema 获取数据表列表
const fetchTables = async () => {
  if (!selectedSourceId.value || !selectedSchema.value) return;
  
  // 重置后续选择
  modelForm.dataTable = '';
  modelForm.selectedWell = '';
  modelForm.dataParam = '';
  wellOptions.value = [];
  dataParams.value = [];
  previewData.value = [];
  
  loadingTables.value = true;
  try {
    const selectedSource = dataSources.value.find(s => s.id === selectedSourceId.value);
    if (!selectedSource) return;
    
    // --- MODIFICATION: Use apiService with schema parameter ---
    const response = await api.post('/api/database/tables', {
      ...selectedSource,
      schema: selectedSchema.value
    });
    if (response.data.success) {
      dataTables.value = response.data.data.map(table => ({
        label: table.description || table.name, 
        value: table.name
      }));
    } else {
      ElMessage.error(`获取数据表失败: ${response.data.error}`);
    }
  } catch (error) {
    console.error(`请求数据表列表时出错: ${error.message}`);
  } finally {
    loadingTables.value = false;
  }
};

// 4. 获取表的字段列表
const fetchTableFields = async (tableName) => {
  if (!tableName || !selectedSourceId.value || !selectedSchema.value) return;
  try {
    const selectedSource = dataSources.value.find(s => s.id === selectedSourceId.value);
    if (!selectedSource) return;
    
    const requestData = {
      ...selectedSource,
      schema: selectedSchema.value,
      table_name: tableName
    };
    
    const response = await api.post('/api/database/fields', requestData);
    if (response.data.success) {
      availableFields.value = response.data.data;
      // 自动选择第一个匹配的井名字段
      if (wellFields.value.length <= 0) {
        selectedWellField.value = '';
        ElMessage.warning('未找到井名相关字段，请手动选择');
      }
    } else {
      ElMessage.error(`获取字段列表失败: ${response.data.error}`);
      availableFields.value = [];
      selectedWellField.value = '';
    }
  } catch (error) {
    console.error('获取字段列表失败:', error);
    ElMessage.error('获取字段列表失败');
    availableFields.value = [];
    selectedWellField.value = '';
  }
};

// 5. 获取井列表
const fetchWells = async (wellFieldName) => {
  if (!wellFieldName || !modelForm.dataTable || !selectedSourceId.value || !selectedSchema.value) return;
  loadingWells.value = true;
  try {
    const response = await api.get('/api/database/field-values', {
      params: {
        source_id: selectedSourceId.value,
        schema: selectedSchema.value,
        table_name: modelForm.dataTable,
        field_name: wellFieldName
      }
    });
    if (response.data.success) {
      wellOptions.value = response.data.data.map(well => ({label: well, value: well}));
    } else {
      ElMessage.warning(`获取井列表失败: ${response.data.error}`);
      wellOptions.value = [];
    }
  } catch (error) {
    console.error(`请求井列表时出错: ${error.message}`);
    ElMessage.warning(`请求井列表时出错`);
    wellOptions.value = [];
  } finally {
    loadingWells.value = false;
  }
};

// 6. 获取参数列表
const fetchParams = async (tableName) => {
  if (!tableName || !selectedSourceId.value || !selectedSchema.value) return;
  loadingParams.value = true;
  try {
    const selectedSource = dataSources.value.find(s => s.id === selectedSourceId.value);
    if (!selectedSource) return;
    
    // --- MODIFICATION: Use api with schema parameter ---
    const response = await api.post('/api/database/fields', {
        ...selectedSource,
        schema: selectedSchema.value,
        table_name: tableName
    });
    if (response.data.success) {
      const allColumns = response.data.data.map(fieldInfo => ({
        name: fieldInfo.name,
        description: fieldInfo.description || fieldInfo.name
      }));
      const sknoIndex = allColumns.findIndex(f => f.name === 'skno');
      const filteredColumns = sknoIndex !== -1 ? allColumns.slice(sknoIndex + 1) : allColumns;
      dataParams.value = filteredColumns.map(param => ({
        label: param.description, 
        value: param.name
      }));
    } else {
      ElMessage.error(`获取参数列表失败: ${response.data.error}`);
    }
  } catch (error) {
    console.error(`请求参数列表时出错: ${error.message}`);
  } finally {
    loadingParams.value = false;
  }
};

// 6. 获取数据预览
const fetchPreviewData = async () => {
  if (!modelForm.dataTable || !modelForm.dataParam || !selectedSourceId.value || !selectedSchema.value) return;
  loadingPreview.value = true;
  try {
    // 动态构建预览字段列表，优先使用常见字段，不存在则跳过
    const commonFields = ['guid', 'month', 'wid', 'date'];
    const previewFields = [...commonFields, modelForm.dataParam];
    // 去重（如果 dataParam 已经在 commonFields 中）
    const uniqueFields = [...new Set(previewFields)];
    
    const payload = {
      data_source_id: selectedSourceId.value,
      schema: selectedSchema.value,
      table_name: modelForm.dataTable,
      fields: uniqueFields,
      limit: 20
    };
    // --- MODIFICATION: Use apiService ---
    const response = await apiService.database.previewData(payload);
    if (response.data.success) {
      previewData.value = response.data.data;
      if (previewData.value.length > 0) {
        previewColumns.value = Object.keys(previewData.value[0]).map(key => ({
          prop: key,
          label: key,
          width: 100
        }));
      } else {
        previewColumns.value = [];
      }
    } else {
      // 如果失败，可能是某些字段不存在，尝试只预览选定的参数
      console.warn(`使用全部字段预览失败，尝试只使用选定参数: ${response.data.error}`);
      const fallbackPayload = {
        data_source_id: selectedSourceId.value,
        schema: selectedSchema.value,
        table_name: modelForm.dataTable,
        fields: [modelForm.dataParam],
        limit: 20
      };
      const fallbackResponse = await apiService.database.previewData(fallbackPayload);
      if (fallbackResponse.data.success) {
        previewData.value = fallbackResponse.data.data;
        if (previewData.value.length > 0) {
          previewColumns.value = Object.keys(previewData.value[0]).map(key => ({
            prop: key,
            label: key,
            width: 100
          }));
        }
      } else {
        ElMessage.error(`获取预览数据失败: ${fallbackResponse.data.error}`);
      }
    }
  } catch (error) {
    console.error(`请求预览数据时出错: ${error.message}`);
    ElMessage.warning(`请求预览数据时出错。某些字段可能不存在于当前数据表中。`);
  } finally {
    loadingPreview.value = false;
  }
};

// 7. 运行异常检测
const runAnomalyDetection = async () => {
  if (!selectedSourceId.value || !selectedSchema.value || !modelForm.dataTable || !modelForm.selectedWell || !modelForm.dataParam) {
    ElMessage.warning('请先完整选择数据源、Schema、数据表、井和参数');
    return;
  }
  
  // 验证时间范围
  if (modelForm.startDate && modelForm.endDate && modelForm.startDate > modelForm.endDate) {
    ElMessage.warning('开始时间不能晚于结束时间');
    return;
  }
  
  isDetecting.value = true;
  anomalyData.value = [];
  try {
    const payload = {
      data_source_id: selectedSourceId.value,
      schema: selectedSchema.value,
      table_name: modelForm.dataTable,
      well_id: modelForm.selectedWell,
      parameter: modelForm.dataParam,
      limit: modelForm.dataLimit,  // 添加数据量限制
    };
    
    // 添加时间范围参数（如果设置了）
    if (modelForm.startDate) {
      payload.start_date = modelForm.startDate;
    }
    if (modelForm.endDate) {
      payload.end_date = modelForm.endDate;
    }
    // 添加时间字段参数
    if (modelForm.dateField) {
      payload.date_field = modelForm.dateField;
    }
    
    // 构建提示信息
    let infoMsg = '';
    if (modelForm.startDate || modelForm.endDate) {
      const timeRange = `${modelForm.startDate || '最早'} 至 ${modelForm.endDate || '最新'}`;
      if (modelForm.dataLimit) {
        infoMsg = `正在分析时间范围 ${timeRange} 内最近 ${modelForm.dataLimit.toLocaleString()} 条数据...`;
      } else {
        infoMsg = `正在分析时间范围 ${timeRange} 内的全部数据...`;
      }
    } else {
      if (modelForm.dataLimit) {
        infoMsg = `正在分析最近 ${modelForm.dataLimit.toLocaleString()} 条数据...`;
      } else {
        infoMsg = '正在分析全部数据，这可能需要较长时间...';
      }
    }
    ElMessage.info(infoMsg);
    
    // --- MODIFICATION: Use apiService ---
    const response = await apiService.lstmAnomaly.detectForUI(payload);

    if (response.data && response.data.success) {
      const anomalies = response.data.anomalies || [];
      const totalPoints = Number(response.data.total_points) || 0;
      anomalyData.value = anomalies.map(anomaly => ({
        parameter: modelForm.dataParam,
        rawValue: anomaly.value,
        unit: '',
        type: anomaly.type,
        timestamp: anomaly.timestamp
      }));
      // 更新统计信息...
      if (totalPoints > 0) {
        const missingPoints = anomalies.filter(a => a.type === '数据缺失').length;
        const validPoints = totalPoints - missingPoints;
        const completeness = (validPoints / totalPoints) * 100;
        const modelAnomalies = anomalies.filter(a => a.type === '模型检测异常').length;
        const errorRate = validPoints > 0 ? (modelAnomalies / validPoints) * 100 : 0;
        const cappedErrorImpact = Math.min(errorRate * 10, 100);
        const score = (completeness * 0.7) + ((100 - cappedErrorImpact) * 0.3);

        overviewStats.value[0].value = completeness.toFixed(1);
        overviewStats.value[1].value = anomalies.length;
        overviewStats.value[2].value = errorRate.toFixed(2);
        dataQualityScore.value = Math.max(0, Math.min(100, Math.round(score)));
      } else {
        overviewStats.value.forEach(stat => stat.value = 0);
        dataQualityScore.value = 0;
      }
      ElMessage.success(`检测完成，共分析 ${totalPoints} 个数据点，发现 ${anomalies.length} 个异常`);
    } else {
      ElMessage.error(`异常检测失败: ${response.data.error || '未知错误'}`);
    }
  } catch (error) {
    console.error("请求异常检测时出错:", error);
    // No need for a redundant ElMessage.error here, the api.js interceptor handles it.
  } finally {
    isDetecting.value = false;
  }
};

// --- 辅助函数 ---
const getTagType = (type) => {
  switch (type) {
    case '数据缺失': return 'warning';
    case '阈值超标': return 'danger';
    case '数据中断': return 'info';
    default: return 'danger';
  }
};

// 快捷设置时间范围
const setTimeRange = (range) => {
  const now = new Date();
  const formatDateTime = (date) => {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    const seconds = String(date.getSeconds()).padStart(2, '0');
    return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
  };
  
  switch (range) {
    case 'today':
      // 今天：从今天 00:00:00 到现在
      const todayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate(), 0, 0, 0);
      modelForm.startDate = formatDateTime(todayStart);
      modelForm.endDate = formatDateTime(now);
      ElMessage.success('已设置为今天的数据');
      break;
    case 'week':
      // 近7天
      const weekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
      modelForm.startDate = formatDateTime(weekAgo);
      modelForm.endDate = formatDateTime(now);
      ElMessage.success('已设置为近7天的数据');
      break;
    case 'month':
      // 近30天
      const monthAgo = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
      modelForm.startDate = formatDateTime(monthAgo);
      modelForm.endDate = formatDateTime(now);
      ElMessage.success('已设置为近30天的数据');
      break;
  }
};

const resetParameters = () => {
  modelForm.dataLimit = 5000;
  modelForm.startDate = null;
  modelForm.endDate = null;
  ElMessage.success('参数已重置');
};
const saveModelConfig = () => ElMessage.success('配置保存成功');

// --- 导出报告功能 ---
const exportReport = () => {
  if (anomalyData.value.length === 0) {
    ElMessage.warning('暂无检测结果数据可导出');
    return;
  }
  
  try {
    // 生成报告内容
    const reportTitle = '钻井数据质检报告';
    const reportTime = new Date().toLocaleString('zh-CN');
    
    let content = `${reportTitle}\n`;
    content += `=`.repeat(60) + '\n\n';
    content += `生成时间：${reportTime}\n`;
    content += `数据源：${dataSources.value.find(s => s.id === selectedSourceId.value)?.name || '未知'}\n`;
    content += `Schema：${selectedSchema.value}\n`;
    content += `数据表：${modelForm.dataTable}\n`;
    content += `井号：${modelForm.selectedWell}\n`;
    content += `参数：${modelForm.dataParam}\n`;
    
    // 添加时间范围信息
    if (modelForm.startDate || modelForm.endDate) {
      content += `时间范围：${modelForm.startDate || '最早'} 至 ${modelForm.endDate || '最新'}\n`;
    }
    if (modelForm.dataLimit) {
      content += `数据量限制：最近 ${modelForm.dataLimit.toLocaleString()} 条\n`;
    }
    
    content += `\n`;
    content += `数据质量评分：${dataQualityScore.value}/100\n`;
    content += `数据完整率：${overviewStats.value[0].value}%\n`;
    content += `今日异常点：${overviewStats.value[1].value}\n`;
    content += `错误率：${overviewStats.value[2].value}%\n`;
    content += `\n${'='.repeat(60)}\n\n`;
    
    // 异常检测结果详情
    content += `异常检测结果详情（共 ${anomalyData.value.length} 条）\n`;
    content += `${'-'.repeat(60)}\n\n`;
    
    anomalyData.value.forEach((item, index) => {
      content += `[${index + 1}] ${item.parameter}：${item.rawValue} ${item.unit}\n`;
      content += `    异常类型：${item.type}\n`;
      if (item.timestamp) {
        content += `    时间戳：${item.timestamp}\n`;
      }
      content += `\n`;
    });
    
    content += `${'='.repeat(60)}\n`;
    content += `报告结束\n`;
    
    // 创建Blob并下载
    const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    
    // 生成文件名
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5);
    link.download = `钻井数据质检报告_${modelForm.selectedWell}_${modelForm.dataParam}_${timestamp}.txt`;
    
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    
    ElMessage.success('报告导出成功');
  } catch (error) {
    console.error('导出报告失败:', error);
    ElMessage.error('导出报告失败，请重试');
  }
};

// --- 逻辑控制与生命周期 (已重构) ---

onMounted(async () => {
  modelForm.name = selectedModel.value.name;
  modelForm.description = selectedModel.value.description;
  // 页面加载时，首先获取所有数据源
  await fetchDataSources();
});

// 监听数据源变化 -> 获取Schema列表
watch(selectedSourceId, (newSourceId) => {
  // 清空所有下游选择
  selectedSchema.value = '';
  schemas.value = [];
  modelForm.dataTable = '';
  modelForm.selectedWell = '';
  modelForm.dataParam = '';
  dataTables.value = [];
  wellOptions.value = [];
  dataParams.value = [];
  previewData.value = [];

  if (newSourceId) {
    loadSchemas();
  }
});

// 监听Schema变化 -> 获取数据表
watch(selectedSchema, (newSchema) => {
  // 清空下游选择
  modelForm.dataTable = '';
  modelForm.selectedWell = '';
  modelForm.dataParam = '';
  dataTables.value = [];
  wellOptions.value = [];
  dataParams.value = [];
  previewData.value = [];

  if (newSchema) {
    fetchTables();
  }
});

// 监听数据表变化 -> 获取字段列表、井和参数
watch(() => modelForm.dataTable, (newTable) => {
  // 清空下游选择
  selectedWellField.value = '';
  modelForm.selectedWell = '';
  modelForm.dataParam = '';
  availableFields.value = [];
  wellOptions.value = [];
  dataParams.value = [];
  previewData.value = [];

  if (newTable) {
    fetchTableFields(newTable);
    fetchParams(newTable);
  }
});

// 监听井名字段变化 -> 获取井列表
watch(() => selectedWellField.value, (newWellField) => {
  modelForm.selectedWell = '';
  wellOptions.value = [];
  
  if (newWellField) {
    fetchWells(newWellField);
  }
});

// 监听井或参数变化 -> 更新数据预览
watch(() => [modelForm.selectedWell, modelForm.dataParam], () => {
  fetchPreviewData();
});
</script>

<style scoped>
/* 样式与原文件保持一致，此处省略以减少篇幅 */
.model-container {
  padding: 0;
}

/* 新增样式 */
.drilling-data-content {
  padding: 10px;
}

.drilling-data-content p {
  margin-bottom: 15px;
  color: #606266;
  font-size: 14px;
}

.data-quality-stats {
  margin: 20px 0;
}

.stat-card {
  text-align: center;
  padding: 10px;
  background-color: #f8f9fa;
  border-radius: 4px;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: #409EFF;
}

.stat-label {
  font-size: 12px;
  color: #909399;
}

.progress-labels {
  display: flex;
  justify-content: space-between;
  margin-top: 5px;
  font-size: 12px;
  color: #606266;
}

.anomaly-model-card {
  height: 100%;
}

.model-display {
  text-align: center;
  padding: 15px 0;
}

.model-icon {
  margin-bottom: 10px;
  color: #409EFF;
}

.model-name {
  font-size: 20px;
  font-weight: bold;
  margin-bottom: 5px;
}

.model-desc {
  font-size: 12px;
  color: #909399;
  margin-bottom: 10px;
}

.model-status {
  margin-top: 15px;
}

/* 异常数据展示样式 */
.anomaly-value {
  display: flex;
  align-items: center;
}

.anomaly-value .label {
  font-weight: bold;
  margin-right: 5px;
}

.anomaly-value .value {
  font-weight: bold;
  color: #e53935;
}

.anomaly-value .unit {
  font-size: 0.8em;
  color: #888;
}

/* 原有样式保持不变 */
.parameter-panel-card,
.data-preview-card,
.anomaly-results-card {
  height: 600px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
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

/* 新增配置区域样式 */
.config-section {
  margin-bottom: 20px;
}

.config-item {
  margin-bottom: 15px;
}

.config-label {
  font-weight: bold;
  margin-bottom: 8px;
  color: #606266;
  font-size: 14px;
}

.el-select {
  width: 100%;
}

/* 字段选择器选项样式 */
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
  margin-left: 8px;
}
</style>