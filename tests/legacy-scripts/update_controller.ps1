$content = Get-Content "f:\桌面\disaster\backend\src\main\java\com\yunnan\emergency\controller\IncidentReportController.java" -Raw -Encoding UTF8

# 1. 添加 SqlNeo4jSyncService 注入
$content = $content -replace "private final IncidentMapper incidentMapper;", "private final IncidentMapper incidentMapper;`n    private final SqlNeo4jSyncService sqlNeo4jSyncService;"

# 2. 在 create 方法中添加 locationName 组装逻辑
$oldCreate = "        report.setStatus(`"pending`");
        reportMapper.insert(report);

        return Result.success(report);"
$newCreate = "        report.setStatus(`"pending`");
        // 组装 locationName：州市 + 区/县 + 具体地址
        StringBuilder locName = new StringBuilder();
        if (report.getCity() != null) locName.append(report.getCity());
        if (report.getDistrict() != null) locName.append(report.getDistrict());
        if (report.getAddress() != null) locName.append(report.getAddress());
        if (locName.length() > 0) {
            report.setLocationName(locName.toString());
        }
        reportMapper.insert(report);

        return Result.success(report);"
$content = $content -replace [regex]::Escape($oldCreate), $newCreate

# 3. 在 review 方法的 approved 分支中添加新字段和 Neo4j 同步
$oldApproved = "            incident.setDescription(report.getDescription());
            incidentMapper.insert(incident);

            // 关联上报记录
            report.setIncidentId(incident.getId());
            reportMapper.updateById(report);"
$newApproved = "            incident.setDescription(report.getDescription());
            incident.setAffectedPeople(report.getAffectedPeople());
            incident.setDistrict(report.getDistrict());
            incident.setStreet(report.getStreet());
            incident.setRoadName(report.getRoadName());
            incidentMapper.insert(incident);

            // 关联上报记录
            report.setIncidentId(incident.getId());
            reportMapper.updateById(report);

            // 同步到 Neo4j
            try {
                sqlNeo4jSyncService.syncIncidentCreate(incident);
            } catch (Exception e) {
                // Neo4j 同步失败不影响 SQL 主流程
            }"
$content = $content -replace [regex]::Escape($oldApproved), $newApproved

[System.IO.File]::WriteAllText("f:\桌面\disaster\backend\src\main\java\com\yunnan\emergency\controller\IncidentReportController.java", $content, [System.Text.Encoding]::UTF8)
Write-Host "IncidentReportController updated successfully"
