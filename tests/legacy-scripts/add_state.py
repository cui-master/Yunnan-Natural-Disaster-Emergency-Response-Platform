file_path = r'f:\桌面\disaster\backend\src\main\java\com\yunnan\emergency\service\SqlNeo4jSyncService.java'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

with open(r'f:\桌面\disaster\helper_method.txt', 'r', encoding='utf-8') as f:
    helper = f.read()

# 第一步：在 props.put("incidentId", ...) 后面加 state 和 name
old1 = '        props.put("incidentId", incident.getId());\n        props.put("incidentNo", incident.getIncidentNo());'
new1 = '        props.put("incidentId", incident.getId());\n        props.put("state", 1);\n        props.put("name", incident.getTitle());\n        props.put("location", incident.getLocationName());\n        props.put("road", incident.getRoadName());\n        props.put("riskLevelValue", mapRiskLevelToIntValue(incident.getRiskLevel()));\n        props.put("incidentNo", incident.getIncidentNo());'

if old1 in content:
    content = content.replace(old1, new1)
    print('第一步：添加 state/name/location/road/riskLevelValue 成功')
else:
    print('第一步：未找到 old1')

# 第二步：在 buildIncidentProps 方法结束后插入辅助方法
old2 = '        return props;\n    }\n\n    /**\n     * 风险等级映射：低->1, 中->2, 高->3, 极高->4'
new2 = '        return props;\n    }' + helper + '\n    /**\n     * 风险等级映射：低->1, 中->2, 高->3, 极高->4'

if old2 in content:
    content = content.replace(old2, new2)
    print('第二步：添加辅助方法成功')
else:
    print('第二步：未找到 old2')

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print(f'文件已保存，长度: {len(content)}')
