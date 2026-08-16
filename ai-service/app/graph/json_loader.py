"""从本地 JSON 文件加载知识图谱三元组，替代 Neo4j 查询。

数据文件默认指向 backend 的 full_graph_triples.json，路径可通过环境变量
GRAPH_TRIPLES_JSON_PATH 覆盖。
"""
import json
import os
from typing import Dict, List, Optional, Any
from app.core.config import settings
from app.core.logging import logger


class GraphJsonLoader:
    """本地三元组 JSON 加载器"""

    _instance = None
    _data = None
    _triples = None
    _by_subject = None
    _by_subject_type = None
    _incidents_by_id = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._data is None:
            self._load()

    def _default_json_path(self) -> str:
        # 默认指向 ai-service/app 下的 full_graph_triples.json
        # 用户已将图数据库 JSON 文件移动到此目录
        service_root = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..")
        )
        return os.path.join(
            service_root, "app", "full_graph_triples.json"
        )

    def _load(self):
        path = getattr(settings, "GRAPH_TRIPLES_JSON_PATH", None) or self._default_json_path()
        if not os.path.exists(path):
            raise FileNotFoundError(f"图谱 JSON 文件不存在: {path}")

        with open(path, "r", encoding="utf-8") as f:
            self._data = json.load(f)

        self._triples = self._data.get("triples", [])
        self._by_subject: Dict[str, List[Dict[str, Any]]] = {}
        self._by_subject_type: Dict[str, List[Dict[str, Any]]] = {}
        self._incidents_by_id: Dict[int, str] = {}

        for t in self._triples:
            subj = t.get("subject", "")
            stype = t.get("subject_type", "")
            self._by_subject.setdefault(subj, []).append(t)
            self._by_subject_type.setdefault(stype, []).append(t)

        # 建立受灾点 id -> name 索引（predicate 为"编号为"且 object_type 为"受灾点编号"）
        for t in self._triples:
            if (
                t.get("subject_type") == "受灾点"
                and t.get("predicate") == "编号为"
                and t.get("object_type") == "受灾点编号"
            ):
                try:
                    self._incidents_by_id[int(t["object"])] = t["subject"]
                except (ValueError, TypeError):
                    continue

        logger.info(
            f"图谱 JSON 加载完成: {path}, 三元组 {len(self._triples)} 条, "
            f"受灾点 {len(self._incidents_by_id)} 个"
        )

    def reload(self):
        """热重载 JSON 文件"""
        self._data = None
        self._triples = None
        self._by_subject = None
        self._by_subject_type = None
        self._incidents_by_id = None
        self._load()

    @property
    def triples(self) -> List[Dict[str, Any]]:
        return self._triples or []

    @property
    def graph_meta(self) -> Dict[str, Any]:
        return {
            "graph_name": self._data.get("graph_name", ""),
            "version": self._data.get("version", ""),
            "total_triples": len(self._triples or []),
        }

    def get_incident_by_id(self, incident_id: int) -> Optional[str]:
        """根据受灾点编号返回受灾点名称"""
        return self._incidents_by_id.get(incident_id)

    def get_incident_name_by_area(self, area_name: str) -> Optional[str]:
        """按区域名称模糊匹配受灾点"""
        if not area_name:
            return None
        area = area_name.strip()
        # 精确匹配名称
        for name in self._incidents_by_id.values():
            if name == area or name.replace("受灾点", "") == area:
                return name
        # 模糊匹配
        for name in self._incidents_by_id.values():
            short = name.replace("受灾点", "")
            if area in name or area in short or short in area:
                return name
        return None

    def get_subject_properties(self, subject: str) -> Dict[str, Any]:
        """获取某个实体的所有属性和关系值（predicate -> object）"""
        props = {}
        for t in self._by_subject.get(subject, []):
            pred = t.get("predicate", "")
            obj = t.get("object", "")
            props[pred] = obj
        return props

    def get_subjects_by_type(
        self, subject_type: str, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """根据 subject_type 查询所有实体，并返回其属性字典"""
        seen = set()
        results = []
        for t in self._by_subject_type.get(subject_type, []):
            subj = t.get("subject", "")
            if subj in seen or not subj:
                continue
            seen.add(subj)
            props = self.get_subject_properties(subj)
            props["_name"] = subj
            props["_subject_type"] = subject_type
            results.append(props)
            if len(results) >= limit:
                break
        return results

    def list_incidents(self) -> List[Dict[str, Any]]:
        """返回所有受灾点列表（供前端下拉选择）"""
        incidents = []
        for iid, name in sorted(self._incidents_by_id.items()):
            props = self.get_subject_properties(name)
            incidents.append({
                "id": iid,
                "internalId": iid,
                "name": name.replace("受灾点", ""),
                "location": props.get("位于", ""),
                "disasterType": props.get("是", ""),
                "riskLevel": props.get("具备", ""),
                "affectedPeople": int(props.get("涉及", "0") or 0),
                "reportTime": props.get("上报时间", ""),
                "reviewTime": props.get("审核时间", ""),
                "approvalReportTime": props.get("审核同意上报时间", ""),
                "occurredTime": props.get("发生时间", ""),
            })
        return incidents

    def build_triples_text(
        self, incident_names: List[str], include_global: bool = True
    ) -> List[str]:
        """以受灾点为中心生成三元组文本列表"""
        triples = []

        # 受灾点信息
        for name in incident_names:
            props = self.get_subject_properties(name)
            triples.append(f"【受灾点】{name}")
            if "位于" in props:
                triples.append(f"- 受灾点 -[位于]-> 地点 '{props['位于']}'")
            if "是" in props:
                triples.append(f"- 受灾点 -[是]-> 灾害类型 '{props['是']}'")
            if "具备" in props:
                triples.append(f"- 受灾点 -[具备]-> 危险等级 '{props['具备']}'")
            if "涉及" in props:
                triples.append(f"- 受灾点 -[涉及]-> 受灾人数 {props['涉及']}人")
            if "发生时间" in props:
                triples.append(f"- 受灾点 -[发生时间]-> {props['发生时间']}")
            if "上报时间" in props:
                triples.append(f"- 受灾点 -[上报时间]-> {props['上报时间']}")
            if "审核时间" in props:
                triples.append(f"- 受灾点 -[审核时间]-> {props['审核时间']}")
            if "审核同意上报时间" in props:
                triples.append(f"- 受灾点 -[审核同意上报时间]-> {props['审核同意上报时间']}")

        if not include_global:
            return triples

        # 全局资源：仓库
        warehouses = self.get_subjects_by_type("物资仓库", 20)
        if warehouses:
            triples.append("- 【物资仓库】")
            for w in warehouses:
                name = w.get("_name", "未知仓库")
                loc = w.get("位于", "云南省")
                triples.append(f"  - 物资仓库 '{name}' 位于 '{loc}'")

        # 救援队伍
        teams = self.get_subjects_by_type("救援队伍", 20)
        if teams:
            triples.append("- 【救援队伍】")
            for t in teams:
                name = t.get("_name", "未知队伍")
                loc = t.get("位于", "云南省")
                stype = t.get("队伍类型", "")
                good = t.get("擅长", "")
                extra = f"，类型：{stype}" if stype else ""
                if good:
                    extra += f"，擅长：{good}"
                triples.append(f"  - 救援队伍 '{name}' 位于 '{loc}'{extra}")

        # 避难场所
        shelters = self.get_subjects_by_type("避难场所", 20)
        if shelters:
            triples.append("- 【避难场所】")
            for s in shelters:
                name = s.get("_name", "未知避难所")
                loc = s.get("位于", "云南省")
                cap = s.get("最大容纳人数", s.get("承载上限", "未知"))
                triples.append(f"  - 避难场所 '{name}' 位于 '{loc}'，最大容纳 {cap}人")

        # 物资单品
        materials = self.get_subjects_by_type("物资单品", 50)
        if materials:
            triples.append("- 【应急物资/设备（按仓库可分配）】")
            for m in materials:
                name = m.get("_name", "未知物资")
                qty = m.get("数量", "0")
                unit = m.get("单位", "件")
                triples.append(f"  - 物资 '{name}' 库存 {qty}{unit}")

        # 道路
        roads = self.get_subjects_by_type("道路", 10)
        if roads:
            triples.append("- 【道路信息】")
            for rd in roads:
                name = rd.get("_name", "未知道路")
                level = rd.get("道路等级", "")
                status = rd.get("通行状态", "正常")
                triples.append(f"  - 道路 '{name}'，等级：{level}，通行状态：{status}")

        return triples

    def get_full_graph(self) -> Dict[str, Any]:
        """返回完整图谱节点和关系（兼容之前的 full_graph 结构）"""
        nodes = []
        rels = []
        seen_nodes = set()
        for t in self._triples:
            subj = t.get("subject", "")
            obj = t.get("object", "")
            stype = t.get("subject_type", "")
            otype = t.get("object_type", "")
            pred = t.get("predicate", "")
            if subj and subj not in seen_nodes:
                seen_nodes.add(subj)
                nodes.append({
                    "id": len(nodes),
                    "labels": [stype],
                    "label": stype,
                    "properties": {"name": subj},
                })
            if obj and obj not in seen_nodes:
                seen_nodes.add(obj)
                nodes.append({
                    "id": len(nodes),
                    "labels": [otype],
                    "label": otype,
                    "properties": {"name": obj},
                })
            # 关系
            from_idx = next((i for i, n in enumerate(nodes) if n["properties"].get("name") == subj), -1)
            to_idx = next((i for i, n in enumerate(nodes) if n["properties"].get("name") == obj), -1)
            if from_idx >= 0 and to_idx >= 0:
                rels.append({
                    "id": len(rels),
                    "from": from_idx,
                    "to": to_idx,
                    "type": pred,
                    "label": pred,
                    "properties": {},
                    "fromLabel": stype,
                    "toLabel": otype,
                })
        return {
            "nodes": nodes,
            "relationships": rels,
            "nodeCount": len(nodes),
            "relationshipCount": len(rels),
        }


graph_loader = GraphJsonLoader()
