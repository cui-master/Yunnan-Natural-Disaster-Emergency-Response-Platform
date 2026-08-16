$content = Get-Content "f:\桌面\disaster\backend\src\main\java\com\yunnan\emergency\service\Neo4jService.java" -Raw -Encoding UTF8

$oldBlock = '    /** 根据 label 反推业务主键字段名 */
    public static String businessKeyOf(String label) {
        return switch (label) {
            case "Incident" -> "incidentId";
            case "Resource" -> "resourceId";
            case "DispatchOrder" -> "dispatchOrderId";
            case "Location" -> "locationId";
            default -> "id";
        };
    }'

$newBlock = '    /** 根据 label 反推业务主键字段名 */
    public static String businessKeyOf(String label) {
        return switch (label) {
            case "Incident" -> "incidentId";
            case "Resource" -> "resourceId";
            case "DispatchOrder" -> "dispatchOrderId";
            case "Location" -> "locationId";
            case "RiskLevel" -> "level";
            case "AffectedCount" -> "incidentId";
            case "DisasterType" -> "typeName";
            case "Road" -> "roadName";
            case "PlaceName" -> "placeName";
            default -> "id";
        };
    }'

$content = $content.Replace($oldBlock, $newBlock)

[System.IO.File]::WriteAllText("f:\桌面\disaster\backend\src\main\java\com\yunnan\emergency\service\Neo4jService.java", $content, [System.Text.Encoding]::UTF8)
Write-Host "Neo4jService updated successfully"
