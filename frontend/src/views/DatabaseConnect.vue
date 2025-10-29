<template>
  <div class="database-connect">
    <!-- 页面标题 -->
    <div class="page-header">
      <h2>数据库连接管理</h2>
      <p>管理您的数据库连接配置，支持PostgreSQL数据库</p>
    </div>

    <el-row :gutter="24">
      <!-- 左侧：连接列表 -->
      <el-col :span="14">
        <el-card class="connection-list-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <div class="header-left">
                <el-icon class="header-icon"><Connection /></el-icon>
                <span class="header-title">连接列表</span>
                <el-tag type="info" size="small">{{ dataSources.length }} 个连接</el-tag>
              </div>
              <el-button type="primary" @click="showAddDialog = true" class="add-btn">
                <el-icon><Plus /></el-icon>
                添加连接
              </el-button>
            </div>
          </template>
          
          <div v-if="dataSources.length === 0" class="empty-state">
            <el-icon class="empty-icon"><Connection /></el-icon>
            <p>暂无数据库连接</p>
            <el-button type="primary" @click="showAddDialog = true">添加第一个连接</el-button>
          </div>
          
          <div v-else class="connection-grid">
            <div 
              v-for="source in dataSources" 
              :key="source.id" 
              class="connection-item"
              :class="{ 'active': source.is_active }"
            >
              <div class="connection-header">
                <div class="connection-info">
                  <h4>{{ source.name }}</h4>
                  <el-tag :type="source.is_active ? 'success' : 'danger'" size="small">
                    {{ source.is_active ? '正常' : '异常' }}
                  </el-tag>
                </div>
                <div class="connection-actions">
                  <el-button size="small" type="primary" @click="testConnection(source)">
                    <el-icon><Connection /></el-icon>
                    测试
                  </el-button>
                  <el-button size="small" type="danger" @click="deleteConnection(source)">
                    <el-icon><Delete /></el-icon>
                    删除
                  </el-button>
                </div>
              </div>
              
              <div class="connection-details">
                <div class="detail-item">
                  <span class="label">类型:</span>
                  <span class="value">{{ source.db_type }}</span>
                </div>
                <div class="detail-item">
                  <span class="label">主机:</span>
                  <span class="value">{{ source.host }}:{{ source.port }}</span>
                </div>
                <div class="detail-item">
                  <span class="label">数据库:</span>
                  <span class="value">{{ source.database }}</span>
                </div>
                <div class="detail-item">
                  <span class="label">用户:</span>
                  <span class="value">{{ source.username }}</span>
                </div>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <!-- 右侧：快速配置 -->
      <el-col :span="10">
        <el-card class="quick-config-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <div class="header-left">
                <el-icon class="header-icon"><Setting /></el-icon>
                <span class="header-title">快速配置</span>
              </div>
            </div>
          </template>
          
          <el-form :model="connectionForm" label-position="top" class="quick-form">
            <el-form-item label="连接名称" required>
              <el-input 
                v-model="connectionForm.name" 
                placeholder="输入连接名称"
                size="large"
              />
            </el-form-item>
            
            <el-form-item label="数据库类型" required>
              <el-select v-model="connectionForm.db_type" style="width: 100%" size="large" disabled>
                <el-option label="PostgreSQL" value="postgresql" />
              </el-select>
            </el-form-item>
            
            <el-row :gutter="12">
              <el-col :span="16">
                <el-form-item label="主机地址" required>
                  <el-input 
                    v-model="connectionForm.host" 
                    placeholder="localhost"
                    size="large"
                  />
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="端口" required>
                  <el-input-number 
                    v-model="connectionForm.port" 
                    :min="1" 
                    :max="65535"
                    size="large"
                    style="width: 100%"
                  />
                </el-form-item>
              </el-col>
            </el-row>
            
            <el-form-item label="数据库名" required>
              <el-input 
                v-model="connectionForm.database" 
                placeholder="数据库名称"
                size="large"
              />
            </el-form-item>
            
            <el-form-item label="用户名" required>
              <el-input 
                v-model="connectionForm.username" 
                placeholder="用户名"
                size="large"
              />
            </el-form-item>
            
            <el-form-item label="密码" required>
              <el-input 
                v-model="connectionForm.password" 
                type="password" 
                placeholder="密码"
                size="large"
                show-password
              />
            </el-form-item>
            
            <el-form-item>
              <div class="form-actions">
                <el-button type="primary" @click="saveConnection" size="large" style="width: 100%">
                  <el-icon><Check /></el-icon>
                  保存连接
                </el-button>
                <el-button @click="resetForm" size="large" style="width: 100%; margin-top: 12px;">
                  <el-icon><Refresh /></el-icon>
                  重置
                </el-button>
              </div>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 添加连接对话框 -->
    <el-dialog 
      v-model="showAddDialog" 
      title="添加数据库连接" 
      width="600px"
      class="add-dialog"
    >
      <el-form :model="addForm" label-position="top">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="连接名称" required>
              <el-input v-model="addForm.name" placeholder="输入连接名称" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="数据库类型" required>
              <el-select v-model="addForm.db_type" style="width: 100%" disabled>
                <el-option label="PostgreSQL" value="postgresql" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-row :gutter="16">
          <el-col :span="16">
            <el-form-item label="主机地址" required>
              <el-input v-model="addForm.host" placeholder="localhost" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="端口" required>
              <el-input-number v-model="addForm.port" :min="1" :max="65535" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-form-item label="数据库名" required>
          <el-input 
            v-model="addForm.database" 
            placeholder="数据库名称"
          />
        </el-form-item>
        
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="用户名" required>
              <el-input v-model="addForm.username" placeholder="用户名" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="密码" required>
              <el-input v-model="addForm.password" type="password" placeholder="密码" show-password />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="showAddDialog = false">取消</el-button>
          <el-button type="primary" @click="addConnection">确定</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, onMounted } from 'vue'
import { Plus, Connection, Delete, Setting, Check, Refresh } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import axios from 'axios'

export default {
  name: 'DatabaseConnect',
  components: {
    Plus, Connection, Delete, Setting, Check, Refresh
  },
  setup() {
    const dataSources = ref([])
    const showAddDialog = ref(false)
    
    const connectionForm = reactive({
      name: '',
      db_type: 'postgresql',
      host: '',
      port: 5432,
      database: '',
      username: '',
      password: ''
    })
    
    const addForm = reactive({
      name: '',
      db_type: 'postgresql',
      host: '',
      port: 5432,
      database: '',
      username: '',
      password: ''
    })
    
    const loadDataSources = async () => {
      try {
        const response = await axios.get('/api/database/sources')
        if (response.data.success) {
          dataSources.value = response.data.data
        }
      } catch (error) {
        ElMessage.error('加载数据源失败')
      }
    }
    
    const testConnection = async (source) => {
      try {
        const response = await axios.post('/api/database/test-connection', source)
        if (response.data.success) {
          ElMessage.success('连接测试成功')
        } else {
          ElMessage.error('连接测试失败')
        }
      } catch (error) {
        ElMessage.error('连接测试失败')
      }
    }
    
    const deleteConnection = async (source) => {
      try {
        await ElMessageBox.confirm('确定要删除这个连接吗？', '提示', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        })
        
        const response = await axios.delete(`/api/database/sources/${source.id}`)
        if (response.data.success) {
          ElMessage.success('删除成功')
          loadDataSources()
        }
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error('删除失败')
        }
      }
    }
    
    const saveConnection = async () => {
      try {
        const response = await axios.post('/api/database/sources', connectionForm)
        if (response.data.success) {
          ElMessage.success('保存成功，正在测试连接...')
          loadDataSources()
          resetForm()
        }
      } catch (error) {
        ElMessage.error('保存失败')
      }
    }
    
    const addConnection = async () => {
      try {
        const response = await axios.post('/api/database/sources', addForm)
        if (response.data.success) {
          ElMessage.success('添加成功，正在测试连接...')
          showAddDialog.value = false
          loadDataSources()
        }
      } catch (error) {
        ElMessage.error('添加失败')
      }
    }
    
    const resetForm = () => {
      Object.assign(connectionForm, {
        name: '',
        db_type: 'postgresql',
        host: '',
        port: 5432,
        database: '',
        username: '',
        password: ''
      })
    }
    
    onMounted(() => {
      loadDataSources()
    })
    
    return {
      dataSources,
      showAddDialog,
      connectionForm,
      addForm,
      testConnection,
      deleteConnection,
      saveConnection,
      addConnection,
      resetForm
    }
  }
}
</script>

<style scoped>
.database-connect {
  padding: 20px;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  min-height: calc(100vh - 60px);
}

.page-header {
  margin-bottom: 30px;
  text-align: center;
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

.connection-list-card,
.quick-config-card {
  background: rgba(255, 255, 255, 0.95);
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
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

.add-btn {
  background: linear-gradient(135deg, #3498db, #2980b9);
  border: none;
  border-radius: 8px;
  padding: 10px 20px;
  font-weight: 500;
  transition: all 0.3s ease;
}

.add-btn:hover {
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
  margin-bottom: 25px;
  font-size: 16px;
}

.connection-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 20px;
  padding: 10px 0;
}

.connection-item {
  background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
  border: 2px solid #e9ecef;
  border-radius: 12px;
  padding: 20px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
}

.connection-item::before {
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

.connection-item:hover {
  background: linear-gradient(135deg, #ecf5ff 0%, #e1f0ff 100%);
  border-color: #3498db;
  transform: translateY(-4px);
  box-shadow: 0 12px 40px rgba(52, 152, 219, 0.15);
}

.connection-item:hover::before {
  transform: scaleX(1);
}

.connection-item.active {
  border-color: #27ae60;
  background: linear-gradient(135deg, #f0fff4 0%, #e6fffa 100%);
}

.connection-item.active::before {
  background: linear-gradient(90deg, #27ae60, #2ecc71);
  transform: scaleX(1);
}

.connection-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 15px;
}

.connection-info h4 {
  margin: 0 0 8px 0;
  font-size: 18px;
  color: #2c3e50;
  font-weight: 600;
}

.connection-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.connection-actions .el-button {
  border-radius: 6px;
  font-weight: 500;
  transition: all 0.3s ease;
}

.connection-actions .el-button:hover {
  transform: translateY(-1px);
}

.connection-details {
  font-size: 14px;
  color: #606266;
  line-height: 1.6;
}

.detail-item {
  margin-bottom: 8px;
  display: flex;
  align-items: center;
}

.detail-item .label {
  font-weight: 600;
  margin-right: 8px;
  color: #34495e;
  min-width: 60px;
}

.detail-item .value {
  color: #7f8c8d;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
}

.quick-config-card {
  position: sticky;
  top: 20px;
}

.quick-form .el-form-item {
  margin-bottom: 20px;
}

.quick-form .el-form-item label {
  font-size: 14px;
  color: #2c3e50;
  font-weight: 600;
  margin-bottom: 8px;
}

.quick-form .el-input,
.quick-form .el-select,
.quick-form .el-input-number {
  width: 100%;
}

.quick-form .el-input__wrapper,
.quick-form .el-select .el-input__wrapper {
  border-radius: 8px;
  border: 2px solid #e9ecef;
  transition: all 0.3s ease;
}

.quick-form .el-input__wrapper:hover,
.quick-form .el-select .el-input__wrapper:hover {
  border-color: #3498db;
}

.quick-form .el-input__wrapper.is-focus,
.quick-form .el-select .el-input__wrapper.is-focus {
  border-color: #3498db;
  box-shadow: 0 0 0 3px rgba(52, 152, 219, 0.1);
}

.form-actions {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 20px;
}

.form-actions .el-button {
  border-radius: 8px;
  font-weight: 600;
  transition: all 0.3s ease;
}

.form-actions .el-button--primary {
  background: linear-gradient(135deg, #3498db, #2980b9);
  border: none;
}

.form-actions .el-button--primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(52, 152, 219, 0.3);
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.add-dialog .el-dialog {
  border-radius: 12px;
  overflow: hidden;
}

.add-dialog .el-dialog__header {
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  border-bottom: 1px solid #dee2e6;
  padding: 20px 24px;
}

.add-dialog .el-dialog__title {
  font-size: 20px;
  font-weight: 600;
  color: #2c3e50;
}

.add-dialog .el-dialog__body {
  padding: 24px;
}

.add-dialog .el-dialog__footer {
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  border-top: 1px solid #dee2e6;
  padding: 16px 24px;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .connection-grid {
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  }
}

@media (max-width: 768px) {
  .database-connect {
    padding: 15px;
  }
  
  .page-header h2 {
    font-size: 24px;
  }
  
  .connection-grid {
    grid-template-columns: 1fr;
  }
  
  .connection-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
  
  .connection-actions {
    width: 100%;
    justify-content: flex-end;
  }
}
</style> 