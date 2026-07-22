"""
云南省自然灾害应急平台 - Neo4j 图数据库初始化脚本
包含：DDL约束 + 云南省示例数据（10个高风险区县 + 8个仓库 + 15种物资 + 6支救援队 + 8个避难所 + 路网）

使用方式：
    python scripts/init_neo4j.py   # 完整初始化（先清空再建）
    python scripts/init_neo4j.py --no-clear   # 不清空，仅追加
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.neo4j_client import neo4j_manager
from app.core.config import settings
from app.core.logging import logger


def clear_database():
    logger.warning("正在清空 Neo4j 数据库...")
    neo4j_manager.execute_query_sync("MATCH (n) DETACH DELETE n")
    logger.info("数据库已清空")


def create_constraints():
    """创建节点唯一性约束（类似关系型数据库的主键）"""
    constraints = [
        "CREATE CONSTRAINT dis_spot_id IF NOT EXISTS FOR (s:DisasterSpot) REQUIRE s.id IS UNIQUE",
        "CREATE CONSTRAINT warehouse_id IF NOT EXISTS FOR (w:Warehouse) REQUIRE w.id IS UNIQUE",
        "CREATE CONSTRAINT material_id IF NOT EXISTS FOR (m:Material) REQUIRE m.id IS UNIQUE",
        "CREATE CONSTRAINT rescue_team_id IF NOT EXISTS FOR (t:RescueTeam) REQUIRE t.id IS UNIQUE",
        "CREATE CONSTRAINT shelter_id IF NOT EXISTS FOR (sh:Shelter) REQUIRE sh.id IS UNIQUE",
        "CREATE CONSTRAINT dis_spot_name IF NOT EXISTS FOR (s:DisasterSpot) REQUIRE s.name IS UNIQUE",
    ]
    for cql in constraints:
        neo4j_manager.execute_query_sync(cql)
    logger.info("唯一性约束创建完成")


def create_disaster_spots():
    """创建云南10个典型高风险区县点位"""
    spots = [
        {"id": "spot-001", "name": "昭通市镇雄县", "disaster_type": ["滑坡", "泥石流", "洪涝"],
         "risk_level": "高", "urgent_level": 4, "lng": 104.86, "lat": 27.44},
        {"id": "spot-002", "name": "昆明市东川区", "disaster_type": ["滑坡", "泥石流"],
         "risk_level": "极高", "urgent_level": 5, "lng": 103.18, "lat": 26.08},
        {"id": "spot-003", "name": "大理州漾濞县", "disaster_type": ["地震", "滑坡"],
         "risk_level": "高", "urgent_level": 4, "lng": 99.97, "lat": 25.68},
        {"id": "spot-004", "name": "怒江州贡山县", "disaster_type": ["泥石流", "滑坡", "崩塌"],
         "risk_level": "极高", "urgent_level": 5, "lng": 98.67, "lat": 27.74},
        {"id": "spot-005", "name": "普洱市澜沧县", "disaster_type": ["地震", "洪涝"],
         "risk_level": "中", "urgent_level": 3, "lng": 99.93, "lat": 22.55},
        {"id": "spot-006", "name": "楚雄州南华县", "disaster_type": ["滑坡", "干旱"],
         "risk_level": "中", "urgent_level": 2, "lng": 101.26, "lat": 25.22},
        {"id": "spot-007", "name": "丽江市宁蒗县", "disaster_type": ["地震", "森林火灾"],
         "risk_level": "高", "urgent_level": 4, "lng": 100.85, "lat": 27.29},
        {"id": "spot-008", "name": "红河州元阳县", "disaster_type": ["滑坡", "泥石流"],
         "risk_level": "高", "urgent_level": 4, "lng": 102.82, "lat": 23.14},
        {"id": "spot-009", "name": "文山州广南县", "disaster_type": ["洪涝", "滑坡"],
         "risk_level": "中", "urgent_level": 3, "lng": 105.08, "lat": 24.06},
        {"id": "spot-010", "name": "德宏州盈江县", "disaster_type": ["地震", "洪涝"],
         "risk_level": "高", "urgent_level": 4, "lng": 97.94, "lat": 24.70},
    ]
    cql = """
    MERGE (s:DisasterSpot {id: $id})
    SET s.name = $name,
        s.disaster_type = $disaster_type,
        s.risk_level = $risk_level,
        s.urgent_level = $urgent_level,
        s.lng = $lng,
        s.lat = $lat,
        s.create_time = datetime()
    """
    for s in spots:
        neo4j_manager.execute_query_sync(cql, s)
    logger.info(f"已创建 {len(spots)} 个受灾/高风险点位")


def create_warehouses():
    """创建省级/州市级应急物资仓库"""
    warehouses = [
        {"id": "wh-001", "name": "云南省应急物资储备中心（昆明）", "address": "昆明市呈贡区",
         "lng": 102.83, "lat": 24.91, "manager": "张主任", "contact": "13800000001"},
        {"id": "wh-002", "name": "昭通市应急物资储备库", "address": "昭通市昭阳区",
         "lng": 103.72, "lat": 27.34, "manager": "李主任", "contact": "13800000002"},
        {"id": "wh-003", "name": "大理州应急物资储备库", "address": "大理市下关镇",
         "lng": 100.23, "lat": 25.61, "manager": "王主任", "contact": "13800000003"},
        {"id": "wh-004", "name": "普洱市应急物资储备库", "address": "普洱市思茅区",
         "lng": 100.97, "lat": 22.78, "manager": "赵主任", "contact": "13800000004"},
        {"id": "wh-005", "name": "楚雄州应急物资储备库", "address": "楚雄市鹿城镇",
         "lng": 101.54, "lat": 25.04, "manager": "刘主任", "contact": "13800000005"},
        {"id": "wh-006", "name": "丽江市应急物资储备库", "address": "丽江市古城区",
         "lng": 100.23, "lat": 26.87, "manager": "陈主任", "contact": "13800000006"},
        {"id": "wh-007", "name": "红河州应急物资储备库", "address": "蒙自市文澜镇",
         "lng": 103.40, "lat": 23.37, "manager": "杨主任", "contact": "13800000007"},
        {"id": "wh-008", "name": "怒江州应急物资储备库", "address": "泸水市六库镇",
         "lng": 98.86, "lat": 25.86, "manager": "周主任", "contact": "13800000008"},
    ]
    cql = """
    MERGE (w:Warehouse {id: $id})
    SET w.name = $name, w.address = $address, w.lng = $lng, w.lat = $lat,
        w.manager = $manager, w.contact = $contact
    """
    for w in warehouses:
        neo4j_manager.execute_query_sync(cql, w)
    logger.info(f"已创建 {len(warehouses)} 个物资仓库")


def create_materials():
    """创建物资品类"""
    materials = [
        {"id": "mat-001", "name": "救生衣", "type": "防汛物资", "unit": "件", "weight": 0.5,
         "suitable_disaster": ["暴雨", "洪涝", "山洪"]},
        {"id": "mat-002", "name": "编织袋/沙袋", "type": "防汛物资", "unit": "条", "weight": 0.3,
         "suitable_disaster": ["暴雨", "洪涝", "山洪"]},
        {"id": "mat-003", "name": "移动抽水机", "type": "防汛物资", "unit": "台", "weight": 50.0,
         "suitable_disaster": ["暴雨", "洪涝"]},
        {"id": "mat-004", "name": "应急帐篷", "type": "地震救援物资", "unit": "顶", "weight": 25.0,
         "suitable_disaster": ["地震", "滑坡", "泥石流", "崩塌"]},
        {"id": "mat-005", "name": "急救医疗包", "type": "地震救援物资", "unit": "套", "weight": 2.0,
         "suitable_disaster": ["地震", "滑坡", "泥石流", "洪涝", "崩塌"]},
        {"id": "mat-006", "name": "折叠行军床", "type": "地震救援物资", "unit": "张", "weight": 8.0,
         "suitable_disaster": ["地震", "滑坡", "泥石流"]},
        {"id": "mat-007", "name": "安全帽", "type": "地质灾害物资", "unit": "顶", "weight": 0.4,
         "suitable_disaster": ["滑坡", "泥石流", "崩塌", "地震"]},
        {"id": "mat-008", "name": "逃生绳", "type": "地质灾害物资", "unit": "米", "weight": 0.2,
         "suitable_disaster": ["滑坡", "崩塌", "地震"]},
        {"id": "mat-009", "name": "手持式生命探测仪", "type": "地震救援物资", "unit": "台", "weight": 3.0,
         "suitable_disaster": ["地震", "滑坡", "泥石流"]},
        {"id": "mat-010", "name": "应急食品（饼干）", "type": "防汛物资", "unit": "箱", "weight": 10.0,
         "suitable_disaster": ["暴雨", "洪涝", "地震", "滑坡", "泥石流", "干旱"]},
        {"id": "mat-011", "name": "瓶装饮用水", "type": "防汛物资", "unit": "箱", "weight": 15.0,
         "suitable_disaster": ["洪涝", "地震", "干旱", "滑坡", "泥石流"]},
        {"id": "mat-012", "name": "照明应急灯", "type": "防汛物资", "unit": "台", "weight": 1.5,
         "suitable_disaster": ["暴雨", "洪涝", "地震", "滑坡", "泥石流", "森林火灾"]},
        {"id": "mat-013", "name": "便携式发电机", "type": "防汛物资", "unit": "台", "weight": 30.0,
         "suitable_disaster": ["暴雨", "洪涝", "地震", "森林火灾"]},
        {"id": "mat-014", "name": "卫星电话", "type": "地质灾害物资", "unit": "部", "weight": 0.5,
         "suitable_disaster": ["地震", "滑坡", "泥石流", "崩塌"]},
        {"id": "mat-015", "name": "防护服套装", "type": "地质灾害物资", "unit": "套", "weight": 1.0,
         "suitable_disaster": ["滑坡", "泥石流", "崩塌", "地震"]},
    ]
    cql = """
    MERGE (m:Material {id: $id})
    SET m.name = $name, m.type = $type, m.unit = $unit, m.weight = $weight,
        m.suitable_disaster = $suitable_disaster
    """
    for m in materials:
        neo4j_manager.execute_query_sync(cql, m)
    logger.info(f"已创建 {len(materials)} 种物资品类")


def create_stock():
    """建立仓库-库存-物资关系（每个仓库配备主要物资）"""
    stock_data = [
        ("wh-001", "mat-001", 5000, 2000),
        ("wh-001", "mat-002", 20000, 10000),
        ("wh-001", "mat-003", 50, 20),
        ("wh-001", "mat-004", 1000, 500),
        ("wh-001", "mat-005", 2000, 1000),
        ("wh-001", "mat-009", 30, 10),
        ("wh-001", "mat-010", 3000, 1500),
        ("wh-001", "mat-013", 80, 30),
        ("wh-002", "mat-001", 3000, 1000),
        ("wh-002", "mat-002", 15000, 8000),
        ("wh-002", "mat-003", 30, 10),
        ("wh-002", "mat-004", 600, 300),
        ("wh-002", "mat-007", 2000, 1000),
        ("wh-002", "mat-008", 5000, 2000),
        ("wh-002", "mat-011", 2000, 1000),
        ("wh-003", "mat-004", 800, 400),
        ("wh-003", "mat-005", 1500, 800),
        ("wh-003", "mat-006", 500, 200),
        ("wh-003", "mat-009", 20, 8),
        ("wh-003", "mat-014", 15, 5),
        ("wh-003", "mat-015", 500, 200),
        ("wh-004", "mat-001", 2000, 800),
        ("wh-004", "mat-002", 10000, 5000),
        ("wh-004", "mat-004", 500, 200),
        ("wh-004", "mat-010", 2000, 1000),
        ("wh-005", "mat-001", 2500, 1000),
        ("wh-005", "mat-002", 12000, 6000),
        ("wh-005", "mat-007", 1500, 800),
        ("wh-005", "mat-008", 3000, 1500),
        ("wh-006", "mat-004", 700, 350),
        ("wh-006", "mat-005", 1200, 600),
        ("wh-006", "mat-009", 15, 6),
        ("wh-006", "mat-012", 500, 200),
        ("wh-007", "mat-001", 2000, 800),
        ("wh-007", "mat-002", 8000, 4000),
        ("wh-007", "mat-007", 1000, 500),
        ("wh-007", "mat-010", 1500, 700),
        ("wh-008", "mat-002", 5000, 2000),
        ("wh-008", "mat-007", 800, 400),
        ("wh-008", "mat-008", 2000, 1000),
        ("wh-008", "mat-014", 10, 3),
        ("wh-008", "mat-015", 300, 100),
    ]
    cql = """
    MATCH (w:Warehouse {id: $wh_id})
    MATCH (m:Material {id: $mat_id})
    MERGE (w)-[:HAS_STOCK]->(ws:WarehouseStock)-[:STOCK_MATERIAL]->(m)
    SET ws.stock_num = $stock_num, ws.safe_stock = $safe_stock
    """
    for wh_id, mat_id, stock_num, safe_stock in stock_data:
        neo4j_manager.execute_query_sync(cql, {
            "wh_id": wh_id, "mat_id": mat_id,
            "stock_num": stock_num, "safe_stock": safe_stock,
        })
    logger.info(f"已建立 {len(stock_data)} 条库存关系")


def create_rescue_teams():
    """创建救援队伍"""
    teams = [
        {"id": "team-001", "team_name": "云南省消防救援总队直属支队",
         "current_lng": 102.71, "current_lat": 25.04, "carry_limit": 50.0,
         "suitable_disaster": ["地震", "洪涝", "滑坡", "泥石流", "森林火灾"], "status": "空闲"},
        {"id": "team-002", "team_name": "昭通市应急救援支队",
         "current_lng": 103.72, "current_lat": 27.34, "carry_limit": 20.0,
         "suitable_disaster": ["滑坡", "泥石流", "洪涝"], "status": "空闲"},
        {"id": "team-003", "team_name": "大理州地震应急救援大队",
         "current_lng": 100.23, "current_lat": 25.61, "carry_limit": 15.0,
         "suitable_disaster": ["地震", "滑坡"], "status": "空闲"},
        {"id": "team-004", "team_name": "云南省地质灾害应急救援队",
         "current_lng": 102.71, "current_lat": 25.04, "carry_limit": 25.0,
         "suitable_disaster": ["滑坡", "泥石流", "崩塌"], "status": "空闲"},
        {"id": "team-005", "team_name": "怒江军分区应急民兵连",
         "current_lng": 98.86, "current_lat": 25.86, "carry_limit": 10.0,
         "suitable_disaster": ["泥石流", "滑坡", "洪涝", "地震"], "status": "空闲"},
        {"id": "team-006", "team_name": "武警云南总队机动一支队",
         "current_lng": 102.83, "current_lat": 24.91, "carry_limit": 30.0,
         "suitable_disaster": ["地震", "洪涝", "滑坡", "泥石流", "森林火灾"], "status": "空闲"},
    ]
    cql = """
    MERGE (t:RescueTeam {id: $id})
    SET t.team_name = $team_name, t.current_lng = $current_lng, t.current_lat = $current_lat,
        t.carry_limit = $carry_limit, t.suitable_disaster = $suitable_disaster, t.status = $status
    """
    for t in teams:
        neo4j_manager.execute_query_sync(cql, t)
    logger.info(f"已创建 {len(teams)} 支救援队伍")


def create_shelters():
    """创建避难场所"""
    shelters = [
        {"id": "sh-001", "name": "昭通市体育中心避难所", "max_capacity": 5000, "remain_space": 5000,
         "lng": 103.72, "lat": 27.31},
        {"id": "sh-002", "name": "昆明东川体育场避难所", "max_capacity": 3000, "remain_space": 3000,
         "lng": 103.18, "lat": 26.09},
        {"id": "sh-003", "name": "大理州下关一中避难所", "max_capacity": 4000, "remain_space": 4000,
         "lng": 100.22, "lat": 25.61},
        {"id": "sh-004", "name": "怒江州六库镇中心小学避难所", "max_capacity": 2000, "remain_space": 2000,
         "lng": 98.85, "lat": 25.85},
        {"id": "sh-005", "name": "普洱市思茅区一中避难所", "max_capacity": 3500, "remain_space": 3500,
         "lng": 100.97, "lat": 22.78},
        {"id": "sh-006", "name": "楚雄市鹿城小学避难所", "max_capacity": 2500, "remain_space": 2500,
         "lng": 101.54, "lat": 25.04},
        {"id": "sh-007", "name": "丽江市区一中避难所", "max_capacity": 3000, "remain_space": 3000,
         "lng": 100.23, "lat": 26.87},
        {"id": "sh-008", "name": "蒙自市第一小学避难所", "max_capacity": 2800, "remain_space": 2800,
         "lng": 103.40, "lat": 23.37},
    ]
    cql = """
    MERGE (sh:Shelter {id: $id})
    SET sh.name = $name, sh.max_capacity = $max_capacity, sh.remain_space = $remain_space,
        sh.lng = $lng, sh.lat = $lat
    """
    for s in shelters:
        neo4j_manager.execute_query_sync(cql, s)
    logger.info(f"已创建 {len(shelters)} 个避难场所")


def create_road_connections():
    """
    建立路网（简化版：仓库-灾区、灾区-仓库、仓库-仓库、队伍-灾区、避难所-灾区）
    用近似直线距离模拟公路里程（系数 1.2）
    """
    import math

    def haversine_km(lng1, lat1, lng2, lat2):
        R = 6371.0
        dlon = math.radians(lng2 - lng1)
        dlat = math.radians(lat2 - lat1)
        a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
        return R * 2 * math.asin(math.sqrt(a)) * 1.2

    spots = neo4j_manager.execute_query_sync("MATCH (s:DisasterSpot) RETURN s.id AS id, s.lng AS lng, s.lat AS lat, s.name AS name")
    warehouses = neo4j_manager.execute_query_sync("MATCH (w:Warehouse) RETURN w.id AS id, w.lng AS lng, w.lat AS lat, w.name AS name")
    teams = neo4j_manager.execute_query_sync("MATCH (t:RescueTeam) RETURN t.id AS id, t.current_lng AS lng, t.current_lat AS lat")
    shelters = neo4j_manager.execute_query_sync("MATCH (sh:Shelter) RETURN sh.id AS id, sh.lng AS lng, sh.lat AS lat")

    count = 0

    # 仓库 - 仓库（相邻/同区域的连通）
    for i, w1 in enumerate(warehouses):
        for j, w2 in enumerate(warehouses):
            if i >= j:
                continue
            dist = haversine_km(w1["lng"], w1["lat"], w2["lng"], w2["lat"])
            if dist < 400:
                cql = """
                MATCH (a:Warehouse {id: $a_id})
                MATCH (b:Warehouse {id: $b_id})
                MERGE (a)-[r:ROAD_CONNECT]-(b)
                SET r.distance = $dist, r.blocked = false, r.speed = 60.0
                """
                neo4j_manager.execute_query_sync(cql, {"a_id": w1["id"], "b_id": w2["id"], "dist": round(dist, 2)})
                count += 1

    # 仓库 - 受灾点（全部连通，用于 shortestPath 计算）
    for wh in warehouses:
        for spot in spots:
            dist = haversine_km(wh["lng"], wh["lat"], spot["lng"], spot["lat"])
            if dist < 500:
                cql = """
                MATCH (w:Warehouse {id: $wh_id})
                MATCH (s:DisasterSpot {id: $spot_id})
                MERGE (w)-[r:ROAD_CONNECT]-(s)
                SET r.distance = $dist, r.blocked = false, r.speed = 50.0
                """
                neo4j_manager.execute_query_sync(cql, {"wh_id": wh["id"], "spot_id": spot["id"], "dist": round(dist, 2)})
                count += 1

    # 救援队 - 受灾点
    for team in teams:
        for spot in spots:
            dist = haversine_km(team["lng"], team["lat"], spot["lng"], spot["lat"])
            if dist < 600:
                cql = """
                MATCH (t:RescueTeam {id: $team_id})
                MATCH (s:DisasterSpot {id: $spot_id})
                MERGE (t)-[r:ROAD_CONNECT]-(s)
                SET r.distance = $dist, r.blocked = false, r.speed = 55.0
                """
                neo4j_manager.execute_query_sync(cql, {"team_id": team["id"], "spot_id": spot["id"], "dist": round(dist, 2)})
                count += 1

    # 受灾点 - 避难所
    for spot in spots:
        for sh in shelters:
            dist = haversine_km(spot["lng"], spot["lat"], sh["lng"], sh["lat"])
            if dist < 300:
                cql = """
                MATCH (s:DisasterSpot {id: $spot_id})
                MATCH (sh:Shelter {id: $sh_id})
                MERGE (s)-[r:ROAD_CONNECT]-(sh)
                SET r.distance = $dist, r.blocked = false, r.speed = 45.0
                """
                neo4j_manager.execute_query_sync(cql, {"spot_id": spot["id"], "sh_id": sh["id"], "dist": round(dist, 2)})
                count += 1
                # 同时建立 NEED_EVACUATE 关系
                ev_cql = """
                MATCH (s:DisasterSpot {id: $spot_id})
                MATCH (sh:Shelter {id: $sh_id})
                MERGE (s)-[:NEED_EVACUATE]->(sh)
                """
                neo4j_manager.execute_query_sync(ev_cql, {"spot_id": spot["id"], "sh_id": sh["id"]})

    logger.info(f"已建立 {count} 条道路连通关系")


def create_needs():
    """建立高风险区域的物资需求关系（模拟预测性需求）"""
    needs_data = [
        ("spot-001", "mat-001", 2000, 4),
        ("spot-001", "mat-002", 10000, 5),
        ("spot-001", "mat-007", 1000, 3),
        ("spot-001", "mat-010", 1000, 3),
        ("spot-002", "mat-002", 8000, 5),
        ("spot-002", "mat-007", 1500, 4),
        ("spot-002", "mat-008", 3000, 4),
        ("spot-002", "mat-004", 500, 3),
        ("spot-003", "mat-004", 800, 4),
        ("spot-003", "mat-005", 1000, 5),
        ("spot-003", "mat-009", 10, 5),
        ("spot-003", "mat-014", 5, 4),
        ("spot-004", "mat-002", 5000, 5),
        ("spot-004", "mat-007", 800, 4),
        ("spot-004", "mat-008", 2000, 5),
        ("spot-004", "mat-015", 300, 4),
        ("spot-005", "mat-001", 1500, 3),
        ("spot-005", "mat-004", 400, 3),
        ("spot-005", "mat-010", 800, 2),
        ("spot-006", "mat-002", 5000, 2),
        ("spot-006", "mat-011", 1000, 2),
        ("spot-007", "mat-004", 600, 4),
        ("spot-007", "mat-005", 800, 4),
        ("spot-007", "mat-012", 300, 3),
        ("spot-008", "mat-002", 6000, 4),
        ("spot-008", "mat-007", 1000, 3),
        ("spot-008", "mat-008", 1500, 4),
        ("spot-009", "mat-001", 1500, 3),
        ("spot-009", "mat-002", 8000, 3),
        ("spot-010", "mat-001", 2000, 3),
        ("spot-010", "mat-004", 500, 4),
        ("spot-010", "mat-009", 8, 4),
    ]
    cql = """
    MATCH (s:DisasterSpot {id: $spot_id})
    MATCH (m:Material {id: $mat_id})
    MERGE (s)-[n:NEED]->(m)
    SET n.need_num = $need_num, n.urgent = $urgent
    """
    for spot_id, mat_id, need_num, urgent in needs_data:
        neo4j_manager.execute_query_sync(cql, {
            "spot_id": spot_id, "mat_id": mat_id,
            "need_num": need_num, "urgent": urgent,
        })
    logger.info(f"已建立 {len(needs_data)} 条物资需求关系")


def main():
    parser = argparse.ArgumentParser(description="Neo4j 初始化脚本")
    parser.add_argument("--no-clear", action="store_true", help="不清空数据库，直接追加数据")
    args = parser.parse_args()

    logger.info(f"连接 Neo4j: {settings.NEO4J_URI}")
    neo4j_manager.init()

    if not args.no_clear:
        clear_database()

    create_constraints()
    create_disaster_spots()
    create_warehouses()
    create_materials()
    create_stock()
    create_rescue_teams()
    create_shelters()
    create_road_connections()
    create_needs()

    logger.info("=" * 60)
    logger.info("Neo4j 图数据库初始化完成！")
    logger.info("数据概览：")
    stats = neo4j_manager.execute_query_sync("""
        MATCH (n)
        RETURN labels(n)[0] AS label, count(*) AS cnt
        ORDER BY cnt DESC
    """)
    for s in stats:
        logger.info(f"  {s['label']}: {s['cnt']} 个节点")

    rel_stats = neo4j_manager.execute_query_sync("""
        MATCH ()-[r]->()
        RETURN type(r) AS type, count(*) AS cnt
        ORDER BY cnt DESC
    """)
    logger.info("  --- 关系 ---")
    for s in rel_stats:
        logger.info(f"  {s['type']}: {s['cnt']} 条")
    logger.info("=" * 60)

    neo4j_manager.close()


if __name__ == "__main__":
    main()
