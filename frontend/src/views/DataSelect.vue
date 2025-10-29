<template>
  <div class="data-select">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>数据选择</span>
        </div>
      </template>
      
      <el-row :gutter="20">
        <el-col :span="8">
          <el-form label-width="100px">
            <el-form-item label="数据源">
              <el-select v-model="selectedSource" placeholder="选择数据源" @change="loadSchemas" style="width: 100%">
                <el-option
                  v-for="source in dataSources"
                  :key="source.id"
                  :label="source.name"
                  :value="source"
                />
              </el-select>
            </el-form-item>
            
            <el-form-item label="Schema" v-if="selectedSource">
              <el-select 
                v-model="selectedSchema" 
                placeholder="选择Schema" 
                @change="loadTables" 
                style="width: 100%"
                :loading="loadingSchemas"
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
            
            <el-form-item label="数据表" v-if="selectedSchema">
              <el-select v-model="selectedTable" placeholder="选择数据表" @change="loadFields" style="width: 100%">
                <el-option
                  v-for="table in tables"
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
          </el-form>
        </el-col>
        
        <el-col :span="16">
          <div v-if="fields.length > 0">
            <h4>字段选择</h4>
            <el-checkbox-group v-model="selectedFields" class="field-group">
              <el-checkbox
                v-for="field in fields"
                :key="field.name"
                :label="field.name"
                class="field-checkbox"
              >
                <div class="field-info">
                  <div class="field-name-wrapper">
                    <span class="field-description">{{ field.description }}</span>
                    <span class="field-real-name" v-if="field.description !== field.name">（{{ field.name }}）</span>
                  </div>
                  <el-tag size="small" type="info">{{ field.type }}</el-tag>
                </div>
              </el-checkbox>
            </el-checkbox-group>
            
            <el-button type="primary" style="margin-top: 10px;" @click="loadPreviewData">
              预览数据
            </el-button>
          </div>
        </el-col>
      </el-row>
      
      <!-- 数据预览 -->
      <div v-if="previewData.length > 0" style="margin-top: 20px;">
        <h4>数据预览</h4>
        <el-table :data="previewData" style="width: 100%" height="400">
          <el-table-column
            v-for="field in selectedFields"
            :key="field"
            :prop="field"
            :label="getFieldDescription(field)"
            show-overflow-tooltip
          />
        </el-table>
      </div>
    </el-card>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'

export default {
  name: 'DataSelect',
  setup() {
    const dataSources = ref([])
    const selectedSource = ref(null)
    const schemas = ref([])
    const selectedSchema = ref('')
    const loadingSchemas = ref(false)
    const tables = ref([])
    const selectedTable = ref('')
    const fields = ref([])
    const selectedFields = ref([])
    const previewData = ref([])
    
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
    
    const loadSchemas = async () => {
      if (!selectedSource.value) return
      
      // 重置后续选择
      selectedSchema.value = ''
      tables.value = []
      selectedTable.value = ''
      fields.value = []
      selectedFields.value = []
      previewData.value = []
      
      try {
        loadingSchemas.value = true
        const response = await axios.post('/api/database/schemas', selectedSource.value)
        if (response.data.success) {
          schemas.value = response.data.data
          // 默认选择 public 或第一个
          if (schemas.value.length > 0) {
            selectedSchema.value = schemas.value.includes('public') ? 'public' : schemas.value[0]
            // 自动加载表
            loadTables()
          }
        }
      } catch (error) {
        ElMessage.error('加载Schema列表失败')
      } finally {
        loadingSchemas.value = false
      }
    }
    
    const loadTables = async () => {
      if (!selectedSource.value || !selectedSchema.value) return
      
      // 重置后续选择
      tables.value = []
      selectedTable.value = ''
      fields.value = []
      selectedFields.value = []
      previewData.value = []
      
      try {
        const response = await axios.post('/api/database/tables', {
          ...selectedSource.value,
          schema: selectedSchema.value
        })
        if (response.data.success) {
          tables.value = response.data.data
        }
      } catch (error) {
        ElMessage.error('加载数据表失败')
      }
    }
    
    const loadFields = async () => {
      if (!selectedTable.value) return
      
      try {
        const response = await axios.post('/api/database/fields', {
          ...selectedSource.value,
          schema: selectedSchema.value,
          table_name: selectedTable.value
        })
        if (response.data.success) {
          fields.value = response.data.data
          selectedFields.value = fields.value.map(f => f.name)
        }
      } catch (error) {
        ElMessage.error('加载字段失败')
      }
    }
    
    const loadPreviewData = async () => {
      if (selectedFields.value.length === 0) {
        ElMessage.warning('请先选择字段')
        return
      }
      
      if (!selectedSource.value || !selectedSource.value.id) {
        ElMessage.error('请先选择数据源')
        return
      }
      
      try {
        const response = await axios.post('/api/database/preview', {
          data_source_id: selectedSource.value.id,
          schema: selectedSchema.value,
          table_name: selectedTable.value,
          fields: selectedFields.value,
          limit: 100
        })
        if (response.data.success) {
          previewData.value = response.data.data
        }
      } catch (error) {
        ElMessage.error('加载数据预览失败')
      }
    }
    
    const getFieldDescription = (fieldName) => {
      const field = fields.value.find(f => f.name === fieldName)
      return field ? field.description : fieldName
    }
    
    onMounted(() => {
      loadDataSources()
    })
    
    return {
      dataSources,
      selectedSource,
      schemas,
      selectedSchema,
      loadingSchemas,
      tables,
      selectedTable,
      fields,
      selectedFields,
      previewData,
      loadSchemas,
      loadTables,
      loadFields,
      loadPreviewData,
      getFieldDescription
    }
  }
}
</script>

<style scoped>
.data-select {
  padding: 0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.field-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.field-checkbox {
  width: 100%;
  margin-right: 0;
}

.field-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

h4 {
  margin-bottom: 15px;
  color: #606266;
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

.field-name-wrapper {
  display: flex;
  align-items: center;
  gap: 4px;
}

.field-description {
  font-weight: 500;
}

.field-real-name {
  font-size: 12px;
  color: #909399;
}
</style> 