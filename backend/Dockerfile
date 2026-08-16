# ============================================================
# 云南省自然灾害应急响应平台 - Spring Boot 后端镜像
# 多阶段构建：Maven 编译 -> JRE 运行
# ============================================================

# ---------- 构建阶段 ----------
FROM maven:3.9-eclipse-temurin-21 AS builder
WORKDIR /build

# 注入阿里云 Maven 镜像（加速国内依赖下载，避免 Maven Central 超时）
COPY docker-maven-settings.xml /root/.m2/settings.xml

# 先拷贝 pom.xml，利用 Docker 层缓存加速依赖下载
COPY pom.xml .
RUN mvn -B dependency:go-offline \
    -Dorg.slf4j.simpleLogger.log.org.apache.maven.cli.transfer.Slf4jMavenTransferListener=warn

# 拷贝源码并打包（跳过测试以加速构建）
COPY src ./src
RUN mvn -B clean package -DskipTests \
    -Dorg.slf4j.simpleLogger.log.org.apache.maven.cli.transfer.Slf4jMavenTransferListener=warn

# ---------- 运行阶段 ----------
FROM eclipse-temurin:21-jre
WORKDIR /app

# 创建上传目录与日志目录
RUN mkdir -p uploads logs

# 拷贝构建产物
COPY --from=builder /build/target/*.jar app.jar

# 时区设置（Asia/Shanghai）
ENV TZ=Asia/Shanghai
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

EXPOSE 8083

# JVM 参数可通过 JAVA_OPTS 注入
ENTRYPOINT ["sh", "-c", "java $JAVA_OPTS -jar app.jar"]
