# 勘探开发数据湖数据质量智能探查系统

基于Flask与Vue3的勘探开发数据湖数据质量智能探查系统，支持多模型可配置的数据处理流程、数据库表字段级数据选取、动态规则库生成与质检分离、CNOOC数据库专项对接能力，集成中海油SSO单点登录系统。

## 系统架构

- **后端**: Flask + SQLAlchemy + scikit-learn
- **前端**: Vue3 + Element Plus + ECharts
- **数据库**: MySQL/PostgreSQL

## 核心功能

1. **身份认证系统**: 
   - 中海油SSO单点登录集成
   - 传统用户名密码登录（备用方案）
   - 用户会话管理和状态维护
   
2. **数据库管理**: 数据库连接配置、数据源管理、表字段选择

3. **模型配置中心**: 支持回归类和聚簇类模型参数配置

4. **模型训练**: 可视化模型训练界面，支持多种算法

5. **规则生成系统**: 基于数据特征的自动规则生成

6. **规则库管理**: 规则库版本控制和规则查看

7. **质量检测系统**: 
   - 独立质检界面和批量检测
   - 文本质量检测（LLM集成）
   - 井名白名单管理

8. **检测报告**: 质量检测结果查看、导出和删除

9. **系统监控**: 系统健康状态监控、用户活动跟踪

## 项目结构

```
StructuredDataV4.0/
├── backend/                 # Flask后端
│   ├── app/
│   │   ├── models/         # 数据模型
│   │   │   ├── data_source.py      # 数据源模型
│   │   │   ├── model_config.py     # 模型配置模型
│   │   │   ├── quality_result.py   # 质量检测结果模型
│   │   │   ├── rule_model.py       # 规则库模型
│   │   │   ├── knowledge_base.py   # 知识库模型
│   │   │   └── training_history.py # 训练历史模型
│   │   ├── routes/         # API路由
│   │   │   ├── database_routes.py  # 数据库管理API
│   │   │   ├── model_routes.py     # 模型相关API
│   │   │   ├── quality_routes.py   # 质量检测API
│   │   │   ├── rule_routes.py      # 规则管理API
│   │   │   └── system_routes.py    # 系统统计/SSO认证API
│   │   ├── services/       # 业务逻辑
│   │   │   ├── database_service.py # 数据库服务
│   │   │   ├── model_service.py    # 模型服务
│   │   │   ├── quality_service.py  # 质量检测服务
│   │   │   ├── rule_service.py     # 规则服务
│   │   │   ├── sso_service.py      # SSO单点登录服务
│   │   │   ├── llm_client.py       # LLM客户端服务
│   │   │   ├── text_quality_service.py # 文本质量服务
│   │   │   └── field_mapping_service.py # 字段映射服务
│   │   └── __init__.py     # Flask应用初始化
│   ├── config/             # 配置文件
│   │   └── db_config.ini   # 数据库配置
│   ├── uploads/            # 上传文件
│   │   └── knowledge_bases/ # 知识库文件
│   ├── static/             # 静态文件
│   │   └── quality_plots/  # 质检图表
│   ├── app.py              # 应用入口
│   ├── init_mysql_database.py # 数据库初始化
│   ├── requirements.txt    # Python依赖
│   ├── requirements-arm.txt # ARM架构依赖
│   └── block_info.csv      # 井名白名单数据
├── frontend/               # Vue3前端
│   ├── src/
│   │   ├── views/          # 页面组件
│   │   │   ├── Home.vue              # 首页
│   │   │   ├── Login.vue             # 登录页面
│   │   │   ├── DatabaseConnect.vue   # 数据库连接
│   │   │   ├── DataSelect.vue        # 数据选择
│   │   │   ├── ModelConfig.vue       # 模型配置
│   │   │   ├── ModelList.vue         # 模型列表
│   │   │   ├── ModelTraining.vue     # 模型训练
│   │   │   ├── QualityCheck.vue      # 质量检测
│   │   │   ├── LLMQualityCheck.vue   # LLM质量检测
│   │   │   ├── QualityReport.vue     # 检测报告
│   │   │   ├── RuleGenerate.vue      # 规则生成
│   │   │   ├── RuleLibrary.vue       # 规则库管理
│   │   │   └── WellWhitelist.vue     # 井名白名单管理
│   │   ├── components/     # 公共组件
│   │   ├── router/         # 路由配置
│   │   │   └── index.js    # 路由定义
│   │   ├── stores/         # 状态管理
│   │   │   ├── index.js    # 主状态管理
│   │   │   └── user.js     # 用户状态管理
│   │   ├── utils/          # 工具函数
│   │   │   ├── api.js      # API请求封装
│   │   │   └── sso.js      # SSO工具函数
│   │   ├── data/           # 数据配置
│   │   │   └── models.js   # 模型配置数据
│   │   ├── App.vue         # 根组件
│   │   └── main.js         # 应用入口
│   ├── vite.config.js      # Vite配置
│   ├── package.json        # Node.js依赖
│   └── package-lock.json   # 依赖锁定文件
├── deploy_arm.sh           # ARM部署脚本
├── start_backend.bat       # 后端启动脚本
├── start_frontend.bat      # 前端启动脚本
├── install_dependencies.bat # 依赖安装脚本
├── README.md               # 项目说明文档
├── 快速启动说明.md         # 快速启动指南
├── SSO单点登录代码总结.md  # SSO功能详细文档
└── knowledge_base_example.md # 知识库示例
```

## 快速开始

### 环境要求

- **Python**: 3.8+
- **Node.js**: 16+
- **数据库**: MySQL / PostgreSQL

### 1. 克隆项目

```bash
git clone <repository-url>
cd StructuredDataV4.0
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

### 3. 系统配置

#### 数据库配置
1. 修改 `backend/config/db_config.ini` 中的数据库连接信息
2. 创建数据库和用户
3. 运行数据库初始化：
   ```bash
   cd backend
   python init_mysql_database.py
   ```

#### SSO配置（可选）
系统默认集成中海油SSO单点登录：
- SSO服务地址：`http://10.77.78.162/apigateway`
- 如需修改SSO配置，请编辑 `backend/app/services/sso_service.py`
- 备用登录：用户名 `admin`，密码 `Admin123`

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

- **开发环境**: http://localhost:3000
- **生产环境**: http://10.77.76.232:3000
- **后端API**: http://10.77.76.232:5000

#### 登录方式
1. **SSO登录**: 通过中海油SSO系统跳转（URL包含token参数）
2. **传统登录**: 用户名 `admin`，密码 `Admin123`

## 功能使用指南

### 1. 用户登录
- **SSO登录**: 从中海油门户系统跳转，系统自动解析token完成登录
- **传统登录**: 在登录页面输入用户名密码（备用方案）
- **会话管理**: 系统自动维护登录状态，页面刷新后保持登录

### 2. 数据库管理
- 配置数据库连接信息
- 查看数据源列表
- 选择数据表和字段
- 支持字段映射和数据预览

### 3. 模型配置
- 创建模型配置
- 设置算法参数
- 管理配置列表
- 支持多种机器学习算法

### 4. 模型训练
- 选择数据源和表
- 配置训练参数
- 查看训练进度和结果
- 训练历史记录管理

### 5. 规则生成
- 基于数据特征自动生成规则
- 配置规则类型和参数
- 保存规则到规则库
- 支持自定义规则编辑

### 6. 规则库管理
- 创建和管理规则库
- 版本控制
- 查看规则详情
- 规则导入导出

### 7. 质量检测
- **传统质检**: 基于规则库的批量质量检测
- **LLM质检**: 集成大语言模型的智能质量检测
- **井名白名单**: 井名质检白名单管理
- 支持多种检测策略

### 8. 检测报告
- 查看历史检测报告
- 导出报告数据（Excel/PDF）
- 删除不需要的报告
- 报告数据可视化

### 9. 系统管理
- 系统健康状态监控
- 用户活动日志查看
- 系统统计数据展示

## 🚀 技术特性

### 身份认证
- **SSO集成**: 完整的中海油SSO单点登录集成
- **Token验证**: 安全的token验证机制，支持缓存优化
- **会话管理**: 完善的用户会话管理和状态维护
- **备用登录**: 传统用户名密码登录作为备用方案

### 数据处理
- **多数据库支持**: MySQL、PostgreSQL等主流数据库
- **字段级选择**: 支持表字段级别的数据选取和映射
- **批量处理**: 高效的批量数据处理能力
- **实时预览**: 数据选择和处理的实时预览功能

### AI集成
- **机器学习**: 集成scikit-learn，支持多种ML算法
- **LLM集成**: 大语言模型集成，智能文本质量检测
- **规则引擎**: 基于数据特征的智能规则生成
- **模型管理**: 完善的模型配置和训练流程

### 系统架构
- **前后端分离**: Vue3 + Flask的现代化架构
- **RESTful API**: 标准化的API接口设计
- **状态管理**: Pinia状态管理，支持持久化
- **组件化**: 高度组件化的前端架构

## 🔧 部署说明

### 开发环境
```bash
# 克隆项目
git clone <repository-url>
cd StructuredDataV4.0

# 安装依赖
install_dependencies.bat

# 启动服务
start_backend.bat    # 后端服务
start_frontend.bat   # 前端服务
```

### 生产环境
```bash
# ARM架构部署
chmod +x deploy_arm.sh
./deploy_arm.sh

# 服务器地址
# 前端: http://10.77.76.232:3000
# 后端: http://10.77.76.232:5000
```

### 系统要求
- **操作系统**: Windows 10+, Ubuntu 18.04+, CentOS 7+
- **内存**: 建议4GB以上
- **存储**: 建议10GB以上可用空间
- **网络**: 需要访问中海油内网（SSO功能）

## 📚 相关文档

- [SSO单点登录详细文档](./SSO单点登录代码总结.md) - SSO功能的完整技术文档
- [快速启动指南](./快速启动说明.md) - 系统快速部署和使用指南
- [知识库示例](./knowledge_base_example.md) - 知识库配置和使用示例

