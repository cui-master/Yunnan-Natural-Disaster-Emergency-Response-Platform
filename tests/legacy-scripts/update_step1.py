file_path = r'f:\桌面\disaster\backend\src\main\java\com\yunnan\emergency\service\SqlNeo4jSyncService.java'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. 修改 syncIncidentCreate 方法末尾添加调用
old_create_end = '''            }
        }
    }

    public void syncIncidentUpdate'''

new_calls = '''            }
        }
        // 同步风险等级节点及关系
        syncRiskLevel(incident);
        // 同步受灾人数节点及关系
        syncAffectedCount(incident);
        // 同步地点名称节点及关系
        syncPlaceName(incident);
        // 同步灾害类型节点及关系
        syncDisasterType(incident);
        // 同步道路节点及关系
        syncRoadRelations(incident);
    }

    public void syncIncidentUpdate'''

if old_create_end in content:
    content = content.replace(old_create_end, new_calls)
    print('1. syncIncidentCreate 添加调用成功')
else:
    print('1. 未找到 old_create_end')

# 2. 修改 syncIncidentUpdate 方法
old_update = '''    public void syncIncidentUpdate(Incident incident) {
        neo4jService.updateNode("Incident", incident.getId(), buildIncidentProps(incident));
    }'''

new_update = '''    public void syncIncidentUpdate(Incident incident) {
        neo4jService.updateNode("Incident", incident.getId(), buildIncidentProps(incident));
        // 重新同步所有关联节点和关系
        syncRiskLevel(incident);
        syncAffectedCount(incident);
        syncPlaceName(incident);
        syncDisasterType(incident);
        syncRoadRelations(incident);
    }'''

if old_update in content:
    content = content.replace(old_update, new_update)
    print('2. syncIncidentUpdate 更新成功')
else:
    print('2. 未找到 old_update')

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print(f'中间结果已保存，长度: {len(content)}')
