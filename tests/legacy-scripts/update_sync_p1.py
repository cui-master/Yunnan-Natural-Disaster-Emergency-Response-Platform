import os

file_path = r'f:\桌面\disaster\backend\src\main\java\com\yunnan\emergency\service\SqlNeo4jSyncService.java'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

print(f'原文件长度: {len(content)}')

# 第一步：替换 syncIncidentCreate
old_create = '''    public void syncIncidentCreate(Incident incident) {
        Map<String, Object> props = buildIncidentProps(incident);
        neo4jService.createNode("Incident", props);
        // 灾情-地点关系
        if (incident.getLocationId() != null) {
            try {
                neo4jService.createRelationship(
                    "Incident", incident.getId(),
                    "Location", incident.getLocationId(),
                    "LOCATED_AT", Map.of()
                );
            } catch (Exception e) {
                log.warn("[sync] 灾情-地点关系建立失败（地点节点可能不存在）: incidentId={}, err={}",
                    incident.getId(), e.getMessage());
            }
        }
    }'''

print('找到 old_create:', old_create in content)
