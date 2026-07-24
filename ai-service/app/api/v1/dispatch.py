from fastapi import APIRouter, HTTPException, Query
from app.graph import graph_repo
from app.graph.repository import GraphRepository
from app.core.neo4j_client import neo4j_manager
from app.schemas import DispatchPlanResponse
from app.core.logging import logger

router = APIRouter(prefix="/api/v1/dispatch", tags=["物资调度"])


@router.get("/optimal-warehouses", summary="接口1：高风险区域最优物资仓库（预防前置调度）")
async def get_optimal_warehouses(risk_level: str = Query("极高", description="风险等级")):
    """
    获取指定风险等级区域的最优物资仓库调配方案。
    综合考虑：物资可用性、路网距离、紧急程度，计算评分排序。
    """
    try:
        result = await graph_repo.get_optimal_warehouses(risk_level)
        return {"risk_level": risk_level, "recommendations": result}
    except Exception as e:
        logger.error(f"查询最优仓库失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/available-teams", summary="接口2：筛选可调度救援队伍")
async def get_available_teams(
    area_name: str = Query(..., description="区域名称"),
    disaster_type: str | None = Query(None, description="灾害类型"),
):
    """
    筛选未被占用、可调度的救援队伍，按距离排序。
    Dify 工作流 HTTP 节点调用此接口。
    """
    try:
        teams = await graph_repo.get_available_teams_by_area(area_name, disaster_type)
        return {"area_name": area_name, "available_teams": teams}
    except Exception as e:
        logger.error(f"查询可用队伍失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/nearby-shelters", summary="接口3：附近避难场所")
async def get_nearby_shelters(area_name: str = Query(..., description="区域名称")):
    """获取受灾点附近、有剩余容量的避难场所"""
    try:
        shelters = await graph_repo.get_nearby_shelters(area_name)
        return {"area_name": area_name, "shelters": shelters}
    except Exception as e:
        logger.error(f"查询避难场所失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/plan", response_model=DispatchPlanResponse, summary="综合调度方案（Dify 调用主接口）")
async def get_dispatch_plan(
    area_name: str = Query(..., description="目标区域名称"),
    disaster_type: str = Query(..., description="灾害类型"),
):
    """
    Dify 工作流 HTTP 节点主调用接口。
    一次性返回：物资仓库推荐 + 可用救援队伍 + 附近避难场所
    """
    try:
        plan = await graph_repo.get_dispatch_plan(area_name, disaster_type)
        risk_spots = await graph_repo.list_high_risk_spots()
        spot = next((s for s in risk_spots if s.get("name") == area_name), {})
        plan["risk_level"] = spot.get("risk_level", "中")
        return plan
    except Exception as e:
        logger.error(f"生成调度方案失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/teams/{team_id}/allocate", summary="派发救援队伍（标记已调度）")
async def allocate_team(team_id: str, spot_id: str):
    """标记队伍已派发，防止重复调度"""
    try:
        ok = await graph_repo.allocate_team(team_id, spot_id)
        return {"success": ok}
    except Exception as e:
        logger.error(f"派发队伍失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Dify MCP 专用接口 ====================

@router.get("/graph/triples", summary="MCP 调用：查询灾害点三元组")
async def get_disaster_triples(
    area_name: str = Query(..., description="灾害点区域名称"),
):
    """Dify MCP 接口：查询灾害点关联的三元组数据

    返回：
    - spot: 灾害点信息
    - triples: 三元组列表 [{subject, predicate, object}, ...]
    - warehouses: 关联仓库
    - shelters: 关联避难所
    - teams: 关联救援队
    - materials: 需求物资
    - roads: 关联道路
    """
    try:
        result = await graph_repo.get_dispatch_triples(area_name)
        return result
    except Exception as e:
        logger.error(f"[MCP] 查询三元组失败: {e}")
        return {"success": False, "message": str(e), "triples": []}


@router.get("/graph/dispatch-triples", summary="MCP 调用：调度方案完整三元组（Dify 工作流主接口）")
async def get_dispatch_triples(
    disaster_name: str = Query(..., description="灾区名称（受灾点 name）"),
):
    """Dify 调度方案工作流主接口：查询完整的三元组数据作为 Neo4j 变量输入

    返回内容包括：
    1. 灾区(受灾点)实体及其 2-4 级子实体
    2. 周边救援队(救援队伍)实体及其下属实体
    3. 周边仓库(物资仓库)实体及其下属实体
    4. 周边避难所(避难场所)实体及其下属实体
    5. 涉及的道路(道路)实体及其下属实体
       - 救援队→灾区的路径路（起点救援队临近，终点服务灾区）
       - 仓库→灾区的路径路（起点仓库临近，终点服务灾区）
       - 灾区→避难所的路径路（起点灾区临近，终点服务避难所）
       - 只要连通的路，不必全部路
    6. 所有三元组列表（可直接作为 LLM 的输入变量）

    返回示例：
    {
      "success": true,
      "disaster_name": "漾濞县苍山西镇受灾点",
      "entities": {
        "disaster": {"name": "...", "properties": {...}},
        "rescue_teams": [...],
        "warehouses": [...],
        "shelters": [...],
        "roads": [...]
      },
      "triples": [
        {"subject": "灾区", "predicate": "位于", "object": "地点", "object_type": "地点名称", "level": 2},
        {"subject": "救援队", "predicate": "救援前往", "object": "灾区", "object_type": "受灾点", "level": 1, "path_roads": ["路1","路2"]},
        ...
      ],
      "total_triples": 50
    }
    """
    try:
        result = await graph_repo.get_dispatch_triples(disaster_name)
        logger.info(f"[MCP] 调度方案三元组查询: {disaster_name}, 共 {result.get('total_triples', 0)} 条")
        return result
    except Exception as e:
        logger.error(f"[MCP] 调度方案三元组查询失败: {e}")
        return {"success": False, "message": str(e), "triples": []}


@router.get("/graph/context", summary="MCP 调用：获取调度上下文（给 LLM）")
async def get_dispatch_context(
    area_name: str = Query(..., description="灾害点区域名称"),
    disaster_type: str = Query(None, description="灾害类型"),
):
    """Dify MCP 接口：生成调度方案的上下文信息（直接传给 LLM）

    返回自然语言描述的三元组信息，便于 LLM 理解
    """
    try:
        # 获取综合调度方案
        plan = await graph_repo.get_dispatch_plan(area_name, disaster_type or "")

        # 生成上下文描述
        context_lines = [
            f"# 灾害点: {area_name}",
            f"# 灾害类型: {disaster_type or '未知'}",
            f"# 风险等级: {plan.get('risk_level', '中')}",
            "",
            "## 附近可用仓库及物资:",
        ]

        for wh in plan.get("recommendations", [])[:5]:
            context_lines.append(
                f"- {wh.get('warehouse_name')}: 物资 {wh.get('material_name')}, "
                f"库存 {wh.get('stock_num')}, 距离 {wh.get('total_dist', 0):.1f}km"
            )

        context_lines.append("")
        context_lines.append("## 可调度救援队伍:")

        for team in plan.get("available_teams", [])[:5]:
            context_lines.append(f"- {team.get('team_name')}: 距离 {team.get('dist', 0):.1f}km")

        context_lines.append("")
        context_lines.append("## 附近避难所:")

        for shelter in plan.get("shelters", [])[:5]:
            context_lines.append(
                f"- {shelter.get('name')}: 容量 {shelter.get('max_capacity')}, "
                f"已容纳 {shelter.get('accommodated_count')}, 可用 {shelter.get('available_space')}"
            )

        context = "\n".join(context_lines)

        return {
            "success": True,
            "context": context,
            "plan": plan,
        }

    except Exception as e:
        logger.error(f"[MCP] 获取调度上下文失败: {e}")
        return {"success": False, "message": str(e), "context": ""}
