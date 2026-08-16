file_path = r'f:\桌面\disaster\backend\src\main\java\com\yunnan\emergency\service\SqlNeo4jSyncService.java'
with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()
print(f'总行数: {len(lines)}')
# 找 syncIncidentCreate 的行号
for i, line in enumerate(lines):
    if 'public void syncIncidentCreate' in line:
        print(f'syncIncidentCreate 在第 {i+1} 行')
    if 'public void syncIncidentUpdate' in line:
        print(f'syncIncidentUpdate 在第 {i+1} 行')
    if 'private Map<String, Object> buildIncidentProps' in line:
        print(f'buildIncidentProps 在第 {i+1} 行')
    if '// ============ Resource 同步 ============' in line:
        print(f'Resource同步开始 在第 {i+1} 行')
