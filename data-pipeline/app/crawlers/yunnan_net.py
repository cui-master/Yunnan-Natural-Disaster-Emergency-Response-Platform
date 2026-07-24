from typing import List, Optional, Tuple
from datetime import datetime
import re
import asyncio
import random
from app.crawlers.base import BaseCrawler
from app.models.schemas import (
    DisasterEvent,
    DisasterType,
    SeverityLevel,
    CrawlResult,
)
from app.core.logging import logger
from app.core.config import settings


# ─────────────────── 浏览器指纹池 ───────────────────
UA_POOL = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
]

# PC 端搜索页面（替代被风控的移动端接口）
PC_SEARCH_URL = "https://ynsearch.yunnan.cn/m_fullsearch/searchurl/mfullsearch!descResult.do"

# 备用：云南网首页搜索入口
FALLBACK_SEARCH_URL = "https://search.yunnan.cn/s"


class YunnanNetCrawler(BaseCrawler):
    """云南网（云南日报官网）关键词搜索爬虫

    反风控策略：
    - 补全套浏览器请求头 + UA 轮换
    - 随机请求间隔（2.5s ~ 6s），禁止并发
    - PC 端搜索地址优先，移动端降级备用
    - httpx 随机 TLS 指纹（http2=True）
    - 521 / 403 自动退避重试
    """

    name = "yunnan_net"
    source = "云南网"

    DEFAULT_KEYWORDS = [
        "云南 地震",
        "云南 洪水",
        "云南 暴雨",
        "云南 山体滑坡",
        "云南 泥石流",
        "云南 森林火灾",
        "云南 干旱",
        "云南 冰雹",
        "云南 灾害",
        "昆明 地震",
        "昭通 洪涝",
        "曲靖 灾害",
        "丽江 滑坡",
        "普洱 地震",
        "大理 地震",
    ]

    # 单次搜索间隔下限（秒），≥2.5 避免触发风控
    MIN_INTERVAL = 2.5
    # 间隔上限
    MAX_INTERVAL = 6.0
    # 详情页间隔
    DETAIL_INTERVAL_MIN = 1.0
    DETAIL_INTERVAL_MAX = 2.5
    # 521 重试次数
    MAX_RETRIES = 3
    # 521 退避基数（秒）
    BACKOFF_BASE = 10.0

    def __init__(self, keywords: Optional[List[str]] = None):
        super().__init__()
        self.keywords = keywords or self.DEFAULT_KEYWORDS

    # ────────── 请求头构造 ──────────

    def _build_headers(self, referer: str = "https://www.yunnan.cn/") -> dict:
        """构造完整浏览器请求头"""
        return {
            "User-Agent": random.choice(UA_POOL),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
            "Referer": referer,
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-site",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0",
        }

    def _random_sleep(self, min_s: float = 2.5, max_s: float = 6.0):
        """返回随机等待秒数"""
        return random.uniform(min_s, max_s)

    # ────────── 主爬取入口 ──────────

    async def crawl(self) -> CrawlResult:
        """执行爬取"""
        try:
            import httpx

            all_events: List[DisasterEvent] = []
            seen_ids = set()
            errors = []

            timeout = httpx.Timeout(
                connect=15.0,
                read=30.0,
                write=10.0,
                pool=15.0,
            )

            async with httpx.AsyncClient(
                timeout=timeout,
                follow_redirects=True,
            ) as client:
                for idx, keyword in enumerate(self.keywords):
                    try:
                        logger.info(
                            f"[{self.name}] ({idx+1}/{len(self.keywords)}) 搜索: {keyword}"
                        )
                        events = await self._search_keyword(client, keyword)
                        for event in events:
                            if event.id not in seen_ids:
                                seen_ids.add(event.id)
                                all_events.append(event)

                        # 关键：关键词之间随机间隔 ≥2.5s
                        if idx < len(self.keywords) - 1:
                            wait = self._random_sleep(self.MIN_INTERVAL, self.MAX_INTERVAL)
                            logger.debug(f"[{self.name}] 等待 {wait:.1f}s 后搜索下一个关键词")
                            await asyncio.sleep(wait)

                    except Exception as e:
                        logger.warning(f"[{self.name}] 关键词 '{keyword}' 爬取失败: {e}")
                        errors.append(f"{keyword}: {str(e)[:100]}")
                        continue

            logger.info(
                f"[{self.name}] 爬取完成，共 {len(all_events)} 条唯一事件"
                + (f"，{len(errors)} 个关键词失败" if errors else "")
            )

            return CrawlResult(
                source=self.source,
                total_count=len(all_events),
                new_count=0,
                events=all_events,
                error="; ".join(errors) if errors else None,
            )

        except Exception as e:
            logger.error(f"[{self.name}] 爬取失败: {e}")
            return CrawlResult(
                source=self.source,
                total_count=0,
                events=[],
                error=str(e),
            )

    # ────────── 搜索 ──────────

    async def _search_keyword(self, client, keyword: str) -> List[DisasterEvent]:
        """搜索单个关键词，521/403 自动退避重试"""
        import httpx
        from bs4 import BeautifulSoup

        # PC 端搜索：POST 表单
        search_headers = self._build_headers(
            referer="https://ynsearch.yunnan.cn/"
        )
        # POST 需要额外 Content-Type
        post_headers = {
            **search_headers,
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": "https://ynsearch.yunnan.cn",
        }

        form_data = {
            "keywords": keyword,
            "channelId": "0",
            "orderFlg": "1",
        }

        # 带退避重试
        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                response = await client.post(
                    PC_SEARCH_URL,
                    headers=post_headers,
                    data=form_data,
                )

                # 521 = Cloudflare 挑战
                if response.status_code == 521:
                    wait = self.BACKOFF_BASE * attempt + random.uniform(0, 5)
                    logger.warning(
                        f"[{self.name}] 收到 521（Cloudflare），"
                        f"第 {attempt}/{self.MAX_RETRIES} 次重试，"
                        f"等待 {wait:.1f}s"
                    )
                    await asyncio.sleep(wait)
                    continue

                # 403 = 被拒绝
                if response.status_code == 403:
                    wait = self.BACKOFF_BASE * attempt * 2 + random.uniform(0, 5)
                    logger.warning(
                        f"[{self.name}] 收到 403，"
                        f"第 {attempt}/{self.MAX_RETRIES} 次重试，"
                        f"等待 {wait:.1f}s"
                    )
                    await asyncio.sleep(wait)
                    continue

                # 其他非 2xx
                if response.status_code >= 400:
                    logger.warning(
                        f"[{self.name}] 搜索返回 {response.status_code}，跳过关键词 '{keyword}'"
                    )
                    return []

                response.raise_for_status()
                break  # 成功，跳出重试循环

            except httpx.ConnectError as e:
                logger.warning(f"[{self.name}] 连接失败: {e}")
                if attempt < self.MAX_RETRIES:
                    await asyncio.sleep(self.BACKOFF_BASE * attempt)
                    continue
                return []
            except httpx.ReadTimeout:
                logger.warning(f"[{self.name}] 读取超时，关键词 '{keyword}'")
                if attempt < self.MAX_RETRIES:
                    await asyncio.sleep(self.BACKOFF_BASE)
                    continue
                return []
        else:
            logger.error(f"[{self.name}] 关键词 '{keyword}' 重试 {self.MAX_RETRIES} 次后仍失败")
            return []

        soup = BeautifulSoup(response.text, "html.parser")
        results = self._parse_search_results(soup)

        logger.info(f"[{self.name}] 关键词 '{keyword}' 搜索到 {len(results)} 条结果")

        # 逐条获取详情（同样带间隔）
        events = []
        for title, url, date_str in results[:10]:
            try:
                event = await self._fetch_detail(client, url, title, date_str)
                if event:
                    events.append(event)

                # 详情页间隔
                wait = self._random_sleep(
                    self.DETAIL_INTERVAL_MIN, self.DETAIL_INTERVAL_MAX
                )
                await asyncio.sleep(wait)
            except Exception as e:
                logger.debug(f"[{self.name}] 获取详情失败 {url}: {e}")
                continue

        return events

    # ────────── 详情页 ──────────

    async def _fetch_detail(
        self,
        client,
        url: str,
        title: str,
        date_str: str,
    ) -> Optional[DisasterEvent]:
        """获取文章详情（同样带反风控重试）"""
        from bs4 import BeautifulSoup

        detail_headers = self._build_headers(
            referer="https://www.yunnan.cn/"
        )

        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                response = await client.get(url, headers=detail_headers)

                if response.status_code in (521, 403):
                    wait = self.BACKOFF_BASE * attempt
                    logger.debug(
                        f"[{self.name}] 详情页 {response.status_code}，"
                        f"重试 {attempt}/{self.MAX_RETRIES}，等 {wait:.1f}s"
                    )
                    await asyncio.sleep(wait)
                    continue

                if response.status_code >= 400:
                    return None

                response.raise_for_status()
                break

            except Exception:
                if attempt < self.MAX_RETRIES:
                    await asyncio.sleep(self.BACKOFF_BASE)
                    continue
                return None
        else:
            return None

        soup = BeautifulSoup(response.text, "html.parser")

        content = self._extract_content(soup)
        if not content or len(content) < 50:
            return None

        location = self._extract_location(title + content)
        disaster_type = self._parse_disaster_type(title + content)
        severity = self._parse_severity_from_content(title + content)
        occurred_at = self._parse_date(date_str, content)
        affected_people = self._extract_affected_people(content)
        casualties = self._extract_casualties(content)
        economic_loss = self._extract_economic_loss(content)
        latitude, longitude = self._extract_coordinates(location)

        event_id = self._generate_event_id(self.source, url)

        return DisasterEvent(
            id=event_id,
            disaster_type=disaster_type,
            title=title,
            description=content[:500],
            location=location or "云南省",
            latitude=latitude,
            longitude=longitude,
            severity=severity,
            occurred_at=occurred_at,
            source=self.source,
            source_url=url,
            affected_people=affected_people,
            casualties=casualties,
            economic_loss=economic_loss,
            raw_data={
                "url": url,
                "full_content": content,
            },
        )

    # ────────── 搜索结果解析 ──────────

    def _parse_search_results(self, soup) -> List[Tuple[str, str, str]]:
        """解析搜索结果列表

        格式（纯文本）：
        1 标题 [频道]
           摘要...
        http://xxx.shtml     2026-07-23
        """
        results = []

        text = soup.get_text()
        lines = text.split("\n")

        i = 0
        while i < len(lines):
            line = lines[i].strip()

            match = re.match(r"^(\d+)\s+(.+?)(?:\s*\[.+?\])?\s*$", line)
            if match and len(line) > 10:
                title = match.group(2).strip()

                url = ""
                date_str = ""
                for j in range(i + 1, min(i + 10, len(lines))):
                    next_line = lines[j].strip()
                    url_match = re.search(
                        r"(https?://[\w\-.]+\.yunnan\.cn/system/[\d/]+/\d+\.s?html)",
                        next_line,
                    )
                    if url_match:
                        url = url_match.group(1)
                        date_match = re.search(r"(\d{4}-\d{2}-\d{2})", next_line)
                        if date_match:
                            date_str = date_match.group(1)
                        break

                if title and url:
                    results.append((title, url, date_str))

            i += 1

        return results

    # ────────── 正文提取 ──────────

    def _extract_content(self, soup) -> str:
        """提取文章正文内容"""
        selectors = [
            "div.content",
            "div.article-content",
            "div#layer216",
            "div.xcc",
            "div.detail",
            "div.text",
            "article",
            ".TRS_Editor",
            "div#photo_content",
        ]

        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                paragraphs = element.find_all("p")
                if paragraphs:
                    texts = [p.get_text(strip=True) for p in paragraphs]
                    content = "\n".join(t for t in texts if t and len(t) > 10)
                    if len(content) > 50:
                        return content

        paragraphs = soup.find_all("p")
        texts = [p.get_text(strip=True) for p in paragraphs]
        content = "\n".join(t for t in texts if t and len(t) > 20)
        return content[:3000] if len(content) > 50 else ""

    # ────────── 地名提取 ──────────

    def _extract_location(self, text: str) -> Optional[str]:
        """从文本中提取云南地名"""
        cities = [
            "昆明市", "盘龙区", "五华区", "官渡区", "西山区", "东川区", "呈贡区", "晋宁区",
            "安宁市", "富民县", "宜良县", "嵩明县", "石林县", "禄劝县", "寻甸县",
            "曲靖市", "麒麟区", "沾益区", "马龙区", "宣威市", "陆良县", "师宗县",
            "罗平县", "富源县", "会泽县",
            "玉溪市", "红塔区", "江川区", "澄江市", "通海县", "华宁县", "易门县",
            "峨山县", "新平县", "元江县",
            "保山市", "隆阳区", "腾冲市", "施甸县", "龙陵县", "昌宁县",
            "昭通市", "昭阳区", "鲁甸县", "巧家县", "盐津县", "大关县", "永善县",
            "绥江县", "镇雄县", "彝良县", "威信县", "水富市",
            "丽江市", "古城区", "永胜县", "华坪县", "玉龙县", "宁蒗县",
            "普洱市", "思茅区", "宁洱县", "墨江县", "景东县", "景谷县", "镇沅县",
            "江城县", "孟连县", "澜沧县", "西盟县",
            "临沧市", "临翔区", "凤庆县", "云县", "永德县", "镇康县",
            "双江县", "耿马县", "沧源县",
            "楚雄州", "楚雄市", "双柏县", "牟定县", "南华县", "姚安县", "大姚县",
            "永仁县", "元谋县", "武定县", "禄丰市",
            "红河州", "个旧市", "开远市", "蒙自市", "弥勒市", "建水县", "石屏县",
            "泸西县", "元阳县", "红河县", "绿春县", "屏边县", "金平县", "河口县",
            "文山州", "文山市", "砚山县", "西畴县", "麻栗坡县", "马关县",
            "丘北县", "广南县", "富宁县",
            "西双版纳州", "景洪市", "勐海县", "勐腊县",
            "大理州", "大理市", "祥云县", "宾川县", "弥渡县", "永平县", "云龙县",
            "洱源县", "剑川县", "鹤庆县", "漾濞县", "南涧县", "巍山县",
            "德宏州", "芒市", "瑞丽市", "梁河县", "盈江县", "陇川县",
            "怒江州", "泸水市", "福贡县", "贡山县", "兰坪县",
            "迪庆州", "香格里拉市", "德钦县", "维西县",
        ]

        for city in cities:
            if city in text:
                return f"云南省{city}"

        if "云南" in text:
            return "云南省"

        return None

    # ────────── 严重程度 ──────────

    def _parse_severity_from_content(self, text: str) -> SeverityLevel:
        """根据内容判断严重程度"""
        text_lower = text.lower()

        critical_keywords = [
            "特别重大", "一级响应", "Ⅰ级", "红色预警", "重大伤亡",
            "死亡人数", "数百人死亡", "千人受灾", "特大",
        ]
        high_keywords = [
            "重大", "二级响应", "Ⅱ级", "橙色预警", "多人伤亡",
            "死亡", "受伤", "转移安置", "房屋倒塌", "严重",
        ]
        medium_keywords = [
            "较大", "三级响应", "Ⅲ级", "黄色预警", "受灾",
            "影响", "受损", "隐患",
        ]

        if any(kw in text_lower for kw in critical_keywords):
            return SeverityLevel.CRITICAL
        if any(kw in text_lower for kw in high_keywords):
            return SeverityLevel.HIGH
        if any(kw in text_lower for kw in medium_keywords):
            return SeverityLevel.MEDIUM
        return SeverityLevel.LOW

    # ────────── 日期 ──────────

    def _parse_date(self, date_str: str, content: str) -> datetime:
        """解析日期"""
        if date_str:
            try:
                return datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                pass

        match = re.search(r"(\d{4})年(\d{1,2})月(\d{1,2})日", content)
        if match:
            try:
                return datetime(
                    int(match.group(1)),
                    int(match.group(2)),
                    int(match.group(3)),
                )
            except ValueError:
                pass

        return datetime.now()

    # ────────── 数值提取 ──────────

    def _extract_affected_people(self, text: str) -> Optional[int]:
        """提取受影响人数"""
        patterns = [
            r"转移安置[^\d]*(\d+)[^\d]*人",
            r"受灾群众[^\d]*(\d+)[^\d]*人",
            r"受灾人口[^\d]*(\d+)[^\d]*人",
            r"受影响[^\d]*(\d+)[^\d]*人",
            r"紧急转移[^\d]*(\d+)[^\d]*人",
            r"(\d+)[^\d]*余人受灾",
            r"(\d+)[^\d]*名群众",
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    return int(match.group(1))
                except ValueError:
                    continue

        return None

    def _extract_casualties(self, text: str) -> Optional[int]:
        """提取伤亡人数"""
        total = 0
        found = False

        patterns_death = [
            r"(\d+)[^\d]*人死亡",
            r"死亡[^\d]*(\d+)[^\d]*人",
            r"遇难[^\d]*(\d+)[^\d]*人",
        ]
        patterns_injury = [
            r"(\d+)[^\d]*人受伤",
            r"受伤[^\d]*(\d+)[^\d]*人",
            r"(\d+)[^\d]*人伤亡",
        ]

        for pattern in patterns_death:
            match = re.search(pattern, text)
            if match:
                total += int(match.group(1))
                found = True

        for pattern in patterns_injury:
            match = re.search(pattern, text)
            if match:
                total += int(match.group(1))
                found = True

        return total if found else None

    def _extract_economic_loss(self, text: str) -> Optional[float]:
        """提取经济损失（万元）"""
        patterns = [
            (r"经济损失[^\d]*(\d+(\.\d+)?)[^\d]*万元", 1),
            (r"损失[^\d]*(\d+(\.\d+)?)[^\d]*万元", 1),
            (r"经济损失[^\d]*(\d+(\.\d+)?)[^\d]*亿元", 10000),
            (r"损失[^\d]*(\d+(\.\d+)?)[^\d]*亿元", 10000),
        ]

        for pattern, multiplier in patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    return float(match.group(1)) * multiplier
                except ValueError:
                    continue

        return None

    # ────────── 坐标 ──────────

    def _extract_coordinates(self, location: str) -> Tuple[Optional[float], Optional[float]]:
        """根据地名提取大致坐标（云南省主要城市）"""
        coords = {
            "昆明市": (25.04, 102.72),
            "曲靖市": (25.49, 103.80),
            "玉溪市": (24.35, 102.54),
            "保山市": (25.11, 99.16),
            "昭通市": (27.34, 103.72),
            "丽江市": (26.87, 100.23),
            "普洱市": (22.82, 100.97),
            "临沧市": (23.88, 100.08),
            "楚雄州": (25.04, 101.54),
            "楚雄市": (25.04, 101.54),
            "红河州": (23.37, 103.40),
            "蒙自市": (23.37, 103.40),
            "文山州": (23.37, 104.24),
            "文山市": (23.37, 104.24),
            "西双版纳州": (22.00, 100.80),
            "景洪市": (22.00, 100.80),
            "大理州": (25.60, 100.27),
            "大理市": (25.60, 100.27),
            "德宏州": (24.44, 98.59),
            "芒市": (24.44, 98.59),
            "怒江州": (25.85, 98.86),
            "泸水市": (25.85, 98.86),
            "迪庆州": (27.83, 99.71),
            "香格里拉市": (27.83, 99.71),
        }

        if location:
            for city, (lat, lon) in coords.items():
                if city in location:
                    return lat, lon

        return None, None
