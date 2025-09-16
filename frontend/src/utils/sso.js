/**
 * SSO单点登录工具类
 */

/**
 * 从URL参数中获取token
 * @returns {string|null} token值或null
 */
export function getTokenFromUrl() {
  const urlParams = new URLSearchParams(window.location.search)
  
  // 根据需求，token参数名为 'token'
  const token = urlParams.get('token')
  
  if (token) {
    console.log(`从URL获取到token: ${token.substring(0, 30)}...`)
    return token
  }
  
  return null
}

/**
 * 清除URL中的token参数（避免token在URL中暴露）
 */
export function clearTokenFromUrl() {
  const url = new URL(window.location.href)
  const params = url.searchParams
  
  if (params.has('token')) {
    params.delete('token')
    const newUrl = url.pathname + (params.toString() ? '?' + params.toString() : '') + url.hash
    window.history.replaceState({}, '', newUrl)
    console.log('已清除URL中的token参数')
  }
}

/**
 * 检查是否是SSO跳转（URL中包含token）
 * @returns {boolean}
 */
export function isSSORedirect() {
  return !!getTokenFromUrl()
}

/**
 * 格式化用户信息
 * @param {object} userInfo 原始用户信息
 * @returns {object} 格式化后的用户信息
 */
export function formatUserInfo(userInfo) {
  return {
    id: userInfo.id || 'unknown',
    username: userInfo.username || 'unknown',
    name: userInfo.name || userInfo.displayName || userInfo.realName || '未知用户',
    role: userInfo.role || 'user',
    avatar: userInfo.avatar || '',
    email: userInfo.email || '',
    department: userInfo.department || '',
    phone: userInfo.phone || '',
    loginType: userInfo.loginType || 'sso',
    token: userInfo.token || '',
    originalData: userInfo.originalData || null
  }
}

/**
 * 保存SSO登录状态到本地存储
 * @param {object} userInfo 用户信息
 */
export function saveSSOSession(userInfo) {
  sessionStorage.setItem('ssoLogin', 'true')
  sessionStorage.setItem('ssoUserInfo', JSON.stringify(userInfo))
  sessionStorage.setItem('isLoggedIn', 'true')
  sessionStorage.setItem('userInfo', JSON.stringify(userInfo))
  
  console.log('SSO会话已保存')
}

/**
 * 清除SSO登录状态
 */
export function clearSSOSession() {
  sessionStorage.removeItem('ssoLogin')
  sessionStorage.removeItem('ssoUserInfo')
  sessionStorage.removeItem('isLoggedIn')
  sessionStorage.removeItem('userInfo')
  localStorage.removeItem('rememberedUser')
  
  console.log('SSO会话已清除')
}

/**
 * 检查是否是SSO登录状态
 * @returns {boolean}
 */
export function isSSOLoggedIn() {
  return sessionStorage.getItem('ssoLogin') === 'true'
}

/**
 * 处理SSO登录错误
 * @param {string} error 错误信息
 * @returns {object} 错误处理结果
 */
export function handleSSOError(error) {
  console.error('SSO登录错误:', error)
  
  // 清除可能存在的错误状态
  clearSSOSession()
  
  // 清除URL中的token
  clearTokenFromUrl()
  
  return {
    success: false,
    error: error,
    shouldRedirectToLogin: true
  }
}

/**
 * 获取SSO登录状态信息
 * @returns {object|null}
 */
export function getSSOUserInfo() {
  const userInfoStr = sessionStorage.getItem('ssoUserInfo')
  if (userInfoStr) {
    try {
      return JSON.parse(userInfoStr)
    } catch (error) {
      console.error('解析SSO用户信息失败:', error)
      return null
    }
  }
  return null
}

/**
 * 验证当前是否有有效的SSO会话
 * @returns {boolean}
 */
export function hasValidSSOSession() {
  const isLoggedIn = sessionStorage.getItem('isLoggedIn') === 'true'
  const isSSOLogin = isSSOLoggedIn()
  const userInfo = getSSOUserInfo()
  
  return isLoggedIn && isSSOLogin && userInfo && userInfo.token
}
