file_path = r'f:\桌面\disaster\backend\src\main\java\com\yunnan\emergency\service\SqlNeo4jSyncService.java'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

with open(r'f:\桌面\disaster\helper_method.txt', 'r', encoding='utf-8') as f:
    helper = f.read()

# 找 buildIncidentProps 的起始和结束行号
lines = content.split('\n')
start = -1
end = -1
for i, line in enumerate(lines):
    if 'private Map<String, Object> buildIncidentProps' in line:
        start = i
    if start > 0 and line.strip() == '}' and end == -1:
        # 找到方法结束的右大括号
        # 检查后面的内容确认
        if i > start and i < start + 40:
            end = i
            break

print(f'buildIncidentProps: 第{start+1}行 - 第{end+1}行')
print(f'第{end+1}行内容: {lines[end].strip()}')
