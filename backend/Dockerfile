# 多模块后端镜像：通过 MODULE 指定要构建运行的子系统，PORT 指定监听端口
# 用法：docker build --build-arg MODULE=admin-service --build-arg PORT=8084 -t yn-admin ./backend
FROM maven:3.9.6-eclipse-temurin-8 AS build
WORKDIR /app
COPY pom.xml .
COPY common ./common
COPY report-service ./report-service
COPY command-service ./command-service
COPY resource-service ./resource-service
COPY admin-service ./admin-service
RUN mvn -q -DskipTests clean package

FROM eclipse-temurin:8-jre
ARG MODULE=admin-service
ARG PORT=8094
WORKDIR /app
COPY --from=build /app/${MODULE}/target/${MODULE}.jar /app/app.jar
EXPOSE ${PORT}
ENTRYPOINT ["java", "-jar", "/app/app.jar"]
