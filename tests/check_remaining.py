# 检查各个问题文件
files = {
    'IncidentController': r'f:\桌面\disaster\backend\src\main\java\com\yunnan\emergency\controller\IncidentController.java',
    'IncidentReportController': r'f:\桌面\disaster\backend\src\main\java\com\yunnan\emergency\controller\IncidentReportController.java',
    'EventStatusWebSocketHandler': r'f:\桌面\disaster\backend\src\main\java\com\yunnan\emergency\websocket\EventStatusWebSocketHandler.java',
    'Neo4jConfig': r'f:\桌面\disaster\backend\src\main\java\com\yunnan\emergency\config\Neo4jConfig.java',
    'AuthController': r'f:\桌面\disaster\backend\src\main\java\com\yunnan\emergency\controller\AuthController.java',
}

for name, path in files.items():
    with open(path, 'r', encoding='utf-8') as f:
        c = f.read()
    has_log = 'private static final Logger log' in c
    has_slf4j = '@Slf4j' in c
    print(f'{name}: has_log={has_log}, has_slf4j={has_slf4j}, lines={len(c.splitlines())}')
