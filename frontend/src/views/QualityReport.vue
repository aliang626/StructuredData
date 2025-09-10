<template>
  <div class="quality-report">
    <!-- 页面标题 -->
    <div class="page-header">
      <h2>检测报告</h2>
      <p>查看和管理数据质量检测报告，支持详细分析和导出功能</p>
    </div>

    <!-- 统计概览 -->
    <el-card class="stats-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <el-icon class="header-icon"><Document /></el-icon>
            <span class="header-title">统计概览</span>
          </div>
          <div class="header-actions">
            <el-button type="info" @click="exportAllReports" class="action-btn">
              <el-icon><Download /></el-icon>
              导出所有报告
            </el-button>
            <el-button type="primary" @click="refreshReports" class="action-btn">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
          </div>
        </div>
      </template>
      
      <div class="stats-grid">
        <div class="stat-item">
          <div class="stat-icon">
            <el-icon><Document /></el-icon>
          </div>
          <div class="stat-content">
            <span class="stat-number">{{ totalChecks }}</span>
            <span class="stat-label">总检测次数</span>
          </div>
        </div>
        <div class="stat-item">
          <div class="stat-icon success">
            <el-icon><CircleCheck /></el-icon>
          </div>
          <div class="stat-content">
            <span class="stat-number success">{{ avgPassRate }}%</span>
            <span class="stat-label">平均通过率</span>
          </div>
        </div>
        <div class="stat-item">
          <div class="stat-icon warning">
            <el-icon><Document /></el-icon>
          </div>
          <div class="stat-content">
            <span class="stat-number warning">{{ totalRecords }}</span>
            <span class="stat-label">总记录数</span>
          </div>
        </div>
        <div class="stat-item">
          <div class="stat-icon danger">
            <el-icon><CircleClose /></el-icon>
          </div>
          <div class="stat-content">
            <span class="stat-number danger">{{ totalFailed }}</span>
            <span class="stat-label">总失败数</span>
          </div>
        </div>
      </div>
      
    <!-- 报告列表 -->
    <el-card class="reports-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <el-icon class="header-icon"><Document /></el-icon>
            <span class="header-title">检测报告列表</span>
            <el-tag type="info" size="small">{{ qualityReports.length }} 个报告</el-tag>
          </div>
        </div>
      </template>
      
      <div v-if="qualityReports.length === 0" class="empty-state">
        <el-icon class="empty-icon"><Document /></el-icon>
        <p>暂无检测报告</p>
        <span>请先进行数据质量检测</span>
      </div>
      
      <div v-else class="reports-grid">
        <div 
          v-for="report in qualityReports" 
          :key="report.id"
          class="report-item"
          :class="getReportStatusClass(report.pass_rate)"
        >
          <div class="report-header">
            <div class="report-info">
              <div class="report-title">
                <el-icon class="report-icon"><Document /></el-icon>
                <span>{{ report.table_name }}</span>
              </div>
              <el-tag :type="getReportStatusType(report.pass_rate)" size="small">
                {{ getReportStatusText(report.pass_rate) }}
              </el-tag>
            </div>
            <div class="report-actions">
              <el-button size="small" type="primary" @click="viewReport(report)">
                <el-icon><View /></el-icon>
                查看
              </el-button>
              <el-button size="small" type="info" @click="exportReport(report)">
                <el-icon><Download /></el-icon>
                导出
              </el-button>
              <el-button size="small" type="danger" @click="deleteReport(report)">
                <el-icon><Delete /></el-icon>
                删除
              </el-button>
            </div>
          </div>
          
          <div class="report-content">
            <div class="report-details">
              <div class="detail-row">
                <div class="detail-item">
                  <span class="label">规则库:</span>
                  <span class="value">{{ report.rule_library_name }}</span>
                </div>
                <div class="detail-item">
                  <span class="label">版本:</span>
                  <span class="value">{{ report.version }}</span>
                </div>
              </div>
              
              <div class="detail-row">
                <div class="detail-item">
                  <span class="label">总记录:</span>
                  <span class="value">{{ report.total_records }}</span>
                </div>
                <div class="detail-item">
                  <span class="label">通过:</span>
                  <span class="value success">{{ report.passed_records }}</span>
                </div>
                <div class="detail-item">
                  <span class="label">失败:</span>
                  <span class="value danger">{{ report.failed_records }}</span>
                </div>
              </div>
              
              <div class="pass-rate-section">
                <div class="rate-header">
                  <span class="rate-label">通过率</span>
                  <span class="rate-value">{{ report.pass_rate }}%</span>
                </div>
                <el-progress
                  :percentage="report.pass_rate"
                  :color="getProgressColor(report.pass_rate)"
                  :stroke-width="8"
                  :show-text="false"
                />
              </div>
              
              <div class="report-meta">
                <div class="meta-item">
                  <span class="label">执行时间:</span>
                  <span class="value">{{ report.execution_time?.toFixed(2) }}s</span>
                </div>
                <div class="meta-item">
                  <span class="label">检测时间:</span>
                  <span class="value">{{ formatDate(report.created_at) }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </el-card>
    </el-card>
    
    <!-- 报告详情对话框 -->
    <el-dialog v-model="showReportDetail" title="检测报告详情" width="1200px" class="detail-dialog">
      <template #header>
        <div class="dialog-header">
          <el-icon class="dialog-icon"><Document /></el-icon>
          <span>检测报告详情</span>
        </div>
      </template>
      
      <div v-if="reportDetail" class="detail-content">
        <!-- 基本信息 -->
        <div class="detail-section">
          <h4 class="section-title">基本信息</h4>
          <div class="info-grid">
            <div class="info-item">
              <span class="label">报告ID:</span>
              <span class="value">{{ reportDetail.id }}</span>
            </div>
            <div class="info-item">
              <span class="label">数据表:</span>
              <span class="value">{{ reportDetail.table_name }}</span>
            </div>
            <div class="info-item">
              <span class="label">规则库:</span>
              <span class="value">{{ reportDetail.rule_library_name }}</span>
            </div>
            <div class="info-item">
              <span class="label">总记录数:</span>
              <span class="value">{{ reportDetail.total_records }}</span>
            </div>
            <div class="info-item">
              <span class="label">通过记录数:</span>
              <span class="value success">{{ reportDetail.passed_records }}</span>
            </div>
            <div class="info-item">
              <span class="label">失败记录数:</span>
              <span class="value danger">{{ reportDetail.failed_records }}</span>
            </div>
            <div class="info-item">
              <span class="label">通过率:</span>
              <span class="value">{{ reportDetail.pass_rate }}%</span>
            </div>
            <div class="info-item">
              <span class="label">执行时间:</span>
              <span class="value">{{ reportDetail.execution_time }}s</span>
            </div>
            <div class="info-item">
              <span class="label">创建时间:</span>
              <span class="value">{{ reportDetail.created_at }}</span>
            </div>
            <div class="info-item">
              <span class="label">检查类型:</span>
              <span class="value">{{ reportDetail.check_type === 'rule' ? '规则检查' : '其他' }}</span>
            </div>
          </div>
          
          <!-- 规则统计 -->
          <!-- <div class="stats-summary" v-if="reportDetail.summary">
            <h5 class="stats-title">规则统计</h5>
            <div class="stats-grid">
              <div class="stat-item">
                <span class="stat-label">总规则数</span>
                <span class="stat-value">{{ reportDetail.summary.total_rules }}</span>
              </div>
              <div class="stat-item success">
                <span class="stat-label">通过规则</span>
                <span class="stat-value">{{ reportDetail.summary.passed_rules }}</span>
              </div>
              <div class="stat-item danger">
                <span class="stat-label">失败规则</span>
                <span class="stat-value">{{ reportDetail.summary.failed_rules }}</span>
              </div>
              <div class="stat-item">
                <span class="stat-label">平均通过率</span>
                <span class="stat-value">{{ reportDetail.summary.avg_rule_pass_rate }}%</span>
              </div>
            </div>
          </div> -->
        </div>
        
        <!-- 规则检查结果 -->
        <!-- <div class="detail-section">
          <h4 class="section-title">详细规则检查结果</h4>
          <div class="rules-grid">
            <div 
              v-for="rule in reportDetail.rule_results" 
              :key="rule.rule_name"
              class="rule-result-item"
              :class="rule.failed_count > 0 ? 'failed' : 'passed'"
            >
              <div class="rule-header">
                <div class="rule-info">
                  <span class="rule-name">{{ rule.rule_name }}</span>
                  <span class="rule-field">{{ rule.field_name }}</span>
                </div>
                <el-tag :type="rule.failed_count > 0 ? 'danger' : 'success'" size="small">
                  {{ rule.failed_count > 0 ? '失败' : '通过' }}
                </el-tag>
              </div>
              
              <div class="rule-content">
                <div class="rule-stats">
                  <div class="stat-item">
                    <span class="label">类型:</span>
                    <span class="value">{{ rule.rule_type }}</span>
                  </div>
                  <div class="stat-item">
                    <span class="label">通过:</span>
                    <span class="value success">{{ rule.passed_count }}</span>
                  </div>
                  <div class="stat-item">
                    <span class="label">失败:</span>
                    <span class="value danger">{{ rule.failed_count }}</span>
                  </div>
                </div>
                
                <div class="rule-progress">
                  <div class="progress-header">
                    <span class="progress-label">通过率</span>
                    <span class="progress-value">{{ rule.pass_rate }}%</span>
                  </div>
                  <el-progress
                    :percentage="rule.pass_rate"
                    :color="getProgressColor(rule.pass_rate)"
                    :stroke-width="6"
                    :show-text="false"
                  />
                </div>
              </div>
            </div>
          </div>
        </div> -->
        
        <!-- 失败记录详情 -->
        <div v-if="reportDetail.failed_records && reportDetail.failed_records.length > 0" class="detail-section">
          <h4 class="section-title">失败记录详情</h4>
          <div class="failed-records">
            <el-table :data="reportDetail.failed_records" style="width: 100%" height="300" border>
              <el-table-column
                v-for="field in reportDetail.fields"
                :key="field"
                :prop="field"
                :label="field"
                show-overflow-tooltip
              />
            </el-table>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { Download, Refresh, Document, View, CircleCheck, CircleClose, Delete } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import axios from 'axios'

export default {
  name: 'QualityReport',
  components: {
    Download,
    Refresh,
    Document,
    View,
    CircleCheck,
    CircleClose,
    Delete
  },
  setup() {
    const qualityReports = ref([])
    const showReportDetail = ref(false)
    const reportDetail = ref(null)
    const loading = ref(false)
    
    const totalChecks = computed(() => qualityReports.value.length)
    
    const avgPassRate = computed(() => {
      if (qualityReports.value.length === 0) return 0
      const totalRate = qualityReports.value.reduce((sum, report) => sum + report.pass_rate, 0)
      return Math.round(totalRate / qualityReports.value.length)
    })
    
    const totalRecords = computed(() => {
      return qualityReports.value.reduce((sum, report) => sum + report.total_records, 0)
    })
    
    const totalFailed = computed(() => {
      return qualityReports.value.reduce((sum, report) => sum + report.failed_records, 0)
    })
    
    const loadReports = async () => {
      try {
        const response = await axios.get('/api/quality/results')
        if (response.data.success) {
          qualityReports.value = response.data.data
        }
      } catch (error) {
        ElMessage.error('加载报告失败')
      }
    }
    
    const viewReport = async (report) => {
      try {
        loading.value = true
        const response = await axios.get(`/api/quality/results/${report.id}`)
        if (response.data.success) {
          reportDetail.value = response.data.data
          
          // 输出详情数据到控制台，方便调试
          console.log('=== 报告详情数据 ===')
          console.log('基本信息:', {
            id: reportDetail.value.id,
            table_name: reportDetail.value.table_name,
            total_records: reportDetail.value.total_records,
            pass_rate: reportDetail.value.pass_rate
          })
          console.log('规则结果数量:', reportDetail.value.rule_results?.length || 0)
          console.log('统计信息:', reportDetail.value.summary)
          console.log('完整数据:', reportDetail.value)
          console.log('=====================')
          
          showReportDetail.value = true
          ElMessage.success('报告详情加载成功')
        } else {
          ElMessage.error(response.data.error || '加载报告详情失败')
        }
      } catch (error) {
        console.error('加载报告详情错误:', error)
        ElMessage.error('网络错误，请重试')
      } finally {
        loading.value = false
      }
    }
    
    const exportReport = async (report) => {
      try {
        const response = await axios.get(`/api/quality/results/${report.id}/failed-records`)
        
        if (response.data.success) {
          const failedRecords = response.data.data.records
          
          if (failedRecords.length === 0) {
            ElMessage.info('该报告没有失败记录')
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
          link.download = `quality_failed_records_${report.id}_${new Date().toISOString().slice(0, 10)}.csv`
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
    
    const deleteReport = async (report) => {
      try {
        await ElMessageBox.confirm(
          `确定要删除报告 "${report.id}" 吗？此操作不可恢复。`,
          '确认删除',
          {
            confirmButtonText: '确定删除',
            cancelButtonText: '取消',
            type: 'warning',
          }
        )
        
        const response = await axios.delete(`/api/quality/results/${report.id}`)
        if (response.data.success) {
          ElMessage.success('报告删除成功')
          loadReports() // 重新加载报告列表
        } else {
          ElMessage.error(response.data.error || '删除失败')
        }
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error('删除报告失败')
        }
      }
    }
    
    const exportAllReports = () => {
      const dataStr = JSON.stringify(qualityReports.value, null, 2)
      const dataBlob = new Blob([dataStr], { type: 'application/json' })
      const url = URL.createObjectURL(dataBlob)
      const link = document.createElement('a')
      link.href = url
      link.download = 'all_quality_reports.json'
      link.click()
      URL.revokeObjectURL(url)
      ElMessage.success('所有报告导出成功')
    }
    
    const refreshReports = () => {
      loadReports()
      ElMessage.success('报告已刷新')
    }
    
    const getProgressColor = (rate) => {
      if (rate >= 90) return '#67C23A'
      if (rate >= 70) return '#E6A23C'
      return '#F56C6C'
    }
    
    const getReportStatusClass = (rate) => {
      if (rate >= 90) return 'excellent'
      if (rate >= 70) return 'good'
      return 'poor'
    }
    
    const getReportStatusType = (rate) => {
      if (rate >= 90) return 'success'
      if (rate >= 70) return 'warning'
      return 'danger'
    }
    
    const getReportStatusText = (rate) => {
      if (rate >= 90) return '优秀'
      if (rate >= 70) return '良好'
      return '需改进'
    }
    
    const formatDate = (dateString) => {
      if (!dateString) return '未知'
      return new Date(dateString).toLocaleString('zh-CN')
    }
    
    onMounted(() => {
      loadReports()
    })
    
    return {
      qualityReports,
      showReportDetail,
      reportDetail,
      loading,
      totalChecks,
      avgPassRate,
      totalRecords,
      totalFailed,
      viewReport,
      exportReport,
      deleteReport,
      exportAllReports,
      refreshReports,
      getProgressColor,
      getReportStatusClass,
      getReportStatusType,
      getReportStatusText,
      formatDate
    }
  }
}
</script>

<style scoped>
.quality-report {
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

.stats-card,
.reports-card {
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
  gap: 12px;
}

.action-btn {
  border-radius: 8px;
  font-weight: 600;
  transition: all 0.3s ease;
}

.action-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 24px;
  padding: 10px 0;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 24px;
  background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
  border: 2px solid #e9ecef;
  border-radius: 12px;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.stat-item::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, #3498db, #2980b9);
  transform: scaleX(0);
  transition: transform 0.3s ease;
}

.stat-item:hover {
  background: linear-gradient(135deg, #ecf5ff 0%, #e1f0ff 100%);
  border-color: #3498db;
  transform: translateY(-4px);
  box-shadow: 0 12px 40px rgba(52, 152, 219, 0.15);
}

.stat-item:hover::before {
  transform: scaleX(1);
}

.stat-icon {
  font-size: 32px;
  color: #3498db;
  background: rgba(52, 152, 219, 0.1);
  border-radius: 12px;
  padding: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.stat-icon.success {
  color: #27ae60;
  background: rgba(39, 174, 96, 0.1);
}

.stat-icon.warning {
  color: #f39c12;
  background: rgba(243, 156, 18, 0.1);
}

.stat-icon.danger {
  color: #e74c3c;
  background: rgba(231, 76, 60, 0.1);
}

.stat-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stat-number {
  font-size: 32px;
  font-weight: 700;
  color: #2c3e50;
}

.stat-number.success {
  color: #27ae60;
}

.stat-number.warning {
  color: #f39c12;
}

.stat-number.danger {
  color: #e74c3c;
}

.stat-label {
  font-size: 14px;
  color: #7f8c8d;
  font-weight: 500;
}

.empty-state {
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

.empty-state p {
  margin-bottom: 8px;
  font-size: 18px;
  font-weight: 600;
  color: #2c3e50;
}

.empty-state span {
  font-size: 14px;
  color: #7f8c8d;
}

.reports-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
  gap: 24px;
  padding: 10px 0;
}

.report-item {
  background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
  border: 2px solid #e9ecef;
  border-radius: 12px;
  overflow: hidden;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
}

.report-item::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, #3498db, #2980b9);
  transform: scaleX(0);
  transition: transform 0.3s ease;
}

.report-item:hover {
  background: linear-gradient(135deg, #ecf5ff 0%, #e1f0ff 100%);
  border-color: #3498db;
  transform: translateY(-6px);
  box-shadow: 0 16px 50px rgba(52, 152, 219, 0.15);
}

.report-item:hover::before {
  transform: scaleX(1);
}

.report-item.excellent::before {
  background: linear-gradient(90deg, #27ae60, #2ecc71);
}

.report-item.good::before {
  background: linear-gradient(90deg, #f39c12, #f1c40f);
}

.report-item.poor::before {
  background: linear-gradient(90deg, #e74c3c, #c0392b);
}

.report-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  padding: 16px 20px;
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  border-bottom: 2px solid #e9ecef;
  min-height: 80px;
}

.report-info {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 8px;
  flex: 1;
  min-width: 0;
}

.report-title {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
}

.report-icon {
  font-size: 20px;
  color: #3498db;
  background: rgba(52, 152, 219, 0.1);
  border-radius: 8px;
  padding: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.report-title span {
  font-size: 16px;
  font-weight: 600;
  color: #2c3e50;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
}

.report-actions {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  align-items: center;
  min-width: 200px;
  justify-content: flex-end;
  background: rgba(255, 255, 255, 0.1);
  padding: 6px;
  border-radius: 6px;
}

.report-actions .el-button {
  border-radius: 6px;
  font-weight: 500;
  transition: all 0.3s ease;
  min-width: 50px;
  height: 28px;
  font-size: 11px;
}

.report-actions .el-button:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.report-actions .el-button--danger {
  background: linear-gradient(135deg, #e74c3c, #c0392b);
  border: none;
}

.report-actions .el-button--info {
  background: linear-gradient(135deg, #3498db, #2980b9);
  border: none;
}

.report-content {
  padding: 20px;
  background: rgba(255, 255, 255, 0.9);
}

.report-details {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.detail-row {
  display: flex;
  gap: 20px;
  flex-wrap: wrap;
}

.detail-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
}

.detail-item .label {
  font-weight: 600;
  color: #34495e;
  min-width: 60px;
}

.detail-item .value {
  color: #7f8c8d;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
}

.detail-item .value.success {
  color: #27ae60;
  font-weight: 600;
}

.detail-item .value.danger {
  color: #e74c3c;
  font-weight: 600;
}

.pass-rate-section {
  background: rgba(52, 152, 219, 0.05);
  border-radius: 8px;
  padding: 16px;
  border-left: 3px solid #3498db;
}

.rate-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.rate-label {
  font-size: 14px;
  font-weight: 600;
  color: #2c3e50;
}

.rate-value {
  font-size: 16px;
  font-weight: 700;
  color: #3498db;
}

.report-meta {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 12px;
  background: rgba(52, 152, 219, 0.05);
  border-radius: 6px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
}

.meta-item .label {
  font-weight: 600;
  color: #34495e;
  min-width: 80px;
}

.meta-item .value {
  color: #7f8c8d;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
}

.detail-dialog {
  border-radius: 12px;
  overflow: hidden;
}

.dialog-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 0;
}

.dialog-icon {
  font-size: 24px;
  color: #3498db;
  background: linear-gradient(135deg, #3498db, #2980b9);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.detail-content {
  padding: 10px 0;
}

.detail-section {
  margin-bottom: 32px;
}

.section-title {
  font-size: 18px;
  font-weight: 600;
  color: #2c3e50;
  margin-bottom: 16px;
  padding-bottom: 8px;
  border-bottom: 2px solid #e9ecef;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px;
  background: rgba(52, 152, 219, 0.05);
  border-radius: 8px;
  border-left: 3px solid #3498db;
}

.info-item .label {
  font-weight: 600;
  color: #34495e;
  min-width: 100px;
}

.info-item .value {
  color: #7f8c8d;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
}

/* 规则统计样式 */
.stats-summary {
  margin-top: 24px;
  padding: 20px;
  background: #f8fafc;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
}

.stats-title {
  margin: 0 0 16px 0;
  font-size: 16px;
  font-weight: 600;
  color: #2d3748;
  display: flex;
  align-items: center;
  gap: 8px;
}

.stats-title::before {
  content: '';
  width: 4px;
  height: 16px;
  background: #4299e1;
  border-radius: 2px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 16px;
}

.stats-grid .stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 16px 12px;
  background: white;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
  transition: all 0.2s ease;
}

.stats-grid .stat-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.stats-grid .stat-item.success {
  border-color: #68d391;
  background: linear-gradient(135deg, #f0fff4 0%, #c6f6d5 100%);
}

.stats-grid .stat-item.danger {
  border-color: #fc8181;
  background: linear-gradient(135deg, #fff5f5 0%, #fed7d7 100%);
}

.stat-label {
  font-size: 12px;
  color: #6b7280;
  margin-bottom: 4px;
  text-align: center;
}

.stat-value {
  font-size: 20px;
  font-weight: 700;
  color: #1a202c;
}

.stats-grid .stat-item.success .stat-value {
  color: #22543d;
}

.stats-grid .stat-item.danger .stat-value {
  color: #c53030;
}

.info-item .value.success {
  color: #27ae60;
  font-weight: 600;
}

.info-item .value.danger {
  color: #e74c3c;
  font-weight: 600;
}

.rules-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 20px;
}

.rule-result-item {
  background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
  border: 2px solid #e9ecef;
  border-radius: 12px;
  padding: 20px;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.rule-result-item::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  bottom: 0;
  width: 4px;
  background: #27ae60;
  transition: all 0.3s ease;
}

.rule-result-item.failed::before {
  background: #e74c3c;
}

.rule-result-item:hover {
  background: linear-gradient(135deg, #ecf5ff 0%, #e1f0ff 100%);
  border-color: #3498db;
  transform: translateX(4px);
  box-shadow: 0 8px 25px rgba(52, 152, 219, 0.15);
}

.rule-result-item:hover::before {
  transform: scaleY(1);
}

.rule-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
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
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.rule-stats {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
}

.rule-stats .stat-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
}

.rule-stats .label {
  font-weight: 600;
  color: #34495e;
}

.rule-stats .value {
  color: #7f8c8d;
}

.rule-stats .value.success {
  color: #27ae60;
  font-weight: 600;
}

.rule-stats .value.danger {
  color: #e74c3c;
  font-weight: 600;
}

.rule-progress {
  background: rgba(52, 152, 219, 0.05);
  border-radius: 6px;
  padding: 12px;
}

.progress-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.progress-label {
  font-size: 13px;
  font-weight: 600;
  color: #2c3e50;
}

.progress-value {
  font-size: 14px;
  font-weight: 700;
  color: #3498db;
}

.failed-records {
  background: rgba(231, 76, 60, 0.05);
  border-radius: 8px;
  padding: 16px;
  border: 1px solid rgba(231, 76, 60, 0.2);
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .stats-grid {
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  }
  
  .reports-grid {
    grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  }
  
  .rules-grid {
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  }
}

@media (max-width: 768px) {
  .quality-report {
    padding: 15px;
  }
  
  .page-header h2 {
    font-size: 24px;
  }
  
  .stats-grid {
    grid-template-columns: 1fr;
  }
  
  .reports-grid {
    grid-template-columns: 1fr;
  }
  
  .report-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
  
  .report-actions {
    width: 100%;
    justify-content: flex-end;
    flex-wrap: wrap;
  }
  
  .detail-row {
    flex-direction: column;
    gap: 12px;
  }
  
  .rules-grid {
    grid-template-columns: 1fr;
  }
  
  .rule-stats {
    flex-direction: column;
    gap: 8px;
  }
}
</style> 