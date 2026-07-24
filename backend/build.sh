#!/usr/bin/env bash
set -e
export JAVA_HOME="C:/Program Files (x86)/Java/jdk1.8.0_131"
JAVA="/c/Program Files (x86)/Java/jdk1.8.0_131/bin/java.exe"

# 优先用持久化 Maven，否则回退 Temp 缓存
MH_BASH="/c/Users/陈宝宝/AppData/Local/Temp/apache-maven-3.9.6"
if [ -d "/f/shixun(gaoji)/ShangJiaDianCan/backend/apache-maven-3.9.6" ]; then
  MH_BASH="/f/shixun(gaoji)/ShangJiaDianCan/backend/apache-maven-3.9.6"
fi
echo "Using Maven: $MH_BASH"

MH=$(cygpath -w "$MH_BASH")
BOOT_JAR=$(ls "$MH_BASH"/boot/plexus-classworlds-*.jar | head -1)
BOOT=$(cygpath -w "$BOOT_JAR")
CONF=$(cygpath -w "$MH_BASH/bin/m2.conf")
BACKEND_W=$(cygpath -w "/f/shixun(gaoji)/云南自然灾害应急协同决策平台/Yunnan-Natural-Disaster-Emergency-Response-Platform-main/backend")

cd "/f/shixun(gaoji)/云南自然灾害应急协同决策平台/Yunnan-Natural-Disaster-Emergency-Response-Platform-main/backend"
unset SERVER__PORT

"$JAVA" -classpath "$BOOT" \
  -Dclassworlds.conf="$CONF" \
  -Dmaven.home="$MH" \
  -Dmaven.multiModuleProjectDirectory="$BACKEND_W" \
  -Dmaven.wagon.http.ssl.insecure=true \
  -Dmaven.wagon.http.ssl.allowall=true \
  -Dmaven.resolver.transport=wagon \
  -Dmaven.repo.local="$HOME/.m2/repository" \
  org.codehaus.plexus.classworlds.launcher.Launcher \
  -f "$BACKEND_W/pom.xml" clean package -DskipTests
