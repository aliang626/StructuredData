<template>
  <div id="app">
    <!-- 登录页面 -->
    <div v-if="!isLoggedIn" class="login-container">
      <router-view />
    </div>
    
    <!-- 主应用界面 -->
    <div v-else>
      <!-- 顶部导航栏 -->
      <el-header class="top-header">
        <div class="header-left">
          <div class="logo">
            <h2>勘探开发数据湖数据质量智能探查系统</h2>
          </div>
        </div>
        <div class="header-right">
          <el-dropdown @command="handleUserCommand">
            <span class="user-info">
              <el-icon><User /></el-icon>
              <span>{{ username }}</span>
              <el-icon><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">个人资料</el-dropdown-item>
                <el-dropdown-item command="settings">系统设置</el-dropdown-item>
                <el-dropdown-item divided command="logout">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <el-container class="main-container">
        <!-- 侧边菜单 -->
        <el-aside width="200px" class="sidebar">
          <el-menu
            :default-active="$route.path"
            class="sidebar-menu"
            router
            background-color="#304156"
            text-color="#bfcbd9"
            active-text-color="#409EFF"
          >
            <el-menu-item index="/">
              <el-icon><House /></el-icon>
              <span>首页</span>
            </el-menu-item>
            
            <el-sub-menu index="database">
              <template #title>
                <el-icon><Connection /></el-icon>
                <span>数据库管理</span>
              </template>
              <el-menu-item index="/database-connect">数据库连接</el-menu-item>
              <!-- <el-menu-item index="/data-select">数据选择</el-menu-item> -->
            </el-sub-menu>
            
            <el-sub-menu index="model">
              <template #title>
                <el-icon><Setting /></el-icon>
                <span>模型配置</span>
              </template>
              <el-menu-item index="/model-training">预测模型训练</el-menu-item>
              <el-menu-item index="/model-config">配置管理</el-menu-item>
              <el-menu-item index="/model-list">模型列表</el-menu-item>
            </el-sub-menu>
            
            <el-sub-menu index="rules">
              <template #title>
                <el-icon><Document /></el-icon>
                <span>规则生成</span>
              </template>
              <el-menu-item index="/rule-generate">规则生成</el-menu-item>
              <el-menu-item index="/rule-library">规则库管理</el-menu-item>
            </el-sub-menu>
            
            <el-sub-menu index="quality">
              <template #title>
                <el-icon><Check /></el-icon>
                <span>质量检测</span>
              </template>
              <el-menu-item index="/quality-check">质量检测</el-menu-item>
              <el-menu-item index="/quality-report">检测报告</el-menu-item>
            </el-sub-menu>

            <el-sub-menu index="check">
              <template #title>
                <el-icon><ChatDotRound /></el-icon>
                <span>文本型数据检测</span>
              </template>
              <el-menu-item index="/llm-quality-check">文本数据质检</el-menu-item>
            </el-sub-menu>

            <el-sub-menu index="system">
              <template #title>
                <el-icon><Setting /></el-icon>
                <span>系统管理</span>
              </template>
              <el-menu-item index="/well-whitelist">井名白名单管理</el-menu-item>
            </el-sub-menu>
          </el-menu>
        </el-aside>

        <!-- 主内容区 -->
        <el-main class="main-content">
          <el-breadcrumb separator="/" class="breadcrumb">
            <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
            <el-breadcrumb-item v-if="$route.meta.title">{{ $route.meta.title }}</el-breadcrumb-item>
          </el-breadcrumb>
          
          <div class="content-wrapper">
            <router-view />
          </div>
        </el-main>
      </el-container>
    </div>
  </div>
</template>

<script>
import { computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { House, Setting, Connection, Document, Check, ChatDotRound, User, ArrowDown } from '@element-plus/icons-vue'
import { useUserStore } from './stores/user.js'

export default {
  name: 'App',
  components: {
    House,
    Setting,
    Connection,
    Document,
    Check,
    ChatDotRound,
    User,
    ArrowDown
  },
  setup() {
    const router = useRouter()
    const userStore = useUserStore()
    
    // 计算属性
    const isLoggedIn = computed(() => userStore.getIsLoggedIn)
    const username = computed(() => userStore.username)
    
    // 处理用户下拉菜单命令
    const handleUserCommand = async (command) => {
      switch (command) {
        case 'profile':
          ElMessage.info('个人资料功能开发中...')
          break
        case 'settings':
          ElMessage.info('系统设置功能开发中...')
          break
        case 'logout':
          try {
            await ElMessageBox.confirm(
              '确定要退出登录吗？',
              '确认退出',
              {
                confirmButtonText: '确定',
                cancelButtonText: '取消',
                type: 'warning'
              }
            )
            userStore.logout()
            ElMessage.success('已退出登录')
            router.push('/login')
          } catch {
            // 用户取消退出
          }
          break
      }
    }
    
    // 初始化认证状态
    onMounted(() => {
      userStore.initAuthState()
    })
    
    return {
      isLoggedIn,
      username,
      handleUserCommand
    }
  }
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

#app {
  height: 100vh;
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', '微软雅黑', Arial, sans-serif;
}

.login-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
}

.top-header {
  background-color: #fff;
  border-bottom: 1px solid #e6e6e6;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  height: 60px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.header-left {
  display: flex;
  align-items: center;
}

.header-right {
  display: flex;
  align-items: center;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: #f5f7fa;
  border-radius: 20px;
  cursor: pointer;
  transition: all 0.3s ease;
  color: #606266;
  font-size: 14px;
}

.user-info:hover {
  background: #ecf5ff;
  color: #409EFF;
}

.logo h2 {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.main-container {
  height: calc(100vh - 60px);
}

.sidebar {
  background-color: #304156;
  color: #bfcbd9;
}

.sidebar-menu {
  border-right: none;
  height: 100%;
}

.main-content {
  background-color: #f0f2f5;
  padding: 20px;
  overflow-y: auto;
}

.breadcrumb {
  margin-bottom: 20px;
  padding: 10px 0;
}

.content-wrapper {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  min-height: calc(100vh - 140px);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .sidebar {
    width: 64px !important;
  }
  
  .main-content {
    padding: 10px;
  }
  
  .content-wrapper {
    padding: 15px;
  }
}
</style> 