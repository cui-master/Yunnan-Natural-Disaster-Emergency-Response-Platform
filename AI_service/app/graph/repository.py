from app.core.neo4j_client import neo4j_manager
from app.core.logging import logger
from app.schemas import (
    DisasterSpotCreate, WarehouseCreate, MaterialCreate,
    RescueTeamCreate, ShelterCreate,
)


class GraphRepository:
    # ==================== 节点 CRUD ====================

    @staticmethod
    async def create_disaster_spot(spot: DisasterSpotCreate) -> dict:
        query = """
        CREATE (s:DisasterSpot {
            id: $id,
            name: $name,
            disaster_type: $disaster_type,
            risk_level: $risk_level,
            urgent_level: $urgent_level,
            lng: $lng,
            lat: $lat,
            create_time: datetime()
        })
        RETURN s
        """
        result = await neo4j_manager.execute_query(query, spot.model_dump())
        return result[0]["s"] if result else {}

    @staticmethod
    async def update_risk_level(spot_id: str, risk_level: str, urgent_level: int | None = None,
                                disaster_type: list[str] | None = None) -> dict | None:
        params = {"spot_id": spot_id, "risk_level": risk_level}
        set_clauses = ["s.risk_level = $risk_level"]
        if urgent_level is not None:
            set_clauses.append("s.urgent_level = $urgent_level")
            params["urgent_level"] = urgent_level
        if disaster_type is not None:
            set_clauses.append("s.disaster_type = $disaster_type")
            params["disaster_type"] = disaster_type

        query = f"""
        MATCH (s:DisasterSpot {{id: $spot_id}})
        SET {', '.join(set_clauses)}
        RETURN s
        """
        result = await neo4j_manager.execute_query(query, params)
        return result[0]["s"] if result else None

    @staticmethod
    async def create_warehouse(warehouse: WarehouseCreate) -> dict:
        query = """
        CREATE (w:Warehouse {
            id: $id,
            name: $name,
            address: $address,
            lng: $lng,
            lat: $lat,
            manager: $manager,
            contact: $contact
        })
        RETURN w
        """
        result = await neo4j_manager.execute_query(query, warehouse.model_dump())
        return result[0]["w"] if result else {}

    @staticmethod
    async def create_material(material: MaterialCreate) -> dict:
        query = """
        CREATE (m:Material {
            id: $id,
            name: $name,
            type: $type,
            unit: $unit,
            weight: $weight,
            suitable_disaster: $suitable_disaster
        })
        RETURN m
        """
        result = await neo4j_manager.execute_query(query, material.model_dump())
        return result[0]["m"] if result else {}

    @staticmethod
    async def create_rescue_team(team: RescueTeamCreate) -> dict:
        query = """
        CREATE (t:RescueTeam {
            id: $id,
            team_name: $team_name,
            current_lng: $current_lng,
            current_lat: $current_lat,
            carry_limit: $carry_limit,
            suitable_disaster: $suitable_disaster,
            status: $status
        })
        RETURN t
        """
        result = await neo4j_manager.execute_query(query, team.model_dump())
        return result[0]["t"] if result else {}

    @staticmethod
    async def create_shelter(shelter: ShelterCreate) -> dict:
        query = """
        CREATE (sh:Shelter {
            id: $id,
            name: $name,
            max_capacity: $max_capacity,
            remain_space: $remain_space,
            lng: $lng,
            lat: $lat
        })
        RETURN sh
        """
        result = await neo4j_manager.execute_query(query, shelter.model_dump())
        return result[0]["sh"] if result else {}

    # ==================== 关系建立 ====================

    @staticmethod
    async def add_stock(warehouse_id: str, material_id: str, stock_num: int, safe_stock: int = 0) -> bool:
        query = """
        MATCH (w:Warehouse {id: $warehouse_id})
        MATCH (m:Material {id: $material_id})
        MERGE (w)-[:HAS_STOCK]->(ws:WarehouseStock)-[:STOCK_MATERIAL]->(m)
        SET ws.stock_num = $stock_num, ws.safe_stock = $safe_stock
        RETURN ws
        """
        params = {
            "warehouse_id": warehouse_id,
            "material_id": material_id,
            "stock_num": stock_num,
            "safe_stock": safe_stock,
        }
        result = await neo4j_manager.execute_query(query, params)
        return len(result) > 0

    @staticmethod
    async def add_road_connect(from_id: str, to_id: str, from_label: str, to_label: str,
                               distance: float, blocked: bool = False, speed: float = 40.0) -> bool:
        query = f"""
        MATCH (a:{from_label} {{id: $from_id}})
        MATCH (b:{to_label} {{id: $to_id}})
        MERGE (a)-[r:ROAD_CONNECT {{distance: $distance, blocked: $blocked, speed: $speed}}]-(b)
        RETURN r
        """
        params = {
            "from_id": from_id,
            "to_id": to_id,
            "distance": distance,
            "blocked": blocked,
            "speed": speed,
        }
        result = await neo4j_manager.execute_query(query, params)
        return len(result) > 0

    @staticmethod
    async def add_need(spot_id: str, material_id: str, need_num: int, urgent: int = 3) -> bool:
        query = """
        MATCH (s:DisasterSpot {id: $spot_id})
        MATCH (m:Material {id: $material_id})
        MERGE (s)-[n:NEED]->(m)
        SET n.need_num = $need_num, n.urgent = $urgent
        RETURN n
        """
        params = {"spot_id": spot_id, "material_id": material_id, "need_num": need_num, "urgent": urgent}
        result = await neo4j_manager.execute_query(query, params)
        return len(result) > 0

    @staticmethod
    async def allocate_team(team_id: str, spot_id: str) -> bool:
        query = """
        MATCH (t:RescueTeam {id: $team_id})
        MATCH (s:DisasterSpot {id: $spot_id})
        SET t.status = '已调度'
        MERGE (t)-[:ALLOCATED]->(s)
        RETURN t
        """
        params = {"team_id": team_id, "spot_id": spot_id}
        result = await neo4j_manager.execute_query(query, params)
        return len(result) > 0

    @staticmethod
    async def add_need_evacuate(spot_id: str, shelter_id: str) -> bool:
        query = """
        MATCH (s:DisasterSpot {id: $spot_id})
        MATCH (sh:Shelter {id: $shelter_id})
        MERGE (s)-[:NEED_EVACUATE]->(sh)
        RETURN s, sh
        """
        params = {"spot_id": spot_id, "shelter_id": shelter_id}
        result = await neo4j_manager.execute_query(query, params)
        return len(result) > 0

    # ==================== 调度核心查询 ====================

    @staticmethod
    async def get_optimal_warehouses(risk_level: str = "极高") -> list[dict]:
        """接口1：获取高风险区域最优物资仓库（预防前置调度）"""
        query = """
        MATCH (area:DisasterSpot {risk_level: $risk_level})-[:NEED]->(m:Material)
        MATCH (wh:Warehouse)-[:HAS_STOCK]->(ws:WarehouseStock)-[:STOCK_MATERIAL]->(m)
        WHERE ws.stock_num > 0
        MATCH p = shortestPath((wh)-[:ROAD_CONNECT*1..8 {blocked:false}]-(area))
        WITH wh, ws, m, area, reduce(total=0, r IN relationships(p) | total + r.distance) AS total_dist
        WITH wh, ws, m, area, total_dist,
             (1.0 / total_dist) * 0.5 + area.urgent_level * 0.3 AS score
        ORDER BY score DESC
        RETURN wh.name AS warehouse_name, m.name AS material_name,
               ws.stock_num AS stock_num, total_dist AS total_dist, score AS score,
               area.name AS area_name
        """
        return await neo4j_manager.execute_query(query, {"risk_level": risk_level})

    @staticmethod
    async def get_optimal_warehouses_by_area(area_name: str, disaster_type: str | None = None) -> list[dict]:
        """按区域名称获取最优物资仓库"""
        params: dict = {"area_name": area_name}
        type_filter = ""
        if disaster_type:
            type_filter = "AND $disaster_type IN m.suitable_disaster"
            params["disaster_type"] = disaster_type

        query = f"""
        MATCH (area:DisasterSpot {{name: $area_name}})-[:NEED]->(m:Material)
        WHERE 1=1 {type_filter}
        MATCH (wh:Warehouse)-[:HAS_STOCK]->(ws:WarehouseStock)-[:STOCK_MATERIAL]->(m)
        WHERE ws.stock_num > 0
        MATCH p = shortestPath((wh)-[:ROAD_CONNECT*1..8 {{blocked:false}}]-(area))
        WITH wh, ws, m, area, reduce(total=0, r IN relationships(p) | total + r.distance) AS total_dist
        WITH wh, ws, m, area, total_dist,
             (1.0 / total_dist) * 0.5 + area.urgent_level * 0.3 AS score
        ORDER BY score DESC
        RETURN wh.name AS warehouse_name, m.name AS material_name,
               ws.stock_num AS stock_num, total_dist AS total_dist, score AS score
        """
        return await neo4j_manager.execute_query(query, params)

    @staticmethod
    async def get_available_teams(spot_id: str, disaster_type: str | None = None) -> list[dict]:
        """接口2：筛选未被占用、可调度救援队伍"""
        params: dict = {"spot_id": spot_id}
        type_filter = ""
        if disaster_type:
            type_filter = "AND $disaster_type IN t.suitable_disaster"
            params["disaster_type"] = disaster_type

        query = f"""
        MATCH (area:DisasterSpot {{id: $spot_id}})
        MATCH (t:RescueTeam {{status: "空闲"}})
        WHERE 1=1 {type_filter}
        AND NOT (t)-[:ALLOCATED]->(:DisasterSpot)
        MATCH p = shortestPath((t)-[:ROAD_CONNECT*1..8 {{blocked:false}}]-(area))
        WITH t, reduce(d=0, r IN relationships(p) | d + r.distance) AS dist
        ORDER BY dist ASC
        RETURN t.team_name AS team_name, dist AS dist, t.id AS team_id
        """
        return await neo4j_manager.execute_query(query, params)

    @staticmethod
    async def get_available_teams_by_area(area_name: str, disaster_type: str | None = None) -> list[dict]:
        """按区域名称获取可调度救援队伍"""
        params: dict = {"area_name": area_name}
        type_filter = ""
        if disaster_type:
            type_filter = "AND $disaster_type IN t.suitable_disaster"
            params["disaster_type"] = disaster_type

        query = f"""
        MATCH (area:DisasterSpot {{name: $area_name}})
        MATCH (t:RescueTeam {{status: "空闲"}})
        WHERE 1=1 {type_filter}
        AND NOT (t)-[:ALLOCATED]->(:DisasterSpot)
        MATCH p = shortestPath((t)-[:ROAD_CONNECT*1..8 {{blocked:false}}]-(area))
        WITH t, reduce(d=0, r IN relationships(p) | d + r.distance) AS dist
        ORDER BY dist ASC
        RETURN t.team_name AS team_name, dist AS dist, t.id AS team_id
        """
        return await neo4j_manager.execute_query(query, params)

    @staticmethod
    async def get_nearby_shelters(area_name: str) -> list[dict]:
        """获取受灾点附近避难场所"""
        query = """
        MATCH (area:DisasterSpot {name: $area_name})
        MATCH (sh:Shelter)
        WHERE sh.remain_space > 0
        MATCH p = shortestPath((area)-[:ROAD_CONNECT*1..8 {blocked:false}]-(sh))
        WITH sh, reduce(d=0, r IN relationships(p) | d + r.distance) AS dist
        ORDER BY dist ASC
        RETURN sh.name AS name, sh.max_capacity AS max_capacity,
               sh.remain_space AS remain_space, dist AS dist
        LIMIT 10
        """
        return await neo4j_manager.execute_query(query, {"area_name": area_name})

    @staticmethod
    async def get_dispatch_plan(area_name: str, disaster_type: str) -> dict:
        """综合调度方案：物资+队伍+避难所"""
        warehouses = await GraphRepository.get_optimal_warehouses_by_area(area_name, disaster_type)
        teams = await GraphRepository.get_available_teams_by_area(area_name, disaster_type)
        shelters = await GraphRepository.get_nearby_shelters(area_name)

        return {
            "area_name": area_name,
            "disaster_type": disaster_type,
            "recommendations": warehouses,
            "available_teams": teams,
            "shelters": shelters,
        }

    # ==================== 辅助查询 ====================

    @staticmethod
    async def list_high_risk_spots(risk_level: str | None = None) -> list[dict]:
        """列出高风险区域"""
        if risk_level:
            query = "MATCH (s:DisasterSpot {risk_level: $risk_level}) RETURN s ORDER BY s.urgent_level DESC"
            result = await neo4j_manager.execute_query(query, {"risk_level": risk_level})
        else:
            query = "MATCH (s:DisasterSpot) RETURN s ORDER BY s.urgent_level DESC"
            result = await neo4j_manager.execute_query(query)
        return [r["s"] for r in result]

    @staticmethod
    async def clear_all() -> None:
        """清空数据库（慎用，初始化时使用）"""
        query = "MATCH (n) DETACH DELETE n"
        await neo4j_manager.execute_query(query)
        logger.warning("Neo4j 数据库已清空")


graph_repo = GraphRepository()
