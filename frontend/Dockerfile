# ============================================================
# 云南省自然灾害应急响应平台 - 前端镜像 (Vue3 + Vite + Nginx)
# 多阶段构建：Node 编译 -> Nginx 托管静态资源
# ============================================================

# ---------- 构建阶段 ----------
FROM node:20-alpine AS builder
WORKDIR /build

# 使用淘宝镜像加速 npm
RUN npm config set registry https://registry.npmmirror.com

# 先拷贝依赖清单，利用层缓存
COPY package*.json ./
RUN npm ci

# 拷贝源码并构建（生产模式）
COPY . .
RUN npm run build

# ---------- 运行阶段 ----------
FROM nginx:alpine

# 时区
ENV TZ=Asia/Shanghai

# 拷贝构建产物
COPY --from=builder /build/dist /usr/share/nginx/html

# 拷贝 Nginx 配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
