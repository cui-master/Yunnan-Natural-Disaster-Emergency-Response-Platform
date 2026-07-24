from app.core.neo4j_client import neo4j_manager
from app.core.logging import logger
from app.schemas import (
    DisasterSpotCreate, WarehouseCreate, MaterialCreate,
    RescueTeamCreate, ShelterCreate,
)


class GraphRepository:
    # ==================== 节点 Create ====================

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
            reporter: $reporter,
            report_time: $report_time,
            casualties: $casualties,
            affected_people: $affected_people,
            description: $description,
            severity: $severity,
            create_time: datetime()
        })
        RETURN s
        """
        result = await neo4j_manager.execute_query(query, spot.model_dump())
        return result[0]["s"] if result else {}

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
            accommodated_count: $accommodated_count,
            lng: $lng,
            lat: $lat
        })
        RETURN sh
        """
        result = await neo4j_manager.execute_query(query, shelter.model_dump())
        return result[0]["sh"] if result else {}

    # ==================== 节点 Update ====================

    @staticmethod
    async def _update_node(label: str, node_id: str, data: dict) -> dict | None:
        """通用节点更新（只更新非 None 字段）"""
        updates = {k: v for k, v in data.items() if v is not None}
        if not updates:
            return None
        set_clauses = ", ".join(f"n.{k} = ${k}" for k in updates.keys())
        params = {"id": node_id, **updates}
        query = f"""
        MATCH (n:{label} {{id: $id}})
        SET {set_clauses}
        RETURN n
        """
        result = await neo4j_manager.execute_query(query, params)
        return result[0]["n"] if result else None

    @staticmethod
    async def update_disaster_spot(spot_id: str, data: dict) -> dict | None:
        return await GraphRepository._update_node("DisasterSpot", spot_id, data)

    @staticmethod
    async def update_warehouse(warehouse_id: str, data: dict) -> dict | None:
        return await GraphRepository._update_node("Warehouse", warehouse_id, data)

    @staticmethod
    async def update_material(material_id: str, data: dict) -> dict | None:
        return await GraphRepository._update_node("Material", material_id, data)

    @staticmethod
    async def update_rescue_team(team_id: str, data: dict) -> dict | None:
        return await GraphRepository._update_node("RescueTeam", team_id, data)

    @staticmethod
    async def update_shelter(shelter_id: str, data: dict) -> dict | None:
        return await GraphRepository._update_node("Shelter", shelter_id, data)

    # ==================== 节点 Delete ====================

    @staticmethod
    async def _delete_node(label: str, node_id: str) -> bool:
        query = f"""
        MATCH (n:{label} {{id: $id}})
        DETACH DELETE n
        RETURN count(n) AS deleted
        """
        result = await neo4j_manager.execute_query(query, {"id": node_id})
        return result[0]["deleted"] > 0 if result else False

    @staticmethod
    async def delete_disaster_spot(spot_id: str) -> bool:
        return await GraphRepository._delete_node("DisasterSpot", spot_id)

    @staticmethod
    async def delete_warehouse(warehouse_id: str) -> bool:
        return await GraphRepository._delete_node("Warehouse", warehouse_id)

    @staticmethod
    async def delete_material(material_id: str) -> bool:
        return await GraphRepository._delete_node("Material", material_id)

    @staticmethod
    async def delete_rescue_team(team_id: str) -> bool:
        return await GraphRepository._delete_node("RescueTeam", team_id)

    @staticmethod
    async def delete_shelter(shelter_id: str) -> bool:
        return await GraphRepository._delete_node("Shelter", shelter_id)

    # ==================== 节点 List ====================

    @staticmethod
    async def _list_nodes(label: str, limit: int = 100) -> list[dict]:
        query = f"MATCH (n:{label}) RETURN n LIMIT $limit"
        result = await neo4j_manager.execute_query(query, {"limit": limit})
        return [r["n"] for r in result]

    @staticmethod
    async def list_disaster_spots(limit: int = 100) -> list[dict]:
        return await GraphRepository._list_nodes("DisasterSpot", limit)

    @staticmethod
    async def list_warehouses(limit: int = 100) -> list[dict]:
        return await GraphRepository._list_nodes("Warehouse", limit)

    @staticmethod
    async def list_materials(limit: int = 100) -> list[dict]:
        return await GraphRepository._list_nodes("Material", limit)

    @staticmethod
    async def list_rescue_teams(limit: int = 100) -> list[dict]:
        return await GraphRepository._list_nodes("RescueTeam", limit)

    @staticmethod
    async def list_shelters(limit: int = 100) -> list[dict]:
        return await GraphRepository._list_nodes("Shelter", limit)

    @staticmethod
    async def get_node(label: str, node_id: str) -> dict | None:
        """按 ID 获取单个节点"""
        query = f"MATCH (n:{label} {{id: $id}}) RETURN n"
        result = await neo4j_manager.execute_query(query, {"id": node_id})
        return result[0]["n"] if result else None

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
    async def get_optimal_warehouses(risk_level: str = "极高") -> list[dict]:
        """接口1：获取高风险区域最优物资仓库（预防前置调度）"""
        query = """
        MATCH (area:DisasterSpot {risk_level: $risk_level})-[:NEED]->(m:Material)
        MATCH (wh:Warehouse)-[:HAS_STOCK]->(ws:WarehouseStock)-[:STOCK_MATERIAL]->(m)
        WHERE ws.stock_num > 0
        MATCH p = shortestPath((wh)-[:ROAD_CONNECT*1..8]-(area))
        WHERE ALL(r IN relationships(p) WHERE NOT r.blocked)
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
        MATCH p = shortestPath((wh)-[:ROAD_CONNECT*1..8]-(area))
        WHERE ALL(r IN relationships(p) WHERE NOT r.blocked)
        WITH wh, ws, m, area, reduce(total=0, r IN relationships(p) | total + r.distance) AS total_dist
        WITH wh, ws, m, area, total_dist,
             (1.0 / total_dist) * 0.5 + area.urgent_level * 0.3 AS score
        ORDER BY score DESC
        RETURN wh.name AS warehouse_name, m.name AS material_name,
               ws.stock_num AS stock_num, total_dist AS total_dist, score AS score
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
        MATCH p = shortestPath((t)-[:ROAD_CONNECT*1..8]-(area))
        WHERE ALL(r IN relationships(p) WHERE NOT r.blocked)
        WITH t, reduce(d=0, r IN relationships(p) | d + r.distance) AS dist
        ORDER BY dist ASC
        RETURN t.team_name AS team_name, dist AS dist, t.id AS team_id
        """
        return await neo4j_manager.execute_query(query, params)

    @staticmethod
    async def get_nearby_shelters(area_name: str) -> list[dict]:
        """获取受灾点附近、还能容纳的避难场所

        Shelter 已改为 accommodated_count（已容纳人数），
        过滤条件：accommodated_count < max_capacity
        返回 available_space = max_capacity - accommodated_count
        """
        query = """
        MATCH (area:DisasterSpot {name: $area_name})
        MATCH (sh:Shelter)
        WHERE sh.accommodated_count < sh.max_capacity
        MATCH p = shortestPath((area)-[:ROAD_CONNECT*1..8]-(sh))
        WHERE ALL(r IN relationships(p) WHERE NOT r.blocked)
        WITH sh, reduce(d=0, r IN relationships(p) | d + r.distance) AS dist
        ORDER BY dist ASC
        RETURN sh.name AS name, sh.max_capacity AS max_capacity,
               sh.accommodated_count AS accommodated_count,
               sh.max_capacity - sh.accommodated_count AS available_space,
               dist AS dist
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

    @staticmethod
    async def get_disaster_graph(spot_id: str) -> dict:
        """查询灾害点关联的三元组（避难所/仓库/队伍/道路/物资需求）"""
        query = """
        MATCH (s:DisasterSpot {id: $spot_id})
        OPTIONAL MATCH (s)-[r]-(n)
        RETURN s, collect({
            node: n,
            labels: labels(n),
            relationship: type(r),
            properties: properties(r)
        }) AS relations
        """
        result = await neo4j_manager.execute_query(query, {"spot_id": spot_id})
        if not result:
            return {}
        row = result[0]
        return {
            "spot": row["s"],
            "relations": row["relations"],
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

    # ==================== Dify 调度方案：完整三元组查询 ====================

    @staticmethod
    async def get_dispatch_triples(disaster_name: str) -> dict:
        """查询调度方案的完整三元组数据（供 Dify 工作流使用）

        数据库结构（中文标签）：
        - 一级实体：受灾点/物资仓库/救援队伍/避难场所/道路
        - 2-4 级实体：属性节点（地点名称/灾害类型/危险等级/物资单品/数量 等）
        - 关系：
          - 实体 -[:临近]-> 道路，道路 -[:服务]-> 实体
          - 道路 -[:连通]-> 道路
          - 一级实体 -[:位于/是/拥有/包含/...]-> 属性节点

        本方法返回：
        1. 灾区(受灾点)及其 2-4 级子实体
        2. 周边救援队(救援队伍)及其 2-4 级子实体
        3. 周边仓库(物资仓库)及其 2-4 级子实体
        4. 周边避难所(避难场所)及其 2-4 级子实体
        5. 涉及的道路(道路)及其 2-4 级子实体（要求路连通且能到达灾区）
           - 救援队→灾区：起点救援队临近的路，通过连通到达服务灾区的路
           - 仓库→灾区：起点仓库临近的路，通过连通到达服务灾区的路
           - 灾区→避难所：起点灾区临近的路，通过连通到达服务避难所的路
        6. 所有三元组
        """
        # ============ Step 1: 找出所有相关的一级实体 ============
        # 灾区 + 通过路网可达的救援队/仓库 + 灾区可达的避难所
        find_entities_query = """
        MATCH (disaster:受灾点 {name: $disaster_name})

        // 灾区临近的道路
        OPTIONAL MATCH (disaster)-[:临近]->(dr:道路)

        // 救援队→灾区：救援队临近的路 通过 连通 到达 服务灾区的路
        OPTIONAL MATCH (team:救援队伍)-[:临近]->(tr:道路)
        WHERE EXISTS {
            MATCH (tr)-[:连通*0..6]->(mid1:道路)
            MATCH (mid1)-[:服务]->(disaster)
        }

        // 仓库→灾区：仓库临近的路 通过 连通 到达 服务灾区的路
        OPTIONAL MATCH (wh:物资仓库)-[:临近]->(wr:道路)
        WHERE EXISTS {
            MATCH (wr)-[:连通*0..6]->(mid2:道路)
            MATCH (mid2)-[:服务]->(disaster)
        }

        // 灾区→避难所：灾区临近的路 通过 连通 到达 服务避难所的路
        OPTIONAL MATCH (disaster)-[:临近]->(sr:道路)
        OPTIONAL MATCH (sr)-[:连通*0..6]->(mid3:道路)
        OPTIONAL MATCH (mid3)-[:服务]->(shelter:避难场所)

        WITH disaster,
             collect(DISTINCT team) AS teams,
             collect(DISTINCT wh) AS warehouses,
             collect(DISTINCT shelter) AS shelters,
             collect(DISTINCT dr) + collect(DISTINCT tr) + collect(DISTINCT wr) + collect(DISTINCT sr) + collect(DISTINCT mid1) + collect(DISTINCT mid2) + collect(DISTINCT mid3) AS all_roads_raw

        // 过滤掉 null
        WITH disaster, teams, warehouses, shelters,
             [r IN all_roads_raw WHERE r IS NOT NULL] AS all_roads
        RETURN disaster AS disaster,
               teams AS teams,
               warehouses AS warehouses,
               shelters AS shelters,
               all_roads AS roads
        """
        entities = await neo4j_manager.execute_query(
            find_entities_query, {"disaster_name": disaster_name}
        )

        if not entities:
            return {"success": False, "message": f"未找到灾区: {disaster_name}", "triples": []}

        row = entities[0]
        disaster_node = row["disaster"]
        teams = [t for t in row["teams"] if t is not None]
        warehouses = [w for w in row["warehouses"] if w is not None]
        shelters = [s for s in row["shelters"] if s is not None]
        roads = [r for r in row["roads"] if r is not None]

        # 收集所有一级实体名称
        disaster_names = [disaster_node.get("name")] if disaster_node else []
        team_names = [t.get("name") for t in teams if t.get("name")]
        wh_names = [w.get("name") for w in warehouses if w.get("name")]
        shelter_names = [s.get("name") for s in shelters if s.get("name")]
        road_names = [r.get("name") for r in roads if r.get("name")]

        # ============ Step 2: 查询每个一级实体的 2-4 级子实体三元组 ============
        # 统一查询所有一级实体的出边三元组
        sub_query = """
        UNWIND $entity_names AS ename
        MATCH (root {name: ename})
        WHERE root:受灾点 OR root:物资仓库 OR root:救援队伍 OR root:避难场所 OR root:道路
        OPTIONAL MATCH (root)-[rel]->(child)
        WHERE NOT child:受灾点 AND NOT child:物资仓库 AND NOT child:救援队伍
          AND NOT child:避难场所 AND NOT child:道路
        WITH root, rel, child
        WHERE rel IS NOT NULL AND child IS NOT NULL
        // 再展开一层（3级→4级）
        OPTIONAL MATCH (child)-[rel2]->(grandchild)
        WHERE grandchild IS NOT NULL
          AND NOT grandchild:受灾点 AND NOT grandchild:物资仓库
          AND NOT grandchild:救援队伍 AND NOT grandchild:避难场所 AND NOT grandchild:道路
        RETURN root.name AS subject,
               type(rel) AS predicate,
               child.name AS object,
               labels(child)[0] AS object_type,
               properties(child) AS object_props,
               collect({
                   predicate: type(rel2),
                   object: grandchild.name,
                   object_type: labels(grandchild)[0],
                   object_props: properties(grandchild)
               }) AS grandchildren
        """

        all_entity_names = disaster_names + team_names + wh_names + shelter_names + road_names
        sub_triples = []
        if all_entity_names:
            sub_result = await neo4j_manager.execute_query(
                sub_query, {"entity_names": all_entity_names}
            )
            for r in sub_result:
                # 二级三元组
                sub_triples.append({
                    "subject": r["subject"],
                    "predicate": r["predicate"],
                    "object": r["object"],
                    "object_type": r["object_type"],
                    "level": 2,
                })
                # 三级三元组（child → grandchild）
                for gc in r["grandchildren"]:
                    if gc["object"]:
                        sub_triples.append({
                            "subject": r["object"],
                            "predicate": gc["predicate"],
                            "object": gc["object"],
                            "object_type": gc["object_type"],
                            "level": 3,
                        })

        # ============ Step 3: 查询一级实体之间的关系三元组 ============
        # 救援队→灾区、仓库→灾区、灾区→避难所（通过道路）
        rel_query = """
        MATCH (disaster:受灾点 {name: $disaster_name})

        // 救援队→灾区路径
        OPTIONAL MATCH (team:救援队伍)-[:临近]->(tr:道路)
        OPTIONAL MATCH (tr)-[:连通*0..6]->(tr_mid:道路)-[:服务]->(disaster)
        WITH disaster, team, tr, collect(DISTINCT tr_mid) AS team_path_roads
        WHERE team IS NOT NULL AND size(team_path_roads) > 0

        // 仓库→灾区路径
        OPTIONAL MATCH (wh:物资仓库)-[:临近]->(wr:道路)
        OPTIONAL MATCH (wr)-[:连通*0..6]->(wr_mid:道路)-[:服务]->(disaster)
        WITH disaster, team, team_path_roads, wh, collect(DISTINCT wr_mid) AS wh_path_roads
        WHERE wh IS NOT NULL AND size(wh_path_roads) > 0

        // 灾区→避难所路径
        OPTIONAL MATCH (disaster)-[:临近]->(sr:道路)
        OPTIONAL MATCH (sr)-[:连通*0..6]->(sr_mid:道路)-[:服务]->(shelter:避难场所)
        WITH disaster, team, team_path_roads, wh, wh_path_roads,
             shelter, collect(DISTINCT sr_mid) AS sh_path_roads
        WHERE shelter IS NOT NULL AND size(sh_path_roads) > 0

        RETURN collect(DISTINCT {
            from: team.name, to: disaster.name, relation: '救援前往',
            path_roads: [r IN team_path_roads WHERE r IS NOT NULL | r.name]
        }) AS team_to_disaster,
        collect(DISTINCT {
            from: wh.name, to: disaster.name, relation: '物资调运',
            path_roads: [r IN wh_path_roads WHERE r IS NOT NULL | r.name]
        }) AS wh_to_disaster,
        collect(DISTINCT {
            from: disaster.name, to: shelter.name, relation: '人员转移',
            path_roads: [r IN sh_path_roads WHERE r IS NOT NULL | r.name]
        }) AS disaster_to_shelter
        """
        rel_result = await neo4j_manager.execute_query(
            rel_query, {"disaster_name": disaster_name}
        )

        # ============ Step 4: 整理所有三元组 ============
        all_triples = []

        # 4.1 添加属性子节点三元组
        all_triples.extend(sub_triples)

        # 4.2 添加一级实体间的关系三元组
        if rel_result:
            r0 = rel_result[0]

            # 救援队 → 灾区
            for item in r0.get("team_to_disaster", []):
                if item.get("from") and item.get("to"):
                    all_triples.append({
                        "subject": item["from"],
                        "predicate": item["relation"],
                        "object": item["to"],
                        "object_type": "受灾点",
                        "level": 1,
                        "path_roads": item.get("path_roads", []),
                    })

            # 仓库 → 灾区
            for item in r0.get("wh_to_disaster", []):
                if item.get("from") and item.get("to"):
                    all_triples.append({
                        "subject": item["from"],
                        "predicate": item["relation"],
                        "object": item["to"],
                        "object_type": "受灾点",
                        "level": 1,
                        "path_roads": item.get("path_roads", []),
                    })

            # 灾区 → 避难所
            for item in r0.get("disaster_to_shelter", []):
                if item.get("from") and item.get("to"):
                    all_triples.append({
                        "subject": item["from"],
                        "predicate": item["relation"],
                        "object": item["to"],
                        "object_type": "避难场所",
                        "level": 1,
                        "path_roads": item.get("path_roads", []),
                    })

        # ============ Step 5: 按类别归类返回 ============
        def _extract_props(node):
            if not node:
                return {}
            return {k: v for k, v in node.items() if k != "name"}

        return {
            "success": True,
            "disaster_name": disaster_name,
            "entities": {
                "disaster": {
                    "name": disaster_node.get("name") if disaster_node else disaster_name,
                    "properties": _extract_props(disaster_node),
                },
                "rescue_teams": [
                    {"name": t.get("name"), "properties": _extract_props(t)} for t in teams
                ],
                "warehouses": [
                    {"name": w.get("name"), "properties": _extract_props(w)} for w in warehouses
                ],
                "shelters": [
                    {"name": s.get("name"), "properties": _extract_props(s)} for s in shelters
                ],
                "roads": [
                    {"name": r.get("name"), "properties": _extract_props(r)} for r in roads
                ],
            },
            "triples": all_triples,
            "total_triples": len(all_triples),
            "summary": {
                "disaster_count": 1 if disaster_node else 0,
                "team_count": len(teams),
                "warehouse_count": len(warehouses),
                "shelter_count": len(shelters),
                "road_count": len(roads),
            },
        }


graph_repo = GraphRepository()
