<template>
  <div class="field-comparison-rules">
    <el-card class="rule-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <el-icon class="header-icon"><Operation /></el-icon>
            <span class="header-title">字段比较规则配置</span>
            <el-tag type="info" size="small">{{ comparisons.length }} 条规则</el-tag>
          </div>
          <el-button type="primary" @click="addComparison" size="small">
            <el-icon><Plus /></el-icon>
            添加规则
          </el-button>
        </div>
      </template>

      <div v-if="comparisons.length === 0" class="empty-state">
        <el-icon class="empty-icon"><Operation /></el-icon>
        <p>暂无字段比较规则</p>
        <el-button type="primary" @click="addComparison">添加第一条规则</el-button>
      </div>

      <div v-else class="comparisons-list">
        <div 
          v-for="(comp, index) in comparisons" 
          :key="index"
          class="comparison-item"
        >
          <div class="comparison-index">{{ index + 1 }}</div>
          
          <div class="comparison-content">
            <el-row :gutter="12">
              <!-- 字段1 -->
              <el-col :span="8">
                <el-form-item label="字段1" size="small">
                  <el-select 
                    v-model="comp.field1" 
                    placeholder="选择字段1"
                    filterable
                    @change="onField1Change(index)"
                  >
                    <el-option
                      v-for="field in availableFields"
                      :key="field.name"
                      :label="field.description || field.name"
                      :value="field.name"
                    >
                      <div style="display: flex; justify-content: space-between;">
                        <span>{{ field.description || field.name }}</span>
                        <span style="color: #909399; font-size: 12px;">{{ field.type }}</span>
                      </div>
                    </el-option>
                  </el-select>
                </el-form-item>
              </el-col>

              <!-- 比较运算符 -->
              <el-col :span="4">
                <el-form-item label="运算符" size="small">
                  <el-select v-model="comp.operator" placeholder="选择运算符">
                    <el-option label="大于 (>)" value=">"></el-option>
                    <el-option label="小于 (<)" value="<"></el-option>
                    <el-option label="大于等于 (>=)" value=">="></el-option>
                    <el-option label="小于等于 (<=)" value="<="></el-option>
                    <el-option label="等于 (==)" value="=="></el-option>
                    <el-option label="不等于 (!=)" value="!="></el-option>
                  </el-select>
                </el-form-item>
              </el-col>

              <!-- 字段2 -->
              <el-col :span="8">
                <el-form-item label="字段2" size="small">
                  <el-select 
                    v-model="comp.field2" 
                    placeholder="选择字段2"
                    filterable
                    @change="onField2Change(index)"
                  >
                    <el-option
                      v-for="field in availableFields"
                      :key="field.name"
                      :label="field.description || field.name"
                      :value="field.name"
                    >
                      <div style="display: flex; justify-content: space-between;">
                        <span>{{ field.description || field.name }}</span>
                        <span style="color: #909399; font-size: 12px;">{{ field.type }}</span>
                      </div>
                    </el-option>
                  </el-select>
                </el-form-item>
              </el-col>

              <!-- 删除按钮 -->
              <el-col :span="4">
                <el-form-item label=" " size="small">
                  <el-button 
                    type="danger" 
                    @click="removeComparison(index)"
                    size="small"
                    style="width: 100%;"
                  >
                    <el-icon><Delete /></el-icon>
                    删除
                  </el-button>
                </el-form-item>
              </el-col>
            </el-row>

            <!-- 规则描述 -->
            <el-row>
              <el-col :span="24">
                <el-form-item label="规则描述（可选）" size="small">
                  <el-input
                    v-model="comp.description"
                    placeholder="例如：该数据项小于<解释层底界深>"
                    :disabled="!comp.field1 || !comp.field2 || !comp.operator"
                  >
                    <template #prepend>
                      <span v-if="comp.field1_desc || comp.field1">
                        {{ comp.field1_desc || comp.field1 }}
                      </span>
                      <span v-else>字段1</span>
                    </template>
                    <template #append>
                      <span v-if="comp.field2_desc || comp.field2">
                        {{ comp.field2_desc || comp.field2 }}
                      </span>
                      <span v-else>字段2</span>
                    </template>
                  </el-input>
                  <div class="rule-preview" v-if="comp.field1 && comp.field2 && comp.operator">
                    <el-icon><View /></el-icon>
                    <span>
                      规则预览：该数据项（{{ comp.field1_desc || comp.field1 }}）
                      {{ getOperatorDesc(comp.operator) }}
                      （{{ comp.field2_desc || comp.field2 }}）
                    </span>
                  </div>
                </el-form-item>
              </el-col>
            </el-row>
          </div>
        </div>
      </div>

      <template #footer v-if="comparisons.length > 0">
        <div class="card-footer">
          <el-button @click="clearAll" size="large">清空全部</el-button>
          <el-button type="success" @click="generateRules" :loading="generating" size="large">
            <el-icon><Check /></el-icon>
            生成规则
          </el-button>
        </div>
      </template>
    </el-card>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { Operation, Plus, Delete, View, Check } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'

const props = defineProps({
  availableFields: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['rules-generated'])

const comparisons = ref([])
const generating = ref(false)

// 添加新的比较规则
const addComparison = () => {
  comparisons.value.push({
    field1: '',
    field1_desc: '',
    field2: '',
    field2_desc: '',
    operator: '>',
    description: ''
  })
}

// 移除比较规则
const removeComparison = (index) => {
  comparisons.value.splice(index, 1)
}

// 清空全部
const clearAll = () => {
  comparisons.value = []
}

// 字段1改变时更新描述
const onField1Change = (index) => {
  const comp = comparisons.value[index]
  const field = props.availableFields.find(f => f.name === comp.field1)
  if (field) {
    comp.field1_desc = field.description || field.name
  }
}

// 字段2改变时更新描述
const onField2Change = (index) => {
  const comp = comparisons.value[index]
  const field = props.availableFields.find(f => f.name === comp.field2)
  if (field) {
    comp.field2_desc = field.description || field.name
  }
}

// 获取运算符描述
const getOperatorDesc = (operator) => {
  const map = {
    '>': '大于',
    '<': '小于',
    '>=': '大于等于',
    '<=': '小于等于',
    '==': '等于',
    '!=': '不等于'
  }
  return map[operator] || operator
}

// 生成规则
const generateRules = async () => {
  // 验证
  const validComparisons = comparisons.value.filter(comp => 
    comp.field1 && comp.field2 && comp.operator
  )
  
  if (validComparisons.length === 0) {
    ElMessage.warning('请至少配置一条完整的比较规则')
    return
  }

  // 检查是否有重复字段
  for (const comp of validComparisons) {
    if (comp.field1 === comp.field2) {
      ElMessage.warning('字段1和字段2不能相同')
      return
    }
  }

  generating.value = true
  
  try {
    const response = await axios.post('/api/rules/generate-field-comparison', {
      field_comparisons: validComparisons
    })
    
    if (response.data.success) {
      const rules = response.data.data.rules
      ElMessage.success(`成功生成 ${rules.length} 条字段比较规则`)
      emit('rules-generated', rules)
      
      // 清空已生成的规则
      // comparisons.value = []
    } else {
      ElMessage.error(`生成规则失败: ${response.data.error}`)
    }
  } catch (error) {
    console.error('生成规则失败:', error)
    ElMessage.error(`生成规则失败: ${error.message}`)
  } finally {
    generating.value = false
  }
}

// 暴露方法供父组件调用
defineExpose({
  addComparison,
  clearAll,
  getComparisons: () => comparisons.value
})
</script>

<style scoped>
.field-comparison-rules {
  margin-bottom: 24px;
}

.rule-card {
  background: rgba(255, 255, 255, 0.95);
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
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
  color: #67c23a;
}

.header-title {
  font-size: 18px;
  font-weight: 600;
  color: #2c3e50;
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

.comparisons-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.comparison-item {
  display: flex;
  gap: 12px;
  padding: 16px;
  background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
  border: 2px solid #e9ecef;
  border-radius: 12px;
  transition: all 0.3s ease;
  position: relative;
}

.comparison-item::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, #67c23a, #85ce61);
  border-radius: 12px 12px 0 0;
}

.comparison-item:hover {
  border-color: #67c23a;
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(103, 194, 58, 0.15);
}

.comparison-index {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background: linear-gradient(135deg, #67c23a, #85ce61);
  color: white;
  border-radius: 50%;
  font-weight: 600;
  font-size: 14px;
  flex-shrink: 0;
}

.comparison-content {
  flex: 1;
  min-width: 0;
}

.rule-preview {
  margin-top: 8px;
  padding: 8px 12px;
  background: #f0f9ff;
  border-left: 3px solid #409eff;
  border-radius: 4px;
  font-size: 13px;
  color: #606266;
  display: flex;
  align-items: center;
  gap: 8px;
}

.rule-preview .el-icon {
  color: #409eff;
}

.card-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding-top: 16px;
  border-top: 1px solid #e9ecef;
}

.card-footer .el-button {
  border-radius: 8px;
  font-weight: 600;
  transition: all 0.3s ease;
}

.card-footer .el-button--success {
  background: linear-gradient(135deg, #67c23a, #85ce61);
  border: none;
}

.card-footer .el-button--success:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(103, 194, 58, 0.3);
}

:deep(.el-form-item) {
  margin-bottom: 12px;
}

:deep(.el-form-item__label) {
  font-size: 13px;
  font-weight: 600;
  color: #606266;
}
</style>

