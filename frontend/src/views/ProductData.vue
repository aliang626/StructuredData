<template>
  <div class="model-container">
    <!-- ================= 1. 数据概览 ================= -->
    <el-row :gutter="20" class="section-margin">
      <el-col :span="24">
        <el-card class="data-overview-card">
          <div class="card-title-wrapper">
            <h3 class="card-title">生产数据概览</h3>
            <el-button type="primary" link @click="refreshOverview">
              <el-icon>
                <Refresh/>
              </el-icon>
              <span>刷新</span>
            </el-button>
          </div>
          <div class="data-quality-stats">
            <el-row :gutter="20">
              <el-col :span="5" v-for="(stat, index) in overviewStats" :key="index">
                <div class="stat-card-item">
                  <div :class="['stat-icon', stat.iconClass]">
                    <el-icon :size="24">
                      <component :is="stat.icon"></component>
                    </el-icon>
                  </div>
                  <div class="stat-info">
                    <div class="stat-label">{{ stat.label }}</div>
                    <div class="stat-value">{{ stat.value }}</div>
                  </div>
                </div>
              </el-col>
            </el-row>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- ================= 2. 配置/趋势 ================= -->
    <el-row :gutter="20" class="section-margin">
      <!-- 左侧配置 -->
      <el-col :span="12">
        <el-card class="parameter-panel-card">
          <template #header>
            <div class="card-header">
              <span class="card-header-title">检测点与参数配置</span>
            </div>
          </template>
          <div class="parameter-content">
            <el-form :model="detectionPointForm" label-width="150px" label-position="left">
              <!-- ================== 新增的数据源下拉框 ================== -->
              <el-form-item label="数据源">
                <el-select
                    v-model="selectedSourceId"
                    placeholder="请先选择一个数据源"
                    class="full-width-select"
                    :loading="loadingSources"
                    filterable
                >
                  <el-option
                      v-for="source in dataSources"
                      :key="source.id"
                      :label="source.name"
                      :value="source.id"
                  />
                </el-select>
              </el-form-item>

              <el-form-item label="Schema">
                <el-select
                    v-model="selectedSchema"
                    placeholder="请先选择数据源"
                    class="full-width-select"
                    :loading="loadingSchemas"
                    :disabled="!selectedSourceId"
                    filterable
                >
                  <el-option
                      v-for="schema in schemas"
                      :key="schema"
                      :label="schema"
                      :value="schema"
                  />
                </el-select>
              </el-form-item>

              <el-form-item label="数据集">
                <el-select v-model="detectionPointForm.dataTable"
                           placeholder="请先选择Schema"
                           class="full-width-select"
                           :disabled="!selectedSchema"
                           filterable
                >
                  <el-option v-for="t in dataTables" :key="t.value" :label="t.label" :value="t.value"/>
                </el-select>
              </el-form-item>

              <el-form-item label="字段选择">
                <el-select
                    v-model="selectedTagField"
                    placeholder="请先选择数据表"
                    :disabled="!detectionPointForm.dataTable"
                    filterable
                    clearable
                    class="full-width-select"
                >
                  <el-option
                      v-for="field in availableFields"
                      :key="field.name"
                      :label="field.description || field.name"
                      :value="field.name"
                  >
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                      <span style="font-weight: 500;">{{ field.description || field.name }}</span>
                      <span style="color: #909399; font-size: 12px; margin-left: 8px;">
                        {{ field.type }}<span v-if="field.description && field.description !== field.name"> | {{ field.name }}</span>
                      </span>
                    </div>
                  </el-option>
                </el-select>
              </el-form-item>

              <el-form-item label="字段值">
                <el-select v-model="detectionPointForm.tagCode"
                           placeholder="请先选择字段"
                           filterable
                           class="full-width-select"
                           :disabled="!selectedTagField"
                >
                  <el-option v-for="tag in tagOptions" :key="tag.value" :label="tag.label" :value="tag.value"/>
                </el-select>
              </el-form-item>

              <el-divider>检测参数</el-divider>

              <el-form-item label="断流检测窗口(分钟)">
                <el-slider
                    v-model="detectionPointForm.windowSize"
                    :min="1" :max="60" :step="1" show-input
                    :format-tooltip="val => val + ' 分钟'" class="custom-slider"
                />
              </el-form-item>

              <el-form-item label="数据丢失阈值(秒)">
                <el-input-number v-model="detectionPointForm.gapThreshold" :min="1" :max="3600"/>
              </el-form-item>

              <el-form-item label="Z-Score检测窗口">
                <el-input-number v-model="detectionPointForm.zScoreWindow" :min="10" :max="200"/>
              </el-form-item>

              <el-form-item label="Z-Score阈值">
                <el-slider
                    v-model="detectionPointForm.zScoreThreshold"
                    :min="1" :max="5" :step="0.1" show-input class="custom-slider"
                />
              </el-form-item>

              <el-divider>数据量控制</el-divider>

              <el-form-item label="数据量限制">
                <el-tooltip content="建议：生产环境限制数据量以避免系统负载过高" placement="top">
                  <el-select v-model="detectionPointForm.dataLimit" class="full-width-select">
                    <el-option label="最近 500 条（极快）" :value="500" />
                    <el-option label="最近 1,000 条（推荐）" :value="1000" />
                    <el-option label="最近 5,000 条" :value="5000" />
                    <el-option label="最近 10,000 条" :value="10000" />
                    <el-option label="最近 50,000 条（慎用）" :value="50000" />
                  </el-select>
                </el-tooltip>
              </el-form-item>

              <el-divider>时间范围筛选</el-divider>

              <el-form-item label="时间范围">
                <el-tooltip content="留空表示不限制时间，仅使用数据量限制" placement="top">
                  <el-date-picker
                      v-model="detectionPointForm.timeRange"
                      type="datetimerange"
                      range-separator="至"
                      start-placeholder="开始时间"
                      end-placeholder="结束时间"
                      format="YYYY-MM-DD HH:mm:ss"
                      value-format="YYYY-MM-DD HH:mm:ss"
                      :clearable="true"
                      class="full-width-select"
                  />
                </el-tooltip>
              </el-form-item>

              <el-form-item label="快捷选择">
                <el-row :gutter="8">
                  <el-col :span="8">
                    <el-button size="small" @click="setTimeRange('today')" style="width: 100%;">今天</el-button>
                  </el-col>
                  <el-col :span="8">
                    <el-button size="small" @click="setTimeRange('last-hour')" style="width: 100%;">最近1小时</el-button>
                  </el-col>
                  <el-col :span="8">
                    <el-button size="small" @click="setTimeRange('last-24h')" style="width: 100%;">最近24小时</el-button>
                  </el-col>
                </el-row>
              </el-form-item>

              <el-form-item>
                <el-button
                    type="danger"
                    @click="runAnomalyDetection"
                    :loading="isDetecting"
                    class="full-width-select"
                    style="margin-top: 10px;"
                >
                  开始检测
                </el-button>
              </el-form-item>

            </el-form>
          </div>
        </el-card>
      </el-col>

      <!-- 右侧趋势图 -->
      <el-col :span="12">
        <el-card class="data-preview-card">
          <template #header>
            <div class="card-header">
              <span class="card-header-title">数据趋势图</span>
              <el-button type="primary" :icon="Refresh" @click="refreshTrend" class="refresh-button">刷新</el-button>
            </div>
          </template>
          <div v-loading="chartLoading" element-loading-text="加载中..." class="chart-container-wrapper">
            <div ref="chartRef" class="echart-instance"></div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- ================= 3. 异常列表 ================= -->
    <el-row :gutter="20" class="section-margin">
      <el-col :span="24">
        <el-card class="anomaly-results-card">
          <template #header>
            <div class="card-header">
              <span class="card-header-title">数据异常列表</span>
              <el-button type="success" size="small" @click="exportReport" :disabled="anomalyData.length === 0">
                <el-icon style="margin-right: 5px;"><Download /></el-icon>
                导出报告
              </el-button>
            </div>
          </template>
          <el-table :data="anomalyData" style="width: 100%" height="450" class="anomaly-table" stripe
                    v-loading="isDetecting">
            <el-table-column type="index" label="序号" width="60" align="center"/>
            <el-table-column prop="code" label="点位代码" width="200" show-overflow-tooltip/>
            <el-table-column prop="type" label="异常类型" width="120">
              <template #default="scope">
                <el-tag :type="getTagType(scope.row.type)" effect="light" round size="small">{{
                    scope.row.type
                  }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="timestamp" label="时间" width="180" sortable/>
            <el-table-column prop="value" label="数值" width="120">
              <template #default="scope">
                <span v-if="scope.row.value !== null">{{ scope.row.value }}</span>
                <span v-else>--</span>
              </template>
            </el-table-column>
            <el-table-column prop="details" label="详情" min-width="250" show-overflow-tooltip/>
            <el-table-column label="操作" fixed="right" width="80" align="center">
              <template #default="scope">
                <el-popover placement="left" :width="400" trigger="click">
                  <template #reference>
                    <el-button link type="primary" size="small">详情</el-button>
                  </template>
                  <div>
                    <h4>异常详情</h4>
                    <p><strong>点位代码:</strong> {{ scope.row.code }}</p>
                    <p><strong>异常类型:</strong> {{ scope.row.type }}</p>
                    <p><strong>时间戳:</strong> {{ scope.row.timestamp }}</p>
                    <p v-if="scope.row.value !== null"><strong>数值:</strong> {{ scope.row.value }}</p>
                    <p><strong>详细信息:</strong> {{ scope.row.details }}</p>
                    <p v-if="scope.row.time_range">
                      <strong>影响时间范围:</strong> {{ scope.row.time_range[0] }} 至 {{ scope.row.time_range[1] }}
                    </p>
                  </div>
                </el-popover>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import {ref, reactive, onMounted, watch, nextTick} from 'vue';
import * as echarts from 'echarts';
import axios from 'axios';
import {Refresh, DataLine, Warning, CircleClose, TrendCharts, Download} from '@element-plus/icons-vue';
import {ElMessage} from 'element-plus';

/* ===================================================
   1. 状态和 API 配置
   =================================================== */
const API_BASE_URL = '/api/database';

// --- 新增状态变量 ---
const dataSources = ref([]);
const selectedSourceId = ref(null);
const loadingSources = ref(false);
const schemas = ref([]);
const selectedSchema = ref('');
const loadingSchemas = ref(false);

const dataTables = ref([]);
const availableFields = ref([]);  // 存储所有字段
const selectedTagField = ref('');  // 用户选择的字段
const tagOptions = ref([]);
const trendData = ref([]);
const anomalyChartData = ref(null);

const detectionPointForm = reactive({
  dataTable: '',
  tagCode: '',
  windowSize: 5,
  gapThreshold: 60,
  zScoreWindow: 50,
  zScoreThreshold: 2.0,
  dataLimit: 1000,  // 默认1000条（推荐）
  timeRange: null,   // 时间范围
});

const anomalyData = ref([]);
const isDetecting = ref(false);

const overviewStats = ref([
  {label: '当前数据集点位数', value: 0, icon: DataLine, iconClass: 'icon-total'},
  {label: '数据丢失异常', value: 0, icon: CircleClose, iconClass: 'icon-loss'},
  {label: '数据断流异常', value: 0, icon: TrendCharts, iconClass: 'icon-break'},
  {label: '数值异常', value: 0, icon: Warning, iconClass: 'icon-stat'}
]);

const resetAnomalyStats = () => {
  overviewStats.value.forEach(stat => {
    if (stat.label.includes('异常')) {
      stat.value = 0;
    }
  });
};

/* ===================================================
   2. API 调用函数 (已重构)
   =================================================== */

// --- 新增函数：获取所有数据源 ---
const fetchDataSources = async () => {
  loadingSources.value = true;
  try {
    const response = await axios.get(`${API_BASE_URL}/sources`);
    if (response.data.success) {
      dataSources.value = response.data.data;
      if (dataSources.value.length > 0) {
        selectedSourceId.value = dataSources.value[0].id; // 自动选中第一个
      }
    } else {
      ElMessage.error(`获取数据源列表失败: ${response.data.error}`);
    }
  } catch (error) {
    ElMessage.error(`请求数据源列表时出错: ${error.message}`);
  } finally {
    loadingSources.value = false;
  }
};

// --- 新增函数：获取Schema列表 ---
const loadSchemas = async () => {
  if (!selectedSourceId.value) return;
  
  // 重置后续选择
  selectedSchema.value = '';
  dataTables.value = [];
  detectionPointForm.dataTable = '';
  detectionPointForm.tagCode = '';
  tagOptions.value = [];
  trendData.value = [];
  anomalyData.value = [];
  anomalyChartData.value = null;
  resetAnomalyStats();
  
  loadingSchemas.value = true;
  try {
    const selectedSource = dataSources.value.find(s => s.id === selectedSourceId.value);
    if (!selectedSource) return;
    
    const response = await axios.post(`${API_BASE_URL}/schemas`, selectedSource);
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

// --- 重构函数：根据 source_id 和 schema 获取数据表 ---
const fetchTables = async () => {
  if (!selectedSourceId.value || !selectedSchema.value) {
    dataTables.value = [];
    return;
  }
  
  // 重置后续选择
  detectionPointForm.dataTable = '';
  detectionPointForm.tagCode = '';
  availableFields.value = [];
  selectedTagField.value = '';
  tagOptions.value = [];
  trendData.value = [];
  anomalyData.value = [];
  anomalyChartData.value = null;
  resetAnomalyStats();
  
  try {
    const selectedSource = dataSources.value.find(s => s.id === selectedSourceId.value);
    if (!selectedSource) return;
    
    const response = await axios.post(`${API_BASE_URL}/tables`, {
      ...selectedSource,
      schema: selectedSchema.value
    });
    if (response.data.success) {
      dataTables.value = response.data.data.map(table => ({
        label: table.description || table.name, 
        value: table.name
      }));
      if (dataTables.value.length > 0) {
        detectionPointForm.dataTable = dataTables.value[0].value;
      } else {
        detectionPointForm.dataTable = '';
      }
    } else {
      ElMessage.error(`获取数据表失败: ${response.data.error}`);
      dataTables.value = [];
    }
  } catch (error) {
    ElMessage.error(`请求数据表列表时出错: ${error.message}`);
    console.error("fetchTables error:", error.response || error);
  }
};

// --- 新增函数：获取表的所有字段 ---
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
    
    const response = await axios.post(`${API_BASE_URL}/fields`, requestData);
    if (response.data.success) {
      availableFields.value = response.data.data;
      // 不自动选择，让用户手动选择
      selectedTagField.value = '';
    } else {
      ElMessage.error(`获取字段列表失败: ${response.data.error}`);
      availableFields.value = [];
      selectedTagField.value = '';
    }
  } catch (error) {
    console.error('获取字段列表失败:', error);
    ElMessage.error('获取字段列表失败');
    availableFields.value = [];
    selectedTagField.value = '';
  }
};

// --- 重构函数：根据动态字段获取唯一值 ---
const fetchUniqueValues = async (fieldName) => {
  if (!detectionPointForm.dataTable || !selectedSourceId.value || !fieldName) {
    tagOptions.value = [];
    return;
  }
  try {
    const response = await axios.get(`${API_BASE_URL}/field-values`, {
      params: {
        source_id: selectedSourceId.value,
        table_name: detectionPointForm.dataTable,
        schema: selectedSchema.value,
        field_name: fieldName
      }
    });
    if (response.data.success) {
      tagOptions.value = response.data.data.map(val => ({label: val, value: val}));
      // 不自动选择，让用户手动选择
      detectionPointForm.tagCode = '';
    } else {
      ElMessage.warning(`获取字段值失败: ${response.data.error}`);
      tagOptions.value = [];
      detectionPointForm.tagCode = '';
    }
  } catch (error) {
    ElMessage.warning(`请求字段值列表时出错: ${error.message}`);
    tagOptions.value = [];
    detectionPointForm.tagCode = '';
  }
};

const refreshTrend = async () => {
  anomalyChartData.value = null;
  if (!detectionPointForm.dataTable || !detectionPointForm.tagCode || !selectedSchema.value || !selectedTagField.value) {
    trendData.value = [];
    renderChart();
    return;
  }
  chartLoading.value = true;
  try {
    const selectedSource = dataSources.value.find(s => s.id === selectedSourceId.value);
    if (!selectedSource) {
      ElMessage.error("未找到所选数据源的配置信息");
      return;
    }

    const payload = {
      ...selectedSource, // 传递当前数据源的完整配置
      schema: selectedSchema.value,
      table_name: detectionPointForm.dataTable,
      tag_field_name: selectedTagField.value,  // 动态字段名
      tag_code: detectionPointForm.tagCode,
      limit: Math.min(detectionPointForm.dataLimit || 1000, 300)  // 趋势图最多300条
    };
    
    // 如果有时间范围限制，添加到payload
    if (detectionPointForm.timeRange && detectionPointForm.timeRange.length === 2) {
      payload.start_time = detectionPointForm.timeRange[0];
      payload.end_time = detectionPointForm.timeRange[1];
    }
    
    const response = await axios.post(`${API_BASE_URL}/tag-data`, payload);
    if (response.data.success) {
      trendData.value = response.data.data.map(item => ({
        ts: new Date(item.tag_time).toLocaleString('zh-CN', {hour12: false}),
        value: parseFloat(item.tag_value)
      }));
      ElMessage.success('趋势图已刷新');
    } else {
      ElMessage.error(`获取趋势数据失败: ${response.data.error}`);
    }
  } catch (error) {
    ElMessage.error(`请求趋势数据时出错: ${error.message}`);
  } finally {
    chartLoading.value = false;
  }
};

const runAnomalyDetection = async () => {
  if (!detectionPointForm.dataTable || !detectionPointForm.tagCode || !selectedSchema.value || !selectedTagField.value) {
    ElMessage.warning('请先选择Schema、数据集、字段和字段值');
    return;
  }
  
  // 验证时间范围
  if (detectionPointForm.timeRange && detectionPointForm.timeRange.length === 2) {
    if (new Date(detectionPointForm.timeRange[0]) > new Date(detectionPointForm.timeRange[1])) {
      ElMessage.warning('开始时间不能晚于结束时间');
      return;
    }
  }
  
  isDetecting.value = true;
  anomalyData.value = [];
  anomalyChartData.value = null;
  resetAnomalyStats();

  try {
    const selectedSource = dataSources.value.find(s => s.id === selectedSourceId.value);
    if (!selectedSource) {
      ElMessage.error("未找到所选数据源的配置信息");
      return;
    }
    
    const payload = {
      ...selectedSource, // 传递当前数据源的完整配置
      schema: selectedSchema.value,
      table_name: detectionPointForm.dataTable,
      tag_field_name: selectedTagField.value,  // 动态字段名
      tag_code: detectionPointForm.tagCode,
      gap_thres: detectionPointForm.gapThreshold,
      win_sec: detectionPointForm.windowSize * 60,
      z_win: detectionPointForm.zScoreWindow,
      z_thres: detectionPointForm.zScoreThreshold,
      limit: detectionPointForm.dataLimit,  // 添加数据量限制
    };
    
    // 如果有时间范围限制，添加到payload
    if (detectionPointForm.timeRange && detectionPointForm.timeRange.length === 2) {
      payload.start_time = detectionPointForm.timeRange[0];
      payload.end_time = detectionPointForm.timeRange[1];
    }
    
    // 显示提示信息
    let infoMsg = '';
    if (detectionPointForm.timeRange && detectionPointForm.timeRange.length === 2) {
      infoMsg = `正在分析时间范围内最近 ${detectionPointForm.dataLimit.toLocaleString()} 条数据...`;
    } else {
      infoMsg = `正在分析最近 ${detectionPointForm.dataLimit.toLocaleString()} 条数据...`;
    }
    ElMessage.info(infoMsg);
    
    const response = await axios.post(`${API_BASE_URL}/anomaly-check`, payload);
    if (response.data.success) {
      const {anomalies_list, chart_data} = response.data.data;
      anomalyData.value = anomalies_list;
      anomalyChartData.value = chart_data;
      ElMessage.success(`检测完成！发现 ${anomalies_list.length} 条异常。`);
      anomalies_list.forEach(anomaly => {
        if (anomaly.type === '数据丢失') {
          overviewStats.value.find(s => s.label === '数据丢失异常').value++;
        } else if (anomaly.type === '数据断流') {
          overviewStats.value.find(s => s.label === '数据断流异常').value++;
        } else if (anomaly.type === '数据异常') {
          overviewStats.value.find(s => s.label === '数值异常').value++;
        }
      });
      renderChart();
    } else {
      ElMessage.error(`检测失败: ${response.data.error}`);
    }
  } catch (error) {
    ElMessage.error(`请求异常检测时出错: ${error.message}`);
  } finally {
    isDetecting.value = false;
  }
};

/* ===================================================
   3. 趋势图 ECharts
   =================================================== */
const chartRef = ref(null);
let chartInstance = null;
const chartLoading = ref(false);

const renderChart = () => {
  if (!chartRef.value) return;
  if (chartInstance) chartInstance.dispose();
  chartInstance = echarts.init(chartRef.value);
  const sourceData = anomalyChartData.value ? anomalyChartData.value : trendData.value;
  if (!sourceData || sourceData.length === 0) {
    chartInstance.setOption({title: {text: '暂无数据', left: 'center', top: 'center'}});
    return;
  }
  const chartDataForSeries = sourceData.map(d => {
    const time = d.tag_time ? new Date(d.tag_time).toLocaleString('zh-CN', {hour12: false}) : d.ts;
    const value = d.tag_value !== undefined ? d.tag_value : d.value;
    const anomalyType = d.anomaly_type || null;
    return [time, value, anomalyType];
  });
  const xAxisData = chartDataForSeries.map(item => item[0]);
  const markPointData = chartDataForSeries
      .map((item) => {
        if (item[2]) {
          return {
            name: item[2],
            coord: [item[0], item[1]],
            value: item[1],
            itemStyle: {
              color: item[2] === '数据异常' ? '#f56c6c' : '#e6a23c'
            }
          };
        }
        return null;
      })
      .filter(Boolean);
  chartInstance.setOption({
    title: {
      text: `${detectionPointForm.tagCode || '实时数据'}趋势`,
      subtext: anomalyChartData.value ? '（含异常点标记）' : '',
      left: 'center',
      textStyle: {fontSize: 16, color: '#333'}
    },
    tooltip: {
      trigger: 'axis',
      formatter: function (params) {
        const data = params[0].data;
        const marker = params[0].marker;
        let tooltipText = `${data[0]}<br/>${marker}数值: ${data[1]}`;
        if (data[2]) {
          const pointColor = markPointData.find(p => p.coord[0] === data[0])?.itemStyle.color || '#f56c6c';
          tooltipText += `<br/><strong style="color: ${pointColor}">异常: ${data[2]}</strong>`;
        }
        return tooltipText;
      }
    },
    grid: {left: '3%', right: '4%', bottom: '15%', top: '20%', containLabel: true},
    xAxis: {type: 'category', boundaryGap: false, data: xAxisData},
    yAxis: {type: 'value', name: `数值`},
    series: [{
      name: '实时数据',
      type: 'line',
      data: chartDataForSeries,
      smooth: true,
      markPoint: {
        symbol: 'circle',
        symbolSize: 10,
        label: {show: false},
        emphasis: {
          label: {
            show: true,
            formatter: '{b}: {c}'
          }
        },
        data: markPointData
      }
    }]
  });
};

/* ===================================================
   4. 逻辑控制与生命周期 (已重构)
   =================================================== */

// --- 新增监听器：监听数据源选择的变化 ---
watch(selectedSourceId, (newSourceId) => {
  selectedSchema.value = '';
  schemas.value = [];
  detectionPointForm.dataTable = '';
  detectionPointForm.tagCode = '';
  dataTables.value = [];
  tagOptions.value = [];
  trendData.value = [];
  anomalyData.value = [];
  anomalyChartData.value = null;
  resetAnomalyStats();
  if (newSourceId) {
    loadSchemas();
  }
});

// --- 新增监听器：监听Schema选择的变化 ---
watch(selectedSchema, (newSchema) => {
  detectionPointForm.dataTable = '';
  detectionPointForm.tagCode = '';
  dataTables.value = [];
  tagOptions.value = [];
  trendData.value = [];
  anomalyData.value = [];
  anomalyChartData.value = null;
  resetAnomalyStats();
  if (newSchema) {
    fetchTables();
  }
});

// --- 原有监听器保持不变，但现在是联动链的一部分 ---
watch(() => detectionPointForm.dataTable, (newTable) => {
  detectionPointForm.tagCode = '';
  availableFields.value = [];
  selectedTagField.value = '';
  tagOptions.value = [];
  trendData.value = [];
  anomalyData.value = [];
  anomalyChartData.value = null;
  resetAnomalyStats();
  if (newTable) {
    fetchTableFields(newTable);
  }
});

// --- 新增监听器：监听字段选择的变化 ---
watch(selectedTagField, (newField) => {
  detectionPointForm.tagCode = '';
  tagOptions.value = [];
  trendData.value = [];
  anomalyData.value = [];
  anomalyChartData.value = null;
  resetAnomalyStats();
  if (newField) {
    fetchUniqueValues(newField);
  }
});

watch(() => detectionPointForm.tagCode, (newTag) => {
  anomalyData.value = [];
  anomalyChartData.value = null;
  resetAnomalyStats();
  if (newTag) {
    refreshTrend();
  } else {
    trendData.value = [];
    renderChart();
  }
});

watch(trendData, () => {
  if (!isDetecting.value) {
    nextTick(renderChart);
  }
}, {deep: true});

watch(tagOptions, (newTags) => {
  const totalStat = overviewStats.value.find(s => s.label === '当前数据集点位数');
  if (totalStat) {
    totalStat.value = newTags.length;
  }
}, {deep: true});

// --- 导出报告功能 ---
const exportReport = () => {
  if (anomalyData.value.length === 0) {
    ElMessage.warning('暂无检测结果数据可导出');
    return;
  }
  
  try {
    // 生成报告内容
    const reportTitle = '生产数据质检报告';
    const reportTime = new Date().toLocaleString('zh-CN');
    
    let content = `${reportTitle}\n`;
    content += `=`.repeat(60) + '\n\n';
    content += `生成时间：${reportTime}\n`;
    content += `数据源：${dataSources.value.find(s => s.id === selectedSourceId.value)?.name || '未知'}\n`;
    content += `Schema：${selectedSchema.value}\n`;
    content += `数据表：${detectionPointForm.dataTable}\n`;
    
    // 显示字段信息
    const selectedField = availableFields.value.find(f => f.name === selectedTagField.value);
    if (selectedField) {
      content += `选择字段：${selectedField.description || selectedField.name} (${selectedField.name})\n`;
    }
    content += `字段值：${detectionPointForm.tagCode}\n`;
    
    // 添加时间范围信息
    if (detectionPointForm.timeRange && detectionPointForm.timeRange.length === 2) {
      content += `时间范围：${detectionPointForm.timeRange[0]} 至 ${detectionPointForm.timeRange[1]}\n`;
    }
    if (detectionPointForm.dataLimit) {
      content += `数据量限制：最近 ${detectionPointForm.dataLimit.toLocaleString()} 条\n`;
    }
    
    // 添加检测参数
    content += `\n检测参数：\n`;
    content += `  - 时间窗口大小：${detectionPointForm.windowSize} 分钟\n`;
    content += `  - 数据丢失阈值：${detectionPointForm.gapThreshold} 秒\n`;
    content += `  - Z-Score 窗口：${detectionPointForm.zScoreWindow} 个点\n`;
    content += `  - Z-Score 阈值：${detectionPointForm.zScoreThreshold}\n`;
    
    content += `\n`;
    content += `数据质量统计：\n`;
    content += `  - ${overviewStats.value[0].label}：${overviewStats.value[0].value}\n`;
    content += `  - ${overviewStats.value[1].label}：${overviewStats.value[1].value}\n`;
    content += `  - ${overviewStats.value[2].label}：${overviewStats.value[2].value}\n`;
    content += `  - ${overviewStats.value[3].label}：${overviewStats.value[3].value}\n`;
    content += `\n${'='.repeat(60)}\n\n`;
    
    // 异常检测结果详情
    content += `异常检测结果详情（共 ${anomalyData.value.length} 条）\n`;
    content += `${'-'.repeat(60)}\n\n`;
    
    anomalyData.value.forEach((item, index) => {
      content += `[${index + 1}] ${item.code}\n`;
      content += `    异常类型：${item.type}\n`;
      content += `    时间戳：${item.timestamp}\n`;
      if (item.value !== null) {
        content += `    数值：${item.value}\n`;
      }
      content += `    详细信息：${item.details}\n`;
      if (item.time_range) {
        content += `    影响时间范围：${item.time_range[0]} 至 ${item.time_range[1]}\n`;
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
    link.download = `生产数据质检报告_${detectionPointForm.tagCode}_${timestamp}.txt`;
    
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

// --- 重构 onMounted：页面加载时获取数据源 ---
onMounted(async () => {
  await fetchDataSources();
  window.addEventListener('resize', () => {
    chartInstance && chartInstance.resize();
  });
});

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
  
  let startTime, endTime;
  switch (range) {
    case 'today':
      // 今天：从今天 00:00:00 到现在
      startTime = new Date(now.getFullYear(), now.getMonth(), now.getDate(), 0, 0, 0);
      endTime = now;
      ElMessage.success('已设置为今天的数据');
      break;
    case 'last-hour':
      // 最近1小时
      startTime = new Date(now.getTime() - 60 * 60 * 1000);
      endTime = now;
      ElMessage.success('已设置为最近1小时的数据');
      break;
    case 'last-24h':
      // 最近24小时
      startTime = new Date(now.getTime() - 24 * 60 * 60 * 1000);
      endTime = now;
      ElMessage.success('已设置为最近24小时的数据');
      break;
    default:
      return;
  }
  
  detectionPointForm.timeRange = [formatDateTime(startTime), formatDateTime(endTime)];
};

const getTagType = (type) => {
  switch (type) {
    case '数据丢失':
      return 'warning';
    case '数据断流':
      return 'info';
    case '数据异常':
      return 'danger';
    default:
      return 'primary';
  }
};
const refreshOverview = () => {
  ElMessage.info('刷新概览数据功能待实现。概览数据在每次检测后自动更新。');
};
</script>

<style scoped>
/* 全局样式调整 */
.model-container {
  padding: 20px;
  background-color: #f0f2f5; /* 页面背景色 */
  min-height: calc(100vh - 80px); /* 确保内容区有最小高度 */
}

.section-margin {
  margin-bottom: 20px;
}

/* 卡片通用样式 */
.el-card {
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.05);
}

.card-title-wrapper {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 10px;
  border-bottom: 1px solid #ebeef5;
  margin-bottom: 10px;
}

.card-title {
  margin: 0;
  font-size: 18px;
  color: #303133;
  font-weight: bold;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0; /* 移除el-card__header默认padding，让title居中 */
}

.card-header-title {
  font-size: 16px;
  color: #303133;
  font-weight: bold;
}

/* ================= 1. 数据概览样式 ================= */
.data-overview-card {
  height: auto; /* 自动高度 */
}

.data-quality-stats {
  padding: 10px 0;
}

.stat-card-item {
  display: flex;
  align-items: center;
  padding: 15px;
  background: #fff;
  border-radius: 6px;
  box-shadow: 0 1px 4px rgba(0, 21, 41, .08);
  transition: all 0.3s ease;
  height: 90px;
}

.stat-card-item:hover {
  box-shadow: 0 4px 16px rgba(0, 21, 41, .15);
  transform: translateY(-3px);
}

.stat-icon {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  display: flex;
  justify-content: center;
  align-items: center;
  margin-right: 15px;
  color: #fff;
}

.icon-total {
  background-color: #409eff;
}

/* primary */
.icon-zero {
  background-color: #e6a23c;
}

/* warning */
.icon-loss {
  background-color: #f56c6c;
}

/* danger */
.icon-break {
  background-color: #909399;
}

/* info */
.icon-stat {
  background-color: #67c23a;
}

/* success */


.stat-info {
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.stat-label {
  font-size: 14px;
  color: #606266;
  margin-bottom: 5px;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: #303133;
}


/* ================= 2. 配置/趋势样式 ================= */
.parameter-panel-card {
  height: auto;
  min-height: 520px;
}

.data-preview-card {
  height: 520px;
}

.parameter-content {
  padding: 20px 0;
}

.el-form-item {
  margin-bottom: 20px;
}

.el-form-item__label {
  font-weight: bold;
  color: #606266;
}

.full-width-select {
  width: 100%;
}

.custom-slider {
  margin-left: 10px; /* 避免与label过近 */
}

.refresh-button {
  display: flex;
  align-items: center;
  padding: 8px 15px;
  border-radius: 4px;
}

.refresh-button .el-icon {
  margin-right: 5px;
}

.chart-container-wrapper {
  height: 400px; /* 确保图表容器高度 */
  display: flex;
  justify-content: center;
  align-items: center;
}

.echart-instance {
  width: 100%;
  height: 100%;
}

/* ================= 3. 异常列表样式 ================= */
.anomaly-results-card {
  height: 550px;
}

.anomaly-table {
  font-size: 14px;
}

.anomaly-table .el-table__header-wrapper th {
  background-color: #f5f7fa;
  color: #606266;
  font-weight: bold;
}

.anomaly-table .el-table__row {
  transition: background-color 0.2s ease;
}

.anomaly-table .el-table__row:hover {
  background-color: #f0f9eb;
}

.el-tag {
  font-weight: normal;
  border-radius: 4px;
}

.anomaly-value-display {
  display: flex;
  align-items: baseline;
  font-size: 14px;
}

.anomaly-value-display .raw-value {
  font-weight: bold;
  color: #303133;
  margin-right: 4px;
}

.anomaly-value-display .unit {
  color: #909399;
  font-size: 12px;
}
</style>