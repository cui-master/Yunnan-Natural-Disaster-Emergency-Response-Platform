file_path = r'f:\桌面\disaster\backend\src\main\java\com\yunnan\emergency\service\SqlNeo4jSyncService.java'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

with open(r'f:\桌面\disaster\helper_method.txt', 'r', encoding='utf-8') as f:
    helper = f.read()

# 找到 return props; 后面的位置，在 syncRiskLevel 方法之前插入
marker = '    /**\n     * 风险等级映射：低->1, 中->2, 高->3, 极高->4\n     * 创建 RiskLevel 节点'
if marker in content:
    content = content.replace(marker, helper + '\n    /**\n     * 风险等级映射：低->1, 中->2, 高->3, 极高->4\n     * 创建 RiskLevel 节点')
    print('插入辅助方法成功')
else:
    print('未找到 marker')

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print(f'文件已保存，长度: {len(content)}')
