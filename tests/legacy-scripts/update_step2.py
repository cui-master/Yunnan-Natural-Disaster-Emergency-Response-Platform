file_path = r'f:\桌面\disaster\backend\src\main\java\com\yunnan\emergency\service\SqlNeo4jSyncService.java'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 读取新方法
with open(r'f:\桌面\disaster\new_methods_part1.txt', 'r', encoding='utf-8') as f:
    part1 = f.read()
with open(r'f:\桌面\disaster\m2_place.txt', 'r', encoding='utf-8') as f:
    part2 = f.read()
with open(r'f:\桌面\disaster\m3_disaster_road.txt', 'r', encoding='utf-8') as f:
    part3 = f.read()

all_new_methods = part1 + part2 + part3

# 在 buildIncidentProps 中添加新字段，并在方法后插入所有新方法
old_build_end = '''        if (incident.getLocationId() != null) {
            props.put("locationId", incident.getLocationId());
        }
        return props;
    }

    // ============ Resource 同步 ============'''

new_build_end = '''        if (incident.getLocationId() != null) {
            props.put("locationId", incident.getLocationId());
        }
        if (incident.getAffectedPeople() != null) {
            props.put("affectedPeople", incident.getAffectedPeople());
        }
        if (incident.getDistrict() != null) {
            props.put("district", incident.getDistrict());
        }
        if (incident.getStreet() != null) {
            props.put("street", incident.getStreet());
        }
        if (incident.getRoadName() != null) {
            props.put("roadName", incident.getRoadName());
        }
        return props;
    }''' + all_new_methods + '''

    // ============ Resource 同步 ============'''

if old_build_end in content:
    content = content.replace(old_build_end, new_build_end)
    print('3. 添加新字段和新方法成功')
else:
    print('3. 未找到 old_build_end')

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print(f'最终文件长度: {len(content)}')
