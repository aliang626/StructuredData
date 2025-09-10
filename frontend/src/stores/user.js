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
      
      if (isLoggedIn && userInfo) {
        try {
          this.user = JSON.parse(userInfo)
          this.isLoggedIn = true
        } catch (error) {
          console.error('恢复用户信息失败:', error)
          this.logout()
        }
      }
    }
  }
})
