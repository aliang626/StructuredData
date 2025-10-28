<template>
  <div class="llm-quality-check">
    <!-- 页面标题 -->
    <div class="page-header">
      <h2>文本数据质检</h2>
      <p>基于规则库对文本数据进行质量检测和分析</p>
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
          
          <el-form :model="qualityForm" label-position="top" class="config-form">
            <!-- 知识库信息 -->
            <el-form-item label="知识库">
              <el-input 
                v-model="knowledgeBaseInfo" 
                disabled 
                style="width: 100%" 
                size="large"
                placeholder="Excel知识库（文本型知识库.xlsx）"
              >
                <template #prepend>Excel知识库</template>
              </el-input>
              <el-button 
                type="text" 
                @click="previewKnowledgeBase" 
                style="margin-top: 8px; font-size: 12px;"
                size="small"
              >
                预览知识库内容
              </el-button>
            </el-form-item>

            <!-- 数据源选择 -->
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

            <!-- 数据表选择 -->
            <el-form-item label="数据表" required>
              <el-select 
                v-model="qualityForm.tableName" 
                placeholder="选择数据表"
                @change="loadFields"
                style="width: 100%"
                size="large"
                filterable
              >
                <el-option
                  v-for="table in availableTables"
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
                @change="onFieldsChange"
              >
                <el-option
                  v-for="field in availableFields"
                  :key="field.name"
                  :label="field.description"
                  :value="field.name"
                >
                  <div class="option-content">
                    <span class="option-name">{{ field.description }}</span>
                    <span class="option-desc" v-if="field.description !== field.name">{{ field.name }}</span>
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
                      <span class="option-desc">{{ field.field_type }} - 分公司字段</span>
                    </div>
                  </el-option>
                </el-select>
              </el-form-item>
              
              <!-- 分公司值选择 -->
              <el-form-item v-if="selectedCompanyField" label="分公司值">
                <el-select 
                  v-model="selectedCompanyValue" 
                  placeholder="选择要检测的分公司"
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
                    <div class="option-name">{{ company }}</div>
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

            <!-- 批处理配置 -->
            <el-form-item label="批处理大小">
              <el-input-number
                v-model="qualityForm.batchSize"
                :min="10"
                :max="1000"
                :step="10"
                placeholder="每批处理的数据条数"
                style="width: 100%"
                size="large"
              />
              <div class="form-item-tip">
                <el-icon><InfoFilled /></el-icon>
                <span>建议值：100-300条，全量数据时可适当增加</span>
              </div>
            </el-form-item>

            <!-- 字段映射 -->
            <el-form-item v-if="qualityForm.fields && qualityForm.fields.length > 0" label="字段映射" class="mapping-form-item">
              <div class="field-mapping-section">
                <div class="mapping-header">
                  <div class="header-left">
                    <el-icon><EditPen /></el-icon>
                    <span>请为英文字段提供中文描述，以便匹配知识库规则</span>
                  </div>
                  <div class="header-actions">
                    <el-button type="primary" @click="autoSuggestMappings" size="small" plain>
                      <el-icon><Star /></el-icon>
                      智能建议
                    </el-button>
                    <el-button type="warning" @click="clearAllMappings" size="small" plain>
                      清空全部
                    </el-button>
                  </div>
                </div>
                
                <el-table 
                  :data="fieldMappings" 
                  border 
                  size="small"
                  class="mapping-table"
                  :max-height="tableExpanded ? 600 : 300"
                  style="width: 100%"
                  :fit="true"
                >
                  <el-table-column prop="englishField" label="英文字段名" width="150" show-overflow-tooltip />
                  <el-table-column label="中文描述" min-width="200">
                    <template #default="{ row }">
                      <el-autocomplete
                        v-model="row.chineseDescription"
                        :fetch-suggestions="(query, cb) => getSuggestions(query, cb)"
                        placeholder="输入中文字段描述"
                        style="width: 100%"
                        size="small"
                        @select="(item) => onSuggestionSelect(row, item)"
                        @input="() => updateFieldMappingStatus(row)"
                        clearable
                      >
                        <template #suffix>
                          <el-icon class="el-input__icon"><Search /></el-icon>
                        </template>
                      </el-autocomplete>
                    </template>
                  </el-table-column>
                  <el-table-column label="匹配状态" width="100" align="center">
                    <template #default="{ row }">
                      <el-tag 
                        :type="row.matchStatus === 'matched' ? 'success' : (row.matchStatus === 'partial' ? 'warning' : 'danger')"
                        size="small"
                        effect="dark"
                      >
                        {{ row.matchStatus === 'matched' ? '已匹配' : (row.matchStatus === 'partial' ? '部分' : '未匹配') }}
                      </el-tag>
                    </template>
                  </el-table-column>
                  <el-table-column label="匹配的知识库规则" min-width="180" show-overflow-tooltip>
                    <template #default="{ row }">
                      <span v-if="row.matchedVariable" class="matched-rule">
                        {{ row.matchedVariable }}
                      </span>
                      <span v-else class="no-match">无匹配规则</span>
                    </template>
                  </el-table-column>
                  <el-table-column label="操作" width="80" align="center">
                    <template #default="{ row }">
                      <el-button 
                        size="small" 
                        type="text" 
                        @click="clearMapping(row)"
                        :disabled="!row.chineseDescription"
                      >
                        清空
                      </el-button>
                    </template>
                  </el-table-column>
                </el-table>
                
                <div class="mapping-summary">
                  <div class="summary-left">
                    <el-tag type="info" size="small">
                      总字段: {{ fieldMappings.length }}
                    </el-tag>
                    <el-tag type="success" size="small">
                      已映射: {{ mappedFieldsCount }}
                    </el-tag>
                    <el-tag type="warning" size="small">
                      未映射: {{ unmappedFieldsCount }}
                    </el-tag>
                  </div>
                  <div class="summary-right">
                    <el-button 
                      size="small" 
                      type="text" 
                      @click="toggleTableExpanded"
                      v-if="fieldMappings.length > 3"
                    >
                      {{ tableExpanded ? '收起表格' : '展开表格' }}
                    </el-button>
                  </div>
                </div>
              </div>
            </el-form-item>

            <!-- 开始检测按钮 -->
            <el-form-item>
                <el-button 
                  type="primary" 
                  @click="runQualityCheck" 
                :disabled="!canRunCheck"
                :loading="checking"
                  size="large" 
                  style="width: 100%"
                >
                <el-icon><Search /></el-icon>
                {{ checking ? '检测中...' : '开始质量检测' }}
                </el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>

      <!-- 右侧结果面板 -->
      <el-col :span="16">
        <el-card class="result-panel" shadow="hover">
          <template #header>
            <div class="card-header">
              <div class="header-left">
                <el-icon class="header-icon"><DataLine /></el-icon>
                <span class="header-title">检测结果</span>
              </div>
              <div class="header-right" v-if="qualityResults.length > 0">
                <el-dropdown @command="handleExportCommand" size="small">
                  <el-button size="small" type="warning">
                    <el-icon><Download /></el-icon>
                    导出数据
                    <el-icon class="el-icon--right"><ArrowDown /></el-icon>
                  </el-button>
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item command="failed">
                        导出不合格数据 ({{ failedRecordsCount }})
                      </el-dropdown-item>
                      <el-dropdown-item command="all">
                        导出全部数据 ({{ currentResult.total_records || 0 }})
                      </el-dropdown-item>
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
              </div>
            </div>
          </template>

          <!-- 检测进度 -->
          <div v-if="checking" class="progress-container">
            <el-progress
              :percentage="checkProgress"
              :status="checkProgress === 100 ? 'success' : ''"
              :stroke-width="8"
            />
            <p class="progress-text">{{ progressText }}</p>
                </div>

          <!-- 检测结果 -->
          <div v-else-if="qualityResults.length > 0" class="results-container">
            <!-- 统计卡片 -->
            <el-row :gutter="16" class="stats-cards">
              <el-col :span="6">
                <div class="stat-card total">
                  <div class="stat-number">{{ currentResult.total_records || 0 }}</div>
                  <div class="stat-label">总记录数</div>
                </div>
              </el-col>
              <el-col :span="6">
                <div class="stat-card passed">
                  <div class="stat-number">{{ currentResult.passed_records || 0 }}</div>
                  <div class="stat-label">通过记录</div>
              </div>
              </el-col>
              <el-col :span="6">
                <div class="stat-card failed">
                  <div class="stat-number">{{ currentResult.failed_records || 0 }}</div>
                  <div class="stat-label">失败记录</div>
                </div>
              </el-col>
              <el-col :span="6">
                <div class="stat-card rate">
                  <div class="stat-number">{{ (currentResult.pass_rate || 0).toFixed(1) }}%</div>
                  <div class="stat-label">通过率</div>
                </div>
              </el-col>
            </el-row>

            <!-- 详细报告表格 -->
            <el-table
              :data="currentResult.reports || []"
              style="width: 100%; margin-top: 20px"
              max-height="500"
            >
              <el-table-column prop="rule_name" label="规则名称" width="200" />
              <el-table-column prop="field_name" label="字段" width="120" />
              <el-table-column prop="rule_type" label="规则类型" width="120" />
              <el-table-column prop="passed_count" label="通过数" width="80" align="center" />
              <el-table-column prop="failed_count" label="失败数" width="80" align="center" />
              <el-table-column label="操作" width="100" align="center">
                <template #default="{ row }">
                  <el-button 
                    v-if="row.failed_count > 0"
                    type="text" 
                    size="small" 
                    @click="showErrorDetails(row)"
                  >
                    查看详情
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
            
            <!-- 不合格数据表格 -->
            <div v-if="failedRecordsCount > 0" class="failed-data-section">
              <div class="section-header">
                <h4>不合格数据详情</h4>
                <el-button 
                  type="primary" 
                  size="small" 
                  @click="loadFailedData"
                  :loading="loadingFailedData"
                >
                  加载不合格数据
                </el-button>
              </div>
              
              <div v-if="failedData.length > 0" class="failed-data-table">
                <el-table :data="failedData" max-height="400" style="width: 100%">
                  <el-table-column prop="row" label="行号" width="80" align="center" />
                  <el-table-column prop="field" label="字段名" width="120" />
                  <el-table-column prop="value" label="原始值" width="200" show-overflow-tooltip />
                  <el-table-column prop="rule" label="规则名称" width="150" />
                  <el-table-column prop="message" label="错误信息" show-overflow-tooltip />
                  <el-table-column prop="result" label="结果" width="80" align="center">
                    <template #default="{ row }">
                      <el-tag type="danger" size="small">{{ row.result }}</el-tag>
                    </template>
                  </el-table-column>
                </el-table>
                
                <!-- 分页组件 -->
                <div v-if="failedDataPagination.totalPages > 1" class="pagination-container">
                  <div class="pagination-info">
                    <span>共 {{ failedDataPagination.total }} 条不合格记录，第 {{ failedDataPagination.page }}/{{ failedDataPagination.totalPages }} 页</span>
                  </div>
                  <div class="pagination-controls">
                    <el-button 
                      @click="changeFailedDataPage(failedDataPagination.page - 1)" 
                      :disabled="!failedDataPagination.hasPrev"
                      size="small"
                    >
                      上一页
                    </el-button>
                    
                    <el-pagination
                      :current-page="failedDataPagination.page"
                      :page-size="failedDataPagination.pageSize"
                      :total="failedDataPagination.total"
                      :page-sizes="[10, 20, 50, 100]"
                      layout="total, sizes, prev, pager, next, jumper"
                      @size-change="changeFailedDataPageSize"
                      @current-change="changeFailedDataPage"
                      small
                    />
                    
                    <el-button 
                      @click="changeFailedDataPage(failedDataPagination.page + 1)" 
                      :disabled="!failedDataPagination.hasNext"
                      size="small"
                    >
                      下一页
                    </el-button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 空状态 -->
          <div v-else class="empty-state">
            <el-empty description="暂无检测结果">
              <el-button type="primary" @click="runQualityCheck" :disabled="!canRunCheck">
                开始质量检测
              </el-button>
            </el-empty>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 错误详情对话框 -->
    <el-dialog v-model="errorDialogVisible" title="错误详情" width="60%">
      <el-table :data="errorDetails" max-height="400">
        <el-table-column prop="row" label="行号" width="80" />
        <el-table-column prop="value" label="错误值" width="200" />
        <el-table-column prop="message" label="错误信息" />
      </el-table>
    </el-dialog>

    <!-- 知识库预览对话框 -->
    <el-dialog v-model="knowledgeBaseVisible" title="知识库内容预览" width="70%">
      <!-- 搜索和过滤区域 -->
      <div class="search-section" style="margin-bottom: 16px;">
        <el-row :gutter="16">
          <el-col :span="8">
            <el-input
              v-model="knowledgeBaseSearch"
              placeholder="搜索变量名或描述..."
              clearable
              @input="onKnowledgeBaseSearchInput"
              style="width: 100%"
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
          </el-col>
          <el-col :span="6">
            <el-select
              v-model="knowledgeBaseCategory"
              placeholder="选择类别"
              clearable
              @change="onKnowledgeBaseSearch"
              style="width: 100%"
            >
              <el-option
                v-for="category in availableCategories"
                :key="category"
                :label="category"
                :value="category"
              />
            </el-select>
          </el-col>
          <el-col :span="4">
            <el-button @click="onKnowledgeBaseSearch" type="primary">
              搜索
            </el-button>
          </el-col>
        </el-row>
        <div style="margin-top: 8px; color: #666; font-size: 12px;">
          共 {{ knowledgeBaseTotalCount }} 条记录，当前显示 {{ knowledgeBaseFilteredCount }} 条
        </div>
      </div>
      
      <el-table :data="knowledgeBaseData" max-height="500">
        <el-table-column prop="Variable" label="变量名" width="150" />
        <el-table-column prop="Category" label="类别" width="120" />
        <el-table-column prop="质量规范描述" label="质量规范描述" />
      </el-table>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="knowledgeBaseVisible = false">关闭</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Setting, Search, DataLine, Download, EditPen, Star, ArrowDown, InfoFilled, Location } from '@element-plus/icons-vue'
import axios from 'axios'

// 响应式数据
const qualityForm = ref({
  dataSource: null,
  tableName: '',
  fields: [],
  batchSize: 100  // 默认批处理大小
})

const knowledgeBaseInfo = ref('文本型知识库.xlsx')
const selectedDataSource = ref('')  // 数据源选择状态
const dataSources = ref([])
const availableTables = ref([])
const availableFields = ref([])
const qualityResults = ref([])
const checking = ref(false)
const checkProgress = ref(0)
const progressText = ref('')
const errorDialogVisible = ref(false)
const errorDetails = ref([])
const knowledgeBaseVisible = ref(false)
const knowledgeBaseData = ref([])
const knowledgeBaseSearch = ref('')
const knowledgeBaseCategory = ref('')
const knowledgeBaseTotalCount = ref(0)
const knowledgeBaseFilteredCount = ref(0)
const availableCategories = ref([])
const fieldMappings = ref([])
const knowledgeBaseVariables = ref([])
const tableExpanded = ref(false)

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

// 不合格数据相关状态
const failedData = ref([])
const loadingFailedData = ref(false)
const failedDataPagination = ref({
  page: 1,
  pageSize: 10,
  total: 0,
  totalPages: 0,
  hasNext: false,
  hasPrev: false
})

// 计算属性
const canRunCheck = computed(() => {
  return qualityForm.value.dataSource && 
         qualityForm.value.tableName &&
         (!fieldMappings.value.length || mappedFieldsCount.value > 0)
})

const currentResult = computed(() => {
  return qualityResults.value[0] || {}
})

const mappedFieldsCount = computed(() => {
  return fieldMappings.value.filter(m => m.chineseDescription && m.chineseDescription.trim()).length
})

const unmappedFieldsCount = computed(() => {
  return fieldMappings.value.length - mappedFieldsCount.value
})

const failedRecordsCount = computed(() => {
  if (!currentResult.value || !currentResult.value.results) return 0
  return currentResult.value.results.filter(item => 
    item.结果 === '不合格' || item.结果 === '检查失败'
  ).length
})

// 分公司字段计算属性
const companyFields = computed(() => {
  return availableFields.value.filter(field => 
    field.name.toLowerCase().includes('公司') ||
    field.name.toLowerCase().includes('branch') ||
    field.name.toLowerCase().includes('company') ||
    field.name.toLowerCase().includes('部门') ||
    field.name.toLowerCase().includes('dept') ||
    field.name.toLowerCase().includes('区域') ||
    field.name.toLowerCase().includes('area') ||
    field.name.toLowerCase().includes('地区') ||
    field.name.toLowerCase().includes('region')
  )
})

// 油气田字段计算属性
const oilfieldFields = computed(() => {
  const oilfieldKeywords = ['field', 'oilfield', 'gasfield', '油田', '气田', '油气田', 'block', '区块', 'area', '工区', 'reserve', '储层']
  return availableFields.value.filter(field => {
    const fieldName = field.name.toLowerCase()
    return oilfieldKeywords.some(keyword => fieldName.includes(keyword.toLowerCase()))
  })
})

// 井名字段计算属性
const wellFields = computed(() => {
  const wellKeywords = ['well', 'wellname', '井', '井名', 'wellid', 'well_id', 'well_name', 'hole', '钻井', 'borehole']
  return availableFields.value.filter(field => {
    const fieldName = field.name.toLowerCase()
    return wellKeywords.some(keyword => fieldName.includes(keyword.toLowerCase()))
  })
})

// 方法
// 预览知识库
const previewKnowledgeBase = async () => {
  try {
    const response = await axios.get('/api/quality/knowledge-base/preview')
    if (response.data.success) {
      knowledgeBaseData.value = response.data.data.entries
      knowledgeBaseTotalCount.value = response.data.data.total_count
      knowledgeBaseFilteredCount.value = response.data.data.filtered_count
      knowledgeBaseVisible.value = true
      
      // 加载可用类别
      await loadAvailableCategories()
      
      ElMessage.success(`加载了 ${response.data.data.total_count} 条知识库记录`)
    }
  } catch (error) {
    ElMessage.error('加载知识库失败')
  }
}

// 加载可用类别
const loadAvailableCategories = async () => {
  try {
    const response = await axios.get('/api/quality/knowledge-base/categories')
    if (response.data.success) {
      availableCategories.value = response.data.data.categories
    }
  } catch (error) {
    console.error('加载类别失败:', error)
  }
}

// 防抖搜索
let searchTimeout = null
const debouncedSearch = () => {
  if (searchTimeout) {
    clearTimeout(searchTimeout)
  }
  searchTimeout = setTimeout(() => {
    onKnowledgeBaseSearch()
  }, 300)
}

// 知识库搜索输入处理
const onKnowledgeBaseSearchInput = () => {
  debouncedSearch()
}

// 知识库搜索
const onKnowledgeBaseSearch = async () => {
  try {
    const params = new URLSearchParams()
    if (knowledgeBaseSearch.value) {
      params.append('q', knowledgeBaseSearch.value)
    }
    if (knowledgeBaseCategory.value) {
      params.append('category', knowledgeBaseCategory.value)
    }
    params.append('limit', '100')  // 搜索时返回更多结果
    
    const response = await axios.get(`/api/quality/knowledge-base/search?${params.toString()}`)
    if (response.data.success) {
      knowledgeBaseData.value = response.data.data.results
      knowledgeBaseFilteredCount.value = response.data.data.filtered_count
    }
  } catch (error) {
    ElMessage.error('搜索失败')
  }
}

// 加载知识库变量列表
const loadKnowledgeBaseVariables = async () => {
  try {
    console.log('🔄 开始加载知识库变量...')
    
    // 首先尝试获取所有变量（使用最大限制）
    const response = await axios.get('/api/quality/knowledge-base/search?limit=200')
    if (response.data.success) {
      knowledgeBaseVariables.value = response.data.data.results.map(entry => ({
        value: entry.Variable,
        label: entry.Variable,
        category: entry.Category,
        description: entry['质量规范描述']
      }))
      
      console.log(`✅ 成功加载 ${knowledgeBaseVariables.value.length} 个知识库变量`)
      console.log('📋 前10个变量:', knowledgeBaseVariables.value.slice(0, 10).map(v => v.value))
      
      // 检查是否包含深度相关变量
      const depthVariables = knowledgeBaseVariables.value.filter(v => 
        v.value.includes('深度') || v.value.includes('井深')
      )
      console.log(`🔍 深度相关变量:`, depthVariables.map(v => v.value))
      
      // 如果没有找到深度变量，尝试专门搜索
      if (depthVariables.length === 0) {
        console.log('🔍 未找到深度变量，尝试专门搜索...')
        const depthResponse = await axios.get('/api/quality/knowledge-base/search?q=深度&limit=50')
        if (depthResponse.data.success) {
          const depthResults = depthResponse.data.data.results
          console.log(`🔍 深度搜索找到 ${depthResults.length} 个结果:`, depthResults.map(r => r.Variable))
          
          // 将深度相关变量添加到现有变量列表中
          depthResults.forEach(entry => {
            if (!knowledgeBaseVariables.value.find(v => v.value === entry.Variable)) {
              knowledgeBaseVariables.value.push({
                value: entry.Variable,
                label: entry.Variable,
                category: entry.Category,
                description: entry['质量规范描述']
              })
            }
          })
          
          console.log(`✅ 更新后知识库变量总数: ${knowledgeBaseVariables.value.length}`)
        }
      }
      
    } else {
      console.error('❌ 加载知识库变量失败:', response.data.error)
    }
  } catch (error) {
    console.error('❌ 加载知识库变量失败:', error)
  }
}

// 创建字段映射
const createFieldMappings = async () => {
  if (!qualityForm.value.fields || qualityForm.value.fields.length === 0) {
    fieldMappings.value = []
    return
  }
  
  // 确保知识库变量已加载
  if (knowledgeBaseVariables.value.length === 0) {
    await loadKnowledgeBaseVariables()
  }
  
  fieldMappings.value = qualityForm.value.fields.map(field => ({
    englishField: field,
    chineseDescription: '',
    matchStatus: 'unmapped',
    matchedVariable: '',
    confidence: 0
  }))
}

// 智能建议映射
const autoSuggestMappings = async () => {
  if (knowledgeBaseVariables.value.length === 0) {
    await loadKnowledgeBaseVariables()
  }
  
  fieldMappings.value.forEach(mapping => {
    if (!mapping.chineseDescription) {
      // 简单的智能匹配逻辑
      const suggestions = findSimilarVariables(mapping.englishField)
      if (suggestions.length > 0) {
        mapping.chineseDescription = suggestions[0].value
        mapping.matchedVariable = suggestions[0].value
        mapping.matchStatus = 'matched'
        mapping.confidence = suggestions[0].confidence
      }
    }
  })
  
  ElMessage.success('智能建议完成')
}

// 查找相似变量
const findSimilarVariables = (englishField) => {
  const field = englishField.toLowerCase()
  const suggestions = []
  
  console.log(`🔍 搜索字段: ${englishField} (${field})`)
  console.log(`📚 可用知识库变量数量: ${knowledgeBaseVariables.value.length}`)
  
  // 预定义的常见映射规则
  const commonMappings = {
    'name': ['名称', '姓名', '产品名称'],
    'date': ['日期', '时间', '生产日期'],
    'number': ['编号', '号码', '批次号'],
    'temperature': ['温度', '操作温度'],
    'pressure': ['压力', '操作压力'],
    'depth': ['深度', '井深', '深度零点'],
    'md': ['深度', '井深'],  // 添加md的映射
    'porosity': ['孔隙度', '有效孔隙度'],
    'permeability': ['渗透率'],
    'type': ['类型', '种类', '产品类型'],
    'code': ['代码', '编码', '类型代码'],
    'version': ['版本', '计划版本'],
    'creator': ['创建人', '编制人'],
    'reviewer': ['审核人', '复核人']
  }
  
  // 检查常见映射
  for (const [key, values] of Object.entries(commonMappings)) {
    if (field.includes(key)) {
      console.log(`✅ 找到关键词匹配: ${key}`)
      values.forEach(value => {
        console.log(`🔍 搜索变量: ${value}`)
        const variable = knowledgeBaseVariables.value.find(v => v.value.includes(value))
        if (variable) {
          console.log(`🎯 找到匹配变量: ${variable.value}`)
          suggestions.push({
            value: variable.value,
            confidence: 0.8
          })
        } else {
          console.log(`❌ 未找到匹配变量: ${value}`)
        }
      })
    }
  }
  
  // 如果没有找到常见映射，尝试模糊匹配
  if (suggestions.length === 0) {
    console.log(`🔍 尝试模糊匹配...`)
    knowledgeBaseVariables.value.forEach(variable => {
      const similarity = calculateSimilarity(field, variable.value)
      if (similarity > 0.3) {
        console.log(`🎯 模糊匹配: ${variable.value} (相似度: ${similarity.toFixed(2)})`)
        suggestions.push({
          value: variable.value,
          confidence: similarity
        })
      }
    })
  }
  
  console.log(`📋 最终建议数量: ${suggestions.length}`)
  return suggestions.sort((a, b) => b.confidence - a.confidence).slice(0, 3)
}

// 计算相似度（简单版本）
const calculateSimilarity = (str1, str2) => {
  const longer = str1.length > str2.length ? str1 : str2
  const shorter = str1.length > str2.length ? str2 : str1
  const editDistance = getEditDistance(longer, shorter)
  return (longer.length - editDistance) / longer.length
}

// 计算编辑距离
const getEditDistance = (a, b) => {
  if (a.length === 0) return b.length
  if (b.length === 0) return a.length
  
  const matrix = []
  for (let i = 0; i <= b.length; i++) {
    matrix[i] = [i]
  }
  for (let j = 0; j <= a.length; j++) {
    matrix[0][j] = j
  }
  
  for (let i = 1; i <= b.length; i++) {
    for (let j = 1; j <= a.length; j++) {
      if (b.charAt(i - 1) === a.charAt(j - 1)) {
        matrix[i][j] = matrix[i - 1][j - 1]
        } else {
        matrix[i][j] = Math.min(
          matrix[i - 1][j - 1] + 1,
          matrix[i][j - 1] + 1,
          matrix[i - 1][j] + 1
        )
      }
    }
  }
  
  return matrix[b.length][a.length]
}

// 获取自动完成建议
const getSuggestions = (queryString, cb) => {
  if (!queryString) {
    cb(knowledgeBaseVariables.value.slice(0, 20))  // 增加到20条
    return
  }
  
  const results = knowledgeBaseVariables.value.filter(variable => {
    const query = queryString.toLowerCase()
    const variableName = variable.value.toLowerCase()
    const description = variable.description ? variable.description.toLowerCase() : ''
    
    // 改进搜索逻辑：同时搜索变量名和描述
    return variableName.includes(query) || description.includes(query)
  }).slice(0, 20)  // 增加到20条
  
  cb(results)
}

// 选择建议后的处理
const onSuggestionSelect = (mapping, suggestion) => {
  mapping.chineseDescription = suggestion.value
  mapping.matchedVariable = suggestion.value
  mapping.matchStatus = 'matched'
  updateFieldMappingStatus(mapping)
}

// 更新字段映射状态
const updateFieldMappingStatus = (mapping) => {
  if (!mapping.chineseDescription || !mapping.chineseDescription.trim()) {
    mapping.matchStatus = 'unmapped'
    mapping.matchedVariable = ''
    return
  }
  
  // 检查是否精确匹配
  const exactMatch = knowledgeBaseVariables.value.find(v => 
    v.value === mapping.chineseDescription
  )
  
  if (exactMatch) {
    mapping.matchStatus = 'matched'
    mapping.matchedVariable = exactMatch.value
  } else {
    // 检查部分匹配
    const partialMatch = knowledgeBaseVariables.value.find(v => 
      v.value.includes(mapping.chineseDescription) || 
      mapping.chineseDescription.includes(v.value)
    )
    
    if (partialMatch) {
      mapping.matchStatus = 'partial'
      mapping.matchedVariable = partialMatch.value
    } else {
      mapping.matchStatus = 'unmapped'
      mapping.matchedVariable = ''
    }
  }
}

// 验证字段映射完整性
const validateFieldMappings = () => {
  if (!fieldMappings.value || fieldMappings.value.length === 0) {
    return { valid: true, message: '' }
  }
  
  const unmappedFields = fieldMappings.value.filter(m => 
    !m.chineseDescription || m.chineseDescription.trim() === '' || m.matchStatus === 'unmapped'
  )
  
  if (unmappedFields.length > 0) {
    return {
      valid: false,
      message: `还有 ${unmappedFields.length} 个字段未映射或映射无效，建议先完成字段映射`
    }
  }
  
    return { valid: true, message: '' }
}

// 清空字段映射
const clearMapping = (mapping) => {
  mapping.chineseDescription = ''
  mapping.matchStatus = 'unmapped'
  mapping.matchedVariable = ''
  mapping.confidence = 0
}

// 清空全部映射
const clearAllMappings = () => {
  fieldMappings.value.forEach(mapping => {
    clearMapping(mapping)
    })
  ElMessage.success('已清空所有字段映射')
}

// 切换表格展开状态
const toggleTableExpanded = () => {
  tableExpanded.value = !tableExpanded.value
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

    // 数据源变化处理
    const onDataSourceChange = async () => {
      if (!selectedDataSource.value) return
      
      // 根据选中的ID找到对应的数据源对象
      const selectedSource = dataSources.value.find(s => s.id === selectedDataSource.value)
      if (selectedSource) {
        qualityForm.value.dataSource = selectedSource
        console.log('数据源选择变化:', selectedSource)
        await loadTables()
      }
    }

    const loadTables = async () => {
  if (!qualityForm.value.dataSource) return
  
  try {
    const response = await axios.get(`/api/database/tables`, {
      params: {
        source_id: qualityForm.value.dataSource.id
      }
    })
    if (response.data.success) {
      availableTables.value = response.data.data
      // 清空之前的字段和表选择
      qualityForm.value.tableName = ''
              qualityForm.value.fields = []
        availableFields.value = []
        
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
  }
}

const loadFields = async () => {
  if (!qualityForm.value.dataSource || !qualityForm.value.tableName) return
  
  try {
    const response = await axios.get(`/api/database/fields`, {
      params: {
        source_id: qualityForm.value.dataSource.id,
        table_name: qualityForm.value.tableName
      }
    })
    if (response.data.success) {
      availableFields.value = response.data.data
      // 清空之前的字段选择和映射
              qualityForm.value.fields = []
        fieldMappings.value = []
        
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
    ElMessage.error('加载字段失败')
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
    // 获取分公司字段的唯一值
    const response = await axios.get(`/api/database/field-values`, {
      params: {
        source_id: qualityForm.value.dataSource.id,
        table_name: qualityForm.value.tableName,
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
        source_id: qualityForm.value.dataSource.id,
        table_name: qualityForm.value.tableName,
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
        source_id: qualityForm.value.dataSource.id,
        table_name: qualityForm.value.tableName,
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

// 监听字段选择变化
const onFieldsChange = async () => {
  createFieldMappings()
  if (knowledgeBaseVariables.value.length === 0) {
    await loadKnowledgeBaseVariables()
  }
}

    const runQualityCheck = async () => {
  if (!canRunCheck.value) {
    ElMessage.warning('请完善配置信息')
    return
  }
  
  // 验证字段映射
  const mappingValidation = validateFieldMappings()
  if (!mappingValidation.valid) {
    ElMessage.warning(mappingValidation.message)
    return
  }
  
  checking.value = true
  checkProgress.value = 0
  progressText.value = '开始文本数据质检...'
  
  try {
    // 分阶段显示进度
    progressText.value = '正在连接数据源...'
    checkProgress.value = 10
    
    await new Promise(resolve => setTimeout(resolve, 200))
    
    progressText.value = '正在加载内嵌知识库...'
    checkProgress.value = 20
    
    await new Promise(resolve => setTimeout(resolve, 200))
    
    // 显示字段映射信息
    if (fieldMappings.value.length > 0) {
      const mappedCount = fieldMappings.value.filter(m => m.matchStatus === 'matched').length
      progressText.value = `正在验证字段映射 (${mappedCount}/${fieldMappings.value.length})...`
      checkProgress.value = 30
      await new Promise(resolve => setTimeout(resolve, 200))
    }
    
    // 构建字段映射对象
    const fieldMappingDict = {}
    fieldMappings.value.forEach(mapping => {
      if (mapping.chineseDescription && mapping.chineseDescription.trim()) {
        fieldMappingDict[mapping.englishField] = mapping.chineseDescription
      }
    })
    
    // 估算处理时间（批处理模式，支持全量数据）
    const estimatedFieldCount = qualityForm.value.fields ? qualityForm.value.fields.length : 2
    // 由于支持全量数据，无法准确预估记录数，给出保守估计
    const estimatedRecords = 5000 // 保守估计5000条记录
    const estimatedBatches = Math.ceil((estimatedFieldCount * estimatedRecords) / qualityForm.value.batchSize) // 使用用户设置的批处理大小
    const estimatedTimeSeconds = Math.ceil(estimatedBatches * 2) // 每批约2秒
    
    progressText.value = `正在调用大模型进行批处理质检... (预估约${estimatedTimeSeconds}秒，${estimatedBatches}个批次，每批${qualityForm.value.batchSize}条，支持全量数据)`
    checkProgress.value = 40
    
    // 构建请求参数
    const requestData = {
      db_config: qualityForm.value.dataSource,
      table_name: qualityForm.value.tableName,
      fields: qualityForm.value.fields && qualityForm.value.fields.length ? qualityForm.value.fields : undefined,
      field_mappings: fieldMappingDict, // 添加字段映射
      batch_size: qualityForm.value.batchSize, // 批处理大小
      created_by: '用户'
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
    
    const response = await axios.post('/api/quality/text-check', requestData, {
      timeout: 300000 // 5分钟超时
    })
    
    checkProgress.value = 100
    progressText.value = '质检完成'
    
    if (response.data.success) {
      qualityResults.value = [response.data.data]
      
      // 显示调试信息（如果有的话）
      if (response.data.data.debug_logs && response.data.data.debug_logs.length > 0) {
        console.log('=== 质检调试信息 ===')
        response.data.data.debug_logs.forEach((log, index) => {
          console.log(`${index + 1}. ${log}`)
        })
        console.log('=====================')
        
        // 如果没有找到数据或字段匹配，给出提示
        const hasWarning = response.data.data.debug_logs.some(log => 
          log.includes('没有找到匹配的字段') || log.includes('数据库查询结果为空')
        )
        
        // 显示批处理信息
        const batchInfo = response.data.data.total_batches ? 
          `（批处理：${response.data.data.total_batches}个批次，每批${response.data.data.batch_size}条）` : ''
        
        if (hasWarning) {
          ElMessage.warning(`质检完成${batchInfo}，但请检查浏览器控制台的调试信息`)
        } else {
          ElMessage.success(`文本数据质检完成${batchInfo}`)
        }
      } else {
        ElMessage.success('文本数据质检完成')
      }
    } else {
      // 显示错误调试信息
      if (response.data.debug_logs && response.data.debug_logs.length > 0) {
        console.error('=== 质检错误调试信息 ===')
        response.data.debug_logs.forEach((log, index) => {
          console.error(`${index + 1}. ${log}`)
        })
        console.error('========================')
      }
      ElMessage.error(response.data.error || '质检失败')
        }
      } catch (error) {
    console.error('质检失败:', error)
    if (error.code === 'ECONNABORTED') {
      ElMessage.error('质检超时，请稍后重试')
    } else {
      ElMessage.error('文本质检失败：' + (error.response?.data?.error || error.message))
    }
      } finally {
    checking.value = false
  }
}

const showErrorDetails = (row) => {
  if (row.error_details) {
    errorDetails.value = JSON.parse(row.error_details)
    errorDialogVisible.value = true
  }
}

// 加载不合格数据
const loadFailedData = async () => {
  if (!currentResult.value || !currentResult.value.results) {
    ElMessage.warning('请先完成质检任务')
    return
  }
  
  loadingFailedData.value = true
  try {
    // 从质检结果中筛选不合格数据
    const allFailedData = currentResult.value.results.filter(item => 
      item.结果 === '不合格' || item.结果 === '检查失败'
    )
    
    // 计算分页
    const total = allFailedData.length
    const start_idx = (failedDataPagination.value.page - 1) * failedDataPagination.value.pageSize
    const end_idx = start_idx + failedDataPagination.value.pageSize
    
    // 分页数据
    const paginatedData = allFailedData.slice(start_idx, end_idx)
    
    // 转换为前端需要的格式
    failedData.value = paginatedData.map((item, index) => ({
      id: `failed_${start_idx + index + 1}`,
      row: item.记录编号 || start_idx + index + 1,
      field: item.变量 || item.原字段 || '未知字段',
      value: item.值 || '',
      rule: item.规则名称 || '文本质检',
      message: item.说明 || '质检失败',
      result: item.结果 || '不合格',
      timestamp: new Date().toLocaleString('zh-CN')
    }))
    
    // 更新分页信息
    failedDataPagination.value = {
      page: failedDataPagination.value.page,
      pageSize: failedDataPagination.value.pageSize,
      total: total,
      totalPages: Math.ceil(total / failedDataPagination.value.pageSize),
      hasNext: end_idx < total,
      hasPrev: failedDataPagination.value.page > 1
    }
    
    // 只在第一次加载时显示消息，分页时不显示
    if (failedDataPagination.value.page === 1) {
      ElMessage.success(`加载了 ${total} 条不合格记录，共 ${Math.ceil(total / failedDataPagination.value.pageSize)} 页`)
    }
  } catch (error) {
    console.error('加载不合格数据失败:', error)
    ElMessage.error('加载不合格数据失败')
  } finally {
    loadingFailedData.value = false
  }
}

// 分页相关函数
const changeFailedDataPage = async (page) => {
  if (page < 1 || page > failedDataPagination.value.totalPages) return
  
  failedDataPagination.value.page = page
  await loadFailedData()
}

const changeFailedDataPageSize = async (pageSize) => {
  failedDataPagination.value.pageSize = pageSize
  failedDataPagination.value.page = 1  // 重置到第一页
  await loadFailedData()
}

// 处理导出命令
const handleExportCommand = (command) => {
  if (command === 'failed') {
    exportResults('failed')
  } else if (command === 'all') {
    exportResults('all')
  }
}

// 导出数据到CSV
const exportResults = (type = 'failed') => {
  try {
    const currentResults = currentResult.value
    
    if (!currentResults || !currentResults.results || currentResults.results.length === 0) {
      ElMessage.warning('没有质检结果数据可导出')
      return
    }
    
    let dataToExport = []
    let filePrefix = ''
    
    if (type === 'failed') {
      // 筛选不合格的数据
      dataToExport = currentResults.results.filter(item => 
        item.结果 === '不合格' || item.结果 === '检查失败'
      )
      filePrefix = '不合格数据'
      
      if (dataToExport.length === 0) {
        ElMessage.success('恭喜！所有数据都符合规范，无不合格数据可导出')
        return
      }
    } else {
      // 导出全部数据
      dataToExport = currentResults.results
      filePrefix = '质检结果'
    }
    
    // 准备CSV数据
    const csvHeaders = [
      '记录编号',
      '原字段名',
      '映射字段名', 
      '字段值',
      '数据类别',
      '质检结果',
      '详细说明',
      '质量规范要求',
      '检查时间'
    ]
    
    // 构建CSV内容
    let csvContent = csvHeaders.join(',') + '\n'
    
    dataToExport.forEach(item => {
      const row = [
        item.记录编号 || '',
        item.原字段 || item.变量 || '',
        item.映射字段 || item.变量 || '',
        `"${(item.值 || '').toString().replace(/"/g, '""')}"`, // 处理特殊字符
        item.类别 || '',
        item.结果 || '',
        `"${(item.说明 || '').toString().replace(/"/g, '""')}"`,
        `"${(item.规范 || '').toString().replace(/"/g, '""')}"`,
        new Date().toLocaleString('zh-CN')
      ]
      csvContent += row.join(',') + '\n'
    })
    
    // 创建并下载文件
    const blob = new Blob(['\uFEFF' + csvContent], { 
      type: 'text/csv;charset=utf-8;' 
    })
    
    const link = document.createElement('a')
    const url = URL.createObjectURL(blob)
    link.setAttribute('href', url)
    
    // 生成文件名
    const timestamp = new Date().toISOString().slice(0, 19).replace(/[:-]/g, '').replace('T', '_')
    const tableName = qualityForm.value.tableName || 'unknown_table'
    const fileName = `${filePrefix}_${tableName}_${timestamp}.csv`
    
    link.setAttribute('download', fileName)
    link.style.visibility = 'hidden'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
    
    ElMessage.success(`成功导出 ${dataToExport.length} 条数据到 ${fileName}`)
    
    // 输出导出统计信息
    console.log('=== 导出统计 ===')
    console.log(`导出类型: ${type === 'failed' ? '不合格数据' : '全部数据'}`)
    console.log(`总质检记录: ${currentResults.results.length}`)
    console.log(`导出记录: ${dataToExport.length}`)
    if (type === 'failed') {
      console.log(`合格率: ${((currentResults.results.length - dataToExport.length) / currentResults.results.length * 100).toFixed(2)}%`)
    }
    console.log(`导出文件: ${fileName}`)
    
  } catch (error) {
    console.error('导出失败:', error)
    ElMessage.error('导出失败: ' + error.message)
  }
}

// 生命周期
onMounted(() => {
  loadDataSources()
  loadKnowledgeBaseVariables()  // 预加载知识库变量以供智能建议使用
})
</script>

<style scoped>
.llm-quality-check {
  padding: 20px;
  background-color: #f5f7fa;
  min-height: calc(100vh - 60px);
}

.page-header {
  margin-bottom: 20px;
  text-align: center;
}

.page-header h2 {
  color: #303133;
  font-size: 28px;
  margin-bottom: 8px;
}

.page-header p {
  color: #909399;
  font-size: 14px;
  margin: 0;
}

.config-panel, .result-panel {
  height: fit-content;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  align-items: center;
}

.header-icon {
  margin-right: 8px;
  color: #409eff;
}

.header-title {
  font-weight: 500;
  color: #303133;
}

.config-form {
  padding: 10px 0;
}

.option-content {
  display: flex;
  flex-direction: column;
}

.option-name {
  font-weight: 500;
}

.option-desc {
  font-size: 12px;
  color: #909399;
}

.progress-container {
  padding: 40px 20px;
  text-align: center;
}

.progress-text {
  margin-top: 15px;
  color: #606266;
}

.results-container {
  padding: 20px 0;
}

.stats-cards {
  margin-bottom: 20px;
}

.stat-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 20px;
  border-radius: 8px;
  text-align: center;
}

.stat-card.total {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.stat-card.passed {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
}

.stat-card.failed {
  background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
}

.stat-card.rate {
  background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
  color: #333;
}

.stat-number {
  font-size: 28px;
  font-weight: bold;
  margin-bottom: 5px;
}

.stat-label {
  font-size: 14px;
  opacity: 0.8;
}

.empty-state {
  padding: 60px 20px;
  text-align: center;
}

.field-help {
  margin-top: 8px;
  color: #909399;
  font-size: 12px;
}

/* 字段映射样式 */
.mapping-form-item {
  width: 100%;
}

.mapping-form-item :deep(.el-form-item__content) {
  width: 100% !important;
}

.field-mapping-section {
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  padding: 16px;
  background: #fafafa;
  width: 100%;
  box-sizing: border-box;
}

.mapping-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
  font-size: 14px;
  color: #606266;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.mapping-table {
  margin-bottom: 12px;
  width: 100%;
}

.mapping-table :deep(.el-table__cell) {
  padding: 8px 12px;
}

.mapping-table :deep(.el-table) {
  width: 100%;
}

.mapping-table :deep(.el-table__header-wrapper) {
  width: 100%;
}

.mapping-table :deep(.el-table__body-wrapper) {
  width: 100%;
}

.matched-rule {
  color: #67c23a;
  font-weight: 500;
  word-break: break-all;
}

.no-match {
  color: #909399;
  font-style: italic;
}

.mapping-summary {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 8px;
  flex-wrap: wrap;
  gap: 8px;
}

.summary-left {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.summary-right {
  display: flex;
  align-items: center;
}

.mapping-summary .el-tag {
  margin: 0;
}

/* 表单提示信息样式 */
.form-item-tip {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-top: 4px;
  color: #909399;
  font-size: 12px;
}

.form-item-tip .el-icon {
  font-size: 14px;
  color: #409eff;
}

/* 不合格数据部分样式 */
.failed-data-section {
  margin-top: 30px;
  border-top: 1px solid #e4e7ed;
  padding-top: 20px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.section-header h4 {
  margin: 0;
  color: #2c3e50;
  font-size: 16px;
  font-weight: 600;
}

.failed-data-table {
  background: white;
  border-radius: 8px;
  border: 1px solid #e4e7ed;
  overflow: hidden;
}

/* 分页样式 */
.pagination-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  background: #f8f9fa;
  border-top: 1px solid #e4e7ed;
}

.pagination-info {
  color: #7f8c8d;
  font-size: 14px;
}

.pagination-controls {
  display: flex;
  align-items: center;
  gap: 15px;
}

.pagination-controls .el-pagination {
  margin: 0;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .section-header {
    flex-direction: column;
    align-items: stretch;
    gap: 15px;
  }
  
  .pagination-container {
    flex-direction: column;
    gap: 15px;
    text-align: center;
  }
  
  .pagination-controls {
    justify-content: center;
    flex-wrap: wrap;
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
</style> 