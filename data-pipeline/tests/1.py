import json

# ====================== 原始图谱数据（与原脚本完全一致）======================
# 1. 受灾点
disaster_list = [
    {"name": "东川区铜都街道受灾点", "location": "昆明市东川区铜都街道", "type": "泥石流灾害风险", "level": 4, "people": 1200},
    {"name": "墨江县联珠镇受灾点", "location": "普洱市墨江县联珠镇", "type": "暴雨灾害风险", "level": 2, "people": 740},
]

# 2. 物资仓库
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

# 物资单品
material_items = [
    {"name": "帐篷", "num": 500, "disaster": "通用"},
    {"name": "折叠床", "num": 800, "disaster": "通用"},
    {"name": "睡袋", "num": 1200, "disaster": "通用"},
    {"name": "简易厕所", "num": 60, "disaster": "通用"},
    {"name": "防寒毛毯", "num": 2000, "disaster": "通用"},
    {"name": "防潮垫", "num": 1500, "disaster": "通用"},
    {"name": "移动卫生间", "num": 35, "disaster": "通用"},
    {"name": "垃圾桶", "num": 300, "disaster": "通用"},
    {"name": "救生衣", "num": 2000, "disaster": "暴雨/洪涝/山洪灾害"},
    {"name": "橡皮艇", "num": 120, "disaster": "暴雨/洪涝/山洪灾害"},
    {"name": "编织沙袋", "num": 50000, "disaster": "暴雨/洪涝/山洪灾害"},
    {"name": "抽水泵", "num": 150, "disaster": "暴雨/洪涝/山洪灾害"},
    {"name": "防水雨衣", "num": 3000, "disaster": "暴雨/洪涝/山洪灾害"},
    {"name": "雨靴", "num": 2500, "disaster": "暴雨/洪涝/山洪灾害"},
    {"name": "救生绳", "num": 800, "disaster": "暴雨/洪涝/山洪灾害"},
    {"name": "土工布", "num": 6000, "disaster": "暴雨/洪涝/山洪灾害"},
    {"name": "救生圈", "num": 400, "disaster": "暴雨/洪涝/山洪灾害"},
    {"name": "撬棍", "num": 300, "disaster": "滑坡/泥石流/崩塌/地震灾害"},
    {"name": "切割机", "num": 80, "disaster": "滑坡/泥石流/崩塌/地震灾害"},
    {"name": "安全帽", "num": 1500, "disaster": "滑坡/泥石流/崩塌/地震灾害"},
    {"name": "滑坡监测简易测桩", "num": 200, "disaster": "滑坡/泥石流/崩塌/地震灾害"},
    {"name": "生命探测仪", "num": 25, "disaster": "滑坡/泥石流/崩塌/地震灾害"},
    {"name": "支撑顶杆", "num": 180, "disaster": "滑坡/泥石流/崩塌/地震灾害"},
    {"name": "液压破拆工具组", "num": 45, "disaster": "滑坡/泥石流/崩塌/地震灾害"},
    {"name": "安全绳", "num": 600, "disaster": "滑坡/泥石流/崩塌/地震灾害"},
    {"name": "裂缝观测尺", "num": 120, "disaster": "滑坡/泥石流/崩塌/地震灾害"},
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

# 3. 救援队伍
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

# 4. 避难场所
shelters = [
    {"name": "昆明市体育中心避难场所", "place_name": "昆明市体育中心", "location": "昆明市呈贡区", "max": 50000, "accommodated": 0},
    {"name": "昭通市望海公园应急避难场所", "place_name": "望海公园应急避难广场", "location": "昭通市昭阳区", "max": 20000, "accommodated": 0},
    {"name": "大理州全民健身中心避难场所", "place_name": "大理州全民健身中心", "location": "大理州大理市", "max": 30000, "accommodated": 0},
    {"name": "怒江州六库公园避难所", "place_name": "六库中央公园", "location": "怒江州泸水市", "max": 12000, "accommodated": 0},
    {"name": "保山市三馆文化广场避难所", "place_name": "三馆文化广场", "location": "保山市隆阳区", "max": 18000, "accommodated": 0},
    {"name": "红河州州政府广场避难场所", "place_name": "红河州政府广场", "location": "红河州蒙自市", "max": 25000, "accommodated": 0},
    {"name": "曲靖市珠江源广场避难所", "place_name": "珠江源广场", "location": "曲靖市麒麟区", "max": 22000, "accommodated": 0},
    {"name": "丽江市红太阳广场避难场所", "place_name": "红太阳广场", "location": "丽江市古城区", "max": 15000, "accommodated": 0},
    {"name": "东川区和平广场应急避难场所", "place_name": "和平广场应急避难场所", "location": "昆明市东川区", "max": 8000, "accommodated": 0},
    {"name": "彝良县行政中心避难广场", "place_name": "彝良县行政中心广场", "location": "昭通市彝良县", "max": 5000, "accommodated": 0},
    {"name": "贡山县民族文化广场避难所", "place_name": "贡山县民族文化广场", "location": "怒江州贡山县", "max": 3000, "accommodated": 0},
    {"name": "漾濞县人和广场避难场所", "place_name": "漾濞县人和广场", "location": "大理州漾濞县", "max": 4000, "accommodated": 0},
    {"name": "会泽县会泽公园避难所", "place_name": "会泽公园", "location": "曲靖市会泽县", "max": 6000, "accommodated": 0},
    {"name": "腾冲市腾越文化广场避难所", "place_name": "腾越文化广场", "location": "保山市腾冲市", "max": 12000, "accommodated": 0},
    {"name": "元阳县南沙广场避难所", "place_name": "南沙民族广场", "location": "红河州元阳县", "max": 4500, "accommodated": 0},
    {"name": "禄劝县民族文化广场避难所", "place_name": "禄劝民族文化广场", "location": "昆明市禄劝县", "max": 5500, "accommodated": 0},
    {"name": "巧家县堂琅广场避难场所", "place_name": "堂琅文化广场", "location": "昭通市巧家县", "max": 4200, "accommodated": 0},
    {"name": "镇雄县赤水源广场避难所", "place_name": "赤水源广场", "location": "昭通市镇雄县", "max": 7000, "accommodated": 0},
    {"name": "香格里拉市坛城广场避难所", "place_name": "坛城文化广场", "location": "迪庆州香格里拉市", "max": 8500, "accommodated": 0},
    {"name": "德钦县升平广场避难所", "place_name": "升平镇文化广场", "location": "迪庆州德钦县", "max": 2000, "accommodated": 0},
    {"name": "澜沧县佛房广场避难所", "place_name": "佛房文化广场", "location": "普洱市澜沧县", "max": 3800, "accommodated": 0},
    {"name": "墨江县太阳广场避难所", "place_name": "太阳广场", "location": "普洱市墨江县", "max": 4800, "accommodated": 0}
]

# 5. 道路
roads = [
    {"name": "G56杭瑞高速", "no": "G56", "road_name": "杭瑞高速公路", "level": "高速公路", "status": "畅通", "limit": 49000, "cost": 80},
    {"name": "G85银昆高速", "no": "G85", "road_name": "银昆高速公路", "level": "高速公路", "status": "畅通", "limit": 49000, "cost": 75},
    {"name": "G8511昆磨高速", "no": "G8511", "road_name": "昆磨高速公路", "level": "高速公路", "status": "畅通", "limit": 49000, "cost": 78},
    {"name": "G78汕昆高速", "no": "G78", "road_name": "汕昆高速公路", "level": "高速公路", "status": "畅通", "limit": 49000, "cost": 82},
    {"name": "G80广昆高速", "no": "G80", "road_name": "广昆高速公路", "level": "高速公路", "status": "畅通", "limit": 49000, "cost": 85},
    {"name": "G5615天猴高速", "no": "G5615", "road_name": "天猴高速公路", "level": "高速公路", "status": "畅通", "limit": 49000, "cost": 90},
    {"name": "G4216蓉丽高速", "no": "G4216", "road_name": "蓉丽高速公路", "level": "高速公路", "status": "畅通", "limit": 49000, "cost": 95},
    {"name": "G0613西丽高速", "no": "G0613", "road_name": "西丽高速公路", "level": "高速公路", "status": "畅通", "limit": 49000, "cost": 92},
    {"name": "G320国道", "no": "G320", "road_name": "320国道", "level": "国道", "status": "畅通", "limit": 30000, "cost": 110},
    {"name": "G213国道", "no": "G213", "road_name": "213国道", "level": "国道", "status": "畅通", "limit": 30000, "cost": 105},
    {"name": "G326国道", "no": "G326", "road_name": "326国道", "level": "国道", "status": "半阻断", "limit": 25000, "cost": 130},
    {"name": "G214国道", "no": "G214", "road_name": "214国道", "level": "国道", "status": "畅通", "limit": 30000, "cost": 115},
    {"name": "G353国道", "no": "G353", "road_name": "353国道", "level": "国道", "status": "半阻断", "limit": 20000, "cost": 125},
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

# 道路连通关系
road_connections = [
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

# 6. 实体与道路关联
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

# ====================== 批量生成三元组 ======================
triples = []

# 1. 受灾点
for item in disaster_list:
    triples.append({"subject": item["name"], "subject_type": "受灾点", "predicate": "位于", "object": item["location"], "object_type": "地点名称"})
    triples.append({"subject": item["name"], "subject_type": "受灾点", "predicate": "是", "object": item["type"], "object_type": "灾害类型"})
    triples.append({"subject": item["name"], "subject_type": "受灾点", "predicate": "具备", "object": str(item["level"]), "object_type": "危险等级"})
    triples.append({"subject": item["name"], "subject_type": "受灾点", "predicate": "涉及", "object": str(item["people"]), "object_type": "受灾人数"})

# 2. 物资仓库
for wh in warehouses:
    triples.append({"subject": wh["name"], "subject_type": "物资仓库", "predicate": "位于", "object": wh["location"], "object_type": "地点"})
    triples.append({"subject": wh["name"], "subject_type": "物资仓库", "predicate": "拥有", "object": "应急物资总类", "object_type": "物资"})

# 物资单品
for item in material_items:
    triples.append({"subject": "应急物资总类", "subject_type": "物资", "predicate": "包含", "object": item["name"], "object_type": "物资单品"})
    triples.append({"subject": item["name"], "subject_type": "物资单品", "predicate": "适用于", "object": item["disaster"], "object_type": "适用灾害"})
    triples.append({"subject": item["name"], "subject_type": "物资单品", "predicate": "有", "object": str(item["num"]), "object_type": "数量"})

# 3. 救援队伍
for team in teams:
    triples.append({"subject": team["name"], "subject_type": "救援队伍", "predicate": "位于", "object": team["location"], "object_type": "地点名称"})
    triples.append({"subject": team["name"], "subject_type": "救援队伍", "predicate": "是", "object": team["type"], "object_type": "队伍类型"})
    triples.append({"subject": team["name"], "subject_type": "救援队伍", "predicate": "最大运载重量", "object": str(team["weight"]), "object_type": "最大运载重量"})
    triples.append({"subject": team["name"], "subject_type": "救援队伍", "predicate": "擅长", "object": team["good_at"], "object_type": "擅长灾害"})
    triples.append({"subject": team["name"], "subject_type": "救援队伍", "predicate": "状态", "object": team["status"], "object_type": "状态"})

# 4. 避难场所
for sh in shelters:
    triples.append({"subject": sh["name"], "subject_type": "避难场所", "predicate": "是", "object": sh["place_name"], "object_type": "场所名称"})
    triples.append({"subject": sh["name"], "subject_type": "避难场所", "predicate": "位于", "object": sh["location"], "object_type": "地点"})
    triples.append({"subject": sh["name"], "subject_type": "避难场所", "predicate": "最大容纳人数", "object": str(sh["max"]), "object_type": "最大容纳人数"})
    triples.append({"subject": sh["name"], "subject_type": "避难场所", "predicate": "已容纳人数", "object": str(sh["accommodated"]), "object_type": "已容纳人数"})

# 5. 道路属性
for road in roads:
    triples.append({"subject": road["name"], "subject_type": "道路", "predicate": "编号为", "object": road["no"], "object_type": "道路编号"})
    triples.append({"subject": road["name"], "subject_type": "道路", "predicate": "命名为", "object": road["road_name"], "object_type": "道路名称"})
    triples.append({"subject": road["name"], "subject_type": "道路", "predicate": "属于", "object": road["level"], "object_type": "道路等级"})
    triples.append({"subject": road["name"], "subject_type": "道路", "predicate": "当前通行", "object": road["status"], "object_type": "通行状态"})
    triples.append({"subject": road["name"], "subject_type": "道路", "predicate": "承载上限", "object": str(road["limit"]), "object_type": "承载上限"})
    triples.append({"subject": road["name"], "subject_type": "道路", "predicate": "通行代价", "object": str(road["cost"]), "object_type": "距离成本"})

# 道路双向连通
for r1, r2 in road_connections:
    triples.append({"subject": r1, "subject_type": "道路", "predicate": "连通", "object": r2, "object_type": "道路"})
    triples.append({"subject": r2, "subject_type": "道路", "predicate": "连通", "object": r1, "object_type": "道路"})

# 6. 实体-道路关联
all_entity_road = point_road + warehouse_road + team_road + shelter_road
for entity, road in all_entity_road:
    if "受灾点" in entity or "镇" in entity:
        s_type = "受灾点"
    elif "储备库" in entity:
        s_type = "物资仓库"
    elif "队" in entity:
        s_type = "救援队伍"
    else:
        s_type = "避难场所"
    triples.append({"subject": entity, "subject_type": s_type, "predicate": "临近", "object": road, "object_type": "道路"})
    triples.append({"subject": road, "subject_type": "道路", "predicate": "服务", "object": entity, "object_type": s_type})

# ====================== 输出JSON文件 ======================
result = {
    "graph_name": "云南自然灾害应急资源知识图谱",
    "version": "1.0",
    "total_triples": len(triples),
    "triples": triples
}

with open("full_graph_triples.json", "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print(f"✅ 导出完成！共 {len(triples)} 条三元组")
print(f"文件已保存：full_graph_triples.json")
