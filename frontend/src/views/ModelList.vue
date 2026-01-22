<template>
  <div class="model-list">
    <!-- 页面标题 -->
    <div class="page-header">
      <h2>配置管理</h2>
      <p>管理机器学习模型的配置信息，支持导入导出和批量操作</p>
    </div>

    <!-- 搜索和筛选 -->
    <el-card class="search-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <el-icon class="header-icon"><Search /></el-icon>
            <span class="header-title">搜索筛选</span>
          </div>
        </div>
      </template>
      
      <el-row :gutter="20">
        <el-col :span="6">
          <el-input
            v-model="searchQuery"
            placeholder="搜索配置名称"
            clearable
            @input="handleSearch"
            size="large"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </el-col>
        <el-col :span="4">
          <el-select v-model="filterType" placeholder="模型类型" clearable @change="handleSearch" size="large" style="width: 100%">
            <el-option label="全部" value="" />
            <el-option label="回归模型" value="regression" />
            <el-option label="分类模型" value="classification" />
            <el-option label="聚类模型" value="clustering" />
            <el-option label="时间序列" value="time_series" />
          </el-select>
        </el-col>
        <el-col :span="4">
          <el-select v-model="filterStatus" placeholder="状态" clearable @change="handleSearch" size="large" style="width: 100%">
            <el-option label="全部" value="" />
            <el-option label="已启用" value="active" />
            <el-option label="已禁用" value="inactive" />
            <el-option label="草稿" value="draft" />
          </el-select>
        </el-col>
        <el-col :span="10">
          <div class="search-actions">
            <el-button type="primary" @click="handleSearch" size="large">
              <el-icon><Search /></el-icon>
              搜索
            </el-button>
            <el-button @click="resetSearch" size="large">
              <el-icon><Refresh /></el-icon>
              重置
            </el-button>
          </div>
        </el-col>
      </el-row>
    </el-card>

    <!-- 操作按钮 -->
    <div class="action-bar">
      <div class="action-left">
        <el-button type="primary" @click="$router.push('/model-config')" class="action-btn">
          <el-icon><Plus /></el-icon>
          新建配置
        </el-button>
        <el-button type="success" @click="importConfig" class="action-btn">
          <el-icon><Upload /></el-icon>
          导入配置
        </el-button>
        <el-button type="warning" @click="exportConfig" class="action-btn">
          <el-icon><Download /></el-icon>
          导出配置
        </el-button>
      </div>
      <div class="action-right">
        <el-button @click="refreshList" class="refresh-btn">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
    </div>

    <!-- 配置列表 -->
    <el-card class="list-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <el-icon class="header-icon"><Setting /></el-icon>
            <span class="header-title">配置列表</span>
            <el-tag type="info" size="small">{{ filteredConfigs.length }} 个配置</el-tag>
          </div>
        </div>
      </template>

      <div v-if="filteredConfigs.length === 0" class="empty-state">
        <el-icon class="empty-icon"><Setting /></el-icon>
        <p>暂无配置信息</p>
        <el-button type="primary" @click="$router.push('/model-config')">创建第一个配置</el-button>
      </div>

      <div v-else class="config-grid">
        <div 
          v-for="config in filteredConfigs" 
          :key="config.id" 
          class="config-item"
          :class="{ 'active': config.status === 'active' }"
        >
          <div class="config-header">
            <div class="config-info">
              <div class="config-name">
                <el-icon :color="getModelTypeColor(config.model_type)" class="config-icon">
                  <Setting />
                </el-icon>
                <span>{{ config.name }}</span>
              </div>
              <el-tag :type="getStatusType(config.status)" size="small">
                {{ getStatusName(config.status) }}
              </el-tag>
            </div>
            <div class="config-actions">
              <el-button size="small" type="primary" @click="editConfig(config)">
                <el-icon><Edit /></el-icon>
                编辑
              </el-button>
              <el-button size="small" type="danger" @click="deleteConfig(config)">
                <el-icon><Delete /></el-icon>
                删除
              </el-button>
            </div>
          </div>
          
          <div class="config-content">
            <p class="config-description">{{ config.description || '暂无描述' }}</p>
            
            <div class="config-details">
              <div class="detail-item">
                <span class="label">类型:</span>
                <el-tag :type="getModelTypeTag(config.model_type)" size="small">
                  {{ getModelTypeName(config.model_type) }}
                </el-tag>
              </div>
              <div class="detail-item">
                <span class="label">模型:</span>
                <span class="value">{{ config.model_name }}</span>
              </div>
              <div class="detail-item">
                <span class="label">创建:</span>
                <span class="value">{{ formatDate(config.created_at) }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script>
import { ref, reactive, computed, onMounted } from 'vue'
import { 
  Plus, Upload, Download, Search, Refresh, Setting, 
  Edit, CopyDocument, Switch, Delete 
} from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'

import axios from 'axios' // Added axios import

export default {
  name: 'ModelList',
  components: {
    Plus, Upload, Download, Search, Refresh, Setting,
    Edit, CopyDocument, Switch, Delete
  },
  setup() {
    const loading = ref(false)
    const searchQuery = ref('')
    const filterType = ref('')
    const filterStatus = ref('')
    const currentPage = ref(1)
    const pageSize = ref(20)
    const editDialogVisible = ref(false)
    const editForm = reactive({
      id: '',
      name: '',
      description: '',
      status: 'draft'
    })

    // 模拟配置数据
    const configs = ref([])
    const loadModelConfigs = async () => {
      loading.value = true
      try {
        console.log('正在加载模型配置列表...')
        const response = await axios.get('/api/models/configs')
        console.log('API响应:', response.data)
        
        if (response.data.success) {
          configs.value = response.data.data || []
          console.log(`成功加载 ${configs.value.length} 个模型配置`)
          
          if (configs.value.length === 0) {
            ElMessage.info('暂无模型配置，请先创建配置')
          }
        } else {
          console.error('API返回失败:', response.data.error)
          ElMessage.error(`加载失败: ${response.data.error}`)
          configs.value = []
        }
      } catch (error) {
        console.error('加载模型配置时发生错误:', error)
        configs.value = []
        
        if (error.response) {
          // 服务器返回了错误响应
          const status = error.response.status
          const errorMsg = error.response.data?.error || '服务器错误'
          console.error(`HTTP ${status}:`, errorMsg)
          
          if (status === 404) {
            ElMessage.error('API接口不存在，请检查后端服务')
          } else if (status === 500) {
            ElMessage.error('服务器内部错误，请检查后端日志')
          } else {
            ElMessage.error(`加载失败: ${errorMsg}`)
          }
        } else if (error.request) {
          // 请求发送失败
          console.error('网络请求失败:', error.request)
          ElMessage.error('无法连接到服务器，请检查网络连接和后端服务状态')
        } else {
          // 其他错误
          console.error('未知错误:', error.message)
          ElMessage.error('加载模型配置失败，请重试')
        }
      } finally {
        loading.value = false
      }
    }

    const filteredConfigs = computed(() => {
      let filtered = configs.value

      if (searchQuery.value) {
        filtered = filtered.filter(config => 
          config.name.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
          config.description.toLowerCase().includes(searchQuery.value.toLowerCase())
        )
      }

      if (filterType.value) {
        filtered = filtered.filter(config => config.model_type === filterType.value)
      }

      if (filterStatus.value) {
        filtered = filtered.filter(config => config.status === filterStatus.value)
      }

      return filtered
    })

    const handleSearch = () => {
      currentPage.value = 1
    }

    const resetSearch = () => {
      searchQuery.value = ''
      filterType.value = ''
      filterStatus.value = ''
      currentPage.value = 1
    }

    const refreshList = async () => {
      loading.value = true
      try {
        // 重新加载模型配置列表
        await loadModelConfigs()
        ElMessage.success('列表已刷新')
      } catch (error) {
        console.error('刷新列表失败:', error)
        ElMessage.error('刷新失败，请重试')
      } finally {
        loading.value = false
      }
    }

    const editConfig = (row) => {
      editForm.id = row.id
      editForm.name = row.name
      editForm.description = row.description
      editForm.status = row.status
      editDialogVisible.value = true
    }

    const saveEdit = async () => {
      try {
        // 调用后端API更新配置
        const response = await axios.post(`/api/models/configs/${editForm.id}/update`, {
          name: editForm.name,
          description: editForm.description,
          status: editForm.status
        })
        
        if (response.data.success) {
          // 更新本地数据
          const index = configs.value.findIndex(config => config.id === editForm.id)
          if (index !== -1) {
            configs.value[index] = {
              ...configs.value[index],
              ...response.data.data,
              updated_at: new Date().toISOString()
            }
          }
          ElMessage.success('配置更新成功')
          editDialogVisible.value = false
        } else {
          throw new Error(response.data.error || '更新失败')
        }
      } catch (error) {
        console.error('更新配置失败:', error)
        if (error.response) {
          ElMessage.error(`更新失败: ${error.response.data?.error || '服务器错误'}`)
        } else {
          ElMessage.error('更新失败，请重试')
        }
      }
    }

    const copyConfig = async (row) => {
      try {
        // 调用后端API复制配置
        const response = await axios.post(`/api/models/configs/${row.id}/copy`, {
          name: `${row.name}_副本`
        })
        
        if (response.data.success) {
          // 将新配置添加到列表顶部
          configs.value.unshift(response.data.data)
          ElMessage.success('配置复制成功')
        } else {
          throw new Error(response.data.error || '复制失败')
        }
      } catch (error) {
        console.error('复制配置失败:', error)
        if (error.response) {
          ElMessage.error(`复制失败: ${error.response.data?.error || '服务器错误'}`)
        } else {
          ElMessage.error('复制失败，请重试')
        }
      }
    }

    const toggleStatus = async (row) => {
      try {
        const newStatus = row.status === 'active' ? 'inactive' : 'active'
        
        // 调用后端API切换状态
        const response = await axios.post(`/api/models/configs/${row.id}/status/update`, {
          status: newStatus
        })
        
        if (response.data.success) {
          // 更新本地数据
          const index = configs.value.findIndex(config => config.id === row.id)
          if (index !== -1) {
            configs.value[index].status = newStatus
            configs.value[index].updated_at = new Date().toISOString()
          }
          ElMessage.success(`配置已${newStatus === 'active' ? '启用' : '禁用'}`)
        } else {
          throw new Error(response.data.error || '状态切换失败')
        }
      } catch (error) {
        console.error('切换状态失败:', error)
        if (error.response) {
          ElMessage.error(`操作失败: ${error.response.data?.error || '服务器错误'}`)
        } else {
          ElMessage.error('操作失败，请重试')
        }
      }
    }

    const deleteConfig = async (row) => {
      try {
        await ElMessageBox.confirm(
          `确定要删除配置"${row.name}"吗？此操作不可恢复。`,
          '确认删除',
          {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'warning'
          }
        )
        
        // 调用后端API删除配置
        const response = await axios.post(`/api/models/configs/${row.id}/delete`)
        
        if (response.data.success) {
          // 从本地列表中移除
          const index = configs.value.findIndex(config => config.id === row.id)
          if (index !== -1) {
            configs.value.splice(index, 1)
          }
          ElMessage.success('配置删除成功')
        } else {
          throw new Error(response.data.error || '删除失败')
        }
      } catch (error) {
        if (error !== 'cancel') {
          console.error('删除配置失败:', error)
          if (error.response) {
            ElMessage.error(`删除失败: ${error.response.data?.error || '服务器错误'}`)
          } else {
            ElMessage.error('删除失败，请重试')
          }
        }
      }
    }

    const importConfig = () => {
      // 创建文件输入元素
      const input = document.createElement('input')
      input.type = 'file'
      input.accept = '.json'
      input.onchange = async (event) => {
        const file = event.target.files[0]
        if (!file) return
        
        try {
          const text = await file.text()
          const configData = JSON.parse(text)
          
          // 验证配置数据格式
          if (!configData.name || !configData.model_type) {
            throw new Error('配置文件格式不正确')
          }
          
          // 调用后端API导入配置
          const response = await axios.post('/api/models/configs/import', configData)
          
          if (response.data.success) {
            // 重新加载配置列表
            await loadModelConfigs()
            ElMessage.success('配置导入成功')
          } else {
            throw new Error(response.data.error || '导入失败')
          }
        } catch (error) {
          console.error('导入配置失败:', error)
          if (error instanceof SyntaxError) {
            ElMessage.error('配置文件格式错误，请检查JSON格式')
          } else if (error.response) {
            ElMessage.error(`导入失败: ${error.response.data?.error || '服务器错误'}`)
          } else {
            ElMessage.error(`导入失败: ${error.message}`)
          }
        }
      }
      input.click()
    }

    const exportConfig = async () => {
      try {
        if (filteredConfigs.value.length === 0) {
          ElMessage.warning('没有可导出的配置')
          return
        }
        
        // 调用后端API导出配置
        const response = await axios.get('/api/models/configs/export', {
          params: {
            ids: filteredConfigs.value.map(config => config.id).join(',')
          }
        })
        
        if (response.data.success) {
          // 创建下载链接
          const blob = new Blob([JSON.stringify(response.data.data, null, 2)], {
            type: 'application/json'
          })
          const url = URL.createObjectURL(blob)
          const a = document.createElement('a')
          a.href = url
          a.download = `model_configs_${new Date().toISOString().split('T')[0]}.json`
          document.body.appendChild(a)
          a.click()
          document.body.removeChild(a)
          URL.revokeObjectURL(url)
          
          ElMessage.success('配置导出成功')
        } else {
          throw new Error(response.data.error || '导出失败')
        }
      } catch (error) {
        console.error('导出配置失败:', error)
        if (error.response) {
          ElMessage.error(`导出失败: ${error.response.data?.error || '服务器错误'}`)
        } else {
          ElMessage.error('导出失败，请重试')
        }
      }
    }

    const handleCloseEdit = () => {
      editDialogVisible.value = false
    }

    const handleSizeChange = (val) => {
      pageSize.value = val
      currentPage.value = 1
    }

    const handleCurrentChange = (val) => {
      currentPage.value = val
    }

    const getModelTypeColor = (type) => {
      const colors = {
        regression: '#67C23A',
        classification: '#E6A23C',
        clustering: '#409EFF',
        time_series: '#F56C6C'
      }
      return colors[type] || '#909399'
    }

    const getModelTypeTag = (type) => {
      const types = {
        regression: 'success',
        classification: 'warning',
        clustering: 'info',
        time_series: 'danger'
      }
      return types[type] || 'info'
    }

    const getModelTypeName = (type) => {
      const names = {
        regression: '回归',
        classification: '分类',
        clustering: '聚类',
        time_series: '时间序列'
      }
      return names[type] || type
    }

    const getStatusType = (status) => {
      const types = {
        active: 'success',
        inactive: 'info',
        draft: 'warning'
      }
      return types[status] || 'info'
    }

    const getStatusName = (status) => {
      const names = {
        active: '已启用',
        inactive: '已禁用',
        draft: '草稿'
      }
      return names[status] || status
    }

    const formatDate = (dateStr) => {
      return new Date(dateStr).toLocaleString('zh-CN')
    }

    onMounted(() => {
      loadModelConfigs()
    })

    return {
      loading,
      searchQuery,
      filterType,
      filterStatus,
      currentPage,
      pageSize,
      editDialogVisible,
      editForm,
      configs,
      filteredConfigs,
      handleSearch,
      resetSearch,
      refreshList,
      editConfig,
      saveEdit,
      copyConfig,
      toggleStatus,
      deleteConfig,
      importConfig,
      exportConfig,
      handleCloseEdit,
      handleSizeChange,
      handleCurrentChange,
      getModelTypeColor,
      getModelTypeTag,
      getModelTypeName,
      getStatusType,
      getStatusName,
      formatDate
    }
  }
}
</script>

<style scoped>
.model-list {
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

.search-card,
.list-card {
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

.search-actions {
  display: flex;
  gap: 12px;
}

.search-actions .el-button {
  border-radius: 8px;
  font-weight: 600;
  transition: all 0.3s ease;
}

.search-actions .el-button--primary {
  background: linear-gradient(135deg, #3498db, #2980b9);
  border: none;
}

.search-actions .el-button--primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(52, 152, 219, 0.3);
}

.action-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding: 16px 20px;
  background: rgba(255, 255, 255, 0.9);
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
}

.action-left {
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

.refresh-btn {
  border-radius: 8px;
  font-weight: 600;
  transition: all 0.3s ease;
}

.refresh-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
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
}

.config-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 20px;
  padding: 10px 0;
}

.config-item {
  background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
  border: 2px solid #e9ecef;
  border-radius: 12px;
  padding: 20px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
}

.config-item::before {
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

.config-item:hover {
  background: linear-gradient(135deg, #ecf5ff 0%, #e1f0ff 100%);
  border-color: #3498db;
  transform: translateY(-4px);
  box-shadow: 0 12px 40px rgba(52, 152, 219, 0.15);
}

.config-item:hover::before {
  transform: scaleX(1);
}

.config-item.active {
  border-color: #27ae60;
  background: linear-gradient(135deg, #f0fff4 0%, #e6fffa 100%);
}

.config-item.active::before {
  background: linear-gradient(90deg, #27ae60, #2ecc71);
  transform: scaleX(1);
}

.config-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
}

.config-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.config-name {
  display: flex;
  align-items: center;
  gap: 8px;
}

.config-icon {
  font-size: 20px;
  background: rgba(52, 152, 219, 0.1);
  border-radius: 8px;
  padding: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.config-name span {
  font-size: 16px;
  font-weight: 600;
  color: #2c3e50;
}

.config-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.config-actions .el-button {
  border-radius: 6px;
  font-weight: 500;
  transition: all 0.3s ease;
}

.config-actions .el-button:hover {
  transform: translateY(-1px);
}

.config-content {
  font-size: 14px;
  color: #606266;
  line-height: 1.6;
}

.config-description {
  margin-bottom: 16px;
  color: #7f8c8d;
  font-style: italic;
  padding: 8px 12px;
  background: rgba(52, 152, 219, 0.05);
  border-radius: 6px;
  border-left: 3px solid #3498db;
}

.config-details {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.detail-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.detail-item .label {
  font-weight: 600;
  color: #34495e;
  min-width: 50px;
}

.detail-item .value {
  color: #7f8c8d;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .config-grid {
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  }
}

@media (max-width: 768px) {
  .model-list {
    padding: 15px;
  }
  
  .page-header h2 {
    font-size: 24px;
  }
  
  .action-bar {
    flex-direction: column;
    gap: 16px;
    align-items: stretch;
  }
  
  .action-left {
    justify-content: center;
  }
  
  .config-grid {
    grid-template-columns: 1fr;
  }
  
  .config-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
  
  .config-actions {
    width: 100%;
    justify-content: flex-end;
  }
}
</style> 