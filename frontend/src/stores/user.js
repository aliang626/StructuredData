import { defineStore } from 'pinia'
import { apiService } from '../utils/api.js'
import { formatUserInfo, saveSSOSession, clearSSOSession, isSSOLoggedIn, getSSOUserInfo } from '../utils/sso.js'

// 用户状态管理
export const useUserStore = defineStore('user', {
  state: () => ({
    // 用户信息
    user: null,
    // 登录状态
    isLoggedIn: false,
    // 记住我状态
    rememberMe: false,
    // SSO登录状态
    isSSOLogin: false,
    // 登录加载状态
    loginLoading: false
  }),
  
  getters: {
    // 获取用户信息
    getUser: (state) => state.user,
    // 检查是否已登录
    getIsLoggedIn: (state) => state.isLoggedIn,
    // 获取用户名
    username: (state) => state.user?.username || '',
    // 获取用户角色
    userRole: (state) => state.user?.role || 'guest',
    // 获取登录类型
    loginType: (state) => state.user?.loginType || 'unknown',
    // 是否SSO登录
    getIsSSOLogin: (state) => state.isSSOLogin
  },
  
  actions: {
    // 设置用户信息
    setUser(userInfo) {
      this.user = userInfo
    },
    
    // 设置登录状态
    setLoginStatus(status) {
      this.isLoggedIn = status
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
      this.rememberMe = remember
    },
    
    // 登录
    login(userInfo) {
      this.setUser(userInfo)
      this.setLoginStatus(true)
    },
    
    // 登出
    logout() {
      this.user = null
      this.isLoggedIn = false
      this.rememberMe = false
      // 清除localStorage中的记住我信息
      localStorage.removeItem('rememberedUser')
    },
    
    // 初始化登录状态（从sessionStorage恢复）
    initAuthState() {
      const isLoggedIn = sessionStorage.getItem('isLoggedIn') === 'true'
      const userInfo = sessionStorage.getItem('userInfo')
      const isSSOLogin = isSSOLoggedIn()
      
      if (isLoggedIn && userInfo) {
        try {
          this.user = JSON.parse(userInfo)
          this.isLoggedIn = true
          this.isSSOLogin = isSSOLogin
          
          console.log('恢复登录状态:', {
            username: this.user.username,
            loginType: this.user.loginType,
            isSSOLogin: this.isSSOLogin
          })
        } catch (error) {
          console.error('恢复用户信息失败:', error)
          this.logout()
        }
      }
    },
    
    // SSO token登录
    async ssoLogin(token) {
      try {
        this.loginLoading = true
        console.log('开始SSO token验证...')
        
        const response = await apiService.auth.verifySSOToken(token)
        
        if (response.data && response.data.success) {
          const userInfo = formatUserInfo(response.data.data)
          
          // 设置用户信息
          this.setUser(userInfo)
          this.setLoginStatus(true)
          this.isSSOLogin = true
          
          // 保存SSO会话
          saveSSOSession(userInfo)
          
          console.log('SSO登录成功:', userInfo)
          return { success: true, user: userInfo }
        } else {
          const errorMsg = response.data?.error || 'Token验证失败'
          console.error('SSO验证失败:', errorMsg)
          return { success: false, error: errorMsg }
        }
      } catch (error) {
        console.error('SSO登录异常:', error)
        const errorMsg = error.response?.data?.error || error.message || 'SSO登录失败'
        return { success: false, error: errorMsg }
      } finally {
        this.loginLoading = false
      }
    },
    
    // 传统登录
    async legacyLogin(username, password, rememberMe = false, captcha = '', sessionId = '') {
      try {
        this.loginLoading = true
        console.log('开始传统登录验证...')
        
        const response = await apiService.auth.legacyLogin(username, password, captcha, sessionId)
        
        if (response.data && response.data.success) {
          const userInfo = formatUserInfo(response.data.data)
          
          // 设置用户信息
          this.setUser(userInfo)
          this.setLoginStatus(true)
          this.isSSOLogin = false
          
          // 处理记住我
          if (rememberMe) {
            this.setRememberMe(true)
            localStorage.setItem('rememberedUser', username)
          }
          
          console.log('传统登录成功:', userInfo)
          return { success: true, user: userInfo }
        } else {
          const errorMsg = response.data?.error || '登录失败'
          const needCaptcha = response.data?.need_captcha || false
          const remainingAttempts = response.data?.remaining_attempts
          console.error('传统登录失败:', errorMsg)
          return { 
            success: false, 
            error: errorMsg,
            need_captcha: needCaptcha,
            remaining_attempts: remainingAttempts
          }
        }
      } catch (error) {
        console.error('传统登录异常:', error)
        const errorMsg = error.response?.data?.error || error.message || '登录失败'
        const needCaptcha = error.response?.data?.need_captcha || false
        const remainingAttempts = error.response?.data?.remaining_attempts
        return { 
          success: false, 
          error: errorMsg,
          need_captcha: needCaptcha,
          remaining_attempts: remainingAttempts
        }
      } finally {
        this.loginLoading = false
      }
    },
    
    // 增强的登出方法
    logout() {
      console.log('用户登出, 登录类型:', this.user?.loginType)
      
      const wasSSOLogin = this.isSSOLogin
      
      // 清除状态
      this.user = null
      this.isLoggedIn = false
      this.rememberMe = false
      this.isSSOLogin = false
      
      // 清除存储
      if (wasSSOLogin) {
        clearSSOSession()
      } else {
        sessionStorage.removeItem('isLoggedIn')
        sessionStorage.removeItem('userInfo')
        localStorage.removeItem('rememberedUser')
      }
    }
  }
})
