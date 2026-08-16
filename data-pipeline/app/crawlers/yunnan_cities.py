"""云南省各地市/区县 天气后报网站 slug 映射表

数据来源: https://tianqihoubao.com/yubao/yunnan.htm
URL 格式: https://tianqihoubao.com/yubao/{slug}.html
"""

# 云南省 16 个地州市 -> 下辖区县
# 每个地市的第一项是该地市本级的天气页面
YUNNAN_CITIES = {
    "昆明": {
        "code": "530100",
        "districts": [
            ("昆明", "kunming"), ("五华", "ynwuhua"), ("盘龙", "panlong"), ("官渡", "guandu"),
            ("西山", "ynxishan"), ("东川", "dongchuan"), ("呈贡", "chenggong"), ("晋宁", "jinning"),
            ("富民", "fumin"), ("宜良", "ynyiliang"), ("石林", "shilin"), ("嵩明", "songming"),
            ("禄劝", "luquan"), ("寻甸", "xundian"), ("安宁", "anning"), ("太华山", "taihuashan"),
        ],
    },
    "曲靖": {
        "code": "530300",
        "districts": [
            ("曲靖", "qujing"), ("麒麟", "qilin"), ("沾益", "zhanyi"), ("马龙", "malong"),
            ("陆良", "luliang"), ("师宗", "shizong"), ("罗平", "luoping"), ("富源", "ynfuyuan"),
            ("会泽", "huize"), ("宣威", "xuanwei"),
        ],
    },
    "玉溪": {
        "code": "530400",
        "districts": [
            ("玉溪", "yuxi"), ("红塔", "hongta"), ("江川", "jiangchuan"), ("澄江", "chengjiang"),
            ("通海", "tonghai"), ("华宁", "huaning"), ("易门", "yimen"), ("峨山", "eshan"),
            ("新平", "xinping"), ("元江", "hnyuanjiang"),
        ],
    },
    "保山": {
        "code": "530500",
        "districts": [
            ("保山", "baoshan"), ("隆阳", "longyang"), ("施甸", "shidian"), ("龙陵", "longling"),
            ("昌宁", "ynchangning"), ("腾冲", "tengchong"),
        ],
    },
    "昭通": {
        "code": "530600",
        "districts": [
            ("昭通", "zhaotong"), ("昭阳", "zhaoyang"), ("鲁甸", "ludian"), ("巧家", "qiaojia"),
            ("盐津", "ynyanjin"), ("大关", "daguan"), ("永善", "yongshan"), ("绥江", "suijiang"),
            ("镇雄", "zhenxiong"), ("彝良", "yiliang"), ("威信", "weixin"), ("水富", "shuifu"),
        ],
    },
    "丽江": {
        "code": "530700",
        "districts": [
            ("丽江", "lijiang"), ("古城", "yngucheng"), ("玉龙", "yulong"), ("永胜", "yongsheng"),
            ("华坪", "huaping"), ("宁蒗", "ninglang"),
        ],
    },
    "普洱": {
        "code": "530800",
        "districts": [
            ("普洱", "puer"), ("思茅", "simao"), ("宁洱", "ninger"), ("墨江", "mojiang"),
            ("景东", "jingdong"), ("景谷", "jinggu"), ("镇沅", "ynzhenyuan"), ("江城", "jiangcheng"),
            ("孟连", "menglian"), ("澜沧", "lancang"), ("西盟", "ximeng"),
        ],
    },
    "临沧": {
        "code": "530900",
        "districts": [
            ("临沧", "lincang"), ("临翔", "ynlinxiang"), ("凤庆", "fengqing"), ("云县", "yunxian"),
            ("永德", "yongde"), ("镇康", "zhenkang"), ("双江", "shuangjiang"),
            ("耿马", "gengma"), ("沧源", "cangyuan"),
        ],
    },
    "楚雄州": {
        "code": "532300",
        "districts": [
            ("楚雄", "chuxiong"), ("双柏", "shuangbai"), ("牟定", "mouding"), ("南华", "nanhua"),
            ("姚安", "yaoan"), ("大姚", "dayao"), ("永仁", "yongren"), ("元谋", "yuanmou"),
            ("武定", "wuding"), ("禄丰", "lufeng"),
        ],
    },
    "红河州": {
        "code": "532500",
        "districts": [
            ("蒙自", "mengzi"), ("个旧", "gejiu"), ("开远", "kaiyuan"), ("弥勒", "mile"),
            ("建水", "jianshui"), ("石屏", "shiping"), ("泸西", "luxi"), ("元阳", "yuanyang"),
            ("红河", "honghe"), ("绿春", "lvchun"), ("屏边", "pingbian"),
            ("金平", "jinping"), ("河口", "hekou"),
        ],
    },
    "文山州": {
        "code": "532600",
        "districts": [
            ("文山", "wenshan"), ("砚山", "yanshan"), ("西畴", "xichou"), ("麻栗坡", "malipo"),
            ("马关", "maguan"), ("丘北", "qiubei"), ("广南", "guangnan"), ("富宁", "funing"),
        ],
    },
    "西双版纳州": {
        "code": "532800",
        "districts": [
            ("景洪", "jinghong"), ("勐海", "menghai"), ("勐腊", "mengla"),
        ],
    },
    "大理州": {
        "code": "532900",
        "districts": [
            ("大理", "dali"), ("祥云", "xiangyun"), ("宾川", "binchuan"), ("弥渡", "midu"),
            ("永平", "yongping"), ("云龙", "yunlong"), ("洱源", "eryuan"), ("剑川", "jianchuan"),
            ("鹤庆", "heqing"), ("漾濞", "yangbi"), ("南涧", "nanjian"), ("巍山", "weishan"),
        ],
    },
    "德宏州": {
        "code": "533100",
        "districts": [
            ("芒市", "mangshi"), ("瑞丽", "ruili"), ("梁河", "lianghe"), ("盈江", "yingjiang"),
            ("陇川", "longchuan"),
        ],
    },
    "怒江州": {
        "code": "533300",
        "districts": [
            ("泸水", "lushui"), ("福贡", "fugong"), ("贡山", "gongshan"), ("兰坪", "lanping"),
        ],
    },
    "迪庆州": {
        "code": "533400",
        "districts": [
            ("香格里拉", "xianggelila"), ("德钦", "deqin"), ("维西", "weixi"),
        ],
    },
}


def get_all_districts():
    """获取所有区县的 (地市, 区县名, slug) 列表"""
    result = []
    for city_name, info in YUNNAN_CITIES.items():
        for district_name, slug in info["districts"]:
            result.append({
                "city": city_name,
                "city_code": info["code"],
                "district": district_name,
                "slug": slug,
                "url": f"https://tianqihoubao.com/yubao/{slug}.html",
            })
    return result


def get_city_list():
    """获取地市列表"""
    return [{"name": k, "code": v["code"]} for k, v in YUNNAN_CITIES.items()]


def get_districts_by_city(city_name):
    """根据地市获取下辖区县"""
    city = YUNNAN_CITIES.get(city_name)
    if not city:
        return []
    return [
        {"name": d[0], "slug": d[1], "url": f"https://tianqihoubao.com/yubao/{d[1]}.html"}
        for d in city["districts"]
    ]


def find_slug_by_name(name):
    """根据区县名查找 slug"""
    for city_name, info in YUNNAN_CITIES.items():
        for district_name, slug in info["districts"]:
            if district_name == name or city_name == name:
                return slug
    return None
