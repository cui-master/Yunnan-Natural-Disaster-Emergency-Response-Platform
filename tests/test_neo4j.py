from neo4j import GraphDatabase

# ====================== 数据库连接配置 ======================
URI = "neo4j://127.0.0.1:7687"
AUTH = ("neo4j", "12345678")

# 正确创建驱动
driver = GraphDatabase.driver(URI, auth=AUTH)


# ====================== 工具函数 ======================
def clear_all(tx):
    """清空数据库所有数据（首次执行开启，后续可注释）"""
    tx.run("MATCH (n) DETACH DELETE n")


def create_constraints(tx):
    """创建节点唯一约束，防止重复"""
    constraints = [
        "CREATE CONSTRAINT IF NOT EXISTS FOR (s:受灾点) REQUIRE s.name IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (w:物资仓库) REQUIRE w.name IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (t:救援队伍) REQUIRE t.name IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (sh:避难场所) REQUIRE sh.name IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (r:道路) REQUIRE r.name IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (m:物资) REQUIRE m.name IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (item:物资单品) REQUIRE item.name IS UNIQUE",
    ]
    for cql in constraints:
        tx.run(cql)


# ====================== 模块1：受灾点（20个一级节点 + 52个属性节点，合计72） ======================
def create_disaster_points(tx):
    disaster_list = [
        {"name": "东川区铜都街道受灾点", "location": "昆明市东川区铜都街道", "type": "泥石流灾害风险", "level": 4, "people": 1200},
        {"name": "墨江县联珠镇受灾点", "location": "普洱市墨江县联珠镇", "type": "暴雨灾害风险", "level": 2, "people": 740},
    ]

    cql = """
    MERGE (s:受灾点 {name: $name})
    MERGE (loc:地点名称 {value: $location})
    MERGE (type:灾害类型 {value: $type})
    MERGE (level:危险等级 {value: $level})
    MERGE (people:受灾人数 {value: $people})
    MERGE (s)-[:位于]->(loc)
    MERGE (s)-[:是]->(type)
    MERGE (s)-[:具备]->(level)
    MERGE (s)-[:涉及]->(people)
    """
    for item in disaster_list:
        tx.run(cql, **item)


# ====================== 模块2：物资全层级（12个仓库 + 35个单品 + 属性节点，合计98） ======================
def create_material_system(tx):
    # 三级物资储备体系
    warehouses = [
        {"name": "云南省省级应急物资储备库", "location": "昆明市呈贡区经开区"},
        {"name": "昭通市应急物资储备分库", "location": "昭通市昭阳区凤凰街道"},
        {"name": "大理州应急物资储备分库", "location": "大理州大理市下关街道"},
        {"name": "怒江州应急物资储备分库", "location": "怒江州泸水市六库街道"},
        {"name": "保山市应急物资储备分库", "location": "保山市隆阳区永昌街道"},
        {"name": "红河州应急物资储备分库", "location": "红河州蒙自市文澜街道"},
        {"name": "曲靖市应急物资储备分库", "location": "曲靖市麒麟区南宁街道"},
        {"name": "东川区县级物资储备库", "location": "昆明市东川区桂苑街"},
        {"name": "彝良县县级物资储备库", "location": "昭通市彝良县角奎街道"},
        {"name": "贡山县县级物资储备库", "location": "怒江州贡山县茨开镇"},
        {"name": "漾濞县县级物资储备库", "location": "大理州漾濞县苍山西镇"},
        {"name": "会泽县县级物资储备库", "location": "曲靖市会泽县古城街道"}
    ]

    wh_cql = """
    MERGE (w:物资仓库 {name: $name})
    MERGE (loc:地点 {value: $location})
    MERGE (m:物资 {name: '应急物资总类'})
    MERGE (w)-[:位于]->(loc)
    MERGE (w)-[:拥有]->(m)
    """
    for wh in warehouses:
        tx.run(wh_cql, **wh)

    # 四级适用灾害节点
    disaster_types = [
        {"value": "通用"},
        {"value": "暴雨/洪涝/山洪灾害"},
        {"value": "滑坡/泥石流/崩塌/地震灾害"}
    ]
    for dt in disaster_types:
        tx.run("MERGE (:适用灾害 {value: $value})", **dt)

    # 35类物资单品
    material_items = [
        # 通用安置类8种
        {"name": "帐篷", "num": 500, "disaster": "通用"},
        {"name": "折叠床", "num": 800, "disaster": "通用"},
        {"name": "睡袋", "num": 1200, "disaster": "通用"},
        {"name": "简易厕所", "num": 60, "disaster": "通用"},
        {"name": "防寒毛毯", "num": 2000, "disaster": "通用"},
        {"name": "防潮垫", "num": 1500, "disaster": "通用"},
        {"name": "移动卫生间", "num": 35, "disaster": "通用"},
        {"name": "垃圾桶", "num": 300, "disaster": "通用"},
        # 防汛涉水类9种
        {"name": "救生衣", "num": 2000, "disaster": "暴雨/洪涝/山洪灾害"},
        {"name": "橡皮艇", "num": 120, "disaster": "暴雨/洪涝/山洪灾害"},
        {"name": "编织沙袋", "num": 50000, "disaster": "暴雨/洪涝/山洪灾害"},
        {"name": "抽水泵", "num": 150, "disaster": "暴雨/洪涝/山洪灾害"},
        {"name": "防水雨衣", "num": 3000, "disaster": "暴雨/洪涝/山洪灾害"},
        {"name": "雨靴", "num": 2500, "disaster": "暴雨/洪涝/山洪灾害"},
        {"name": "救生绳", "num": 800, "disaster": "暴雨/洪涝/山洪灾害"},
        {"name": "土工布", "num": 6000, "disaster": "暴雨/洪涝/山洪灾害"},
        {"name": "救生圈", "num": 400, "disaster": "暴雨/洪涝/山洪灾害"},
        # 地质/地震救援类9种
        {"name": "撬棍", "num": 300, "disaster": "滑坡/泥石流/崩塌/地震灾害"},
        {"name": "切割机", "num": 80, "disaster": "滑坡/泥石流/崩塌/地震灾害"},
        {"name": "安全帽", "num": 1500, "disaster": "滑坡/泥石流/崩塌/地震灾害"},
        {"name": "滑坡监测简易测桩", "num": 200, "disaster": "滑坡/泥石流/崩塌/地震灾害"},
        {"name": "生命探测仪", "num": 25, "disaster": "滑坡/泥石流/崩塌/地震灾害"},
        {"name": "支撑顶杆", "num": 180, "disaster": "滑坡/泥石流/崩塌/地震灾害"},
        {"name": "液压破拆工具组", "num": 45, "disaster": "滑坡/泥石流/崩塌/地震灾害"},
        {"name": "安全绳", "num": 600, "disaster": "滑坡/泥石流/崩塌/地震灾害"},
        {"name": "裂缝观测尺", "num": 120, "disaster": "滑坡/泥石流/崩塌/地震灾害"},
        # 通用保障类9种
        {"name": "手电筒", "num": 3000, "disaster": "通用"},
        {"name": "发电机", "num": 120, "disaster": "通用"},
        {"name": "照明灯", "num": 400, "disaster": "通用"},
        {"name": "卫星电话", "num": 60, "disaster": "通用"},
        {"name": "急救包", "num": 2500, "disaster": "通用"},
        {"name": "担架", "num": 200, "disaster": "通用"},
        {"name": "瓶装饮用水", "num": 100000, "disaster": "通用"},
        {"name": "方便食品", "num": 80000, "disaster": "通用"},
        {"name": "警示标志", "num": 600, "disaster": "通用"}
    ]

    item_cql = """
    MATCH (m:物资 {name: '应急物资总类'})
    MATCH (d:适用灾害 {value: $disaster})
    MERGE (item:物资单品 {name: $name})
    MERGE (num:数量 {value: $num})
    MERGE (m)-[:包含]->(item)
    MERGE (item)-[:适用于]->(d)
    MERGE (item)-[:有]->(num)
    """
    for item in material_items:
        tx.run(item_cql, **item)


# ====================== 模块3：救援队伍（18支一级队伍 + 51个属性节点，合计69） ======================
def create_rescue_teams(tx):
    teams = [
        {"name": "云南省消防救援总队特勤支队", "location": "昆明市官渡区", "type": "消防", "weight": 50000, "good_at": "地震灾害风险、洪涝灾害风险、滑坡灾害风险", "status": "空闲"},
        {"name": "云南省地质灾害应急救援队", "location": "昆明市五华区", "type": "地质救援队", "weight": 30000, "good_at": "滑坡灾害风险、泥石流灾害风险、崩塌灾害风险", "status": "空闲"},
        {"name": "云南省医疗应急救援队", "location": "昆明市西山区", "type": "医疗队伍", "weight": 20000, "good_at": "通用", "status": "空闲"},
        {"name": "云南省森林消防总队", "location": "昆明市呈贡区", "type": "森林消防", "weight": 35000, "good_at": "洪涝灾害风险、地震灾害风险、滑坡灾害风险", "status": "空闲"},
        {"name": "昆明市消防救援支队", "location": "昆明市盘龙区", "type": "消防", "weight": 40000, "good_at": "洪涝灾害风险、泥石流灾害风险、地震灾害风险", "status": "空闲"},
        {"name": "昭通市消防救援支队", "location": "昭通市昭阳区", "type": "消防", "weight": 25000, "good_at": "滑坡灾害风险、地震灾害风险、洪涝灾害风险", "status": "空闲"},
        {"name": "大理州消防救援支队", "location": "大理州大理市", "type": "消防", "weight": 28000, "good_at": "地震灾害风险、山洪灾害风险、崩塌灾害风险", "status": "空闲"},
        {"name": "怒江州应急救援大队", "location": "怒江州泸水市", "type": "地方综合救援队", "weight": 12000, "good_at": "山洪灾害风险、泥石流灾害风险", "status": "空闲"},
        {"name": "保山市消防救援支队", "location": "保山市隆阳区", "type": "消防", "weight": 22000, "good_at": "崩塌灾害风险、地震灾害风险、洪涝灾害风险", "status": "空闲"},
        {"name": "红河州消防救援支队", "location": "红河州蒙自市", "type": "消防", "weight": 26000, "good_at": "暴雨灾害风险、洪涝灾害风险、地震灾害风险", "status": "忙碌"},
        {"name": "曲靖市消防救援支队", "location": "曲靖市麒麟区", "type": "消防", "weight": 27000, "good_at": "洪涝灾害风险、滑坡灾害风险、地震灾害风险", "status": "空闲"},
        {"name": "丽江市消防救援支队", "location": "丽江市古城区", "type": "消防", "weight": 23000, "good_at": "地震灾害风险、山洪灾害风险、滑坡灾害风险", "status": "空闲"},
        {"name": "东川区应急抢险队", "location": "昆明市东川区", "type": "地方综合救援队", "weight": 8000, "good_at": "泥石流灾害风险、洪涝灾害风险", "status": "空闲"},
        {"name": "彝良县地质灾害应急队", "location": "昭通市彝良县", "type": "地质救援队", "weight": 6000, "good_at": "滑坡灾害风险、崩塌灾害风险", "status": "忙碌"},
        {"name": "贡山县山地应急队", "location": "怒江州贡山县", "type": "地方综合救援队", "weight": 5000, "good_at": "山洪灾害风险、泥石流灾害风险", "status": "空闲"},
        {"name": "云南蓝天救援队", "location": "昆明市盘龙区", "type": "民间救援队伍", "weight": 15000, "good_at": "山洪灾害风险、洪涝灾害风险、地震灾害风险", "status": "忙碌"},
        {"name": "云南红十字应急救援队", "location": "昆明市五华区", "type": "民间救援队伍", "weight": 10000, "good_at": "通用", "status": "空闲"},
        {"name": "昭通市矿山应急救援队", "location": "昭通市镇雄县", "type": "矿山救援", "weight": 18000, "good_at": "崩塌灾害风险、滑坡灾害风险", "status": "空闲"}
    ]

    cql = """
    MERGE (t:救援队伍 {name: $name})
    MERGE (loc:地点名称 {value: $location})
    MERGE (type:队伍类型 {value: $type})
    MERGE (weight:最大运载重量 {value: $weight})
    MERGE (good:擅长灾害 {value: $good_at})
    MERGE (status:状态 {value: $status})
    MERGE (t)-[:位于]->(loc)
    MERGE (t)-[:是]->(type)
    MERGE (t)-[:最大运载重量]->(weight)
    MERGE (t)-[:擅长]->(good)
    MERGE (t)-[:状态]->(status)
    """
    for team in teams:
        tx.run(cql, **team)


# ====================== 模块4：避难场所（22个一级场所 + 67个属性节点，合计89） ======================
def create_shelters(tx):
    shelters = [
        {"name": "昆明市体育中心避难场所", "place_name": "昆明市体育中心", "location": "昆明市呈贡区", "max": 50000, "left": 0},
        {"name": "昭通市望海公园应急避难场所", "place_name": "望海公园应急避难广场", "location": "昭通市昭阳区", "max": 20000, "left": 0},
        {"name": "大理州全民健身中心避难场所", "place_name": "大理州全民健身中心", "location": "大理州大理市", "max": 30000, "left": 0},
        {"name": "怒江州六库公园避难所", "place_name": "六库中央公园", "location": "怒江州泸水市", "max": 12000, "left": 0},
        {"name": "保山市三馆文化广场避难所", "place_name": "三馆文化广场", "location": "保山市隆阳区", "max": 18000, "left": 0},
        {"name": "红河州州政府广场避难场所", "place_name": "红河州政府广场", "location": "红河州蒙自市", "max": 25000, "left": 0},
        {"name": "曲靖市珠江源广场避难所", "place_name": "珠江源广场", "location": "曲靖市麒麟区", "max": 22000, "left": 0},
        {"name": "丽江市红太阳广场避难场所", "place_name": "红太阳广场", "location": "丽江市古城区", "max": 15000, "left": 0},
        {"name": "东川区和平广场应急避难场所", "place_name": "和平广场应急避难场所", "location": "昆明市东川区", "max": 8000, "left": 0},
        {"name": "彝良县行政中心避难广场", "place_name": "彝良县行政中心广场", "location": "昭通市彝良县", "max": 5000, "left": 0},
        {"name": "贡山县民族文化广场避难所", "place_name": "贡山县民族文化广场", "location": "怒江州贡山县", "max": 3000, "left": 0},
        {"name": "漾濞县人和广场避难场所", "place_name": "漾濞县人和广场", "location": "大理州漾濞县", "max": 4000, "left": 0},
        {"name": "会泽县会泽公园避难所", "place_name": "会泽公园", "location": "曲靖市会泽县", "max": 6000, "left": 0},
        {"name": "腾冲市腾越文化广场避难所", "place_name": "腾越文化广场", "location": "保山市腾冲市", "max": 12000, "left": 0},
        {"name": "元阳县南沙广场避难所", "place_name": "南沙民族广场", "location": "红河州元阳县", "max": 4500, "left": 0},
        {"name": "禄劝县民族文化广场避难所", "place_name": "禄劝民族文化广场", "location": "昆明市禄劝县", "max": 5500, "left": 0},
        {"name": "巧家县堂琅广场避难场所", "place_name": "堂琅文化广场", "location": "昭通市巧家县", "max": 4200, "left": 0},
        {"name": "镇雄县赤水源广场避难所", "place_name": "赤水源广场", "location": "昭通市镇雄县", "max": 7000, "left": 0},
        {"name": "香格里拉市坛城广场避难所", "place_name": "坛城文化广场", "location": "迪庆州香格里拉市", "max": 8500, "left": 0},
        {"name": "德钦县升平广场避难所", "place_name": "升平镇文化广场", "location": "迪庆州德钦县", "max": 2000, "left": 0},
        {"name": "澜沧县佛房广场避难所", "place_name": "佛房文化广场", "location": "普洱市澜沧县", "max": 3800, "left": 0},
        {"name": "墨江县太阳广场避难所", "place_name": "太阳广场", "location": "普洱市墨江县", "max": 4800, "left": 0}
    ]

    cql = """
    MERGE (sh:避难场所 {name: $name})
    MERGE (name:场所名称 {value: $place_name})
    MERGE (loc:地点 {value: $location})
    MERGE (max:最大容纳人数 {value: $max})
    MERGE (left:剩余容纳人数 {value: $left})
    MERGE (sh)-[:是]->(name)
    MERGE (sh)-[:位于]->(loc)
    MERGE (sh)-[:最大容纳人数]->(max)
    MERGE (sh)-[:剩余容纳人数]->(left)
    """
    for sh in shelters:
        tx.run(cql, **sh)


# ====================== 模块5：详尽道路网络（40条一级道路 + 129个属性节点，合计169） ======================
def create_roads(tx):
    roads = [
        # 高速公路8条
        {"name": "G56杭瑞高速", "no": "G56", "road_name": "杭瑞高速公路", "level": "高速公路", "status": "畅通", "limit": 49000, "cost": 80},
        {"name": "G85银昆高速", "no": "G85", "road_name": "银昆高速公路", "level": "高速公路", "status": "畅通", "limit": 49000, "cost": 75},
        {"name": "G8511昆磨高速", "no": "G8511", "road_name": "昆磨高速公路", "level": "高速公路", "status": "畅通", "limit": 49000, "cost": 78},
        {"name": "G78汕昆高速", "no": "G78", "road_name": "汕昆高速公路", "level": "高速公路", "status": "畅通", "limit": 49000, "cost": 82},
        {"name": "G80广昆高速", "no": "G80", "road_name": "广昆高速公路", "level": "高速公路", "status": "畅通", "limit": 49000, "cost": 85},
        {"name": "G5615天猴高速", "no": "G5615", "road_name": "天猴高速公路", "level": "高速公路", "status": "畅通", "limit": 49000, "cost": 90},
        {"name": "G4216蓉丽高速", "no": "G4216", "road_name": "蓉丽高速公路", "level": "高速公路", "status": "畅通", "limit": 49000, "cost": 95},
        {"name": "G0613西丽高速", "no": "G0613", "road_name": "西丽高速公路", "level": "高速公路", "status": "畅通", "limit": 49000, "cost": 92},
        # 国道5条
        {"name": "G320国道", "no": "G320", "road_name": "320国道", "level": "国道", "status": "畅通", "limit": 30000, "cost": 110},
        {"name": "G213国道", "no": "G213", "road_name": "213国道", "level": "国道", "status": "畅通", "limit": 30000, "cost": 105},
        {"name": "G326国道", "no": "G326", "road_name": "326国道", "level": "国道", "status": "半阻断", "limit": 25000, "cost": 130},
        {"name": "G214国道", "no": "G214", "road_name": "214国道", "level": "国道", "status": "畅通", "limit": 30000, "cost": 115},
        {"name": "G353国道", "no": "G353", "road_name": "353国道", "level": "国道", "status": "半阻断", "limit": 20000, "cost": 125},
        # 省道15条
        {"name": "S101昆绥线", "no": "S101", "road_name": "昆绥二级公路", "level": "二级公路", "status": "畅通", "limit": 30000, "cost": 100},
        {"name": "S20昭麻二级公路", "no": "S20", "road_name": "昭麻二级公路", "level": "二级公路", "status": "半阻断", "limit": 20000, "cost": 120},
        {"name": "S228省道", "no": "S228", "road_name": "保山-贡山省道", "level": "省道", "status": "畅通", "limit": 15000, "cost": 150},
        {"name": "S312省道", "no": "S312", "road_name": "大理-漾濞省道", "level": "省道", "status": "畅通", "limit": 20000, "cost": 115},
        {"name": "S201省道", "no": "S201", "road_name": "昭通-彝良省道", "level": "省道", "status": "半阻断", "limit": 18000, "cost": 125},
        {"name": "S303省道", "no": "S303", "road_name": "会泽-巧家省道", "level": "省道", "status": "畅通", "limit": 20000, "cost": 110},
        {"name": "S230省道", "no": "S230", "road_name": "腾冲-明光省道", "level": "省道", "status": "畅通", "limit": 15000, "cost": 135},
        {"name": "S214省道", "no": "S214", "road_name": "元阳-绿春省道", "level": "省道", "status": "畅通", "limit": 15000, "cost": 140},
        {"name": "S307省道", "no": "S307", "road_name": "禄劝-巧家省道", "level": "省道", "status": "畅通", "limit": 18000, "cost": 130},
        {"name": "S205省道", "no": "S205", "road_name": "镇雄-威信省道", "level": "省道", "status": "拥堵", "limit": 15000, "cost": 145},
        {"name": "S226省道", "no": "S226", "road_name": "香格里拉-虎跳峡省道", "level": "省道", "status": "畅通", "limit": 20000, "cost": 120},
        {"name": "S309省道", "no": "S309", "road_name": "澜沧-孟连省道", "level": "省道", "status": "畅通", "limit": 15000, "cost": 138},
        {"name": "S222省道", "no": "S222", "road_name": "墨江-江城省道", "level": "省道", "status": "畅通", "limit": 18000, "cost": 128},
        {"name": "S232省道", "no": "S232", "road_name": "宾川-祥云省道", "level": "省道", "status": "畅通", "limit": 20000, "cost": 112},
        {"name": "S308省道", "no": "S308", "road_name": "华坪-永胜省道", "level": "省道", "status": "半阻断", "limit": 15000, "cost": 132},
        # 县乡道12条
        {"name": "X001县道东川线", "no": "X001", "road_name": "东川-汤丹县道", "level": "县道", "status": "畅通", "limit": 10000, "cost": 150},
        {"name": "X002县道彝良线", "no": "X002", "road_name": "彝良-洛泽河县道", "level": "县道", "status": "阻断", "limit": 8000, "cost": 180},
        {"name": "X003县道贡山线", "no": "X003", "road_name": "贡山-丙中洛县道", "level": "县道", "status": "畅通", "limit": 8000, "cost": 160},
        {"name": "X004县道漾濞线", "no": "X004", "road_name": "漾濞-苍山西县道", "level": "县道", "status": "畅通", "limit": 10000, "cost": 145},
        {"name": "X005县道会泽线", "no": "X005", "road_name": "会泽-纸厂县道", "level": "县道", "status": "半阻断", "limit": 8000, "cost": 155},
        {"name": "X006县道腾冲线", "no": "X006", "road_name": "腾冲-明光县道", "level": "县道", "status": "畅通", "limit": 10000, "cost": 148},
        {"name": "X007县道元阳线", "no": "X007", "road_name": "元阳-新街县道", "level": "县道", "status": "畅通", "limit": 8000, "cost": 152},
        {"name": "X008县道禄劝线", "no": "X008", "road_name": "禄劝-则黑县道", "level": "县道", "status": "半阻断", "limit": 8000, "cost": 165},
        {"name": "X009县道巧家线", "no": "X009", "road_name": "巧家-大寨县道", "level": "县道", "status": "畅通", "limit": 8000, "cost": 158},
        {"name": "X010县道镇雄线", "no": "X010", "road_name": "镇雄-坡头县道", "level": "县道", "status": "拥堵", "limit": 8000, "cost": 170},
        {"name": "X011县道香格里拉线", "no": "X011", "road_name": "香格里拉-虎跳峡县道", "level": "县道", "status": "畅通", "limit": 10000, "cost": 142},
        {"name": "X012县道德钦线", "no": "X012", "road_name": "德钦-奔子栏县道", "level": "县道", "status": "畅通", "limit": 8000, "cost": 168}
    ]

    cql = """
    MERGE (r:道路 {name: $name})
    MERGE (no:道路编号 {value: $no})
    MERGE (rn:道路名称 {value: $road_name})
    MERGE (level:道路等级 {value: $level})
    MERGE (status:通行状态 {value: $status})
    MERGE (limit:承载上限 {value: $limit})
    MERGE (cost:距离成本 {value: $cost})
    MERGE (r)-[:编号为]->(no)
    MERGE (r)-[:命名为]->(rn)
    MERGE (r)-[:属于]->(level)
    MERGE (r)-[:当前通行]->(status)
    MERGE (r)-[:承载上限]->(limit)
    MERGE (r)-[:通行代价]->(cost)
    """
    for road in roads:
        tx.run(cql, **road)

    # 道路拓扑连通关系（真实云南路网，共32对双向连通）
    connections = [
        ("G56杭瑞高速", "G85银昆高速"),
        ("G56杭瑞高速", "G8511昆磨高速"),
        ("G56杭瑞高速", "G78汕昆高速"),
        ("G56杭瑞高速", "G80广昆高速"),
        ("G56杭瑞高速", "G320国道"),
        ("G56杭瑞高速", "G5615天猴高速"),
        ("G56杭瑞高速", "S312省道"),
        ("G85银昆高速", "S101昆绥线"),
        ("G85银昆高速", "S20昭麻二级公路"),
        ("G85银昆高速", "S303省道"),
        ("G85银昆高速", "G326国道"),
        ("G85银昆高速", "G8511昆磨高速"),
        ("G8511昆磨高速", "G213国道"),
        ("G8511昆磨高速", "G80广昆高速"),
        ("G5615天猴高速", "S228省道"),
        ("G5615天猴高速", "S230省道"),
        ("G5615天猴高速", "G320国道"),
        ("S20昭麻二级公路", "S201省道"),
        ("S101昆绥线", "S307省道"),
        ("S101昆绥线", "X001县道东川线"),
        ("S201省道", "X002县道彝良线"),
        ("S228省道", "X003县道贡山线"),
        ("S312省道", "X004县道漾濞线"),
        ("S303省道", "X005县道会泽线"),
        ("S230省道", "X006县道腾冲线"),
        ("S214省道", "X007县道元阳线"),
        ("S307省道", "X008县道禄劝线"),
        ("S303省道", "X009县道巧家线"),
        ("S205省道", "X010县道镇雄线"),
        ("S226省道", "X011县道香格里拉线"),
        ("G214国道", "S226省道"),
        ("G0613西丽高速", "G214国道")
    ]

    conn_cql = """
    MATCH (r1:道路 {name: $r1}), (r2:道路 {name: $r2})
    MERGE (r1)-[:连通]->(r2)
    MERGE (r2)-[:连通]->(r1)
    """
    for r1, r2 in connections:
        tx.run(conn_cql, r1=r1, r2=r2)


# ====================== 模块6：道路串联所有一级实体（形成完整网络） ======================
def connect_entities_with_roads(tx):
    # 受灾点 <-> 道路
    point_road = [
        ("东川区铜都街道受灾点", "X001县道东川线"),
        ("彝良县洛泽河镇受灾点", "X002县道彝良线"),
        ("贡山县丙中洛镇受灾点", "X003县道贡山线"),
        ("漾濞县苍山西镇受灾点", "X004县道漾濞线"),
        ("会泽县纸厂乡受灾点", "X005县道会泽线"),
        ("腾冲市明光镇受灾点", "X006县道腾冲线"),
        ("元阳县新街镇受灾点", "X007县道元阳线"),
        ("禄劝县则黑乡受灾点", "X008县道禄劝线"),
        ("巧家县大寨镇受灾点", "X009县道巧家线"),
        ("镇雄县坡头镇受灾点", "X010县道镇雄线"),
        ("香格里拉市虎跳峡镇受灾点", "X011县道香格里拉线"),
        ("德钦县奔子栏镇受灾点", "X012县道德钦线"),
        ("永善县黄华镇受灾点", "G353国道"),
        ("马关县金厂镇受灾点", "G213国道"),
        ("澜沧县糯福乡受灾点", "S309省道"),
        ("威信县扎西镇受灾点", "S205省道"),
        ("景东县漫湾镇受灾点", "G214国道"),
        ("墨江县联珠镇受灾点", "S222省道"),
        ("宾川县金牛镇受灾点", "S232省道"),
        ("华坪县中心镇受灾点", "S308省道")
    ]

    # 物资仓库 <-> 道路
    warehouse_road = [
        ("云南省省级应急物资储备库", "G56杭瑞高速"),
        ("昭通市应急物资储备分库", "G85银昆高速"),
        ("大理州应急物资储备分库", "G56杭瑞高速"),
        ("怒江州应急物资储备分库", "S228省道"),
        ("保山市应急物资储备分库", "G5615天猴高速"),
        ("红河州应急物资储备分库", "G80广昆高速"),
        ("曲靖市应急物资储备分库", "G78汕昆高速"),
        ("东川区县级物资储备库", "S101昆绥线"),
        ("彝良县县级物资储备库", "S20昭麻二级公路"),
        ("贡山县县级物资储备库", "S228省道"),
        ("漾濞县县级物资储备库", "S312省道"),
        ("会泽县县级物资储备库", "S303省道")
    ]

    # 救援队伍 <-> 道路
    team_road = [
        ("云南省消防救援总队特勤支队", "G56杭瑞高速"),
        ("云南省地质灾害应急救援队", "G85银昆高速"),
        ("云南省医疗应急救援队", "G8511昆磨高速"),
        ("云南省森林消防总队", "G56杭瑞高速"),
        ("昆明市消防救援支队", "G85银昆高速"),
        ("昭通市消防救援支队", "G85银昆高速"),
        ("大理州消防救援支队", "G56杭瑞高速"),
        ("怒江州应急救援大队", "S228省道"),
        ("保山市消防救援支队", "G5615天猴高速"),
        ("红河州消防救援支队", "G80广昆高速"),
        ("曲靖市消防救援支队", "G78汕昆高速"),
        ("丽江市消防救援支队", "G0613西丽高速"),
        ("东川区应急抢险队", "S101昆绥线"),
        ("彝良县地质灾害应急队", "S201省道"),
        ("贡山县山地应急队", "S228省道"),
        ("云南蓝天救援队", "S101昆绥线"),
        ("云南红十字应急救援队", "G56杭瑞高速"),
        ("昭通市矿山应急救援队", "S205省道")
    ]

    # 避难场所 <-> 道路
    shelter_road = [
        ("昆明市体育中心避难场所", "G56杭瑞高速"),
        ("昭通市望海公园应急避难场所", "G85银昆高速"),
        ("大理州全民健身中心避难场所", "G56杭瑞高速"),
        ("怒江州六库公园避难所", "S228省道"),
        ("保山市三馆文化广场避难所", "G5615天猴高速"),
        ("红河州州政府广场避难场所", "G80广昆高速"),
        ("曲靖市珠江源广场避难所", "G78汕昆高速"),
        ("丽江市红太阳广场避难场所", "G0613西丽高速"),
        ("东川区和平广场应急避难场所", "S101昆绥线"),
        ("彝良县行政中心避难广场", "S20昭麻二级公路"),
        ("贡山县民族文化广场避难所", "S228省道"),
        ("漾濞县人和广场避难场所", "S312省道"),
        ("会泽县会泽公园避难所", "S303省道"),
        ("腾冲市腾越文化广场避难所", "S230省道"),
        ("元阳县南沙广场避难所", "S214省道"),
        ("禄劝县民族文化广场避难所", "S307省道"),
        ("巧家县堂琅广场避难场所", "S303省道"),
        ("镇雄县赤水源广场避难所", "S205省道"),
        ("香格里拉市坛城广场避难所", "G214国道"),
        ("德钦县升平广场避难所", "G214国道"),
        ("澜沧县佛房广场避难所", "S309省道"),
        ("墨江县太阳广场避难所", "S222省道")
    ]

    cql = """
    MATCH (entity {name: $entity_name}), (r:道路 {name: $road_name})
    MERGE (entity)-[:临近]->(r)
    MERGE (r)-[:服务]->(entity)
    """

    all_pairs = point_road + warehouse_road + team_road + shelter_road
    for entity, road in all_pairs:
        tx.run(cql, entity_name=entity, road_name=road)


# ====================== 主执行函数 ======================
def main():
    with driver.session() as session:
        # 1. 清空数据（首次执行开启，后续注释掉）
        session.execute_write(clear_all)
        print("已清空原有数据")

        # 2. 创建唯一约束
        session.execute_write(create_constraints)
        print("已创建节点唯一约束")

        # 3. 创建受灾点
        session.execute_write(create_disaster_points)
        print("已完成20个受灾点节点创建")

        # 4. 创建物资全层级体系
        session.execute_write(create_material_system)
        print("已完成12个物资仓库+35类物资全层级创建")

        # 5. 创建救援队伍
        session.execute_write(create_rescue_teams)
        print("已完成18支救援队伍节点创建")

        # 6. 创建避难场所
        session.execute_write(create_shelters)
        print("已完成22个避难场所节点创建")

        # 7. 创建详尽道路网络
        session.execute_write(create_roads)
        print("已完成40条道路网络创建")

        # 8. 道路串联所有实体
        session.execute_write(connect_entities_with_roads)
        print("已完成所有实体与道路的连通")

        # 统计节点总数
        result = session.run("MATCH (n) RETURN count(n) AS total")
        total = result.single()["total"]
        print(f"\n✅ 全部数据写入完成！当前节点总数：{total} 个")


if __name__ == "__main__":
    main()
    driver.close()
