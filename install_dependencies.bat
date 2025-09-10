@echo off
echo 安装系统依赖...

echo 安装Python后端依赖...
cd backend
pip install -r requirements.txt

echo 安装Node.js前端依赖...
cd ../frontend
npm install

echo 依赖安装完成！
pause 