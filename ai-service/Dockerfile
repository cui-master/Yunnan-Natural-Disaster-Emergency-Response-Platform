# ============================================================
# 云南省自然灾害应急响应平台 - AI 服务镜像 (FastAPI)
# 端口: 8050
# ============================================================
FROM python:3.10-slim

WORKDIR /app

# 时区
ENV TZ=Asia/Shanghai
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# 安装依赖（利用层缓存）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 拷贝应用代码
COPY app/ ./app/

RUN mkdir -p logs

EXPOSE 8050

# 直接用 uvicorn 启动，避免 reload（生产模式）
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8050"]
