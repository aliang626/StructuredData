<template>
  <div class="login-container">
    <div class="login-box">
      <div class="login-header">
        <div class="logo">
          <el-icon size="48" color="#409EFF"><Setting /></el-icon>
        </div>
        <h1>勘探开发数据湖数据质量智能探查系统</h1>
        <p>请登录以访问系统功能</p>
      </div>
      
      <el-form
        ref="loginFormRef"
        :model="loginForm"
        :rules="loginRules"
        class="login-form"
        @submit.prevent="handleLogin"
      >
        <el-form-item prop="username">
          <el-input
            v-model="loginForm.username"
            placeholder="请输入用户名"
            size="large"
            prefix-icon="User"
            clearable
          />
        </el-form-item>
        
        <el-form-item prop="password">
          <el-input
            v-model="loginForm.password"
            type="password"
            placeholder="请输入密码"
            size="large"
            prefix-icon="Lock"
            show-password
            clearable
            @keyup.enter="handleLogin"
          />
        </el-form-item>
        
        <!-- 验证码（根据需要显示） -->
        <el-form-item v-if="showCaptcha" prop="captcha">
          <div style="display: flex; gap: 10px; align-items: center;">
            <el-input
              v-model="loginForm.captcha"
              placeholder="请输入验证码"
              size="large"
              style="flex: 1;"
              @keyup.enter="handleLogin"
            />
            <img
              v-if="captchaImage"
              :src="captchaImage"
              @click="refreshCaptcha"
              style="height: 40px; cursor: pointer; border-radius: 4px; border: 1px solid #dcdfe6;"
              title="点击刷新验证码"
              alt="验证码"
            />
          </div>
          <div v-if="remainingAttempts !== null && remainingAttempts <= 3" style="font-size: 12px; color: #E6A23C; margin-top: 5px;">
            剩余尝试次数: {{ remainingAttempts }}
          </div>
        </el-form-item>
        
        <el-form-item>
          <el-checkbox v-model="loginForm.rememberMe" class="remember-me">
            记住我
          </el-checkbox>
        </el-form-item>
        
        <el-form-item>
          <el-button
            type="primary"
            size="large"
            class="login-btn"
            :loading="loading"
            @click="handleLogin"
          >
            {{ loading ? '登录中...' : '登录' }}
          </el-button>
        </el-form-item>
      </el-form>
      
      <div class="login-footer">
        <p class="copyright">© 2025 勘探开发数据湖系统</p>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Setting, User, Lock } from '@element-plus/icons-vue'
import { useUserStore } from '../stores/user.js'
import { getTokenFromUrl, clearTokenFromUrl, isSSORedirect, handleSSOError } from '../utils/sso.js'
import { apiService } from '../utils/api.js'
import JSEncrypt from 'jsencrypt' // [新增] 引入加密库

const PUBLIC_KEY = `
-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAnVy7hPObrQqFrsTDGVsp
4foWS94PQT/8UtXMs7XE20KVVBrEpFGD7uy23kgVqt7SZ4B63jcHzy7PQHZ0L5tW
4i32+y8UFJ7z/nBX8GctgLvgTr31H6Em0Qv+96YN31oQGdideewHd0FJvMetlFfr
7in+ui5udIVT3RAb49WZ9BZBPJYYgN+4DnY6IXgR7sykp7exQ3D92W1r7DSbQlxA
/kaYk2n9EddK2+Ib6Jz5fxc2HVh3CmKo7A8dTd6QvFJoXEfLn48fQZy+1zIB3miI
SWc6t2L9fMs4JAvuf1rKM+qYqGgCDXHZOHL/s8nkzOEA7zY270kIpFnXhNQdNKhM
lwIDAQAB
-----END PUBLIC KEY-----
`

export default {
  name: 'Login',
  components: {
    Setting,
    User,
    Lock
  },
  setup() {
    const router = useRouter()
    const userStore = useUserStore()
    const loginFormRef = ref()
    const loading = ref(false)
    
    // 验证码相关（始终显示）
    const showCaptcha = ref(true)
    const captchaImage = ref('')
    const sessionId = ref('')
    const remainingAttempts = ref(null)
    
    const loginForm = reactive({
      username: '',
      password: '',
      captcha: '',
      rememberMe: false
    })
    
    const loginRules = {
      username: [
        { required: true, message: '请输入用户名', trigger: 'blur' },
        { min: 2, max: 20, message: '用户名长度在 2 到 20 个字符', trigger: 'blur' }
      ],
      password: [
        { required: true, message: '请输入密码', trigger: 'blur' },
        { min: 6, max: 20, message: '密码长度在 6 到 20 个字符', trigger: 'blur' }
      ],
      captcha: [
        { required: true, message: '请输入验证码', trigger: 'blur' }
      ]
    }
    
    // 刷新验证码
    const refreshCaptcha = async () => {
      try {
        const response = await apiService.auth.getCaptcha()
        if (response.data && response.data.success) {
          captchaImage.value = response.data.data.image
          sessionId.value = response.data.data.session_id
          loginForm.captcha = '' // 清空验证码输入
        }
      } catch (error) {
        console.error('获取验证码失败:', error)
        ElMessage.error('获取验证码失败')
      }
    }
    
    const handleLogin = async () => {
      if (!loginFormRef.value) return
      
      try {
        const valid = await loginFormRef.value.validate()
        if (!valid) return
        
        loading.value = true

        // ============ [新增加密逻辑] 开始 ============
        const encryptor = new JSEncrypt()
        encryptor.setPublicKey(PUBLIC_KEY)
        // 对密码进行加密
        const encryptedPassword = encryptor.encrypt(loginForm.password)
        
        if (!encryptedPassword) {
          ElMessage.error('密码加密失败，请检查公钥配置')
          loading.value = false
          return
        }
        // ============ [新增加密逻辑] 结束 ============
        
        // 使用新的传统登录方法（带验证码）
        const result = await userStore.legacyLogin(
          loginForm.username, 
          encryptedPassword, 
          loginForm.rememberMe,
          loginForm.captcha,
          sessionId.value
        )
        
        if (result.success) {
          ElMessage.success('登录成功！')
          // 跳转到首页
          router.push('/')
        } else {
          ElMessage.error(result.error || '登录失败')
          
          // 登录失败后自动刷新验证码
          await refreshCaptcha()
          
          // 更新剩余尝试次数
          if (result.remaining_attempts !== undefined) {
            remainingAttempts.value = result.remaining_attempts
          }
        }
      } catch (error) {
        console.error('登录失败:', error)
        ElMessage.error('登录失败，请重试！')
      } finally {
        loading.value = false
      }
    }
    
    // SSO自动登录处理
    const handleSSOLogin = async (token) => {
      try {
        loading.value = true
        console.log('检测到SSO token，开始自动登录...')
        
        // 显示SSO登录提示
        ElMessage.info('正在验证SSO登录信息...')
        
        const result = await userStore.ssoLogin(token)
        
        if (result.success) {
          ElMessage.success(`欢迎 ${result.user.name}！SSO登录成功`)
          
          // 清除URL中的token
          clearTokenFromUrl()
          
          // 跳转到首页
          router.push('/')
        } else {
          console.error('SSO登录失败:', result.error)
          ElMessage.error(`SSO登录失败: ${result.error}`)
          
          // 处理SSO错误
          handleSSOError(result.error)
          
          // 显示传统登录表单
          ElMessage.info('请使用用户名密码登录')
        }
      } catch (error) {
        console.error('SSO登录异常:', error)
        ElMessage.error('SSO登录异常，请使用用户名密码登录')
        handleSSOError(error.message)
      } finally {
        loading.value = false
      }
    }
    
    // 检查SSO登录
    const checkSSOLogin = async () => {
      // 如果已经登录，直接跳转到首页
      if (userStore.getIsLoggedIn) {
        console.log('用户已登录，跳转到首页')
        router.push('/')
        return
      }
      
      // 检查URL中是否有token
      if (isSSORedirect()) {
        const token = getTokenFromUrl()
        if (token) {
          console.log('检测到SSO跳转，开始处理...')
          await handleSSOLogin(token)
        }
      } else {
        console.log('普通访问登录页面')
      }
    }
    
    // 检查是否有记住的用户名
    const rememberedUser = localStorage.getItem('rememberedUser')
    if (rememberedUser) {
      loginForm.username = rememberedUser
      loginForm.rememberMe = true
    }
    
    // 组件挂载时检查SSO登录并获取验证码
    onMounted(() => {
      console.log('登录页面加载完成，检查SSO登录状态')
      checkSSOLogin()
      // 自动获取验证码
      refreshCaptcha()
    })
    
    return {
      loginFormRef,
      loginForm,
      loginRules,
      loading,
      showCaptcha,
      captchaImage,
      remainingAttempts,
      handleLogin,
      handleSSOLogin,
      checkSSOLogin,
      refreshCaptcha
    }
  }
}
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  position: relative;
  overflow: hidden;
}

.login-container::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="grain" width="100" height="100" patternUnits="userSpaceOnUse"><circle cx="25" cy="25" r="1" fill="white" opacity="0.1"/><circle cx="75" cy="75" r="1" fill="white" opacity="0.1"/><circle cx="50" cy="10" r="0.5" fill="white" opacity="0.1"/><circle cx="10" cy="60" r="0.5" fill="white" opacity="0.1"/><circle cx="90" cy="40" r="0.5" fill="white" opacity="0.1"/></pattern></defs><rect width="100" height="100" fill="url(%23grain)"/></svg>');
  opacity: 0.3;
}

.login-box {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: 20px;
  padding: 40px;
  width: 100%;
  max-width: 400px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.3);
  position: relative;
  z-index: 1;
  animation: slideUp 0.6s ease-out;
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.login-header {
  text-align: center;
  margin-bottom: 30px;
}

.logo {
  margin-bottom: 20px;
  display: flex;
  justify-content: center;
  align-items: center;
  width: 80px;
  height: 80px;
  background: linear-gradient(135deg, #409EFF, #67C23A);
  border-radius: 50%;
  margin: 0 auto 20px;
  box-shadow: 0 8px 25px rgba(64, 158, 255, 0.3);
}

.logo .el-icon {
  color: white !important;
  font-size: 32px;
}

.login-header h1 {
  font-size: 24px;
  color: #2c3e50;
  margin-bottom: 8px;
  font-weight: 600;
  line-height: 1.3;
}

.login-header p {
  color: #7f8c8d;
  font-size: 14px;
  margin: 0;
}

.login-form {
  margin-bottom: 20px;
}

.login-form .el-form-item {
  margin-bottom: 20px;
}

.login-form .el-input {
  height: 50px;
}

.login-form .el-input__wrapper {
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  border: 2px solid #e9ecef;
  transition: all 0.3s ease;
}

.login-form .el-input__wrapper:hover {
  border-color: #409EFF;
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.15);
}

.login-form .el-input__wrapper.is-focus {
  border-color: #409EFF;
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.2);
}

.remember-me {
  color: #7f8c8d;
  font-size: 14px;
}

.login-btn {
  width: 100%;
  height: 50px;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 600;
  background: linear-gradient(135deg, #409EFF, #67C23A);
  border: none;
  box-shadow: 0 4px 15px rgba(64, 158, 255, 0.3);
  transition: all 0.3s ease;
}

.login-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(64, 158, 255, 0.4);
}

.login-btn:active {
  transform: translateY(0);
}

.login-footer {
  text-align: center;
  margin-top: 20px;
}

.login-footer p {
  color: #7f8c8d;
  font-size: 12px;
  margin: 5px 0;
}

.copyright {
  margin-top: 15px;
  font-size: 11px;
  opacity: 0.7;
}

/* 响应式设计 */
@media (max-width: 480px) {
  .login-container {
    padding: 15px;
  }
  
  .login-box {
    padding: 30px 20px;
  }
  
  .login-header h1 {
    font-size: 20px;
  }
  
  .logo {
    width: 60px;
    height: 60px;
  }
  
  .logo .el-icon {
    font-size: 24px;
  }
}

/* 输入框焦点效果 */
.login-form .el-input__wrapper.is-focus {
  animation: focusGlow 0.3s ease-out;
}

@keyframes focusGlow {
  0% {
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  }
  50% {
    box-shadow: 0 4px 20px rgba(64, 158, 255, 0.3);
  }
  100% {
    box-shadow: 0 4px 12px rgba(64, 158, 255, 0.2);
  }
}
</style>
