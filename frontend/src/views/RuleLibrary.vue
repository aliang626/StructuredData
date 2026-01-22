<template>
  <div class="rule-library">
    <div class="page-header">
      <h2>规则库管理</h2>
      <p>管理质量检测规则库，支持版本控制和规则查看</p>
    </div>

    <el-card class="library-card" shadow="hover" v-loading="loading">
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <el-icon class="header-icon"><Document /></el-icon>
            <span class="header-title">规则库列表</span>
            <el-tag type="info" size="small">{{ total }} 个规则库</el-tag>
          </div>
          
          <div class="header-right">
            <el-input
              v-model="searchQuery"
              placeholder="搜索规则库名称或描述"
              class="search-input"
              clearable
              @clear="handleSearch"
              @keyup.enter="handleSearch"
            >
              <template #append>
                <el-button :icon="Search" @click="handleSearch" />
              </template>
            </el-input>
            
            <el-button type="primary" @click="showCreateDialog = true" class="create-btn">
              <el-icon><Plus /></el-icon>
              新建规则库
            </el-button>
          </div>
        </div>
      </template>
      
      <div v-if="ruleLibraries.length === 0 && !loading" class="empty-state">
        <el-icon class="empty-icon"><Document /></el-icon>
        <p>暂无规则库</p>
        <el-button type="primary" @click="showCreateDialog = true">创建第一个规则库</el-button>
      </div>
      
      <div v-else class="library-content-wrapper">
        <div class="library-grid">
          <div 
            v-for="library in ruleLibraries" 
            :key="library.id"
            class="library-item"
          >
            <div class="library-header">
              <div class="library-info">
                <div class="library-name" :title="library.name">
                  <el-icon class="library-icon"><Document /></el-icon>
                  <span class="library-title-text">{{ library.name }}</span>
                </div>
              </div>
              <div class="library-actions">
                <el-button size="small" type="primary" @click="viewLibraryRules(library)">
                  <el-icon><View /></el-icon>
                  查看
                </el-button>
                <el-button size="small" type="danger" @click="deleteLibrary(library)">
                  <el-icon><Delete /></el-icon>
                  删除
                </el-button>
              </div>
            </div>
            
            <div class="library-content">
              <p class="library-description">{{ library.description || '暂无描述' }}</p>
              
              <div class="library-details">
                <div class="detail-item">
                  <span class="label">创建时间:</span>
                  <span class="value">{{ formatDate(library.created_at) }}</span>
                </div>
                <div class="detail-item">
                  <span class="label">更新时间:</span>
                  <span class="value">{{ formatDate(library.updated_at) }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="pagination-container">
          <el-pagination
            :current-page="currentPage"
            :page-size="pageSize"
            :page-sizes="[20, 50, 100, 200]"
            :background="true"
            layout="total, sizes, prev, pager, next, jumper"
            :total="total"
            @size-change="handleSizeChange"
            @current-change="handleCurrentChange"
          />
        </div>
      </div>
    </el-card>
    
    <el-dialog v-model="showCreateDialog" title="创建规则库" width="600px" class="create-dialog">
      <template #header>
        <div class="dialog-header">
          <el-icon class="dialog-icon"><Plus /></el-icon>
          <span>创建规则库</span>
        </div>
      </template>
      
      <el-form :model="libraryForm" label-position="top" class="create-form">
        <el-form-item label="规则库名称" required>
          <el-input 
            v-model="libraryForm.name" 
            placeholder="输入规则库名称"
            size="large"
          />
        </el-form-item>
        <el-form-item label="描述">
          <el-input
            v-model="libraryForm.description"
            type="textarea"
            :rows="4"
            placeholder="输入规则库描述"
            size="large"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="showCreateDialog = false" size="large">取消</el-button>
          <el-button type="primary" @click="createLibrary" size="large">创建</el-button>
        </div>
      </template>
    </el-dialog>
    
    <el-dialog v-model="showVersionDialog" title="版本管理" width="900px" class="version-dialog">
      <template #header>
        <div class="dialog-header">
          <el-icon class="dialog-icon"><Setting /></el-icon>
          <span>{{ selectedLibrary?.name }} - 版本管理</span>
        </div>
      </template>
      
      <div v-if="selectedLibrary" class="version-content">
        <div class="version-header">
          <div class="version-info">
            <h4>版本列表</h4>
            <el-tag type="info" size="small">{{ libraryVersions.length }} 个版本</el-tag>
          </div>
        </div>
        
        <div v-if="libraryVersions.length === 0" class="empty-versions">
          <el-icon class="empty-icon"><Setting /></el-icon>
          <p>暂无版本</p>
          <span>基于“无版本模式”，当前库尚未保存版本。你仍可在质量检测页直接选择该库检测（系统将使用最新规则）。</span>
        </div>
        
        <div v-else class="version-grid">
          <div 
            v-for="version in libraryVersions" 
            :key="version.id"
            class="version-item"
          >
            <div class="version-header">
            <div class="version-info">
                <div class="version-name">
                  <el-icon class="version-icon"><Setting /></el-icon>
                <span class="version-title" :title="version.version">{{ version.version }}</span>
                </div>
                <el-tag type="primary" size="small">{{ version.rule_count }} 条规则</el-tag>
              </div>
              <div class="version-actions">
                <el-button size="small" type="primary" @click="viewRules(version)">
                  <el-icon><View /></el-icon>
                  查看
                </el-button>
              </div>
            </div>
            
            <div class="version-content">
              <p class="version-description">{{ version.description || '暂无描述' }}</p>
              
              <div class="version-details">
                <div class="detail-item">
                  <span class="label">创建时间:</span>
                  <span class="value">{{ formatDate(version.created_at) }}</span>
                </div>
                <div class="detail-item">
                  <span class="label">创建者:</span>
                  <span class="value">{{ version.created_by || '未知' }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </el-dialog>
    
    <el-dialog 
      v-model="showRuleListDialog" 
      :title="ruleListTitle" 
      width="900px"
      :close-on-click-modal="false"
      class="rule-list-dialog"
    >
      <div class="rules-container">
        <div 
          v-for="(rule, idx) in currentRules" 
          :key="idx"
          class="rule-card"
        >
          <div class="rule-card-header">
            <div class="rule-name">
              <span class="rule-name-text">
                {{ ruleTranslations[`name_${rule.name}`] || rule.name }}
              </span>
              <span v-if="ruleTranslations[`name_${rule.name}`]" class="rule-name-en">
                ({{ rule.name }})
              </span>
            </div>
            <el-button 
              type="primary" 
              size="small" 
              @click="viewRuleDetail(rule)"
            >
              <el-icon><View /></el-icon>
              查看详情
            </el-button>
          </div>
          <div class="rule-card-body">
            <div class="rule-info-row">
              <span class="rule-label">字段:</span>
              <span class="rule-value">
                {{ fieldTranslations[rule.field] ? 
                  `${rule.field} (${fieldTranslations[rule.field]})` : 
                  (rule.field || '-') 
                }}
              </span>
            </div>
            <div class="rule-info-row">
              <span class="rule-label">类型:</span>
              <span class="rule-value">
                {{ ruleTranslations[`type_${rule.rule_type}`] ? 
                  `${ruleTranslations[`type_${rule.rule_type}`]} (${rule.rule_type})` : 
                  (rule.rule_type || '-') 
                }}
              </span>
            </div>
            <div class="rule-info-row">
              <span class="rule-label">描述:</span>
              <span class="rule-value desc">{{ rule.description || '无描述' }}</span>
            </div>
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="showRuleListDialog = false" size="large">关闭</el-button>
      </template>
    </el-dialog>
    
    <el-dialog 
      v-model="showRuleDetailDialog" 
      title="规则详细信息" 
      width="800px"
      :close-on-click-modal="false"
      class="rule-detail-dialog"
    >
      <div v-if="currentRuleDetail" class="rule-detail-content">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="规则名称" :span="2">
            {{ ruleTranslations[`name_${currentRuleDetail.name}`] || currentRuleDetail.name }}
            <span v-if="ruleTranslations[`name_${currentRuleDetail.name}`]" style="color: #909399; font-size: 12px; margin-left: 8px;">
              ({{ currentRuleDetail.name }})
            </span>
          </el-descriptions-item>
          <el-descriptions-item label="字段名称">
            {{ fieldTranslations[currentRuleDetail.field] || currentRuleDetail.field || '-' }}
            <span v-if="fieldTranslations[currentRuleDetail.field]" style="color: #909399; font-size: 12px;">
              ({{ currentRuleDetail.field }})
            </span>
          </el-descriptions-item>
          <el-descriptions-item label="规则类型">
            {{ ruleTranslations[`type_${currentRuleDetail.rule_type}`] || currentRuleDetail.rule_type || '-' }}
            <span v-if="ruleTranslations[`type_${currentRuleDetail.rule_type}`]" style="color: #909399; font-size: 12px;">
              ({{ currentRuleDetail.rule_type }})
            </span>
          </el-descriptions-item>
          <el-descriptions-item label="描述" :span="2">
            {{ currentRuleDetail.description || '无描述' }}
          </el-descriptions-item>
        </el-descriptions>
        
        <div v-if="currentRuleDetail.params && getParamsTableData(currentRuleDetail.params).length > 0" class="detail-section">
          <h4>参数信息</h4>
          <el-table :data="getParamsTableData(currentRuleDetail.params)" border size="small">
            <el-table-column prop="key" label="参数名" width="200" />
            <el-table-column prop="value" label="参数值">
              <template #default="{ row }">
                <pre class="param-value">{{ row.value }}</pre>
              </template>
            </el-table-column>
          </el-table>
        </div>
        
        <div v-if="currentRuleDetail.params && getIntervalsData(currentRuleDetail.params).length > 0" class="detail-section">
          <h4>深度段规则信息</h4>
          <div class="intervals-container">
            <el-collapse accordion>
              <el-collapse-item 
                v-for="(interval, index) in getIntervalsData(currentRuleDetail.params)" 
                :key="index"
                :name="index"
              >
                <template #title>
                  <div class="interval-title">
                    <el-tag type="info" size="small">深度段 {{ index + 1 }}</el-tag>
                    <span class="interval-range">{{ interval.start_depth }}m - {{ interval.end_depth }}m</span>
                  </div>
                </template>
                
                <div class="interval-content">
                  <div class="interval-stats">
                    <el-descriptions :column="2" size="small" border>
                      <el-descriptions-item label="数据点数">{{ interval.count }}</el-descriptions-item>
                      <el-descriptions-item label="平均值">{{ interval.mean?.toFixed(2) }}</el-descriptions-item>
                      <el-descriptions-item label="标准差">{{ interval.std?.toFixed(2) }}</el-descriptions-item>
                      <el-descriptions-item label="最小值">{{ interval.min?.toFixed(2) }}</el-descriptions-item>
                      <el-descriptions-item label="最大值">{{ interval.max?.toFixed(2) }}</el-descriptions-item>
                    </el-descriptions>
                  </div>
                  
                  <div v-if="interval.regex_pattern" class="interval-item">
                    <div class="interval-label">正则表达式：</div>
                    <el-input
                      :value="interval.regex_pattern"
                      readonly
                      size="small"
                      class="regex-input"
                    />
                  </div>
                  
                  <div v-if="interval.validation_sql" class="interval-item">
                    <div class="interval-label">验证SQL：</div>
                    <el-input
                      type="textarea"
                      :value="interval.validation_sql"
                      :rows="4"
                      readonly
                      size="small"
                      class="sql-textarea"
                    />
                  </div>
                </div>
              </el-collapse-item>
            </el-collapse>
          </div>
        </div>
        
        <div v-if="currentRuleDetail.validation_sql" class="detail-section">
          <h4>验证SQL</h4>
          <el-input
            type="textarea"
            :value="currentRuleDetail.validation_sql"
            :rows="6"
            readonly
            class="sql-textarea"
          />
        </div>
        
        <div v-if="currentRuleDetail.regex_pattern" class="detail-section">
          <h4>正则表达式</h4>
          <el-input
            :value="currentRuleDetail.regex_pattern"
            readonly
            class="regex-input"
          />
        </div>
      </div>
      <template #footer>
        <el-button @click="showRuleDetailDialog = false" size="large">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, onMounted } from 'vue'
import { Plus, Document, View, Delete, Setting, Search } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import axios from 'axios'

export default {
  name: 'RuleLibrary',
  components: {
    Plus,
    Document,
    View,
    Delete,
    Setting,
    Search
  },
  setup() {
    const ruleLibraries = ref([])
    const loading = ref(false) // 加载状态
    const showCreateDialog = ref(false)
    const showVersionDialog = ref(false)
    const selectedLibrary = ref(null)
    const libraryVersions = ref([])
    const showRuleListDialog = ref(false)
    const showRuleDetailDialog = ref(false)
    const currentRules = ref([])
    const currentRuleDetail = ref(null)
    const ruleListTitle = ref('')
    const fieldTranslations = ref({})
    const ruleTranslations = ref({})
    
    // 分页和搜索状态
    const searchQuery = ref('')
    const currentPage = ref(1)
    const pageSize = ref(12)
    const total = ref(0)
    
    const libraryForm = reactive({
      name: '',
      description: ''
    })
    
    const loadRuleLibraries = async () => {
      loading.value = true
      try {
        const response = await axios.get('/api/rules/libraries', {
          params: {
            page: currentPage.value,
            page_size: pageSize.value,
            search: searchQuery.value
          }
        })
        
        if (response.data.success) {
          const resData = response.data.data
          // 兼容后端不同返回结构（数组或对象）
          if (Array.isArray(resData)) {
            ruleLibraries.value = resData
            total.value = resData.length
          } else {
            ruleLibraries.value = resData.items || []
            total.value = resData.total || 0
          }
        }
      } catch (error) {
        ElMessage.error('加载规则库失败')
      } finally {
        loading.value = false
      }
    }
    
    // 搜索处理
    const handleSearch = () => {
      currentPage.value = 1 // 搜索时重置到第一页
      loadRuleLibraries()
    }
    
    // 分页处理
    const handleSizeChange = (val) => {
      pageSize.value = val
      currentPage.value = 1 // 改变页大小时重置到第一页
      loadRuleLibraries()
    }
    
    const handleCurrentChange = (val) => {
      currentPage.value = val
      loadRuleLibraries()
    }
    
    const createLibrary = async () => {
      if (!libraryForm.name.trim()) {
        ElMessage.warning('请输入规则库名称')
        return
      }
      
      try {
        const response = await axios.post('/api/rules/libraries', libraryForm)
        if (response.data.success) {
          ElMessage.success('规则库创建成功')
          showCreateDialog.value = false
          libraryForm.name = ''
          libraryForm.description = ''
          loadRuleLibraries()
        }
      } catch (error) {
        ElMessage.error('创建规则库失败')
      }
    }
    
    const deleteLibrary = async (library) => {
      try {
        await ElMessageBox.confirm('确定要删除这个规则库吗？', '提示', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        })
        
        const response = await axios.post(`/api/rules/libraries/${library.id}/delete`)
        if (response.data.success) {
          ElMessage.success('删除成功')
          // 如果当前页数据全部删除，且不是第一页，则跳转到上一页
          if (ruleLibraries.value.length === 1 && currentPage.value > 1) {
            currentPage.value--
          }
          loadRuleLibraries()
        }
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error('删除失败')
        }
      }
    }
    
    const viewVersions = async (library) => {
      selectedLibrary.value = library
      showVersionDialog.value = true
      
      try {
        const response = await axios.get(`/api/rules/libraries/${library.id}/versions`)
        if (response.data.success) {
          libraryVersions.value = response.data.data
        }
      } catch (error) {
        ElMessage.error('加载版本失败')
      }
    }

    // 新增：直接查看该库当前规则（无版本模式）
    const viewLibraryRules = async (library) => {
      try {
        // 直接读取当前规则
        const resp = await axios.get(`/api/rules/libraries/${library.id}/rules`)
        if (resp.data?.success) {
          const rules = resp.data.data || []
          if (!rules.length) {
            ElMessage.info('该规则库暂无规则，请先在规则生成页保存')
            return
          }
          
          // 获取所有字段的中文解释
          const fields = [...new Set(rules.map(r => r.field).filter(Boolean))]
          fieldTranslations.value = {}
          
          if (fields.length > 0) {
            try {
              const translateResp = await axios.post('/api/rules/field-mapping/translate', {
                fields: fields
              })
              if (translateResp.data?.success) {
                fieldTranslations.value = translateResp.data.data.translations
              }
            } catch (e) {
              console.warn('获取字段中文解释失败:', e)
            }
          }
          
          // 获取规则名称和类型的中文翻译
          ruleTranslations.value = {}
          try {
            const ruleTranslateResp = await axios.post('/api/rules/field-mapping/translate-rules', {
              rules: rules
            })
            if (ruleTranslateResp.data?.success) {
              ruleTranslations.value = ruleTranslateResp.data.data.translations
            }
          } catch (e) {
            console.warn('获取规则名称和类型中文解释失败:', e)
          }
          
          // 设置数据并打开对话框
          currentRules.value = rules
          ruleListTitle.value = `${library.name} - 当前规则`
          showRuleListDialog.value = true
        }
      } catch (e) {
        console.error('查看规则失败:', e)
        ElMessage.error('查看规则失败')
      }
    }
    
    const viewRules = async (version) => {
      try {
        const rules = version.rules || []
        if (!rules || rules.length === 0) {
          ElMessage.info('该版本暂无规则')
          return
        }

        // 获取所有字段的中文解释
        const fields = [...new Set(rules.map(r => r.field).filter(Boolean))]
        fieldTranslations.value = {}
        
        if (fields.length > 0) {
          try {
            const translateResp = await axios.post('/api/rules/field-mapping/translate', {
              fields: fields
            })
            if (translateResp.data?.success) {
              fieldTranslations.value = translateResp.data.data.translations
            }
          } catch (e) {
            console.warn('获取字段中文解释失败:', e)
          }
        }

        // 获取规则名称和类型的中文翻译
        ruleTranslations.value = {}
        try {
          const ruleTranslateResp = await axios.post('/api/rules/field-mapping/translate-rules', {
            rules: rules
          })
          if (ruleTranslateResp.data?.success) {
            ruleTranslations.value = ruleTranslateResp.data.data.translations
          }
        } catch (e) {
          console.warn('获取规则名称和类型中文解释失败:', e)
        }

        // 设置数据并打开对话框
        currentRules.value = rules
        ruleListTitle.value = `${version.version} - 规则明细`
        showRuleListDialog.value = true
      } catch (error) {
        console.error('查看规则失败:', error)
        ElMessage.error('查看规则失败')
      }
    }
    
    // 查看单个规则详情
    const viewRuleDetail = (rule) => {
      currentRuleDetail.value = rule
      showRuleDetailDialog.value = true
    }
    
    // 将参数对象转换为表格数据（排除intervals）
    const getParamsTableData = (params) => {
      if (!params || typeof params !== 'object') return []
      return Object.entries(params)
        .filter(([key]) => key !== 'intervals') // 排除intervals参数
        .map(([key, value]) => ({
          key,
          value: typeof value === 'object' ? JSON.stringify(value, null, 2) : String(value)
        }))
    }
    
    // 获取intervals数据用于显示
    const getIntervalsData = (params) => {
      if (!params || !params.intervals || !Array.isArray(params.intervals)) return []
      return params.intervals
    }
    
    const deleteVersion = async (version) => {
      try {
        await ElMessageBox.confirm('确定要删除这个版本吗？', '提示', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        })
        
        const response = await axios.post(`/api/rules/versions/${version.id}/delete`)
        if (response.data.success) {
          ElMessage.success('删除成功')
          viewVersions(selectedLibrary.value)
        }
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error('删除失败')
        }
      }
    }
    
    const formatDate = (dateString) => {
      if (!dateString) return '未知'
      return new Date(dateString).toLocaleString('zh-CN')
    }
    
    onMounted(() => {
      loadRuleLibraries()
    })
    
    return {
      ruleLibraries,
      loading,
      showCreateDialog,
      showVersionDialog,
      selectedLibrary,
      libraryVersions,
      libraryForm,
      createLibrary,
      deleteLibrary,
      viewVersions,
      viewLibraryRules,
      viewRules,
      deleteVersion,
      formatDate,
      showRuleListDialog,
      showRuleDetailDialog,
      currentRules,
      currentRuleDetail,
      ruleListTitle,
      fieldTranslations,
      ruleTranslations,
      viewRuleDetail,
      getParamsTableData,
      getIntervalsData,
      Search, // Expose icon
      searchQuery,
      currentPage,
      pageSize,
      total,
      handleSearch,
      handleSizeChange,
      handleCurrentChange
    }
  }
}
</script>

<style scoped>
.rule-library {
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

.library-card {
  background: rgba(255, 255, 255, 0.95);
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  margin-bottom: 24px;
  /* 保证加载遮罩层圆角正常 */
  overflow: hidden; 
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0;
  flex-wrap: wrap; /* 小屏幕自动换行 */
  gap: 10px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.search-input {
  width: 250px;
  transition: all 0.3s;
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

.create-btn {
  border-radius: 8px;
  font-weight: 600;
  transition: all 0.3s ease;
  background: linear-gradient(135deg, #3498db, #2980b9);
  border: none;
}

.create-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(52, 152, 219, 0.3);
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
  margin-bottom: 20px;
  font-size: 16px;
  font-weight: 600;
  color: #2c3e50;
}

.library-content-wrapper {
  display: flex;
  flex-direction: column;
  min-height: 400px;
}

.library-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 24px;
  padding: 10px 0;
  flex: 1; /* 撑开高度 */
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
  padding-top: 20px;
  border-top: 1px solid #e9ecef;
}

.library-item {
  background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
  border: 2px solid #e9ecef;
  border-radius: 12px;
  overflow: hidden;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
}

.library-item::before {
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

.library-item:hover {
  background: linear-gradient(135deg, #ecf5ff 0%, #e1f0ff 100%);
  border-color: #3498db;
  transform: translateY(-6px);
  box-shadow: 0 16px 50px rgba(52, 152, 219, 0.15);
}

.library-item:hover::before {
  transform: scaleX(1);
}

.library-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  border-bottom: 2px solid #e9ecef;
}

.library-info {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0; /* 允许内部元素收缩 */
}

.library-icon {
  font-size: 24px;
  color: #3498db;
  background: rgba(52, 152, 219, 0.1);
  border-radius: 8px;
  padding: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.library-name {
  display: flex;
  align-items: center;
  gap: 8px;
}

.library-name span {
  font-size: 18px;
  font-weight: 600;
  color: #2c3e50;
}

.library-title-text {
  max-width: 520px;
  display: inline-block;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.library-actions {
  display: flex;
  gap: 8px;
}

.library-actions .el-button {
  border-radius: 6px;
  font-weight: 500;
  transition: all 0.3s ease;
}

.library-actions .el-button:hover {
  transform: translateY(-1px);
}

.library-content {
  padding: 20px;
  background: rgba(255, 255, 255, 0.9);
}

.library-description {
  color: #7f8c8d;
  font-size: 14px;
  margin-bottom: 16px;
  line-height: 1.6;
  padding: 8px 12px;
  background: rgba(52, 152, 219, 0.05);
  border-radius: 6px;
  border-left: 3px solid #3498db;
  height: 60px; /* 固定高度，保持卡片对齐 */
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.library-details {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.detail-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #7f8c8d;
}

.detail-item .label {
  font-weight: 600;
  color: #34495e;
  min-width: 70px;
}

.detail-item .value {
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
}

/* ... 对话框样式保持不变 ... */
.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.dialog-footer .el-button {
  border-radius: 8px;
  font-weight: 600;
  transition: all 0.3s ease;
}

.dialog-footer .el-button--primary {
  background: linear-gradient(135deg, #3498db, #2980b9);
  border: none;
}

.dialog-footer .el-button--primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(52, 152, 219, 0.3);
}

.create-dialog,
.version-dialog {
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

.create-form {
  padding: 10px 0;
}

.create-form .el-form-item {
  margin-bottom: 20px;
}

.create-form .el-form-item label {
  font-size: 14px;
  color: #2c3e50;
  font-weight: 600;
  margin-bottom: 8px;
}

.create-form .el-input__wrapper,
.create-form .el-textarea__wrapper {
  border-radius: 8px;
  border: 2px solid #e9ecef;
  transition: all 0.3s ease;
}

.create-form .el-input__wrapper:hover,
.create-form .el-textarea__wrapper:hover {
  border-color: #3498db;
}

.create-form .el-input__wrapper.is-focus,
.create-form .el-textarea__wrapper.is-focus {
  border-color: #3498db;
  box-shadow: 0 0 0 3px rgba(52, 152, 219, 0.1);
}

.version-content {
  padding: 10px 0;
}

.version-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding-bottom: 12px;
  border-bottom: 2px solid #e9ecef;
}

.version-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.version-info h4 {
  color: #2c3e50;
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.version-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 20px;
}

.version-item {
  background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
  border: 2px solid #e9ecef;
  border-radius: 12px;
  overflow: hidden;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
}

.version-item::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  bottom: 0;
  width: 4px;
  background: #f39c12;
  transition: all 0.3s ease;
}

.version-item:hover {
  background: linear-gradient(135deg, #fdf6ec 0%, #faecd8 100%);
  border-color: #f39c12;
  transform: translateX(4px);
  box-shadow: 0 8px 25px rgba(243, 156, 18, 0.15);
}

.version-item:hover::before {
  transform: scaleY(1);
}

/* 规则列表对话框样式 */
.rule-list-dialog .rules-container {
  max-height: 600px;
  overflow-y: auto;
  padding: 10px 0;
}

.rule-card {
  background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
  border: 2px solid #e9ecef;
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 16px;
  transition: all 0.3s ease;
  position: relative;
}

.rule-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, #409EFF, #67C23A);
  border-radius: 12px 12px 0 0;
}

.rule-card:hover {
  border-color: #409EFF;
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(64, 158, 255, 0.15);
}

.rule-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding-top: 8px;
}

.rule-name {
  flex: 1;
  min-width: 0;
}

.rule-name-text {
  font-size: 16px;
  font-weight: 600;
  color: #2c3e50;
  display: inline-block;
}

.rule-name-en {
  font-size: 12px;
  color: #909399;
  margin-left: 8px;
}

.rule-card-body {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.rule-info-row {
  display: flex;
  align-items: flex-start;
  font-size: 14px;
}

.rule-label {
  font-weight: 600;
  color: #606266;
  min-width: 50px;
  margin-right: 8px;
}

.rule-value {
  color: #909399;
  flex: 1;
  word-break: break-word;
}

.rule-value.desc {
  color: #7f8c8d;
  font-style: italic;
}

/* 规则详情对话框样式 */
.rule-detail-dialog .rule-detail-content {
  max-height: 600px;
  overflow-y: auto;
}

.detail-section {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #e9ecef;
}

.detail-section h4 {
  margin: 0 0 12px 0;
  color: #2c3e50;
  font-size: 16px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 8px;
}

.detail-section h4::before {
  content: '';
  width: 4px;
  height: 16px;
  background: linear-gradient(135deg, #409EFF, #67C23A);
  border-radius: 2px;
}

.param-value {
  margin: 0;
  padding: 8px;
  background: #f5f7fa;
  border-radius: 4px;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 12px;
  line-height: 1.5;
  color: #2c3e50;
  white-space: pre-wrap;
  word-break: break-all;
}

.sql-textarea {
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
}

.sql-textarea :deep(.el-textarea__inner) {
  background: #f5f7fa;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 13px;
  line-height: 1.6;
}

.regex-input :deep(.el-input__inner) {
  background: #f5f7fa;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 13px;
}

/* intervals样式 */
.intervals-container {
  margin-top: 10px;
}

.interval-title {
  display: flex;
  align-items: center;
  gap: 12px;
  font-weight: 600;
  color: #2c3e50;
}

.interval-range {
  font-size: 14px;
  color: #409EFF;
}

.interval-content {
  padding: 12px 0;
}

.interval-stats {
  margin-bottom: 16px;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
}

.interval-item {
  margin-bottom: 16px;
}

.interval-item:last-child {
  margin-bottom: 0;
}

.interval-label {
  font-size: 13px;
  font-weight: 600;
  color: #606266;
  margin-bottom: 8px;
  display: flex;
  align-items: center;
}

.interval-label::before {
  content: '▪';
  color: #409EFF;
  margin-right: 6px;
  font-size: 18px;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .library-grid {
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  }
  
  .version-grid {
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  }
}

@media (max-width: 768px) {
  .rule-library {
    padding: 15px;
  }
  
  .page-header h2 {
    font-size: 24px;
  }
  
  .library-grid {
    grid-template-columns: 1fr;
  }
  
  .library-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
  
  .library-actions {
    width: 100%;
    justify-content: flex-end;
  }
  
  .card-header {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .header-right {
    width: 100%;
    justify-content: space-between;
  }
  
  .search-input {
    flex: 1;
  }
}
</style>