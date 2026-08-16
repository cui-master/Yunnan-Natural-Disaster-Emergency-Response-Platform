file_path = r'f:\桌面\disaster\backend\src\main\java\com\yunnan\emergency\service\SqlNeo4jSyncService.java'
with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 1. 先读入新增方法的内容
with open(r'f:\桌面\disaster\new_methods_part1.txt', 'r', encoding='utf-8') as f:
    part1 = f.read()

print(f'part1 长度: {len(part1)}')
print(f'原文件第48行: {lines[47].rstrip()}')
print(f'原文件第64行: {lines[63].rstrip()}')
