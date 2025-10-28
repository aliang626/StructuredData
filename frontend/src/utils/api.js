import axios from 'axios'
import { ElMessage } from 'element-plus'

// ==================== API配置 ====================
const SERVER_IP = '10.77.76.232'
const API_PORT = 5000

// 动态获取API基础URL
const getBaseURL = () => {
  const currentHost = window.location.hostname
  const currentPort = window.location.port
  
  // 服务器开发模式：端口为3000时，使用相对路径走Vite proxy（不需要开放5000端口）
  if (currentPort === '3000') {
    return '' // 空字符串 = 相对路径，请求会自动走Vite的proxy配置
  }
  
  // 服务器生产模式：直接访问后端（需要5000端口开放）
  if (currentHost === SERVER_IP) {
    return `http://${SERVER_IP}:${API_PORT}`
  }
  
  // ===== 本地开发环境 =====
  // 本地开发：localhost访问
  console.log(`本地开发模式: ${currentHost} → http://localhost:${API_PORT}`)
  return `http://localhost:${API_PORT}`
  
  // 默认：使用服务器后端
  console.log(`默认模式: ${currentHost} → http://${SERVER_IP}:${API_PORT}`)
  return `http://${SERVER_IP}:${API_PORT}`
}

// 创建axios实例
export const api = axios.create({
  baseURL: getBaseURL(),  
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    // 在发送请求之前做些什么
    console.log('发送请求:', config.url, config.data)
    return config
  },
  (error) => {
    // 对请求错误做些什么
    console.error('请求错误:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    // 对响应数据做点什么
    console.log('收到响应:', response.config.url, response.data)
    
    // 检查业务状态码
    if (response.data && response.data.code === 500) {
      ElMessage.error(response.data.message || '服务器内部错误')
      return Promise.reject(new Error(response.data.message || '服务器内部错误'))
    }
    
    return response
  },
  (error) => {
    // 对响应错误做点什么
    console.error('响应错误:', error)
    
    let message = '网络错误'
    
    if (error.response) {
      // 服务器返回了错误状态码
      const status = error.response.status
      switch (status) {
        case 400:
          message = '请求参数错误'
          break
        case 401:
          message = '未授权，请重新登录'
          break
        case 403:
          message = '拒绝访问'
          break
        case 404:
          message = '请求的资源不存在'
          break
        case 500:
          message = '服务器内部错误'
          break
        default:
          message = `请求失败 (${status})`
      }
    } else if (error.request) {
      // 请求已发出但没有收到响应
      message = '网络连接失败，请检查网络设置'
    } else {
      // 其他错误
      message = error.message || '未知错误'
    }
    
    ElMessage.error(message)
    return Promise.reject(error)
  }
)

// API方法封装
export const apiService = {
  // 模型相关API
  models: {
    // 获取可用模型列表
    getAvailable: () => api.get('/api/models/available'),
    
    // 获取模型配置列表
    getConfigs: () => api.get('/api/models/configs'),
    
    // 创建模型配置
    createConfig: (data) => api.post('/api/models/configs', data),
    
    // 更新模型配置
    updateConfig: (id, data) => api.put(`/api/models/configs/${id}`, data),
    
    // 删除模型配置
    deleteConfig: (id) => api.delete(`/api/models/configs/${id}`)
  },
  
  // 数据库相关API
  database: {
    // 获取数据源列表
    getSources: () => api.get('/api/database/sources'),
    
    // 创建数据源
    createSource: (data) => api.post('/api/database/sources', data),
    
    // 删除数据源
    deleteSource: (id) => api.delete(`/api/database/sources/${id}`),
    
    // 测试数据库连接
    testConnection: (data) => api.post('/api/database/test-connection', data),
    
    // 获取数据表列表
    getTables: (data) => api.post('/api/database/tables', data),
    
    // 获取表字段信息
    getFields: (data) => api.post('/api/database/fields', data),
    
    // 预览数据
    previewData: (data) => api.post('/api/database/preview', data)
  },
  
  // 规则相关API
  rules: {
    // 获取规则库列表
    getLibraries: () => api.get('/api/rules/libraries'),
    
    // 创建规则库
    createLibrary: (data) => api.post('/api/rules/libraries', data),
    
    // 删除规则库
    deleteLibrary: (id) => api.delete(`/api/rules/libraries/${id}`),
    
    // 获取规则库版本
    getVersions: (libraryId) => api.get(`/api/rules/libraries/${libraryId}/versions`),
    
    // 删除规则版本
    deleteVersion: (versionId) => api.delete(`/api/rules/versions/${versionId}`),
    
    // 生成规则
    generate: (data) => api.post('/api/rules/generate', data),
    
    // 保存规则
    save: (data) => api.post('/api/rules/save', data)
  },
  
  // 质量检测相关API
  quality: {
    // 运行质量检测
    check: (data) => api.post('/api/quality/check', data),
    
    // 批量质量检测
    batchCheck: (data) => api.post('/api/quality/batch-check', data),
    
    // 获取检测结果
    getResults: () => api.get('/api/quality/results'),
    
    // 获取检测详情
    getDetail: (id) => api.get(`/api/quality/results/${id}/detail`),
    
    // 获取异常数据
    getAnomalyData: () => api.get('/api/quality/anomaly-data'),
    
    // 获取检测报告
    getReports: () => api.get('/api/quality/results'),
    
    // 获取报告详情
    getReportDetail: (id) => api.get(`/api/quality/results/${id}`)
  },
  
  // 系统相关API
  system: {
    // 健康检查
    health: () => api.get('/api/health'),
    
    // 获取系统状态  
    status: () => api.get('/api/stats'),
    
    // 获取活动记录
    activities: () => api.get('/api/activities'),
    
    // 井名白名单相关
    wellWhitelist: {
      list: (params) => api.get('/api/well-whitelist', { params }),
      add: (data) => api.post('/api/well-whitelist', data),
      update: (code, data) => api.put(`/api/well-whitelist/${code}`, data),
      delete: (code) => api.delete(`/api/well-whitelist/${code}`),
      search: (params) => api.get('/api/well-whitelist/search', { params })
    }
  },
  
  // 认证相关API
  auth: {
    // SSO token验证
    verifySSOToken: (token) => api.post('/api/auth/sso/verify-token', { token }),
    
    // 传统登录
    legacyLogin: (username, password) => api.post('/api/auth/legacy/login', { username, password }),
    
    // 刷新appCode（调试用）
    refreshAppCode: () => api.post('/api/auth/sso/refresh-appcode'),
    
    // 测试SSO连通性
    testSSO: () => api.get('/api/auth/sso/test')
  }
}

export default api 