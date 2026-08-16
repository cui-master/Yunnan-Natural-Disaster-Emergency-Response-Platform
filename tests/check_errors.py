# 修复1: IncidentController - 检查方法名
file1 = r'f:\桌面\disaster\backend\src\main\java\com\yunnan\emergency\controller\IncidentController.java'
with open(file1, 'r', encoding='utf-8') as f:
    c = f.read()
# 找 getWeeklyTrend 相关
import re
m = re.search(r'public Result.*getWeeklyTrend', c)
print('IncidentController method:', m.group() if m else 'NOT FOUND')

# 修复2: IncidentReportController - 检查 import
file2 = r'f:\桌面\disaster\backend\src\main\java\com\yunnan\emergency\controller\IncidentReportController.java'
with open(file2, 'r', encoding='utf-8') as f:
    c2 = f.read()
has_import = 'import com.yunnan.emergency.service.SqlNeo4jSyncService' in c2
print('Has SqlNeo4jSyncService import:', has_import)

# 修复3: Result.java - 检查 getter
file3 = r'f:\桌面\disaster\backend\src\main\java\com\yunnan\emergency\common\Result.java'
with open(file3, 'r', encoding='utf-8') as f:
    c3 = f.read()
print('Result has getData:', 'public T getData()' in c3)
print('Result has getCode:', 'public Integer getCode()' in c3)
print('Result line 51:', c3.split(chr(10))[50][:80] if len(c3.split(chr(10)))>50 else 'N/A')
