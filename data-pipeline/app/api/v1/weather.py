"""天气查询 API

提供云南省各地市/区县天气预报查询，数据来源 tianqihoubao.com
"""

from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from datetime import datetime

from app.core.logging import logger
from app.crawlers.weather_crawler import (
    fetch_weather,
    fetch_weather_by_name,
    get_yunnan_city_tree,
)
from app.crawlers.yunnan_cities import (
    get_city_list,
    get_districts_by_city,
    find_slug_by_name,
)

router = APIRouter(prefix="/weather", tags=["天气查询"])


@router.get("/cities", summary="获取云南城市列表")
async def get_cities():
    """获取云南省所有地市及下辖区县列表"""
    return get_yunnan_city_tree()


@router.get("/districts/{city_name}", summary="获取地市下辖区县")
async def get_districts(city_name: str):
    """获取指定地市的下辖区县列表"""
    districts = get_districts_by_city(city_name)
    if not districts:
        raise HTTPException(status_code=404, detail=f"未找到地市: {city_name}")
    return {"city": city_name, "districts": districts}


@router.get("/forecast", summary="查询天气预报")
async def get_weather_forecast(
    city: Optional[str] = Query(None, description="城市/区县名，如 曲靖、麒麟"),
    slug: Optional[str] = Query(None, description="城市 slug，如 qujing"),
):
    """查询指定城市的天气预报（昨天、今天、明天、后天）

    支持两种查询方式：
    - 通过 city 参数：传入城市/区县名（如 "曲靖" 或 "麒麟"）
    - 通过 slug 参数：传入 slug（如 "qujing"）
    """
    if not city and not slug:
        raise HTTPException(status_code=400, detail="请提供 city 或 slug 参数")

    try:
        if slug:
            result = await fetch_weather(slug)
        else:
            result = await fetch_weather_by_name(city)

        return {
            "code": 200,
            "message": "success",
            "data": result,
            "timestamp": datetime.now().isoformat(timespec="seconds"),
        }
    except Exception as e:
        logger.error(f"[weather-api] 查询天气失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/forecast/{slug}", summary="通过 slug 查询天气预报")
async def get_weather_by_slug(slug: str):
    """通过 slug 直接查询天气预报

    示例: /api/v1/weather/forecast/qujing
    """
    try:
        result = await fetch_weather(slug)
        return {
            "code": 200,
            "message": "success",
            "data": result,
            "timestamp": datetime.now().isoformat(timespec="seconds"),
        }
    except Exception as e:
        logger.error(f"[weather-api] 查询天气失败 (slug={slug}): {e}")
        raise HTTPException(status_code=500, detail=str(e))
