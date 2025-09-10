<template>
  <div class="home">
    <!-- 页面标题 -->
    <div class="page-header">
      <h2>系统概览</h2>
      <p>勘探开发数据湖数据质量智能探查系统 - 实时监控与快速操作</p>
    </div>

    <!-- 欢迎区域 -->
    <el-row :gutter="24">
      <el-col :span="24">
        <el-card class="welcome-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <div class="header-left">
                <el-icon class="header-icon"><House /></el-icon>
                <span class="header-title">欢迎使用</span>
              </div>
            </div>
          </template>
          <div class="welcome-content">
            <div class="welcome-text">
              <h3>勘探开发数据湖数据质量智能探查系统</h3>
              <p>本系统提供以下核心功能：</p>
            </div>
            <div class="feature-grid">
              <div class="feature-item">
                <el-icon class="feature-icon"><Setting /></el-icon>
                <span>多模型可配置的数据处理流程</span>
              </div>
              <div class="feature-item">
                <el-icon class="feature-icon"><Connection /></el-icon>
                <span>数据库表字段级数据选取</span>
              </div>
              <div class="feature-item">
                <el-icon class="feature-icon"><Document /></el-icon>
                <span>动态规则库生成与质检分离</span>
              </div>
              <div class="feature-item">
                <el-icon class="feature-icon"><Check /></el-icon>
                <span>CNOOC数据库专项对接能力</span>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 功能统计卡片 -->
    <el-row :gutter="24" style="margin-top: 24px;">
      <el-col :span="6">
        <el-card class="stat-card" @click="$router.push('/model-config')" shadow="hover">
          <div class="stat-item">
            <div class="stat-icon">
              <el-icon size="48" color="#3498db"><Setting /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-number">{{ stats.modelCount }}</div>
              <div class="stat-label">模型配置</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card" @click="$router.push('/database-connect')" shadow="hover">
          <div class="stat-item">
            <div class="stat-icon">
              <el-icon size="48" color="#27ae60"><Connection /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-number">{{ stats.dbCount }}</div>
              <div class="stat-label">数据源</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card" @click="$router.push('/rule-generate')" shadow="hover">
          <div class="stat-item">
            <div class="stat-icon">
              <el-icon size="48" color="#f39c12"><Document /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-number">{{ stats.ruleCount }}</div>
              <div class="stat-label">规则库</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card" @click="$router.push('/quality-check')" shadow="hover">
          <div class="stat-item">
            <div class="stat-icon">
              <el-icon size="48" color="#e74c3c"><Check /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-number">{{ stats.qualityCount }}</div>
              <div class="stat-label">质检任务</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 系统状态和快速操作 -->
    <el-row :gutter="24" style="margin-top: 24px;">
      <el-col :span="12">
        <el-card class="status-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <div class="header-left">
                <el-icon class="header-icon"><Monitor /></el-icon>
                <span class="header-title">系统状态</span>
              </div>
            </div>
          </template>
          <div class="system-status">
            <div class="status-item">
              <div class="status-info">
                <span class="status-label">后端服务</span>
                <span class="status-desc">API服务运行状态</span>
              </div>
              <el-tag :type="backendStatus ? 'success' : 'danger'" size="large" effect="dark">
                <el-icon><CircleCheck v-if="backendStatus" /><CircleClose v-else /></el-icon>
                {{ backendStatus ? '正常' : '异常' }}
              </el-tag>
            </div>
            <div class="status-item">
              <div class="status-info">
                <span class="status-label">数据库连接</span>
                <span class="status-desc">数据库状态</span>
              </div>
              <el-tag :type="dbStatus ? 'success' : 'danger'" size="large" effect="dark">
                <el-icon><CircleCheck v-if="dbStatus" /><CircleClose v-else /></el-icon>
                {{ dbStatus ? '正常' : '异常' }}
              </el-tag>
            </div>
            <div class="status-item">
              <div class="status-info">
                <span class="status-label">系统版本</span>
                <span class="status-desc">当前系统版本号</span>
              </div>
              <el-tag type="info" size="large" effect="dark">v1.0.0</el-tag>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card class="quick-actions-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <div class="header-left">
                <el-icon class="header-icon"><Setting /></el-icon>
                <span class="header-title">快速操作</span>
              </div>
            </div>
          </template>
          <div class="quick-actions">
            <div class="action-grid">
              <el-button type="primary" @click="$router.push('/model-training')" class="action-btn">
                <el-icon><Setting /></el-icon>
                <span>模型训练</span>
              </el-button>
              <el-button type="success" @click="$router.push('/database-connect')" class="action-btn">
                <el-icon><Connection /></el-icon>
                <span>连接数据库</span>
              </el-button>
              <el-button type="warning" @click="$router.push('/rule-generate')" class="action-btn">
                <el-icon><Document /></el-icon>
                <span>生成规则</span>
              </el-button>
              <el-button type="danger" @click="$router.push('/quality-check')" class="action-btn">
                <el-icon><Check /></el-icon>
                <span>质量检测</span>
              </el-button>
              <el-button type="info" @click="$router.push('/llm-quality-check')" class="action-btn">
                <el-icon><ChatDotRound /></el-icon>
                <span>文本数据质检</span>
              </el-button>

            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 最近活动 -->
    <el-row :gutter="24" style="margin-top: 24px;">
      <el-col :span="24">
        <el-card class="activity-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <div class="header-left">
                <el-icon class="header-icon"><Clock /></el-icon>
                <span class="header-title">最近活动</span>
              </div>
            </div>
          </template>
          <div class="activity-content">
            <el-timeline>
              <el-timeline-item
                v-for="activity in recentActivities"
                :key="activity.id"
                :timestamp="activity.time"
                :type="activity.type"
                class="timeline-item"
              >
                <div class="activity-item">
                  <span class="activity-content">{{ activity.content }}</span>
                </div>
              </el-timeline-item>
            </el-timeline>
            <div v-if="recentActivities.length === 0" class="empty-activity">
              <el-icon class="empty-icon"><Clock /></el-icon>
              <p>暂无最近活动</p>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { Setting, Connection, Document, Check, Tools, House, Monitor, Clock, CircleCheck, CircleClose, ChatDotRound } from '@element-plus/icons-vue'

import axios from 'axios'

export default {
  name: 'Home',
  components: {
    Setting,
    Connection,
    Document,
    Check,
    Tools,
    House,
    Monitor,
    Clock,
    CircleCheck,
    CircleClose,
    ChatDotRound
  },
  setup() {
    const stats = ref({
      modelCount: 0,
      dbCount: 0,
      ruleCount: 0,
      qualityCount: 0
    })
    const backendStatus = ref(false)
    const dbStatus = ref(false)
    const recentActivities = ref([])

    const checkSystemStatus = async () => {
      try {
        const response = await axios.get('/api/health')
        backendStatus.value = response.data.status === 'healthy'
        dbStatus.value = response.data.db === 'ok'
      } catch (error) {
        console.log('后端服务未启动或连接失败:', error.message)
        backendStatus.value = false
        dbStatus.value = false
      }
    }

    const loadStats = async () => {
      try {
        console.log('开始加载统计数据...')
        const response = await axios.get('/api/stats', {
          headers: {
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
          }
        })
        console.log('统计数据响应:', response.data)
        if (response.data.success) {
          stats.value = response.data.data
          console.log('更新统计数据:', stats.value)
        }
      } catch (error) {
        console.error('加载统计数据失败:', error)
      }
    }

    const loadRecentActivities = async () => {
      try {
        const response = await axios.get('/api/activities')
        if (response.data.success) {
          recentActivities.value = response.data.data
        }
      } catch (error) {
        console.error('加载最近活动失败:', error)
      }
    }

    onMounted(() => {
      checkSystemStatus()
      loadStats()
      loadRecentActivities()
    })

    return {
      stats,
      backendStatus,
      dbStatus,
      recentActivities
    }
  }
}
</script>

<style scoped>
.home {
  padding: 20px;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  min-height: calc(100vh - 60px);
}

.page-header {
  text-align: center;
  margin-bottom: 30px;
  background: rgba(255, 255, 255, 0.9);
  padding: 20px;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
}

.page-header h2 {
  font-size: 28px;
  color: #2c3e50;
  margin-bottom: 8px;
  font-weight: 600;
}

.page-header p {
  font-size: 16px;
  color: #7f8c8d;
  margin: 0;
}

.welcome-card,
.status-card,
.quick-actions-card,
.activity-card {
  background: rgba(255, 255, 255, 0.95);
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  margin-bottom: 24px;
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
  color: #3498db;
  background: linear-gradient(135deg, #3498db, #2980b9);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.header-title {
  font-size: 20px;
  font-weight: 600;
  color: #2c3e50;
}

.welcome-content {
  font-size: 16px;
  line-height: 1.6;
}

.welcome-text h3 {
  font-size: 22px;
  color: #2c3e50;
  margin-bottom: 12px;
  font-weight: 600;
}

.welcome-text p {
  margin-bottom: 20px;
  color: #7f8c8d;
  font-size: 16px;
}

.feature-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 16px;
  margin-top: 20px;
}

.feature-item {
  display: flex;
  align-items: center;
  padding: 16px 20px;
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  border-radius: 10px;
  border: 2px solid #e9ecef;
  transition: all 0.3s ease;
}

.feature-item:hover {
  background: linear-gradient(135deg, #ecf5ff 0%, #e1f0ff 100%);
  border-color: #3498db;
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(52, 152, 219, 0.15);
}

.feature-icon {
  margin-right: 12px;
  font-size: 24px;
  color: #3498db;
}

.feature-item span {
  font-size: 15px;
  color: #2c3e50;
  font-weight: 500;
}

.stat-card {
  height: 140px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  background: rgba(255, 255, 255, 0.95);
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  position: relative;
  overflow: hidden;
}

.stat-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, #3498db, #2980b9);
  transform: scaleX(0);
  transition: transform 0.3s ease;
}

.stat-card:hover {
  transform: translateY(-6px);
  box-shadow: 0 16px 50px rgba(0, 0, 0, 0.15);
}

.stat-card:hover::before {
  transform: scaleX(1);
}

.stat-item {
  display: flex;
  align-items: center;
  height: 100%;
  padding: 20px;
}

.stat-icon {
  margin-right: 20px;
  background: rgba(52, 152, 219, 0.1);
  border-radius: 12px;
  padding: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.stat-info {
  flex: 1;
}

.stat-number {
  font-size: 32px;
  font-weight: 700;
  color: #2c3e50;
  margin-bottom: 8px;
}

.stat-label {
  color: #7f8c8d;
  font-size: 16px;
  font-weight: 500;
}

.system-status {
  padding: 10px 0;
}

.status-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding: 16px;
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  border-radius: 10px;
  border: 2px solid #e9ecef;
  transition: all 0.3s ease;
}

.status-item:hover {
  background: linear-gradient(135deg, #ecf5ff 0%, #e1f0ff 100%);
  border-color: #3498db;
  transform: translateX(4px);
}

.status-info {
  flex: 1;
  margin-right: 15px;
}

.status-label {
  color: #2c3e50;
  font-weight: 600;
  font-size: 16px;
  display: block;
  margin-bottom: 4px;
}

.status-desc {
  color: #7f8c8d;
  font-size: 14px;
}

.quick-actions {
  padding: 10px 0;
}

.action-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 16px;
}

.action-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 20px 16px;
  height: 100px;
  border-radius: 12px;
  font-weight: 600;
  transition: all 0.3s ease;
  border: 2px solid transparent;
}

.action-btn:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15);
}

.action-btn .el-icon {
  font-size: 24px;
}

.action-btn span {
  font-size: 14px;
}

.el-timeline {
  padding: 0;
}

.el-timeline-item {
  padding-bottom: 24px;
}

.timeline-item {
  padding-left: 20px;
}

.activity-item {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  border-radius: 8px;
  border: 1px solid #e9ecef;
  transition: all 0.3s ease;
}

.activity-item:hover {
  background: linear-gradient(135deg, #ecf5ff 0%, #e1f0ff 100%);
  border-color: #3498db;
  transform: translateX(4px);
}

.activity-content {
  font-size: 16px;
  line-height: 1.6;
  color: #2c3e50;
}

.empty-activity {
  text-align: center;
  padding: 40px 20px;
  color: #95a5a6;
}

.empty-icon {
  font-size: 60px;
  margin-bottom: 16px;
  color: #bdc3c7;
  opacity: 0.6;
}

.empty-activity p {
  font-size: 16px;
  margin: 0;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .feature-grid {
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  }
  
  .action-grid {
    grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  }
}

@media (max-width: 768px) {
  .home {
    padding: 15px;
  }
  
  .page-header h2 {
    font-size: 24px;
  }
  
  .feature-grid {
    grid-template-columns: 1fr;
  }
  
  .action-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .status-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
  
  .stat-item {
    flex-direction: column;
    text-align: center;
    gap: 12px;
  }
  
  .stat-icon {
    margin-right: 0;
  }
}
</style> 