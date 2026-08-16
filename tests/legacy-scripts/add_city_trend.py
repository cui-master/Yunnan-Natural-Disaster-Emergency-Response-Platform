file_path = r'f:\桌面\disaster\backend\src\main\java\com\yunnan\emergency\controller\IncidentController.java'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 添加 import
old_import = 'import java.util.HashMap;\nimport java.util.List;\nimport java.util.Map;'
new_import = 'import java.time.LocalDate;\nimport java.util.ArrayList;\nimport java.util.HashMap;\nimport java.util.List;\nimport java.util.Map;'

if old_import in content:
    content = content.replace(old_import, new_import)
    print('import 添加成功')
else:
    print('未找到 import')

# 在 getDashboardStats 方法后添加 city-count 和 weekly-trend 接口
old_method_end = '''        return Result.success(stats);
    }

    @Operation(summary = "获取实时事件列表")'''

new_method_end = '''        return Result.success(stats);
    }

    @Operation(summary = "获取各地市灾害数量")
    @GetMapping("/dashboard/city-count")
    public Result<List<Map<String, Object>>> getCityDisasterCount() {
        List<Incident> allIncidents = incidentMapper.selectList(null);
        Map<String, Integer> cityCount = new HashMap<>();
        for (Incident inc : allIncidents) {
            String loc = inc.getLocationName();
            if (loc == null || loc.isEmpty()) continue;
            String city = null;
            int idx = loc.indexOf("市");
            if (idx > 0) {
                city = loc.substring(0, idx + 1);
            } else if (loc.length() >= 2) {
                city = loc.substring(0, 2) + "市";
            }
            if (city != null) {
                cityCount.put(city, cityCount.getOrDefault(city, 0) + 1);
            }
        }
        List<Map<String, Object>> result = new ArrayList<>();
        for (Map.Entry<String, Integer> entry : cityCount.entrySet()) {
            Map<String, Object> item = new HashMap<>();
            item.put("city", entry.getKey());
            item.put("count", entry.getValue());
            result.add(item);
        }
        result.sort((a, b) -> ((Integer) b.get("count")).compareTo((Integer) a.get("count")));
        return Result.success(result);
    }

    @Operation(summary = "获取近7日灾害趋势")
    @GetMapping("/dashboard/weekly-trend")
    public Result<List<Map<String, Object>>> getWeeklyTrend() {
        List<Map<String, Object>> result = new ArrayList<>();
        LocalDate today = LocalDate.now();
        for (int i = 6; i >= 0; i--) {
            LocalDate date = today.minusDays(i);
            String dateStr = date.toString();
            Long count = incidentMapper.selectCount(
                new LambdaQueryWrapper<Incident>()
                    .apply("DATE(created_at) = {0}", dateStr)
            );
            Map<String, Object> item = new HashMap<>();
            item.put("date", dateStr.substring(5));
            item.put("count", count.intValue());
            result.add(item);
        }
        return Result.success(result);
    }

    @Operation(summary = "获取实时事件列表")'''

if old_method_end in content:
    content = content.replace(old_method_end, new_method_end)
    print('两个接口添加成功')
else:
    print('未找到方法结束标记')

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print(f'文件已保存，长度: {len(content)}')
