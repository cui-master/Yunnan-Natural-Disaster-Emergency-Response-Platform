FROM postgis/postgis:15-3.4

USER root
RUN apt-get update \
    && apt-get install -y --no-install-recommends postgresql-15-pgvector \
    && rm -rf /var/lib/apt/lists/*

USER postgres

# 初始化脚本挂载到 /docker-entrypoint-initdb.d 会自动执行
# 见 docker-compose.yml 的 volumes 映射
EXPOSE 5432
