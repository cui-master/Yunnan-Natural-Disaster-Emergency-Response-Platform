"""天气后报爬虫 - 爬取 tianqihoubao.com 云南各地市/区县天气预报

功能：
- 爬取指定城市的天气预报（昨天、今天、明天、后天）
- 解析白昼/夜间天气、气温、风力风向
- 返回结构化数据供前端展示

数据来源: https://tianqihoubao.com/yubao/{slug}.html
"""

from typing import List, Dict, Optional
from datetime import datetime, timedelta
import re
import asyncio
import random

import httpx
from bs4 import BeautifulSoup

from app.core.logging import logger
from app.crawlers.yunnan_cities import (
    YUNNAN_CITIES,
    get_all_districts,
    get_city_list,
    get_districts_by_city,
    find_slug_by_name,
)


# 浏览器指纹池
UA_POOL = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
]

BASE_URL = "https://tianqihoubao.com/yubao/{slug}.html"
TIMEOUT = httpx.Timeout(connect=10.0, read=20.0, write=5.0, pool=10.0)
MAX_RETRIES = 3


def _build_headers() -> dict:
    return {
        "User-Agent": random.choice(UA_POOL),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Referer": "https://tianqihoubao.com/yubao/yunnan.htm",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0",
    }


async def fetch_weather(slug: str) -> Dict:
    """爬取指定 slug 的天气预报

    Args:
        slug: 城市 slug，例如 "qujing"

    Returns:
        {
            "city": "曲靖",
            "slug": "qujing",
            "fetched_at": "2026-07-25 10:30:00",
            "forecast": [
                {
                    "date": "2026-07-24",
                    "day_weather": "阴",
                    "day_temp": "26℃",
                    "day_wind": "北风 1-3级",
                    "night_weather": "多云",
                    "night_temp": "17℃",
                    "night_wind": "北风 1-3级",
                },
                ...
            ]
        }
    """
    url = BASE_URL.format(slug=slug)
    logger.info(f"[weather] 爬取天气: {url}")

    async with httpx.AsyncClient(
        timeout=TIMEOUT,
        follow_redirects=True,
        headers=_build_headers(),
        http2=False,
    ) as client:
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                # 每次重试更换 UA 和指纹，降低被识别概率
                response = await client.get(url, headers=_build_headers())

                if response.status_code in (521, 403):
                    wait = 5 * attempt + random.uniform(1, 3)
                    logger.warning(
                        f"[weather] 收到 {response.status_code}，"
                        f"重试 {attempt}/{MAX_RETRIES}，等 {wait:.1f}s"
                    )
                    await asyncio.sleep(wait)
                    continue

                if response.status_code >= 400:
                    return {
                        "city": slug,
                        "slug": slug,
                        "error": f"HTTP {response.status_code}",
                        "fetched_at": datetime.now().isoformat(timespec="seconds"),
                        "forecast": [],
                    }

                response.raise_for_status()
                break

            except (httpx.ConnectError, httpx.ReadTimeout) as e:
                logger.warning(f"[weather] 请求失败 ({attempt}/{MAX_RETRIES}): {e}")
                if attempt < MAX_RETRIES:
                    await asyncio.sleep(2 * attempt)
                    continue
                return {
                    "city": slug,
                    "slug": slug,
                    "error": f"请求失败: {e}",
                    "fetched_at": datetime.now().isoformat(timespec="seconds"),
                    "forecast": [],
                }
        else:
            return {
                "city": slug,
                "slug": slug,
                "error": "重试次数耗尽",
                "fetched_at": datetime.now().isoformat(timespec="seconds"),
                "forecast": [],
            }

    # 解析 HTML
    return parse_weather_html(response.text, slug)


def parse_weather_html(html: str, slug: str) -> Dict:
    """解析天气页面 HTML

    页面结构：
    <table>
      <tr>
        <th colspan=2>日期</th>
        <th>天气状况</th>
        <th>气温</th>
        <th>风力风向</th>
      </tr>
      <tr>
        <td rowspan=2>2026-07-19</td>
        <td>白天</td>
        <td>阴</td>
        <td>26℃</td>
        <td>北风 1-3级</td>
      </tr>
      <tr>
        <td>夜间</td>
        <td>多云</td>
        <td>17℃</td>
        <td>北风 1-3级</td>
      </tr>
      ...
    </table>
    """
    soup = BeautifulSoup(html, "html.parser")

    # 提取城市名（页面标题：xxx天气预报查询）
    title_text = ""
    h1 = soup.find("h1")
    if h1:
        title_text = h1.get_text(strip=True)
    city_name = slug
    m = re.match(r"^(.+?)天气预报", title_text)
    if m:
        city_name = m.group(1)

    # 找到数据表格
    table = soup.find("table")
    if not table:
        logger.warning(f"[weather] 未找到表格: {slug}")
        return {
            "city": city_name,
            "slug": slug,
            "fetched_at": datetime.now().isoformat(timespec="seconds"),
            "forecast": [],
            "error": "未找到数据表格",
        }

    forecast = []
    current_date = None
    current_entry = None

    rows = table.find_all("tr")
    # 跳过表头行
    for row in rows[1:]:
        cells = row.find_all(["td", "th"])
        if not cells:
            continue

        # 获取所有单元格文本
        texts = [c.get_text(strip=True) for c in cells]

        # 判断是否为新的一天（第一列含日期）
        first_cell = cells[0]
        first_text = texts[0]

        # 检查是否包含日期格式
        date_match = re.search(r"(\d{4}-\d{2}-\d{2})", first_text)

        if date_match:
            # 新的一天
            if current_entry:
                forecast.append(current_entry)

            current_date = date_match.group(1)

            # 判断该行是白天还是夜间
            # 格式1: [日期, 白天/夜间, 天气, 气温, 风力] - 5列
            # 格式2: [日期, 白天, 天气, 气温, 风力] + 下一行 [夜间, 天气, 气温, 风力] - rowspan
            period = "白天"
            if len(texts) >= 5:
                period = texts[1] if texts[1] in ("白天", "夜间") else "白天"

            current_entry = {
                "date": current_date,
                "day_weather": "",
                "day_temp": "",
                "day_wind": "",
                "night_weather": "",
                "night_temp": "",
                "night_wind": "",
            }

            # 填充数据
            weather_idx = 2 if len(texts) >= 5 else 1
            temp_idx = 3 if len(texts) >= 5 else 2
            wind_idx = 4 if len(texts) >= 5 else 3

            if period == "白天":
                current_entry["day_weather"] = texts[weather_idx] if weather_idx < len(texts) else ""
                current_entry["day_temp"] = texts[temp_idx] if temp_idx < len(texts) else ""
                current_entry["day_wind"] = texts[wind_idx] if wind_idx < len(texts) else ""
            else:
                current_entry["night_weather"] = texts[weather_idx] if weather_idx < len(texts) else ""
                current_entry["night_temp"] = texts[temp_idx] if temp_idx < len(texts) else ""
                current_entry["night_wind"] = texts[wind_idx] if wind_idx < len(texts) else ""

        elif current_entry and len(texts) >= 4:
            # 续行（夜间数据，rowspan 情况）
            period = texts[0] if texts[0] in ("白天", "夜间") else "夜间"

            weather_idx = 1
            temp_idx = 2
            wind_idx = 3

            if period == "白天":
                current_entry["day_weather"] = texts[weather_idx]
                current_entry["day_temp"] = texts[temp_idx]
                current_entry["day_wind"] = texts[wind_idx]
            else:
                current_entry["night_weather"] = texts[weather_idx]
                current_entry["night_temp"] = texts[temp_idx]
                current_entry["night_wind"] = texts[wind_idx]

    # 添加最后一条
    if current_entry:
        forecast.append(current_entry)

    # 解析日期，过滤出昨天到后天
    forecast = _filter_recent_days(forecast)

    logger.info(f"[weather] {city_name} 解析到 {len(forecast)} 天天气数据")

    return {
        "city": city_name,
        "slug": slug,
        "fetched_at": datetime.now().isoformat(timespec="seconds"),
        "forecast": forecast,
    }


def _filter_recent_days(forecast: List[Dict]) -> List[Dict]:
    """过滤出昨天、今天、明天、后天的天气数据

    tianqihoubao 的预报页面通常包含 4 天数据：昨天、今天、明天、后天
    """
    if not forecast:
        return []

    today = datetime.now().date()
    target_dates = {
        (today - timedelta(days=1)).strftime("%Y-%m-%d"),  # 昨天
        today.strftime("%Y-%m-%d"),                          # 今天
        (today + timedelta(days=1)).strftime("%Y-%m-%d"),    # 明天
        (today + timedelta(days=2)).strftime("%Y-%m-%d"),    # 后天
    }

    filtered = []
    for item in forecast:
        if item.get("date") in target_dates:
            # 添加日期标签
            date_obj = datetime.strptime(item["date"], "%Y-%m-%d").date()
            delta = (date_obj - today).days
            if delta == -1:
                item["date_label"] = "昨天"
            elif delta == 0:
                item["date_label"] = "今天"
            elif delta == 1:
                item["date_label"] = "明天"
            elif delta == 2:
                item["date_label"] = "后天"
            else:
                item["date_label"] = item["date"]
            # 添加星期
            week_days = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
            item["weekday"] = week_days[date_obj.weekday()]
            filtered.append(item)

    # 如果没匹配到，返回全部（兜底）
    if not filtered:
        return forecast[:4]

    return filtered


async def fetch_weather_by_name(name: str) -> Dict:
    """根据城市/区县名爬取天气

    Args:
        name: 城市/区县名，例如 "曲靖" 或 "麒麟"

    Returns:
        天气数据字典
    """
    slug = find_slug_by_name(name)
    if not slug:
        return {
            "city": name,
            "slug": None,
            "error": f"未找到城市: {name}",
            "fetched_at": datetime.now().isoformat(timespec="seconds"),
            "forecast": [],
        }
    return await fetch_weather(slug)


async def fetch_multiple_cities(names: List[str]) -> List[Dict]:
    """批量爬取多个城市天气（带限流）"""
    results = []
    for idx, name in enumerate(names):
        result = await fetch_weather_by_name(name)
        results.append(result)
        if idx < len(names) - 1:
            await asyncio.sleep(random.uniform(2.0, 4.0))  # 增加限流，降低被封概率
    return results


def get_yunnan_city_tree() -> Dict:
    """获取云南城市树状结构（地市 -> 区县）"""
    tree = []
    for city_name, info in YUNNAN_CITIES.items():
        districts = [
            {"name": d[0], "slug": d[1]}
            for d in info["districts"]
        ]
        tree.append({
            "city": city_name,
            "code": info["code"],
            "districts": districts,
        })
    return {"provinces": "云南", "cities": tree}
