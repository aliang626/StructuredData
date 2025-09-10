<template>
  <div class="rule-library">
    <!-- 页面标题 -->
    <div class="page-header">
      <h2>规则库管理</h2>
      <p>管理质量检测规则库，支持版本控制和规则查看</p>
    </div>

    <!-- 规则库列表 -->
    <el-card class="library-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <el-icon class="header-icon"><Document /></el-icon>
            <span class="header-title">规则库列表</span>
            <el-tag type="info" size="small">{{ ruleLibraries.length }} 个规则库</el-tag>
          </div>
          <el-button type="primary" @click="showCreateDialog = true" class="create-btn">
            <el-icon><Plus /></el-icon>
            新建规则库
          </el-button>
        </div>
      </template>
      
      <div v-if="ruleLibraries.length === 0" class="empty-state">
        <el-icon class="empty-icon"><Document /></el-icon>
        <p>暂无规则库</p>
        <el-button type="primary" @click="showCreateDialog = true">创建第一个规则库</el-button>
      </div>
      
      <div v-else class="library-grid">
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
              <!-- 无版本模式下移除版本计数标签 -->
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
    </el-card>
    
    <!-- 创建规则库对话框 -->
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
    
    <!-- 版本管理对话框 -->
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
  </div>
</template>

<script>
import { ref, reactive, onMounted } from 'vue'
import { Plus, Document, View, Delete, Setting } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import axios from 'axios'

export default {
  name: 'RuleLibrary',
  components: {
    Plus,
    Document,
    View,
    Delete,
    Setting
  },
  setup() {
    const ruleLibraries = ref([])
    const showCreateDialog = ref(false)
    const showVersionDialog = ref(false)
    const selectedLibrary = ref(null)
    const libraryVersions = ref([])
    
    const libraryForm = reactive({
      name: '',
      description: ''
    })
    
    const loadRuleLibraries = async () => {
      try {
        const response = await axios.get('/api/rules/libraries')
        if (response.data.success) {
          ruleLibraries.value = response.data.data
        }
      } catch (error) {
        ElMessage.error('加载规则库失败')
      }
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
        
        const response = await axios.delete(`/api/rules/libraries/${library.id}`)
        if (response.data.success) {
          ElMessage.success('删除成功')
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
          let fieldTranslations = {}
          
          if (fields.length > 0) {
            try {
              const translateResp = await axios.post('/api/rules/field-mapping/translate', {
                fields: fields
              })
              if (translateResp.data?.success) {
                fieldTranslations = translateResp.data.data.translations
              }
            } catch (e) {
              console.warn('获取字段中文解释失败:', e)
            }
          }
          
          // 获取规则名称和类型的中文翻译
          let ruleTranslations = {}
          try {
            const ruleTranslateResp = await axios.post('/api/rules/field-mapping/translate-rules', {
              rules: rules
            })
            if (ruleTranslateResp.data?.success) {
              ruleTranslations = ruleTranslateResp.data.data.translations
            }
          } catch (e) {
            console.warn('获取规则名称和类型中文解释失败:', e)
          }
          
          const html = `
            <div style="max-height:520px;overflow:auto;text-align:left">
              ${rules.map((r, idx) => {
                const name = (r.name || `规则_${idx+1}`).replace(/</g,'&lt;')
                const field = (r.field || '-').replace(/</g,'&lt;')
                const type = (r.rule_type || '-').replace(/</g,'&lt;')
                const desc = (r.description || '').replace(/</g,'&lt;')
                
                // 获取字段的中文解释
                const chineseName = fieldTranslations[field] || field
                const fieldDisplay = chineseName !== field ? 
                  `${field} (${chineseName})` : field
                
                // 获取规则名称的中文解释
                const chineseRuleName = ruleTranslations[`name_${name}`] || name
                const nameDisplay = chineseRuleName !== name ? 
                  `${chineseRuleName} (${name})` : name
                
                // 获取规则类型的中文解释
                const chineseRuleType = ruleTranslations[`type_${type}`] || type
                const typeDisplay = chineseRuleType !== type ? 
                  `${chineseRuleType} (${type})` : type
                
                return `<div style=\"margin:10px 0;padding:10px;border-left:3px solid #409EFF;background:#f5f7fa\">`
                       + `<div style=\"font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis\" title=\"${nameDisplay}\">${nameDisplay}</div>`
                       + `<div style=\"font-size:12px;color:#606266\">字段: ${fieldDisplay} | 类型: ${typeDisplay}</div>`
                       + `<div style=\"font-size:12px;color:#909399\">${desc}</div>`
                       + `</div>`
              }).join('')}
            </div>`
          await ElMessageBox.alert(html, `${library.name} - 当前规则`, {
            dangerouslyUseHTMLString: true,
            confirmButtonText: '关闭'
          })
        }
      } catch (e) {
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
        let fieldTranslations = {}
        
        if (fields.length > 0) {
          try {
            const translateResp = await axios.post('/api/rules/field-mapping/translate', {
              fields: fields
            })
            if (translateResp.data?.success) {
              fieldTranslations = translateResp.data.data.translations
            }
          } catch (e) {
            console.warn('获取字段中文解释失败:', e)
          }
        }

        // 获取规则名称和类型的中文翻译
        let ruleTranslations = {}
        try {
          const ruleTranslateResp = await axios.post('/api/rules/field-mapping/translate-rules', {
            rules: rules
          })
          if (ruleTranslateResp.data?.success) {
            ruleTranslations = ruleTranslateResp.data.data.translations
          }
        } catch (e) {
          console.warn('获取规则名称和类型中文解释失败:', e)
        }

        // 弹窗展示简要规则明细
        const html = `
          <div style="max-height:480px;overflow:auto;text-align:left">
            ${rules.map((r, idx) => {
              const name = r.name || `规则_${idx+1}`
              const field = r.field || '-'
              const type = r.rule_type || '-'
              const desc = r.description || ''
              
              // 获取字段的中文解释
              const chineseName = fieldTranslations[field] || field
              const fieldDisplay = chineseName !== field ? 
                `${field} (${chineseName})` : field
              
              // 获取规则名称的中文解释
              const chineseRuleName = ruleTranslations[`name_${name}`] || name
              const nameDisplay = chineseRuleName !== name ? 
                `${chineseRuleName} (${name})` : name
              
              // 获取规则类型的中文解释
              const chineseRuleType = ruleTranslations[`type_${type}`] || type
              const typeDisplay = chineseRuleType !== type ? 
                `${chineseRuleType} (${type})` : type
              
              return `<div style=\"margin:8px 0;padding:8px;border-left:3px solid #409EFF;background:#f5f7fa\">`
                     + `<div style=\"font-weight:600\">${nameDisplay}</div>`
                     + `<div style=\"font-size:12px;color:#606266\">字段: ${fieldDisplay} | 类型: ${typeDisplay}</div>`
                     + `<div style=\"font-size:12px;color:#909399\">${desc}</div>`
                     + `</div>`
            }).join('')}
          </div>`

        await ElMessageBox.alert(html, `${version.version} - 规则明细`, {
          dangerouslyUseHTMLString: true,
          confirmButtonText: '关闭'
        })
      } catch (error) {
        ElMessage.error('查看规则失败')
      }
    }
    
    const deleteVersion = async (version) => {
      try {
        await ElMessageBox.confirm('确定要删除这个版本吗？', '提示', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        })
        
        const response = await axios.delete(`/api/rules/versions/${version.id}`)
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
      formatDate
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

.library-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 24px;
  padding: 10px 0;
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

.version-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: linear-gradient(135deg, #fdf6ec 0%, #faecd8 100%);
  border-bottom: 2px solid #faecd8;
}

.version-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.version-name {
  display: flex;
  align-items: center;
  gap: 8px;
}

.version-name span {
  font-size: 16px;
  font-weight: 600;
  color: #2c3e50;
}

.version-title {
  max-width: 360px;
  display: inline-block;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.version-icon {
  font-size: 20px;
  color: #f39c12;
  background: rgba(243, 156, 18, 0.1);
  border-radius: 8px;
  padding: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.version-actions {
  display: flex;
  gap: 8px;
}

.version-actions .el-button {
  border-radius: 6px;
  font-weight: 500;
  transition: all 0.3s ease;
}

.version-actions .el-button:hover {
  transform: translateY(-1px);
}

.version-content {
  padding: 16px 20px;
  background: rgba(255, 255, 255, 0.9);
}

.version-description {
  color: #7f8c8d;
  font-size: 14px;
  margin-bottom: 12px;
  line-height: 1.6;
  padding: 8px 12px;
  background: rgba(243, 156, 18, 0.05);
  border-radius: 6px;
  border-left: 3px solid #f39c12;
}

.version-details {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.empty-versions {
  text-align: center;
  padding: 60px 20px;
  color: #95a5a6;
}

.empty-versions .empty-icon {
  font-size: 80px;
  margin-bottom: 20px;
  color: #bdc3c7;
  opacity: 0.6;
}

.empty-versions p {
  margin-bottom: 8px;
  font-size: 18px;
  font-weight: 600;
  color: #2c3e50;
}

.empty-versions span {
  font-size: 14px;
  color: #7f8c8d;
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
  
  .version-grid {
    grid-template-columns: 1fr;
  }
  
  .version-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
  
  .version-actions {
    width: 100%;
    justify-content: flex-end;
  }
}
</style> 