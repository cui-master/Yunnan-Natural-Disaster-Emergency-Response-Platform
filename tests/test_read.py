import os

file_path = r'f:\桌面\disaster\backend\src\main\java\com\yunnan\emergency\service\SqlNeo4jSyncService.java'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

print(f'文件长度: {len(content)}')
print('Incident 在文件中:', 'syncIncidentCreate' in content)
