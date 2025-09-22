#!/bin/bash
# 麒麟系统ARM架构自动部署脚本

echo "=== 麒麟系统ARM架构部署脚本 ==="
echo "系统信息: $(uname -a)"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查Python版本
check_python() {
    log_info "检查Python环境..."
    if command -v python3 &> /dev/null; then
        python_version=$(python3 --version)
        log_info "Python版本: $python_version"
    else
        log_error "Python3未安装，请先安装Python3"
        exit 1
    fi
}

# 安装系统依赖
install_system_deps() {
    log_info "安装系统依赖..."
    
    # 检测包管理器
    if command -v yum &> /dev/null; then
        PKG_MANAGER="yum"
    elif command -v apt &> /dev/null; then
        PKG_MANAGER="apt"
    else
        log_error "不支持的包管理器"
        exit 1
    fi
    
    log_info "使用包管理器: $PKG_MANAGER"
    
    if [ "$PKG_MANAGER" = "yum" ]; then
        sudo yum update -y
        sudo yum groupinstall -y "Development Tools"
        sudo yum install -y python3-devel python3-pip mysql-devel postgresql-devel
        sudo yum install -y blas-devel lapack-devel atlas-devel
    else
        sudo apt update
        sudo apt install -y build-essential python3-dev python3-pip
        sudo apt install -y libmysqlclient-dev libpq-dev
        sudo apt install -y libblas-dev liblapack-dev libatlas-base-dev
    fi
}

# 安装Python依赖
install_python_deps() {
    log_info "安装Python依赖..."
    
    # 升级pip
    python3 -m pip install --upgrade pip setuptools wheel
    
    # 检查ARM优化的requirements文件
    if [ -f "backend/requirements-arm.txt" ]; then
        log_info "使用ARM优化的依赖文件..."
        pip3 install -r backend/requirements-arm.txt
    else
        log_warn "未找到ARM优化的依赖文件，使用标准文件..."
        pip3 install -r backend/requirements.txt
    fi
}

# 测试兼容性
test_compatibility() {
    log_info "测试ARM兼容性..."
    if [ -f "backend/test_arm_compatibility.py" ]; then
        cd backend
        python3 test_arm_compatibility.py
        if [ $? -eq 0 ]; then
            log_info "✅ 兼容性测试通过"
        else
            log_error "❌ 兼容性测试失败"
            exit 1
        fi
        cd ..
    else
        log_warn "未找到兼容性测试脚本"
    fi
}

# 安装前端依赖
install_frontend_deps() {
    log_info "安装前端依赖..."
    
    # 检查Node.js
    if command -v node &> /dev/null; then
        log_info "Node.js版本: $(node --version)"
    else
        log_error "Node.js未安装，请先安装Node.js"
        exit 1
    fi
    
    cd frontend
    npm install
    cd ..
}

# 创建启动脚本
create_start_scripts() {
    log_info "创建启动脚本..."
    
    # 服务器IP配置
    SERVER_IP="10.77.76.232"
    
    # 后端启动脚本
    cat > start_backend_arm.sh << EOF
#!/bin/bash
echo "启动ARM后端服务 (${SERVER_IP}:5000)..."
cd backend
export FLASK_ENV=production
export SERVER_IP=${SERVER_IP}
python3 app.py
EOF
    
    # 前端启动脚本
    cat > start_frontend_arm.sh << EOF
#!/bin/bash
echo "启动ARM前端服务 (${SERVER_IP}:3000)..."
cd frontend
npm run dev -- --host 0.0.0.0 --port 3000
EOF
    
    # 生产环境前端构建和启动脚本
    cat > start_frontend_prod.sh << EOF
#!/bin/bash
echo "构建并启动生产环境前端..."
cd frontend
npm run build
echo "前端已构建到 dist/ 目录"
echo "请将 dist/ 目录部署到Web服务器"
echo "或者使用 serve 命令: npx serve dist -l 3000"
EOF
    
    chmod +x start_backend_arm.sh start_frontend_arm.sh start_frontend_prod.sh
    log_info "启动脚本创建完成"
}

# 主函数
main() {
    log_info "开始ARM架构部署..."
    
    check_python
    install_system_deps
    install_python_deps
    test_compatibility
    install_frontend_deps
    create_start_scripts
    
    log_info "🎉 ARM架构部署完成！"
    echo ""
    echo "使用以下命令启动服务:"
    echo "  后端: ./start_backend_arm.sh"
    echo "  前端开发模式: ./start_frontend_arm.sh"
    echo "  前端生产模式: ./start_frontend_prod.sh"
    echo ""
    echo "访问地址:"
    echo "  前端: http://10.77.76.232:3000"
    echo "  后端API: http://10.77.76.232:5000"
    echo "  健康检查: http://10.77.76.232:5000/health"
    echo ""
    echo "内网访问说明:"
    echo "  - 任何内网电脑都可以通过 http://10.77.76.232:3000 访问系统"
    echo "  - 前端会自动调用 http://10.77.76.232:5000 的后端API"
}

# 运行主函数
main "$@"
