# 数据管道服务配置

# ============================================
# 开发环境启动
# ============================================
# 1. 进入 data-pipeline 目录
# cd data-pipeline

# 2. 创建虚拟环境（可选）
# python -m venv venv
# source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. 安装依赖
# pip install -r requirements.txt

# 4. 复制环境变量文件
# cp .env.example .env

# 5. 启动服务
# python -m app.main

# ============================================
# Docker 部署
# ============================================

# 构建镜像
docker build -t yn-data-pipeline:latest ../data-pipeline

# 运行容器
docker run -d \
  --name yn-data-pipeline \
  -p 8000:8000 \
  -v $(pwd)/../data-pipeline/logs:/app/logs \
  --restart unless-stopped \
  yn-data-pipeline:latest

# 使用 docker-compose
docker-compose -f docker-compose.data-pipeline.yml up -d

# ============================================
# Nginx 反向代理配置示例
# ============================================
# server {
#     listen 80;
#     server_name your-domain.com;
#
#     location /sse {
#         proxy_pass http://127.0.0.1:8000/api/v1/sse;
#         proxy_set_header Host $host;
#         proxy_set_header X-Real-IP $remote_addr;
#         proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
#
#         # SSE 相关配置
#         proxy_buffering off;
#         proxy_cache off;
#         proxy_set_header Connection '';
#         proxy_http_version 1.1;
#         chunked_transfer_encoding off;
#
#         # 超时设置
#         proxy_read_timeout 86400;
#         proxy_send_timeout 86400;
#     }
#
#     location /api/ {
#         proxy_pass http://127.0.0.1:8000;
#         proxy_set_header Host $host;
#         proxy_set_header X-Real-IP $remote_addr;
#     }
# }
