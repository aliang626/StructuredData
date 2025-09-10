import { defineStore } from 'pinia'

// 用户状态管理
export const useUserStore = defineStore('user', {
  state: () => ({
    // 用户信息
    user: null,
    // 登录状态
    isLoggedIn: false,
    // 记住我状态
    rememberMe: false
  }),
  
  getters: {
    // 获取用户信息
    getUser: (state) => state.user,
    // 检查是否已登录
    getIsLoggedIn: (state) => state.isLoggedIn,
    // 获取用户名
    username: (state) => state.user?.username || '',
    // 获取用户角色
    userRole: (state) => state.user?.role || 'guest'
  },
  
  actions: {
    // 设置用户信息
    setUser(userInfo) {
      this.$state.user = userInfo
    },
    
    // 设置登录状态
    setLoginStatus(status) {
      this.$state.isLoggedIn = status
      // 保存到sessionStorage
      if (status) {
        sessionStorage.setItem('isLoggedIn', 'true')
        sessionStorage.setItem('userInfo', JSON.stringify(this.user))
      } else {
        sessionStorage.removeItem('isLoggedIn')
        sessionStorage.removeItem('userInfo')
      }
    },
    
    // 设置记住我状态
    setRememberMe(remember) {
      this.$state.rememberMe = remember
    },
    
    // 登录
    login(userInfo) {
      this.setUser(userInfo)
      this.setLoginStatus(true)
    },
    
    // 登出
    logout() {
      this.$state.user = null
      this.$state.isLoggedIn = false
      this.$state.rememberMe = false
      // 清除localStorage中的记住我信息
      localStorage.removeItem('rememberedUser')
    },
    
    // 初始化登录状态（从sessionStorage恢复）
    initAuthState() {
      const isLoggedIn = sessionStorage.getItem('isLoggedIn') === 'true'
      const userInfo = sessionStorage.getItem('userInfo')
      
      if (isLoggedIn && userInfo) {
        try {
          this.$state.user = JSON.parse(userInfo)
          this.$state.isLoggedIn = true
        } catch (error) {
          console.error('恢复用户信息失败:', error)
          this.logout()
        }
      }
    }
  }
})

// 主应用状态管理
export const useMainStore = defineStore('main', {
  state: () => ({
    // 当前用户信息
    user: {
      name: '管理员',
      role: 'admin'
    },
    
    // 系统配置
    systemConfig: {
      version: '1.0.0',
      title: '勘探开发数据湖数据质量智能探查系统'
    },
    
    // 当前选中的模型配置
    currentModel: {
      type: null,
      name: null,
      params: {}
    },
    
    // 数据库连接信息
    database: {
      tables: [],
      selectedFields: []
    },
    
    // 规则库信息
    ruleLibrary: {
      currentLibrary: null,
      currentVersion: null
    },
    
    // 质量检测状态
    qualityCheck: {
      isRunning: false,
      progress: 0,
      currentTask: ''
    }
  }),
  
  getters: {
    // 获取用户显示名称
    userDisplayName: (state) => state.user.name,
    
    // 获取系统标题
    systemTitle: (state) => state.systemConfig.title,
    
    // 检查是否有选中的模型
    hasSelectedModel: (state) => state.currentModel.type && state.currentModel.name,
    
    // 检查是否有选中的字段
    hasSelectedFields: (state) => state.database.selectedFields.length > 0,
    
    // 检查质量检测是否运行中
    isQualityChecking: (state) => state.qualityCheck.isRunning
  },
  
  actions: {
    // 设置当前模型
    setCurrentModel(type, name, params = {}) {
      this.currentModel = {
        type,
        name,
        params
      }
    },
    
    // 更新模型参数
    updateModelParam(param, value) {
      this.currentModel.params[param] = value
    },
    
    // 设置数据库表
    setDatabaseTables(tables) {
      this.database.tables = tables
    },
    
    // 设置选中字段
    setSelectedFields(fields) {
      this.database.selectedFields = fields
    },
    
    // 设置当前规则库
    setCurrentRuleLibrary(library, version = null) {
      this.ruleLibrary.currentLibrary = library
      this.ruleLibrary.currentVersion = version
    },
    
    // 开始质量检测
    startQualityCheck() {
      this.qualityCheck.isRunning = true
      this.qualityCheck.progress = 0
      this.qualityCheck.currentTask = '准备检测...'
    },
    
    // 更新质量检测进度
    updateQualityProgress(progress, task = '') {
      this.qualityCheck.progress = progress
      if (task) {
        this.qualityCheck.currentTask = task
      }
    },
    
    // 完成质量检测
    finishQualityCheck() {
      this.qualityCheck.isRunning = false
      this.qualityCheck.progress = 100
      this.qualityCheck.currentTask = '检测完成'
      
      // 2秒后重置状态
      setTimeout(() => {
        this.qualityCheck.progress = 0
        this.qualityCheck.currentTask = ''
      }, 2000)
    },
    
    // 重置所有状态
    resetState() {
      this.currentModel = {
        type: null,
        name: null,
        params: {}
      }
      this.database = {
        tables: [],
        selectedFields: []
      }
      this.ruleLibrary = {
        currentLibrary: null,
        currentVersion: null
      }
      this.qualityCheck = {
        isRunning: false,
        progress: 0,
        currentTask: ''
      }
    }
  }
})

// 模型配置状态管理
export const useModelStore = defineStore('model', {
  state: () => ({
    // 可用模型列表
    availableModels: {
      regression: {},
      clustering: {}
    },
    
    // 模型配置列表
    modelConfigs: [],
    
    // 当前选中的模型
    selectedModel: null,
    
    // 模型参数表单
    modelForm: {
      name: '',
      description: '',
      parameters: {}
    }
  }),
  
  getters: {
    // 获取回归模型列表
    regressionModels: (state) => Object.values(state.availableModels.regression || {}),
    
    // 获取聚类模型列表
    clusteringModels: (state) => Object.values(state.availableModels.clustering || {}),
    
    // 检查是否有选中的模型
    hasSelectedModel: (state) => state.selectedModel !== null
  },
  
  actions: {
    // 设置可用模型
    setAvailableModels(models) {
      this.availableModels = models
    },
    
    // 设置模型配置列表
    setModelConfigs(configs) {
      this.modelConfigs = configs
    },
    
    // 选择模型
    selectModel(model) {
      this.selectedModel = model
      this.modelForm.name = model.name
      this.modelForm.description = model.description
      this.modelForm.parameters = {}
      
      // 初始化参数默认值
      if (model.parameters) {
        Object.entries(model.parameters).forEach(([key, param]) => {
          this.modelForm.parameters[key] = param.default_value
        })
      }
    },
    
    // 更新模型参数
    updateModelParameter(key, value) {
      this.modelForm.parameters[key] = value
    },
    
    // 重置模型表单
    resetModelForm() {
      this.modelForm = {
        name: '',
        description: '',
        parameters: {}
      }
    }
  }
})

// 数据库状态管理
export const useDatabaseStore = defineStore('database', {
  state: () => ({
    // 数据源列表
    dataSources: [],
    
    // 当前选中的数据源
    selectedSource: null,
    
    // 数据表列表
    tables: [],
    
    // 当前选中的数据表
    selectedTable: null,
    
    // 字段列表
    fields: [],
    
    // 选中的字段
    selectedFields: [],
    
    // 数据预览
    previewData: []
  }),
  
  getters: {
    // 检查是否有选中的数据源
    hasSelectedSource: (state) => state.selectedSource !== null,
    
    // 检查是否有选中的数据表
    hasSelectedTable: (state) => state.selectedTable !== null,
    
    // 检查是否有选中的字段
    hasSelectedFields: (state) => state.selectedFields.length > 0
  },
  
  actions: {
    // 设置数据源列表
    setDataSources(sources) {
      this.dataSources = sources
    },
    
    // 选择数据源
    selectSource(source) {
      this.selectedSource = source
      this.tables = []
      this.selectedTable = null
      this.fields = []
      this.selectedFields = []
      this.previewData = []
    },
    
    // 设置数据表列表
    setTables(tables) {
      this.tables = tables
    },
    
    // 选择数据表
    selectTable(table) {
      this.selectedTable = table
      this.fields = []
      this.selectedFields = []
      this.previewData = []
    },
    
    // 设置字段列表
    setFields(fields) {
      this.fields = fields
      this.selectedFields = fields.map(f => f.name)
    },
    
    // 设置选中字段
    setSelectedFields(fields) {
      this.selectedFields = fields
    },
    
    // 设置预览数据
    setPreviewData(data) {
      this.previewData = data
    },
    
    // 重置数据库状态
    resetDatabaseState() {
      this.selectedSource = null
      this.tables = []
      this.selectedTable = null
      this.fields = []
      this.selectedFields = []
      this.previewData = []
    }
  }
}) 