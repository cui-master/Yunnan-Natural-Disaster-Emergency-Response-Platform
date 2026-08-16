"""应急指挥人员 —— 审核事件 + 生成处置方案

职责：
1. 审核事件：调用 Dify 风险评估工作流
2. 生成处置方案：查 Neo4j 关联三元组 → 调用 Dify 调度工作流
3. 查灾害点关联图（避难所/仓库/队伍/道路）
"""
import json
import re
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List
from app.core.neo4j_client import neo4j_manager
from app.graph.json_loader import graph_loader
from app.agents import dify_client
from app.core.logging import logger

router = APIRouter(prefix="/api/v1/commander", tags=["应急指挥-审核与处置"])


# ════════════════════════════════════════════
# 请求模型
# ════════════════════════════════════════════

class ReviewRequest(BaseModel):
    """审核事件请求"""
    area_name: str = Field(..., description="区域名称")
    disaster_type: str = Field(..., description="灾害类型")
    description: str = Field(..., description="灾情描述")
    features: Optional[dict] = Field(None, description="环境特征（降雨/地质/水位等）")


class DispatchPlanRequest(BaseModel):
    """生成处置方案请求"""
    incident_ids: Optional[List[int]] = Field(None, description="受灾点ID列表（从Neo4j选择，可多选）")
    incident_id: Optional[int] = Field(None, description="单个受灾点ID（兼容旧版）")
    area_name: str = Field("", description="目标区域名称（兼容旧版/手动输入）")
    disaster_type: str = Field(..., description="灾害类型")
    risk_level: str = Field("中", description="风险等级")
    affected_people: int = Field(0, description="受灾人数")
    input_risk_info: str = Field("", description="风险情报摘要")
    vision_text: Optional[str] = Field(None, description="图像识别文本（可选）")


# ════════════════════════════════════════════
# Neo4j 三元组查询（以受灾点为中心，兼容新旧标签）
# ════════════════════════════════════════════

async def _find_incident_node(incident_id: int) -> Optional[dict]:
    """按incident_id查找受灾点节点（中英文标签兼容）"""
    for label in ["受灾点", "Incident"]:
        q = f"MATCH (d:{label} {{incidentId: $bid}}) RETURN d LIMIT 1"
        rows = await neo4j_manager.execute_query(q, {"bid": incident_id})
        if rows:
            d = rows[0]["d"]
            return dict(d) if isinstance(d, dict) else d
    return None


async def _find_incident_by_area(area_name: str) -> Optional[dict]:
    """按区域名称模糊匹配受灾点（中英文标签兼容）"""
    queries = [
        ("受灾点", "WHERE d.location CONTAINS $a OR d.name CONTAINS $a"),
        ("Incident", "WHERE d.locationName CONTAINS $a OR d.name CONTAINS $a OR d.location CONTAINS $a OR d.title CONTAINS $a"),
    ]
    for label, where in queries:
        q = f"MATCH (d:{label}) {where} RETURN d ORDER BY d.incidentId DESC LIMIT 1"
        rows = await neo4j_manager.execute_query(q, {"a": area_name})
        if rows:
            d = rows[0]["d"]
            return dict(d) if isinstance(d, dict) else d
    return None


async def _append_incident_triples(disaster_node: dict, triples: list, area_name: str = "") -> dict:
    """追加单个受灾点的关联关系三元组，返回disaster_relations"""
    disaster_relations = {}
    if not disaster_node:
        return disaster_relations
    d_id = disaster_node.get("incidentId")
    q = """MATCH (d)-[r]->(n)
           WHERE (d:Incident OR d:受灾点) AND d.incidentId = $did
           RETURN type(r) AS rel, labels(n) AS labels, properties(n) AS props"""
    rels = await neo4j_manager.execute_query(q, {"did": d_id})
    for rr in rels:
        disaster_relations[rr["rel"]] = rr["props"]

    d_name = disaster_node.get("name", disaster_node.get("title", "未知受灾点"))
    triples.append(f"【受灾点】{d_name}")

    place = disaster_relations.get("位于", {})
    place_name = place.get("name", place.get("placeName",
        disaster_node.get("locationName", disaster_node.get("location", area_name or "未知地点"))))
    triples.append(f"- 受灾点 -[位于]-> 地点 '{place_name}'")

    dtype_rel = disaster_relations.get("是", {})
    dtype = dtype_rel.get("name", dtype_rel.get("typeName", disaster_node.get("disasterType", "未知")))
    triples.append(f"- 受灾点 -[是]-> 灾害类型 '{dtype}'")

    risk_rel = disaster_relations.get("具备", {})
    risk_val = risk_rel.get("level", disaster_node.get("riskLevelValue", disaster_node.get("riskLevel", 2)))
    risk_name = risk_rel.get("name", "")
    risk_map = {1: "低风险(蓝色)", 2: "中风险(黄色)", 3: "高风险(橙色)", 4: "极高风险(红色)"}
    if isinstance(risk_val, str):
        risk_text = risk_val
    else:
        risk_text = risk_name or risk_map.get(int(risk_val) if risk_val else 2, "中风险(黄色)")
    triples.append(f"- 受灾点 -[具备]-> 危险等级 '{risk_text}'")

    aff_rel = disaster_relations.get("涉及", {})
    affected = aff_rel.get("count", disaster_node.get("affectedPeople", 0))
    triples.append(f"- 受灾点 -[涉及]-> 受灾人数 {affected}人")
    return disaster_relations


async def get_dispatch_triples(
    area_name: str = "",
    incident_id: Optional[int] = None,
    incident_ids: Optional[List[int]] = None,
) -> dict:
    """从本地 JSON 知识图谱获取调度方案所需的三元组数据（支持多选受灾点）

    替代原 Neo4j 查询，避免图数据库查询过慢。JSON 中每个受灾点通过
    "编号为" 三元组与 incident_id 对应。

    返回：disaster_info(list), warehouses, teams, shelters, material_items,
          triples, triples_text, full_graph, total_affected
    """
    graph_loader.reload()
    triples = []
    disaster_infos = []
    warehouses = []
    teams = []
    shelters = []
    material_items = []

    try:
        # ── 1. 确定要查询的受灾点ID列表 ──
        target_ids = []
        if incident_ids:
            target_ids = list(incident_ids)
        if incident_id and incident_id not in target_ids:
            target_ids.append(incident_id)

        # ── 2. 按ID查找受灾点名称 ──
        found_names = []
        for bid in target_ids:
            name = graph_loader.get_incident_by_id(bid)
            if name:
                found_names.append(name)
            else:
                logger.warning(f"未找到编号为 {bid} 的受灾点")

        # ── 3. 如果无ID或按ID未找到，按 area_name 兜底匹配 ──
        if not found_names and area_name:
            name = graph_loader.get_incident_name_by_area(area_name)
            if name:
                found_names.append(name)

        # ── 4. 组装受灾点信息并追加三元组 ──
        total_affected = 0
        for name in found_names:
            props = graph_loader.get_subject_properties(name)
            info = {
                "incidentId": int(props.get("编号为", 0) or 0),
                "name": name.replace("受灾点", ""),
                "location": props.get("位于", ""),
                "disasterType": props.get("是", ""),
                "riskLevel": props.get("具备", ""),
                "affectedPeople": int(props.get("涉及", "0") or 0),
                "reportTime": props.get("上报时间", ""),
                "reviewTime": props.get("审核时间", ""),
                "approvalReportTime": props.get("审核同意上报时间", ""),
                "occurredTime": props.get("发生时间", ""),
            }
            disaster_infos.append(info)
            total_affected += info["affectedPeople"]

        if not found_names:
            triples.append("【受灾点】未匹配到具体受灾点，按全局资源调度")

        # 生成以受灾点为中心的三元组文本
        triples = graph_loader.build_triples_text(found_names, include_global=True)

        # ── 5. 从 JSON 提取结构化资源（用于前端/fallback 自动分配）──
        # 仓库
        for w in graph_loader.get_subjects_by_type("物资仓库", 20):
            warehouses.append({
                "resourceNo": w.get("编号为", ""),
                "name": w.get("_name", ""),
                "location": w.get("位于", ""),
                "availableQty": 10000,  # JSON 中无库存，使用默认值供分配
            })

        # 救援队伍
        for t in graph_loader.get_subjects_by_type("救援队伍", 20):
            teams.append({
                "resourceNo": t.get("编号为", ""),
                "name": t.get("_name", ""),
                "location": t.get("位于", ""),
                "availableQty": 100,
                "size": 100,
                "availableSize": 100,
                "isBusy": False,
                "specialty": t.get("擅长", ""),
            })

        # 避难场所
        for s in graph_loader.get_subjects_by_type("避难场所", 20):
            cap = s.get("最大容纳人数", s.get("承载上限", "1000"))
            try:
                cap_num = int(cap)
            except (ValueError, TypeError):
                cap_num = 1000
            shelters.append({
                "resourceNo": s.get("编号为", ""),
                "name": s.get("_name", ""),
                "location": s.get("位于", ""),
                "maxCapacity": cap_num,
                "capacity": cap_num,
            })

        # 物资单品
        for m in graph_loader.get_subjects_by_type("物资单品", 50):
            qty = m.get("数量", "0")
            try:
                qty_num = int(qty)
            except (ValueError, TypeError):
                qty_num = 0
            # JSON 中未标注库存时，给默认充足库存以便 fallback 分配
            if qty_num <= 0:
                qty_num = 10000
            material_items.append({
                "resourceNo": m.get("编号为", ""),
                "name": m.get("_name", ""),
                "availableQty": qty_num,
                "unit": m.get("单位", "件"),
                "warehouseNo": "",
                "category": "material",
            })

    except Exception as e:
        logger.error(f"查询 JSON 三元组失败: {e}", exc_info=True)

    triples_text = "\n".join(triples) if triples else "暂无可用资源数据"
    print(f"[get_dispatch_triples] 共生成 {len(triples)} 条三元组")
    if triples:
        for t in triples[:10]:
            print(f"  {t}")

    full_graph = graph_loader.get_full_graph()

    return {
        "disaster_info": disaster_infos[0] if disaster_infos else {},
        "disaster_infos": disaster_infos,
        "warehouses": warehouses,
        "teams": teams,
        "shelters": shelters,
        "material_items": material_items,
        "triples": triples,
        "triples_text": triples_text,
        "full_graph": full_graph,
        "total_affected": total_affected,
    }


def extract_json_block(text: str) -> Optional[dict]:
    """从文本中提取JSON块，并归一化新旧两种格式。

    复用 DifyClient 的归一化逻辑，确保 commander.py 与 dify_client.py 解析结果一致，
    支持结构化的物资分配（含 items 明细）、救援队伍任务、人员疏散方案等。
    """
    return dify_client._try_extract_plan_json(text)


# ════════════════════════════════════════════
# 接口
# ════════════════════════════════════════════

@router.post("/review", summary="审核事件（风险评估）")
async def review_event(req: ReviewRequest):
    """应急指挥人员审核灾情事件。

    调用 Dify 风险评估工作流。
    """
    try:
        result = await dify_client.run_risk_assessment(
            area_name=req.area_name,
            disaster_type=req.disaster_type,
            description=req.description,
            features=req.features,
        )
        return {
            "success": True,
            "area_name": req.area_name,
            "disaster_type": req.disaster_type,
            "task_id": result.get("task_id"),
            "status": result.get("status"),
            "fallback_level": result.get("fallback_level", "none"),
            "result": result.get("result"),
        }
    except Exception as e:
        logger.error(f"审核事件失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/dispatch-plan", summary="生成处置方案")
async def generate_dispatch_plan(req: DispatchPlanRequest):
    """生成应急处置方案。

    流程：
    1. 查 Neo4j 获取三元组数据（以受灾点为中心）
    2. 调用 Dify 调度方案工作流，传入三元组
    3. 解析返回的结构化JSON（含短期/中期/长期措施、资源分配等）
    """
    try:
        # Step 1: 从Neo4j获取三元组（支持多选受灾点）
        graph_data = await get_dispatch_triples(
            area_name=req.area_name,
            incident_id=req.incident_id,
            incident_ids=req.incident_ids,
        )
        # 从选中受灾点推断区域名和受灾人数（若前端未传）
        disaster_infos = graph_data.get("disaster_infos", [])
        if disaster_infos:
            locations = [d.get("location", d.get("locationName", "")) for d in disaster_infos if d.get("location") or d.get("locationName")]
            if not req.area_name and locations:
                req.area_name = "、".join(set(locations))
            if not req.affected_people:
                req.affected_people = graph_data.get("total_affected", 0)

        print("=" * 60)
        print("[调度方案] Step1: Neo4j三元组数据")
        print(f"  选中受灾点数: {len(disaster_infos)}")
        for i, d in enumerate(disaster_infos):
            print(f"    [{i+1}] {d.get('name', d.get('title','?'))} (incidentId={d.get('incidentId')}, location={d.get('location', d.get('locationName',''))})")
        print(f"  可用仓库数: {len(graph_data.get('warehouses', []))}")
        print(f"  可用队伍数: {len(graph_data.get('teams', []))}")
        print(f"  可用避难所数: {len(graph_data.get('shelters', []))}")
        print(f"  三元组文本长度: {len(graph_data.get('triples_text', ''))}")
        print(f"  三元组文本:")
        print(graph_data.get('triples_text', ''))

        # Step 2: 调用Dify工作流（失败则DeepSeek兜底）
        result = await dify_client.run_dispatch_workflow(
            area_name=req.area_name,
            disaster_type=req.disaster_type,
            risk_level=req.risk_level,
            affected_people=req.affected_people,
            triples_text=graph_data["triples_text"],
            input_risk_info=req.input_risk_info,
            vision_text=req.vision_text,
        )
        print(f"[调度方案] Step2: Dify/LLM调用完成")
        print(f"  fallback_level: {result.get('fallback_level')}")
        print(f"  status: {result.get('status')}")
        print(f"  task_id: {result.get('task_id')}")

        # Step 3: 解析返回结果（dify_client.run_dispatch_workflow 内部已做归一化，
        # 但对模板兜底等情况，这里再做一次归一化解析）
        ai_raw_output = ""
        if isinstance(result.get("result"), dict):
            ai_raw_output = result["result"].get("text", result["result"].get("output", ""))
        elif isinstance(result.get("result"), str):
            ai_raw_output = result["result"]

        print(f"[调度方案] Step3: AI原始输出长度: {len(ai_raw_output)}")
        print(f"  AI原始输出前2000字:")
        print(ai_raw_output[:2000])
        print("=" * 60)

        # 尝试提取结构化JSON（extract_json_block 已兼容新旧格式并归一化）
        parsed_plan = extract_json_block(ai_raw_output)
        print(f"[调度方案] JSON解析结果: {'成功' if parsed_plan else '失败'}")
        if parsed_plan:
            print(f"  解析到的key: {list(parsed_plan.keys())}")

        # 默认结构
        plan_data = {
            "shortTermMeasures": [],
            "midTermMeasures": [],
            "longTermMeasures": [],
            "materials_plan": [],
            "teams_plan": [],
            "shelters_plan": [],
            "evacuation_plan": {},
            "remarks": ""
        }

        if parsed_plan:
            plan_data["shortTermMeasures"] = parsed_plan.get("短期措施", parsed_plan.get("shortTermMeasures", []))
            plan_data["midTermMeasures"] = parsed_plan.get("中期措施", parsed_plan.get("midTermMeasures", []))
            plan_data["longTermMeasures"] = parsed_plan.get("长期措施", parsed_plan.get("longTermMeasures", []))
            plan_data["materials_plan"] = parsed_plan.get("物资分配", parsed_plan.get("materials", []))
            plan_data["teams_plan"] = parsed_plan.get("救援队伍方案", parsed_plan.get("teams", []))
            plan_data["shelters_plan"] = parsed_plan.get("避难场所方案", parsed_plan.get("shelters", []))
            plan_data["evacuation_plan"] = parsed_plan.get("人员疏散方案", parsed_plan.get("evacuation", {}))
            plan_data["remarks"] = parsed_plan.get("方案备注", parsed_plan.get("remarks", ""))

        # fallback：若AI未返回结构化资源方案，则基于Neo4j真实库存自动分配
        affected = req.affected_people or graph_data.get("total_affected", 0)
        warehouses = graph_data.get("warehouses", [])
        teams = graph_data.get("teams", [])
        shelters = graph_data.get("shelters", [])
        material_items = graph_data.get("material_items", [])

        # 1. 物资分配 fallback：根据受灾人数和 JSON 中实际存在的物资名称自动分配
        if not plan_data["materials_plan"] and warehouses and material_items:
            # 物资需求规则（名称关键词 -> 每人/每几人需求量）
            demand_rules = [
                ("帐篷", max(1, affected // 4)),
                ("饮用", affected * 3),
                ("毯", affected),
                ("食品", affected * 2),
                ("床", affected // 2),
                ("睡袋", affected // 2),
            ]
            wh_count = len(warehouses)
            plan_data["materials_plan"] = []
            for w in warehouses:
                items = []
                used_names = set()
                for keyword, total_need in demand_rules:
                    for mat in material_items:
                        name = mat.get("name", "")
                        if keyword in name and name not in used_names:
                            used_names.add(name)
                            per_wh = min((total_need + wh_count - 1) // wh_count, max(mat.get("availableQty", 0), 1))
                            if per_wh > 0:
                                items.append({
                                    "name": name,
                                    "allocatedQty": per_wh,
                                    "unit": mat.get("unit", "件"),
                                    "availableQty": max(mat.get("availableQty", 0), 1),
                                })
                            break
                if items:
                    plan_data["materials_plan"].append({
                        "resourceNo": w.get("resourceNo", ""),
                        "name": w.get("name", ""),
                        "items": items,
                    })

        # 2. 救援队伍 fallback（补充任务内容）
        if not plan_data["teams_plan"] and teams:
            plan_data["teams_plan"] = [
                {
                    "resourceNo": t.get("resourceNo", ""),
                    "name": t.get("name", ""),
                    "dispatchSize": t.get("availableQty") or t.get("size") or t.get("availableSize") or 0,
                    "isBusy": True,
                    "task": f"赶赴灾区开展{affected}名受灾群众的搜救、转移安置及秩序维护工作",
                }
                for t in teams
            ]

        # 3. 避难场所 fallback
        if not plan_data["shelters_plan"] and shelters:
            plan_data["shelters_plan"] = [
                {
                    "resourceNo": s.get("resourceNo", ""),
                    "name": s.get("name", ""),
                    "maxCapacity": s.get("maxCapacity") or s.get("capacity") or s.get("availableQty") or 0,
                    "evacuees": min(affected, s.get("maxCapacity") or s.get("capacity") or s.get("availableQty") or 0),
                }
                for s in shelters
            ]

        # 4. 人员疏散 fallback：只保留 routes 和 totalEvacuees
        if isinstance(plan_data["evacuation_plan"], dict):
            evac = plan_data["evacuation_plan"]
            plan_data["evacuation_plan"] = {
                "routes": evac.get("routes") or evac.get("疏散路线") or "按就近原则疏散至安全避难场所",
                "totalEvacuees": evac.get("totalEvacuees") or evac.get("疏散人数") or affected,
            }
        else:
            plan_data["evacuation_plan"] = {
                "routes": "按就近原则疏散至安全避难场所",
                "totalEvacuees": affected,
            }

        return {
            "success": True,
            "task_id": result.get("task_id"),
            "status": result.get("status"),
            "fallback_level": result.get("fallback_level", "none"),
            "graph_data": graph_data,
            "ai_raw_output": ai_raw_output,
            "plan": plan_data,
        }
    except Exception as e:
        logger.error(f"生成处置方案失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/disasters/{spot_id}/graph", summary="查灾害点关联三元组")
async def get_disaster_graph(spot_id: str):
    """查询灾害点关联的三元组数据"""
    try:
        graph_data = await get_dispatch_triples(spot_id)
        return {
            "success": True,
            "spot_id": spot_id,
            "data": graph_data,
        }
    except Exception as e:
        logger.error(f"查询灾害点关联图失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dispatch-resources", summary="查询调度资源（物资+队伍+避难所）")
async def get_dispatch_resources(
    area_name: str = Query(..., description="区域名称"),
):
    """直接查询某区域的调度资源"""
    try:
        graph_data = await get_dispatch_triples(area_name)
        return {
            "success": True,
            "area_name": area_name,
            "warehouses": graph_data["warehouses"],
            "teams": graph_data["teams"],
            "shelters": graph_data["shelters"],
            "triples": graph_data["triples"],
        }
    except Exception as e:
        logger.error(f"查询调度资源失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/incidents", summary="查询图数据库中所有受灾点列表（供前端选择）")
async def list_incidents():
    """从本地 JSON 知识图谱查询所有受灾点，返回列表供前端下拉选择（支持多选）"""
    try:
        graph_loader.reload()
        incidents = graph_loader.list_incidents()
        logger.info(f"查询受灾点列表完成，共 {len(incidents)} 个")
        return {"success": True, "data": incidents, "count": len(incidents)}
    except Exception as e:
        logger.error(f"查询受灾点列表失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
