"""
ai-service 全面功能测试脚本
模拟 SpringBoot 调用 FastAPI，测试：
1. Dify 调度方案工作流（含参数打印验证）
2. Dify 风险评估工作流
3. 知识库文档上传/查询/删除
4. LLM 模型切换（deepseek/qwen）
5. 灾情上报到 Neo4j
6. 资源管理员对 Neo4j 的增删改查
"""
import httpx
import asyncio
import json
import sys
import time
import uuid

BASE_URL = "http://localhost:8050"
TIMEOUT = 120.0

# 颜色输出
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"

passed = 0
failed = 0
skipped = 0


def log_pass(msg):
    global passed
    passed += 1
    print(f"{GREEN}[PASS]{RESET} {msg}")


def log_fail(msg, detail=""):
    global failed
    failed += 1
    print(f"{RED}[FAIL]{RESET} {msg}")
    if detail:
        print(f"       详情: {detail}")


def log_skip(msg):
    global skipped
    skipped += 1
    print(f"{YELLOW}[SKIP]{RESET} {msg}")


def log_info(msg):
    print(f"{CYAN}[INFO]{RESET} {msg}")


def log_section(title):
    print(f"\n{'='*60}")
    print(f"{CYAN}  {title}{RESET}")
    print(f"{'='*60}")


async def main():
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=TIMEOUT) as client:

        # ════════════════════════════════════════════
        # 0. 健康检查
        # ════════════════════════════════════════════
        log_section("0. 健康检查")
        try:
            resp = await client.get("/health")
            if resp.status_code == 200:
                log_pass(f"服务健康检查正常: {resp.json()}")
            else:
                log_fail(f"健康检查异常: {resp.status_code}")
                return
        except Exception as e:
            log_fail("服务未启动，请先启动 ai-service", str(e))
            return

        # 数据源状态
        try:
            resp = await client.get("/api/v1/admin/datasources")
            data = resp.json()
            log_info(f"数据源状态: {json.dumps(data, ensure_ascii=False, indent=2)}")
        except Exception as e:
            log_fail("查询数据源状态失败", str(e))

        # ════════════════════════════════════════════
        # 1. 灾情上报到 Neo4j
        # ════════════════════════════════════════════
        log_section("1. 灾情上报到 Neo4j")

        disaster_id = f"test-ds-{uuid.uuid4().hex[:8]}"
        disaster_data = {
            "id": disaster_id,
            "name": "测试灾区-漾濞县苍山西镇",
            "disaster_type": ["地震灾害风险"],
            "risk_level": "高",
            "urgent_level": 4,
            "lng": 99.95,
            "lat": 25.67,
            "reporter": "测试信息员",
            "casualties": 0,
            "affected_people": 500,
            "description": "测试用：漾濞县苍山西镇发生4.5级地震，部分房屋受损",
            "severity": "中等",
        }

        # 创建灾情
        try:
            resp = await client.post("/api/v1/reporter/disasters", json=disaster_data)
            if resp.status_code == 200:
                result = resp.json()
                log_pass(f"灾情上报成功: id={result.get('id')}, name={result.get('name')}")
            else:
                log_fail(f"灾情上报失败: HTTP {resp.status_code}", resp.text[:200])
        except Exception as e:
            log_fail("灾情上报异常", str(e))

        # 查询灾情列表
        try:
            resp = await client.get("/api/v1/reporter/disasters?limit=5")
            if resp.status_code == 200:
                data = resp.json()
                log_pass(f"查询灾情列表成功: 共 {data.get('total', 0)} 条")
            else:
                log_fail(f"查询灾情列表失败: {resp.status_code}")
        except Exception as e:
            log_fail("查询灾情列表异常", str(e))

        # 查询单个灾情
        try:
            resp = await client.get(f"/api/v1/reporter/disasters/{disaster_id}")
            if resp.status_code == 200:
                log_pass(f"查询灾情详情成功: {resp.json().get('name')}")
            else:
                log_fail(f"查询灾情详情失败: {resp.status_code}")
        except Exception as e:
            log_fail("查询灾情详情异常", str(e))

        # ════════════════════════════════════════════
        # 2. 资源管理员对 Neo4j 的增删改查
        # ════════════════════════════════════════════
        log_section("2. 资源管理员 CRUD（Neo4j）")

        # --- 2.1 仓库 CRUD ---
        wh_id = f"test-wh-{uuid.uuid4().hex[:8]}"
        wh_data = {
            "id": wh_id,
            "name": "测试仓库-大理中心库",
            "address": "大理市下关街道",
            "lng": 100.23,
            "lat": 25.61,
            "manager": "张三",
            "contact": "13800138000",
        }

        # 创建仓库
        try:
            resp = await client.post("/api/v1/resource/warehouses", json=wh_data)
            if resp.status_code == 200:
                log_pass(f"创建仓库成功: {resp.json().get('name')}")
            else:
                log_fail(f"创建仓库失败: {resp.status_code}", resp.text[:200])
        except Exception as e:
            log_fail("创建仓库异常", str(e))

        # 查询仓库列表
        try:
            resp = await client.get("/api/v1/resource/warehouses?limit=5")
            if resp.status_code == 200:
                log_pass(f"查询仓库列表成功: {len(resp.json())} 条")
            else:
                log_fail(f"查询仓库列表失败: {resp.status_code}")
        except Exception as e:
            log_fail("查询仓库列表异常", str(e))

        # 更新仓库
        try:
            resp = await client.put(f"/api/v1/resource/warehouses/{wh_id}", json={"manager": "李四", "contact": "13900139000"})
            if resp.status_code == 200:
                updated = resp.json()
                if updated.get("manager") == "李四":
                    log_pass("更新仓库成功: manager 已改为李四")
                else:
                    log_fail("更新仓库失败: 字段未更新", str(updated))
            else:
                log_fail(f"更新仓库失败: {resp.status_code}")
        except Exception as e:
            log_fail("更新仓库异常", str(e))

        # 删除仓库
        try:
            resp = await client.delete(f"/api/v1/resource/warehouses/{wh_id}")
            if resp.status_code == 200:
                log_pass(f"删除仓库成功: {wh_id}")
            else:
                log_fail(f"删除仓库失败: {resp.status_code}")
        except Exception as e:
            log_fail("删除仓库异常", str(e))

        # --- 2.2 救援队伍 CRUD ---
        team_id = f"test-team-{uuid.uuid4().hex[:8]}"
        team_data = {
            "id": team_id,
            "team_name": "测试救援队-蓝天突击队",
            "current_lng": 100.23,
            "current_lat": 25.61,
            "carry_limit": 5000,
            "suitable_disaster": ["地震灾害风险", "洪涝灾害风险"],
            "status": "空闲",
        }

        try:
            resp = await client.post("/api/v1/resource/rescue-teams", json=team_data)
            if resp.status_code == 200:
                log_pass(f"创建救援队伍成功: {resp.json().get('team_name')}")
            else:
                log_fail(f"创建救援队伍失败: {resp.status_code}", resp.text[:200])
        except Exception as e:
            log_fail("创建救援队伍异常", str(e))

        try:
            resp = await client.get("/api/v1/resource/rescue-teams?limit=5")
            if resp.status_code == 200:
                log_pass(f"查询救援队伍列表成功: {len(resp.json())} 条")
            else:
                log_fail(f"查询救援队伍列表失败: {resp.status_code}")
        except Exception as e:
            log_fail("查询救援队伍列表异常", str(e))

        try:
            resp = await client.put(f"/api/v1/resource/rescue-teams/{team_id}", json={"status": "已调度"})
            if resp.status_code == 200 and resp.json().get("status") == "已调度":
                log_pass("更新救援队伍成功: status 已改为已调度")
            else:
                log_fail(f"更新救援队伍失败: {resp.status_code}")
        except Exception as e:
            log_fail("更新救援队伍异常", str(e))

        try:
            resp = await client.delete(f"/api/v1/resource/rescue-teams/{team_id}")
            if resp.status_code == 200:
                log_pass(f"删除救援队伍成功: {team_id}")
            else:
                log_fail(f"删除救援队伍失败: {resp.status_code}")
        except Exception as e:
            log_fail("删除救援队伍异常", str(e))

        # --- 2.3 避难场所 CRUD ---
        shelter_id = f"test-sh-{uuid.uuid4().hex[:8]}"
        shelter_data = {
            "id": shelter_id,
            "name": "测试避难所-体育馆",
            "max_capacity": 3000,
            "accommodated_count": 0,
            "lng": 100.23,
            "lat": 25.61,
        }

        try:
            resp = await client.post("/api/v1/resource/shelters", json=shelter_data)
            if resp.status_code == 200:
                log_pass(f"创建避难场所成功: {resp.json().get('name')}")
            else:
                log_fail(f"创建避难场所失败: {resp.status_code}", resp.text[:200])
        except Exception as e:
            log_fail("创建避难场所异常", str(e))

        try:
            resp = await client.get("/api/v1/resource/shelters?limit=5")
            if resp.status_code == 200:
                log_pass(f"查询避难场所列表成功: {len(resp.json())} 条")
            else:
                log_fail(f"查询避难场所列表失败: {resp.status_code}")
        except Exception as e:
            log_fail("查询避难场所列表异常", str(e))

        try:
            resp = await client.put(f"/api/v1/resource/shelters/{shelter_id}", json={"accommodated_count": 500})
            if resp.status_code == 200 and resp.json().get("accommodated_count") == 500:
                log_pass("更新避难场所成功: accommodated_count=500")
            else:
                log_fail(f"更新避难场所失败: {resp.status_code}")
        except Exception as e:
            log_fail("更新避难场所异常", str(e))

        try:
            resp = await client.delete(f"/api/v1/resource/shelters/{shelter_id}")
            if resp.status_code == 200:
                log_pass(f"删除避难场所成功: {shelter_id}")
            else:
                log_fail(f"删除避难场所失败: {resp.status_code}")
        except Exception as e:
            log_fail("删除避难场所异常", str(e))

        # --- 2.4 物资 CRUD ---
        mat_id = f"test-mat-{uuid.uuid4().hex[:8]}"
        mat_data = {
            "id": mat_id,
            "name": "测试物资-急救包",
            "type": "通用",
            "unit": "个",
            "weight": 1.5,
            "suitable_disaster": ["通用"],
        }

        try:
            resp = await client.post("/api/v1/resource/materials", json=mat_data)
            if resp.status_code == 200:
                log_pass(f"创建物资成功: {resp.json().get('name')}")
            else:
                log_fail(f"创建物资失败: {resp.status_code}", resp.text[:200])
        except Exception as e:
            log_fail("创建物资异常", str(e))

        try:
            resp = await client.get("/api/v1/resource/materials?limit=5")
            if resp.status_code == 200:
                log_pass(f"查询物资列表成功: {len(resp.json())} 条")
            else:
                log_fail(f"查询物资列表失败: {resp.status_code}")
        except Exception as e:
            log_fail("查询物资列表异常", str(e))

        try:
            resp = await client.delete(f"/api/v1/resource/materials/{mat_id}")
            if resp.status_code == 200:
                log_pass(f"删除物资成功: {mat_id}")
            else:
                log_fail(f"删除物资失败: {resp.status_code}")
        except Exception as e:
            log_fail("删除物资异常", str(e))

        # ════════════════════════════════════════════
        # 3. LLM 模型切换
        # ════════════════════════════════════════════
        log_section("3. LLM 模型切换（Dify 失败降级用）")

        # 查询当前配置
        try:
            resp = await client.get("/api/v1/admin/llm/config")
            if resp.status_code == 200:
                cfg = resp.json()
                log_pass(f"查询 LLM 配置成功: provider={cfg['config']['provider']}, model={cfg['config']['model']}")
                log_info(f"  支持的 providers: {cfg.get('supported_providers')}")
            else:
                log_fail(f"查询 LLM 配置失败: {resp.status_code}")
        except Exception as e:
            log_fail("查询 LLM 配置异常", str(e))

        # 切换到 deepseek
        try:
            resp = await client.put("/api/v1/admin/llm/config", json={"provider": "deepseek"})
            if resp.status_code == 200:
                cfg = resp.json()
                if cfg["config"]["provider"] == "deepseek":
                    log_pass("切换 LLM 到 deepseek 成功")
                else:
                    log_fail("切换 LLM 失败: provider 不匹配")
            else:
                log_fail(f"切换 LLM 失败: {resp.status_code}")
        except Exception as e:
            log_fail("切换 LLM 异常", str(e))

        # 测试 LLM 连通性
        try:
            log_info("正在测试 LLM 连通性（可能需要几秒）...")
            resp = await client.post("/api/v1/admin/llm/test", timeout=60.0)
            if resp.status_code == 200:
                result = resp.json()
                if result.get("success"):
                    log_pass(f"LLM 连通性测试成功: {result.get('message', '')[:80]}")
                else:
                    log_fail(f"LLM 连通性测试失败: {result.get('error', '')[:100]}")
            else:
                log_fail(f"LLM 测试请求失败: {resp.status_code}")
        except Exception as e:
            log_fail("LLM 测试异常", str(e))

        # ════════════════════════════════════════════
        # 4. Dify 风险评估工作流
        # ════════════════════════════════════════════
        log_section("4. Dify 风险评估工作流")

        review_req = {
            "area_name": "漾濞县苍山西镇",
            "disaster_type": "地震",
            "description": "据中国地震台网测定，漾濞县苍山西镇发生4.5级地震，震源深度10千米",
            "features": {
                "rainfall_24h": 5,
                "rainfall_3d": 20,
                "geological_risk_level": "中",
                "weather_warning": "无",
                "water_level_ratio": 0.3,
                "max_magnitude": 4.5,
                "opinion_hot_count": 100,
                "sentiment_score": 0.6,
            },
        }

        try:
            log_info("正在调用风险评估工作流（参数会打印到 ai-service 终端）...")
            log_info(f"请求参数: {json.dumps(review_req, ensure_ascii=False, indent=2)}")
            resp = await client.post("/api/v1/commander/review", json=review_req, timeout=120.0)
            if resp.status_code == 200:
                result = resp.json()
                fallback = result.get("fallback_level", "unknown")
                log_pass(f"风险评估完成: fallback_level={fallback}, task_id={result.get('task_id', '')[:20]}")
                log_info(f"  结果摘要: {str(result.get('result', ''))[:200]}...")
            else:
                log_fail(f"风险评估失败: {resp.status_code}", resp.text[:200])
        except Exception as e:
            log_fail("风险评估异常", str(e))

        # ════════════════════════════════════════════
        # 5. Dify 调度方案工作流
        # ════════════════════════════════════════════
        log_section("5. Dify 调度方案工作流")

        dispatch_req = {
            "area_name": "漾濞县苍山西镇",
            "disaster_type": "地震",
            "risk_level": "极高",
            "input_risk_info": "漾濞县苍山西镇4.5级地震，震源深度10km，约500人受灾，部分房屋倒塌",
            "vision_text": "卫星图像显示震中周边有建筑倒塌",
        }

        try:
            log_info("正在调用调度方案工作流（参数会打印到 ai-service 终端）...")
            log_info(f"请求参数: {json.dumps(dispatch_req, ensure_ascii=False, indent=2)}")
            resp = await client.post("/api/v1/commander/dispatch-plan", json=dispatch_req, timeout=180.0)
            if resp.status_code == 200:
                result = resp.json()
                fallback = result.get("fallback_level", "unknown")
                log_pass(f"调度方案生成完成: fallback_level={fallback}")
                log_info(f"  结果摘要:\n{str(result.get('result', ''))[:500]}...")
            else:
                log_fail(f"调度方案失败: {resp.status_code}", resp.text[:200])
        except Exception as e:
            log_fail("调度方案异常", str(e))

        # ════════════════════════════════════════════
        # 6. 知识库管理
        # ════════════════════════════════════════════
        log_section("6. 知识库文档上传/查询/删除")

        # 查询知识库列表
        try:
            resp = await client.get("/knowledge-base/list")
            if resp.status_code == 200:
                kbs = resp.json().get("knowledge_bases", [])
                log_pass(f"查询知识库列表成功: {len(kbs)} 个知识库")
                for kb in kbs:
                    log_info(f"  - {kb['name']}: {kb['dataset_id']}")
            else:
                log_fail(f"查询知识库列表失败: {resp.status_code}")
        except Exception as e:
            log_fail("查询知识库列表异常", str(e))

        # 上传文本文档到"优化调度"知识库
        doc_name = f"测试文档-{uuid.uuid4().hex[:6]}.txt"
        doc_content = "云南省自然灾害应急调度预案测试文档。本文档用于测试知识库上传功能，包含应急物资调度流程、避难场所管理规范、救援队伍调度原则等内容。"

        try:
            resp = await client.post(
                "/knowledge-base/upload-text",
                data={
                    "kb_name": "优化调度",
                    "name": doc_name,
                    "text": doc_content,
                    "indexing_technique": "high_quality",
                },
                timeout=120.0,
            )
            if resp.status_code == 200:
                result = resp.json()
                log_pass(f"上传文本文档成功: {doc_name}")
                log_info(f"  结果: {json.dumps(result, ensure_ascii=False)[:200]}")
            else:
                log_fail(f"上传文本文档失败: {resp.status_code}", resp.text[:200])
        except Exception as e:
            log_fail("上传文本文档异常", str(e))

        # 查询文档列表
        try:
            resp = await client.get("/knowledge-base/documents", params={"kb_name": "优化调度", "limit": 5})
            if resp.status_code == 200:
                data = resp.json().get("data", {})
                docs = data.get("data", [])
                log_pass(f"查询文档列表成功: {len(docs)} 条文档")
                # 找到刚上传的文档
                uploaded_doc = None
                for doc in docs:
                    if doc.get("name") == doc_name:
                        uploaded_doc = doc
                        break
                if uploaded_doc:
                    doc_id = uploaded_doc.get("id")
                    log_info(f"  找到测试文档: id={doc_id}, 状态={uploaded_doc.get('display_status') or uploaded_doc.get('indexing_status')}")

                    # 查询文档状态
                    try:
                        resp2 = await client.get(f"/knowledge-base/documents/{doc_id}/status", params={"kb_name": "优化调度"})
                        if resp2.status_code == 200:
                            doc_status = resp2.json().get("document", {})
                            log_pass(f"查询文档状态成功: {doc_status.get('display_status', 'unknown')}")
                        else:
                            log_fail(f"查询文档状态失败: {resp2.status_code}")
                    except Exception as e:
                        log_fail("查询文档状态异常", str(e))

                    # 删除文档
                    try:
                        resp3 = await client.delete(f"/knowledge-base/documents/{doc_id}", params={"kb_name": "优化调度"})
                        if resp3.status_code == 200:
                            log_pass(f"删除文档成功: {doc_id}")
                        else:
                            log_fail(f"删除文档失败: {resp3.status_code}")
                    except Exception as e:
                        log_fail("删除文档异常", str(e))
                else:
                    log_skip("未找到刚上传的测试文档，跳过状态查询和删除")
            else:
                log_fail(f"查询文档列表失败: {resp.status_code}")
        except Exception as e:
            log_fail("查询文档列表异常", str(e))

        # ════════════════════════════════════════════
        # 7. 调度方案三元组查询（新增 MCP 接口）
        # ════════════════════════════════════════════
        log_section("7. 调度方案三元组查询")

        try:
            resp = await client.get(
                "/api/v1/dispatch/graph/dispatch-triples",
                params={"disaster_name": "漾濞县苍山西镇受灾点"},
                timeout=60.0,
            )
            if resp.status_code == 200:
                result = resp.json()
                if result.get("success"):
                    triples = result.get("triples", [])
                    entities = result.get("entities", {})
                    log_pass(f"三元组查询成功: 共 {len(triples)} 条三元组")
                    log_info(f"  灾区: {entities.get('disaster', {}).get('name', 'N/A')}")
                    log_info(f"  救援队: {len(entities.get('rescue_teams', []))} 个")
                    log_info(f"  仓库: {len(entities.get('warehouses', []))} 个")
                    log_info(f"  避难所: {len(entities.get('shelters', []))} 个")
                    log_info(f"  道路: {len(entities.get('roads', []))} 条")
                    # 显示前5条三元组
                    for t in triples[:5]:
                        log_info(f"    {t.get('subject')} -[{t.get('predicate')}]-> {t.get('object')} ({t.get('object_type')})")
                else:
                    log_fail(f"三元组查询失败: {result.get('message', '')}")
            else:
                log_fail(f"三元组查询请求失败: {resp.status_code}", resp.text[:200])
        except Exception as e:
            log_fail("三元组查询异常", str(e))

        # ════════════════════════════════════════════
        # 8. 清理测试灾情数据
        # ════════════════════════════════════════════
        log_section("8. 清理测试数据")

        try:
            resp = await client.delete(f"/api/v1/resource/disaster-spots/{disaster_id}")
            if resp.status_code == 200:
                log_pass(f"清理测试灾情数据成功: {disaster_id}")
            else:
                log_skip(f"清理测试灾情数据: {resp.status_code} (可能已不存在)")
        except Exception as e:
            log_skip(f"清理测试灾情数据异常: {e}")

        # ════════════════════════════════════════════
        # 测试总结
        # ════════════════════════════════════════════
        log_section("测试总结")
        total = passed + failed + skipped
        print(f"\n  总计: {total}  通过: {GREEN}{passed}{RESET}  失败: {RED}{failed}{RESET}  跳过: {YELLOW}{skipped}{RESET}")
        print(f"  通过率: {passed}/{total} = {passed/total*100:.1f}%\n")

        if failed > 0:
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
