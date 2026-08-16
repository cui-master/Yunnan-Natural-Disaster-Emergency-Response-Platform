file_path = r'f:\桌面\disaster\backend\src\main\java\com\yunnan\emergency\controller\IncidentReportController.java'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

old = '''        // 审核通过时，创建正式灾情事件（状态为"已确认"）
        if ("approved".equals(status)) {
            Incident incident = new Incident();
            incident.setIncidentNo("INC-" + System.currentTimeMillis());
            incident.setTitle(report.getTitle());
            incident.setDisasterType(report.getDisasterType());
            incident.setRiskLevel(report.getRiskLevel());
            incident.setLocationName(report.getLocationName());
            incident.setLng(report.getLng());
            incident.setLat(report.getLat());
            incident.setStatus("已确认");
            incident.setSource("manual");
            incident.setReporterId(report.getReporterId());
            incident.setReviewerId(user.getId());
            incident.setReviewedAt(LocalDateTime.now());
            incident.setOccurredAt(report.getOccurredAt());
            incident.setDescription(report.getDescription());
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
            }
        }'''

new = '''        // 审核通过时，创建正式灾情事件（状态为"已确认"），并从 incident_reports 中删除
        if ("approved".equals(status)) {
            Incident incident = new Incident();
            incident.setIncidentNo("INC-" + System.currentTimeMillis());
            incident.setTitle(report.getTitle());
            incident.setDisasterType(report.getDisasterType());
            incident.setRiskLevel(report.getRiskLevel());
            incident.setLocationName(report.getLocationName());
            incident.setLng(report.getLng());
            incident.setLat(report.getLat());
            incident.setStatus("已确认");
            incident.setSource("manual");
            incident.setReporterId(report.getReporterId());
            incident.setReviewerId(user.getId());
            incident.setReviewedAt(LocalDateTime.now());
            incident.setOccurredAt(report.getOccurredAt());
            incident.setDescription(report.getDescription());
            incident.setAffectedPeople(report.getAffectedPeople());
            incident.setDistrict(report.getDistrict());
            incident.setStreet(report.getStreet());
            incident.setRoadName(report.getRoadName());
            incidentMapper.insert(incident);

            // 同步到 Neo4j（在删除前同步）
            try {
                sqlNeo4jSyncService.syncIncidentCreate(incident);
            } catch (Exception e) {
                // Neo4j 同步失败不影响 SQL 主流程
            }

            // 审核通过后删除 incident_reports 中的记录
            reportMapper.deleteById(report.getId());
        } else {
            // 审核拒绝时，只更新状态和备注，保留记录
            report.setStatus(status);
            report.setReviewComment(comment);
            report.setReviewerId(user.getId());
            report.setReviewedAt(LocalDateTime.now());
            reportMapper.updateById(report);
        }'''

if old in content:
    content = content.replace(old, new)
    print('审核逻辑修改成功')
else:
    print('未找到 old 内容')

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print(f'文件已保存，长度: {len(content)}')
