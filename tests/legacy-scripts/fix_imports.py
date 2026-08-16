# 修复1: IncidentReportController 添加 SqlNeo4jSyncService import
file1 = r'f:\桌面\disaster\backend\src\main\java\com\yunnan\emergency\controller\IncidentReportController.java'
with open(file1, 'r', encoding='utf-8') as f:
    c = f.read()
if 'import com.yunnan.emergency.service.SqlNeo4jSyncService;' not in c:
    c = c.replace(
        'import com.yunnan.emergency.service.IncidentStateMachineService;',
        'import com.yunnan.emergency.service.IncidentStateMachineService;\nimport com.yunnan.emergency.service.SqlNeo4jSyncService;'
    )
    with open(file1, 'w', encoding='utf-8') as f:
        f.write(c)
    print('Fixed: IncidentReportController import')
else:
    print('Skip: IncidentReportController import already exists')

# 修复2: ResultCode getter 问题 - 检查枚举的 getter
file2 = r'f:\桌面\disaster\backend\src\main\java\com\yunnan\emergency\common\ResultCode.java'
with open(file2, 'r', encoding='utf-8') as f:
    c2 = f.read()
print('ResultCode content:')
print(c2[:500])
