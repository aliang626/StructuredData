# 勘探开发数据湖数据质量智能探查系统

基于Flask与Vue3的勘探开发数据湖数据质量智能探查系统，支持多模型可配置的数据处理流程、数据库表字段级数据选取、动态规则库生成与质检分离、CNOOC数据库专项对接能力。

## 系统架构

- **后端**: Flask + SQLAlchemy + scikit-learn
- **前端**: Vue3 + Element Plus + ECharts
- **数据库**: MySQL/PostgreSQL

## 核心功能

1. **数据库管理**: 数据库连接配置、数据源管理、表字段选择
2. **模型配置中心**: 支持回归类和聚簇类模型参数配置
3. **模型训练**: 可视化模型训练界面，支持多种算法
4. **规则生成系统**: 基于数据特征的自动规则生成
5. **规则库管理**: 规则库版本控制和规则查看
6. **质量检测系统**: 独立质检界面和批量检测
7. **检测报告**: 质量检测结果查看、导出和删除

## 项目结构

```
StructuredDataNew/
├── backend/                 # Flask后端
│   ├── app/
│   │   ├── models/         # 数据模型
│   │   │   ├── data_source.py      # 数据源模型
│   │   │   ├── model_config.py     # 模型配置模型
│   │   │   ├── quality_result.py   # 质量检测结果模型
│   │   │   └── rule_model.py       # 规则库模型
│   │   ├── routes/         # API路由
│   │   │   ├── database_routes.py  # 数据库管理API
│   │   │   ├── model_routes.py     # 模型相关API
│   │   │   ├── quality_routes.py   # 质量检测API
│   │   │   ├── rule_routes.py      # 规则管理API
│   │   │   └── system_routes.py    # 系统统计API
│   │   ├── services/       # 业务逻辑
│   │   │   ├── database_service.py # 数据库服务
│   │   │   ├── model_service.py    # 模型服务
│   │   │   ├── quality_service.py  # 质量检测服务
│   │   │   └── rule_service.py     # 规则服务
│   │   └── __init__.py     # Flask应用初始化
│   ├── config/             # 配置文件
│   │   └── db_config.ini   # 数据库配置
│   ├── app.py              # 应用入口
│   └── requirements.txt    # Python依赖
├── frontend/               # Vue3前端
│   ├── src/
│   │   ├── views/          # 页面组件
│   │   │   ├── Home.vue              # 首页
│   │   │   ├── DatabaseConnect.vue   # 数据库连接
│   │   │   ├── ModelConfig.vue       # 模型配置
│   │   │   ├── ModelList.vue         # 模型列表
│   │   │   ├── ModelTraining.vue     # 模型训练
│   │   │   ├── QualityCheck.vue      # 质量检测
│   │   │   ├── QualityReport.vue     # 检测报告
│   │   │   ├── RuleGenerate.vue      # 规则生成
│   │   │   └── RuleLibrary.vue       # 规则库管理
│   │   ├── router/         # 路由配置
│   │   │   └── index.js    # 路由定义
│   │   ├── stores/         # 状态管理
│   │   │   └── index.js    # Pinia状态管理
│   │   ├── utils/          # 工具函数
│   │   │   └── api.js      # API请求封装
│   │   ├── App.vue         # 根组件
│   │   └── main.js         # 应用入口
│   ├── vite.config.js      # Vite配置
│   └── package.json        # Node.js依赖
├── start_backend.bat       # 后端启动脚本
├── start_frontend.bat      # 前端启动脚本
└── install_dependencies.bat # 依赖安装脚本
```

## 快速开始

### 环境要求

- **Python**: 3.8+
- **Node.js**: 16+
- **数据库**: MySQL / PostgreSQL

### 1. 克隆项目

```bash
git clone <repository-url>
cd StructuredDataNew
```

### 2. 安装依赖

#### 方式一：使用批处理脚本（Windows）
```bash
# 安装所有依赖
install_dependencies.bat
```

#### 方式二：手动安装

**后端依赖安装**
```bash
cd backend
pip install -r requirements.txt
```

**前端依赖安装**
```bash
cd frontend
npm install
```

### 3. 配置数据库

#### 数据库配置
1. 修改 `backend/config/db_config.ini` 中的数据库连接信息
2. 创建数据库和用户
3. 运行数据库迁移

### 4. 启动系统

#### 方式一：使用批处理脚本（Windows）
```bash
# 启动后端
start_backend.bat

# 启动前端（新开终端）
start_frontend.bat
```

#### 方式二：手动启动

**启动后端**
```bash
cd backend
python app.py
```
后端将在 http://localhost:5000 启动

**启动前端**
```bash
cd frontend
npm run dev
```
前端将在 http://localhost:3000 启动

### 5. 访问系统

打开浏览器访问 http://localhost:3000

## 功能使用指南

### 1. 数据库管理
- 配置数据库连接信息
- 查看数据源列表
- 选择数据表和字段

### 2. 模型配置
- 创建模型配置
- 设置算法参数
- 管理配置列表

### 3. 模型训练
- 选择数据源和表
- 配置训练参数
- 查看训练进度和结果

### 4. 规则生成
- 基于数据特征自动生成规则
- 配置规则类型和参数
- 保存规则到规则库

### 5. 规则库管理
- 创建和管理规则库
- 版本控制
- 查看规则详情

### 6. 质量检测
- 选择规则库和版本
- 执行质量检测
- 查看检测结果

### 7. 检测报告
- 查看历史检测报告
- 导出报告数据
- 删除不需要的报告
