<template>
  <div class="well-whitelist">
    <div class="header">
      <h2>井名质检白名单管理</h2>
      <p>管理用于井名质检的区块代号白名单</p>
    </div>

    <!-- 操作栏 -->
    <div class="toolbar">
      <div class="search-box">
        <input 
          v-model="searchQuery" 
          @input="handleSearch"
          placeholder="搜索代号或名称..."
          class="search-input"
        />
        <button @click="handleSearch" class="search-btn">搜索</button>
      </div>
      <button @click="showAddModal = true" class="add-btn">+ 添加代号</button>
    </div>

    <!-- 白名单列表 -->
    <div class="whitelist-table">
      <table>
        <thead>
          <tr>
            <th>序号</th>
            <th>代号</th>
            <th>名称</th>
            <th>描述</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in filteredWhitelist" :key="item.id">
            <td>{{ item.id }}</td>
            <td>
              <span class="code-badge">{{ item.code }}</span>
            </td>
            <td>{{ item.name }}</td>
            <td>{{ item.description }}</td>
                         <td>
               <button @click="editItem(item)" class="edit-btn">编辑</button>
               <button @click="deleteItem(item)" class="delete-btn">删除</button>
             </td>
          </tr>
        </tbody>
      </table>
      
             <!-- 空状态 -->
       <div v-if="filteredWhitelist.length === 0" class="empty-state">
         <p>{{ searchQuery ? '没有找到匹配的结果' : '暂无白名单数据' }}</p>
       </div>
       
       <!-- 分页组件 -->
       <div v-if="pagination.totalPages > 1" class="pagination-container">
         <div class="pagination-info">
           <span>共 {{ pagination.total }} 条记录，第 {{ pagination.page }}/{{ pagination.totalPages }} 页</span>
         </div>
         <div class="pagination-controls">
           <button 
             @click="changePage(pagination.page - 1)" 
             :disabled="!pagination.hasPrev"
             class="page-btn"
           >
             上一页
           </button>
           
           <div class="page-numbers">
             <button 
               v-for="pageNum in visiblePageNumbers" 
               :key="pageNum"
               @click="changePage(pageNum)"
               :class="['page-btn', { active: pageNum === pagination.page }]"
             >
               {{ pageNum }}
             </button>
           </div>
           
           <button 
             @click="changePage(pagination.page + 1)" 
             :disabled="!pagination.hasNext"
             class="page-btn"
           >
             下一页
           </button>
         </div>
         
         <div class="page-size-selector">
           <label>每页显示:</label>
           <select v-model="pagination.pageSize" @change="changePageSize">
             <option value="10">10</option>
             <option value="20">20</option>
             <option value="50">50</option>
             <option value="100">100</option>
           </select>
         </div>
       </div>
     </div>

         <!-- 添加/编辑模态框 -->
     <div v-if="showAddModal || showEditModal" class="modal-overlay" @click="closeModal">
       <div class="modal" @click.stop>
         <div class="modal-header">
           <h3>{{ showEditModal ? '编辑井名代号' : '添加井名代号' }}</h3>
           <button @click="closeModal" class="close-btn">&times;</button>
         </div>
         <div class="modal-body">
           <form @submit.prevent="handleSubmit">
             <div class="form-group">
               <label>代号 *</label>
               <input 
                 v-model="formData.code" 
                 type="text" 
                 required
                 placeholder="如: SM"
                 maxlength="10"
                 class="form-input"
                 :readonly="showEditModal"
               />
               <small v-if="!showEditModal">代号用于井名前缀匹配，会自动转换为大写</small>
               <small v-else class="warning">代号不可编辑，如需修改请删除后重新添加</small>
             </div>
             <div class="form-group">
               <label>名称 *</label>
               <input 
                 v-model="formData.name" 
                 type="text" 
                 required
                 placeholder="如: 三门"
                 class="form-input"
               />
             </div>
             <div class="form-group">
               <label>描述</label>
               <textarea 
                 v-model="formData.description" 
                 placeholder="如: 三门区块，位于浙江省台州市"
                 class="form-textarea"
                 rows="3"
               ></textarea>
               <small>描述信息用于说明该代号的具体含义和用途</small>
             </div>
             <div class="form-actions">
               <button type="button" @click="closeModal" class="cancel-btn">取消</button>
               <button type="submit" class="submit-btn">
                 {{ showEditModal ? '更新' : '添加' }}
               </button>
             </div>
           </form>
         </div>
       </div>
     </div>

    <!-- 确认删除模态框 -->
    <div v-if="showDeleteModal" class="modal-overlay" @click="showDeleteModal = false">
      <div class="modal delete-modal" @click.stop>
        <div class="modal-header">
          <h3>确认删除</h3>
          <button @click="showDeleteModal = false" class="close-btn">&times;</button>
        </div>
        <div class="modal-body">
          <p>确定要删除代号为 <strong>{{ itemToDelete?.code }}</strong> 的白名单项吗？</p>
          <p class="warning">此操作不可撤销！</p>
          <div class="form-actions">
            <button @click="showDeleteModal = false" class="cancel-btn">取消</button>
            <button @click="confirmDelete" class="delete-btn">确认删除</button>
          </div>
        </div>
      </div>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading">
      <div class="spinner"></div>
      <p>加载中...</p>
    </div>
  </div>
</template>

<script>
 import { ref, onMounted, computed } from 'vue'
import { api } from '../utils/api'

export default {
  name: 'WellWhitelist',
  setup() {
         const whitelist = ref([])
     const filteredWhitelist = ref([])
     const loading = ref(false)
     const searchQuery = ref('')
     const showAddModal = ref(false)
     const showEditModal = ref(false)
     const showDeleteModal = ref(false)
     const itemToDelete = ref(null)
     
     // 分页状态
     const pagination = ref({
       page: 1,
       pageSize: 10,
       total: 0,
       totalPages: 0,
       hasNext: false,
       hasPrev: false
     })
     
     const formData = ref({
       code: '',
       name: '',
       description: ''
     })

         // 获取白名单数据
     const fetchWhitelist = async (page = 1, pageSize = pagination.value.pageSize) => {
       loading.value = true
       try {
         const response = await api.get('/api/well-whitelist', {
           params: {
             page: page,
             pageSize: pageSize
           }
         })
         if (response.data.success) {
           whitelist.value = response.data.data
           filteredWhitelist.value = response.data.data
           
           // 更新分页信息
           pagination.value = {
             page: response.data.page,
             pageSize: response.data.pageSize,
             total: response.data.total,
             totalPages: response.data.totalPages,
             hasNext: response.data.hasNext,
             hasPrev: response.data.hasPrev
           }
         } else {
           console.error('获取白名单失败:', response.data.error)
         }
       } catch (error) {
         console.error('获取白名单异常:', error)
       } finally {
         loading.value = false
       }
     }

                   // 搜索处理
      const handleSearch = async () => {
        if (!searchQuery.value.trim()) {
          // 清空搜索，恢复显示所有数据，保持当前页码
          await fetchWhitelist(pagination.value.page, pagination.value.pageSize)
          return
        }

       try {
         const response = await api.get('/api/well-whitelist/search', {
           params: {
             q: searchQuery.value,
             page: 1,  // 搜索时重置到第一页
             pageSize: pagination.value.pageSize
           }
         })
         if (response.data.success) {
           filteredWhitelist.value = response.data.data
           
           // 更新分页信息
           pagination.value = {
             page: response.data.page,
             pageSize: response.data.pageSize,
             total: response.data.total,
             totalPages: response.data.totalPages,
             hasNext: response.data.hasNext,
             hasPrev: response.data.hasPrev
           }
         } else {
           console.error('搜索失败:', response.data.error)
         }
       } catch (error) {
         console.error('搜索异常:', error)
         // 本地搜索作为备选（仅当前页数据）
         const query = searchQuery.value.toLowerCase()
         filteredWhitelist.value = whitelist.value.filter(item => 
           item.code.toLowerCase().includes(query) ||
           item.name.toLowerCase().includes(query)
         )
       }
     }

                   // 添加/编辑白名单项
      const handleSubmit = async () => {
        try {
          if (showEditModal.value) {
            // 更新现有项目
            const response = await api.post(`/api/well-whitelist/${formData.value.originalCode}/update`, {
              name: formData.value.name,
              description: formData.value.description
            })
            if (response.data.success) {
              alert('更新成功！')
              // 保持当前页码，不跳转到第一页
              await fetchWhitelist(pagination.value.page, pagination.value.pageSize)
              closeModal()
            } else {
              alert('更新失败: ' + response.data.error)
            }
          } else {
            // 添加新项目
            const response = await api.post('/api/well-whitelist', formData.value)
            if (response.data.success) {
              alert('添加成功！')
              // 添加成功后跳转到第一页查看新添加的项目
              await fetchWhitelist(1, pagination.value.pageSize)
              closeModal()
            } else {
              alert('添加失败: ' + response.data.error)
            }
          }
        } catch (error) {
          console.error('操作失败:', error)
          alert('操作失败，请检查网络连接')
        }
      }

         // 编辑项目
     const editItem = (item) => {
       formData.value = {
         code: item.code,
         name: item.name,
         description: item.description || '',
         originalCode: item.code  // 保存原始代号用于API调用
       }
       showEditModal.value = true
     }

     // 删除项目
     const deleteItem = (item) => {
       itemToDelete.value = item
       showDeleteModal.value = true
     }

         // 确认删除
     const confirmDelete = async () => {
       try {
         const response = await api.post(`/api/well-whitelist/${itemToDelete.value.code}/delete`)
         if (response.data.success) {
           alert('删除成功！')
           // 删除成功后，如果当前页没有数据了，则跳转到上一页
           const currentPage = pagination.value.page
           const currentPageSize = pagination.value.pageSize
           const totalAfterDelete = pagination.value.total - 1
           const maxPageAfterDelete = Math.ceil(totalAfterDelete / currentPageSize)
           
           if (currentPage > maxPageAfterDelete && maxPageAfterDelete > 0) {
             // 当前页超出范围，跳转到最后一页
             await fetchWhitelist(maxPageAfterDelete, currentPageSize)
           } else {
             // 保持当前页
             await fetchWhitelist(currentPage, currentPageSize)
           }
           
           showDeleteModal.value = false
           itemToDelete.value = null
         } else {
           alert('删除失败: ' + response.data.error)
         }
       } catch (error) {
         console.error('删除失败:', error)
         alert('删除失败，请检查网络连接')
       }
     }

         // 分页相关函数
     const changePage = async (page) => {
       if (page < 1 || page > pagination.value.totalPages) return
       
       if (searchQuery.value.trim()) {
         // 搜索状态下的分页
         const response = await api.get('/api/well-whitelist/search', {
           params: {
             q: searchQuery.value,
             page: page,
             pageSize: pagination.value.pageSize
           }
         })
         if (response.data.success) {
           filteredWhitelist.value = response.data.data
           pagination.value.page = page
         }
       } else {
         // 普通状态下的分页
         await fetchWhitelist(page, pagination.value.pageSize)
       }
     }
     
           const changePageSize = async () => {
        // 改变每页显示数量时，计算当前页在新页面大小下的位置
        const currentPage = pagination.value.page
        const currentPageSize = pagination.value.pageSize
        const total = pagination.value.total
        
        // 计算当前页在新页面大小下的位置
        const startRecord = (currentPage - 1) * currentPageSize
        const newPage = Math.floor(startRecord / currentPageSize) + 1
        
        await fetchWhitelist(newPage, currentPageSize)
      }
     
     // 计算可见的页码
     const visiblePageNumbers = computed(() => {
       const current = pagination.value.page
       const total = pagination.value.totalPages
       const delta = 2
       
       let start = Math.max(1, current - delta)
       let end = Math.min(total, current + delta)
       
       // 确保显示足够的页码
       if (end - start < 4) {
         if (start === 1) {
           end = Math.min(total, start + 4)
         } else {
           start = Math.max(1, end - 4)
         }
       }
       
       const pages = []
       for (let i = start; i <= end; i++) {
         pages.push(i)
       }
       
       return pages
     })
     
     // 关闭模态框
     const closeModal = () => {
       showAddModal.value = false
       showEditModal.value = false
       formData.value = {
         code: '',
         name: '',
         description: '',
         originalCode: ''
       }
     }

    // 组件挂载时获取数据
    onMounted(() => {
      fetchWhitelist()
    })

         return {
       whitelist,
       filteredWhitelist,
       loading,
       searchQuery,
       showAddModal,
       showEditModal,
       showDeleteModal,
       itemToDelete,
       formData,
       pagination,
       visiblePageNumbers,
       handleSearch,
       handleSubmit,
       editItem,
       deleteItem,
       confirmDelete,
       changePage,
       changePageSize,
       closeModal
     }
  }
}
</script>

<style scoped>
.well-whitelist {
  padding: 20px;
  max-width: 1000px;
  margin: 0 auto;
}

.header {
  margin-bottom: 30px;
  text-align: center;
}

.header h2 {
  color: #2c3e50;
  margin-bottom: 10px;
  font-size: 24px;
}

.header p {
  color: #7f8c8d;
  margin: 0;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  gap: 20px;
}

.search-box {
  display: flex;
  gap: 10px;
  flex: 1;
  max-width: 400px;
}

.search-input {
  flex: 1;
  padding: 10px 15px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
}

.search-btn {
  padding: 10px 20px;
  background: #3498db;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
}

.search-btn:hover {
  background: #2980b9;
}

.add-btn {
  padding: 10px 20px;
  background: #27ae60;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
}

.add-btn:hover {
  background: #229954;
}

.whitelist-table {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
  overflow: hidden;
}

table {
  width: 100%;
  border-collapse: collapse;
}

th, td {
  padding: 12px 15px;
  text-align: left;
  border-bottom: 1px solid #eee;
}

th {
  background: #f8f9fa;
  font-weight: 600;
  color: #2c3e50;
}

.code-badge {
  background: #e74c3c;
  color: white;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: bold;
}

 .edit-btn, .delete-btn {
   padding: 6px 12px;
   border: none;
   border-radius: 4px;
   cursor: pointer;
   font-size: 12px;
   margin-right: 5px;
 }

 .edit-btn {
   background: #f39c12;
   color: white;
 }

 .edit-btn:hover {
   background: #e67e22;
 }

 .delete-btn {
   background: #e74c3c;
   color: white;
 }

  .delete-btn:hover {
   background: #c0392b;
 }

 .empty-state {
   text-align: center;
   padding: 40px;
   color: #7f8c8d;
 }

 /* 分页样式 */
 .pagination-container {
   display: flex;
   justify-content: space-between;
   align-items: center;
   padding: 20px;
   background: #f8f9fa;
   border-top: 1px solid #eee;
 }

 .pagination-info {
   color: #7f8c8d;
   font-size: 14px;
 }

 .pagination-controls {
   display: flex;
   align-items: center;
   gap: 10px;
 }

 .page-btn {
   padding: 8px 12px;
   border: 1px solid #ddd;
   background: white;
   color: #2c3e50;
   border-radius: 4px;
   cursor: pointer;
   font-size: 14px;
   min-width: 40px;
 }

 .page-btn:hover:not(:disabled) {
   background: #f8f9fa;
   border-color: #3498db;
 }

 .page-btn.active {
   background: #3498db;
   color: white;
   border-color: #3498db;
 }

 .page-btn:disabled {
   background: #f5f5f5;
   color: #ccc;
   cursor: not-allowed;
 }

 .page-numbers {
   display: flex;
   gap: 5px;
 }

 .page-size-selector {
   display: flex;
   align-items: center;
   gap: 10px;
 }

 .page-size-selector label {
   color: #7f8c8d;
   font-size: 14px;
 }

 .page-size-selector select {
   padding: 6px 10px;
   border: 1px solid #ddd;
   border-radius: 4px;
   background: white;
   font-size: 14px;
 }

 .page-size-selector select:focus {
   outline: none;
   border-color: #3498db;
 }

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal {
  background: white;
  border-radius: 8px;
  width: 90%;
  max-width: 400px;
  max-height: 90vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #eee;
}

.modal-header h3 {
  margin: 0;
  color: #2c3e50;
}

.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #7f8c8d;
}

.close-btn:hover {
  color: #2c3e50;
}

.modal-body {
  padding: 20px;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
  color: #2c3e50;
}

.form-input {
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  box-sizing: border-box;
}

.form-textarea {
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  font-family: inherit;
  resize: vertical;
  min-height: 80px;
  box-sizing: border-box;
}

 .form-group small {
   color: #7f8c8d;
   font-size: 12px;
   margin-top: 5px;
   display: block;
 }

 .form-group small.warning {
   color: #e74c3c;
   font-weight: 500;
 }

.form-actions {
  display: flex;
  gap: 15px;
  justify-content: flex-end;
  margin-top: 30px;
}

.cancel-btn, .submit-btn {
  padding: 10px 20px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

.cancel-btn {
  background: #95a5a6;
  color: white;
}

.cancel-btn:hover {
  background: #7f8c8d;
}

.submit-btn {
  background: #27ae60;
  color: white;
}

.submit-btn:hover {
  background: #229954;
}

.delete-modal .modal-body p {
  margin: 10px 0;
  color: #2c3e50;
}

.delete-modal .warning {
  color: #e74c3c;
  font-weight: 500;
}

.loading {
  text-align: center;
  padding: 40px;
  color: #7f8c8d;
}

.spinner {
  border: 3px solid #f3f3f3;
  border-top: 3px solid #3498db;
  border-radius: 50%;
  width: 30px;
  height: 30px;
  animation: spin 1s linear infinite;
  margin: 0 auto 20px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

 @media (max-width: 768px) {
   .toolbar {
     flex-direction: column;
     align-items: stretch;
   }
   
   .search-box {
     max-width: none;
   }
   
   .modal {
     width: 95%;
     margin: 20px;
   }
   
   .pagination-container {
     flex-direction: column;
     gap: 15px;
     text-align: center;
   }
   
   .pagination-controls {
     justify-content: center;
   }
   
   .page-numbers {
     flex-wrap: wrap;
     justify-content: center;
   }
 }
</style>
