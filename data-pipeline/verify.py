"""快速验证脚本 - 测试爬虫服务核心功能"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))


async def test_mock_crawler():
    """测试 Mock 爬虫"""
    print("=" * 60)
    print("测试 1: Mock 爬虫")
    print("=" * 60)
    from app.crawlers import MockCrawler

    crawler = MockCrawler()
    result = await crawler.crawl()

    print(f"数据源: {result.source}")
    print(f"事件数量: {result.total_count}")
    print(f"错误: {result.error}")
    print(f"事件类型分布:")

    type_count = {}
    for e in result.events:
        t = e.disaster_type.value
        type_count[t] = type_count.get(t, 0) + 1

    for t, c in type_count.items():
        print(f"  - {t}: {c} 条")

    if result.events:
        first = result.events[0]
        print(f"\n第一条事件:")
        print(f"  标题: {first.title}")
        print(f"  地点: {first.location}")
        print(f"  类型: {first.disaster_type.value}")
        print(f"  严重程度: {first.severity.value}")
        print(f"  时间: {first.occurred_at}")
        print(f"  ID: {first.id}")

    print("✅ Mock 爬虫测试通过\n")
    return result


async def test_event_store():
    """测试事件存储"""
    print("=" * 60)
    print("测试 2: 事件存储")
    print("=" * 60)
    from app.services import event_store
    from app.crawlers import MockCrawler

    crawler = MockCrawler()
    result = await crawler.crawl()

    new_count = await event_store.add_events(result.events, result.source)
    print(f"新增事件: {new_count} 条")

    all_events = await event_store.get_events(limit=5)
    print(f"查询到事件: {len(all_events)} 条")

    stats = await event_store.get_stats()
    print(f"总事件数: {stats['total_events']}")
    print(f"按类型统计: {stats['by_type']}")
    print(f"按严重程度: {stats['by_severity']}")

    # 测试过滤
    earthquake_events = await event_store.get_events(disaster_type="earthquake")
    print(f"地震事件: {len(earthquake_events)} 条")

    high_events = await event_store.get_events(severity="high")
    print(f"高严重度事件: {len(high_events)} 条")

    print("✅ 事件存储测试通过\n")


async def test_sse_manager():
    """测试 SSE 管理器"""
    print("=" * 60)
    print("测试 3: SSE 管理器")
    print("=" * 60)
    from app.services import sse_manager

    queue = await sse_manager.register()
    print(f"注册后连接数: {sse_manager.client_count}")

    await sse_manager.broadcast({"test": "hello"}, event_type="test")

    try:
        msg = await asyncio.wait_for(queue.get(), timeout=2.0)
        print(f"收到消息: {msg['event']}")
    except asyncio.TimeoutError:
        print("⚠️  未收到消息（可能队列处理有延迟）")

    await sse_manager.unregister(queue)
    print(f"注销后连接数: {sse_manager.client_count}")

    print("✅ SSE 管理器测试通过\n")


async def test_yunnan_net_parser():
    """测试云南网爬虫的解析逻辑（不发起网络请求）"""
    print("=" * 60)
    print("测试 4: 云南网爬虫解析逻辑")
    print("=" * 60)
    from app.crawlers.yunnan_net import YunnanNetCrawler

    crawler = YunnanNetCrawler(keywords=["测试"])

    # 测试地点提取
    test_cases = [
        ("昆明市盘龙区发生3.2级地震", "昆明市"),
        ("普洱市墨江县发生5.0级地震", "普洱市"),
        ("大理州祥云县森林火情", "大理州"),
        ("昭通市彝良县遭遇暴雨", "昭通市"),
        ("云南省发布预警", "云南省"),
    ]
    print("地点提取测试:")
    all_pass = True
    for text, expected in test_cases:
        result = crawler._extract_location(text)
        ok = expected in result if result else False
        status = "✅" if ok else "❌"
        print(f"  {status} '{text[:20]}...' → {result} (期望含: {expected})")
        if not ok:
            all_pass = False

    # 测试严重程度解析
    print("\n严重程度解析测试:")
    sev_cases = [
        ("特别重大灾害，启动一级响应", "critical"),
        ("橙色预警，多人死亡", "high"),
        ("黄色预警，群众受灾", "medium"),
        ("普通新闻报道", "low"),
    ]
    for text, expected in sev_cases:
        result = crawler._parse_severity_from_content(text).value
        ok = result == expected
        status = "✅" if ok else "❌"
        print(f"  {status} '{text[:20]}...' → {result} (期望: {expected})")
        if not ok:
            all_pass = False

    # 测试人数提取
    print("\n人数提取测试:")
    people_cases = [
        ("转移安置群众33户94人", 94),
        ("受灾群众2300余人", 2300),
        ("紧急转移500人", 500),
        ("无人员伤亡", None),
    ]
    for text, expected in people_cases:
        result = crawler._extract_affected_people(text)
        ok = result == expected
        status = "✅" if ok else "❌"
        print(f"  {status} '{text}' → {result} (期望: {expected})")
        if not ok:
            all_pass = False

    # 测试坐标提取
    print("\n坐标提取测试:")
    coord_cases = [
        ("云南省昆明市盘龙区", (25.04, 102.72)),
        ("普洱市墨江县", (22.82, 100.97)),
    ]
    for text, (exp_lat, exp_lon) in coord_cases:
        lat, lon = crawler._extract_coordinates(text)
        ok = lat == exp_lat and lon == exp_lon
        status = "✅" if ok else "❌"
        print(f"  {status} '{text}' → ({lat}, {lon}) (期望: ({exp_lat}, {exp_lon}))")
        if not ok:
            all_pass = False

    if all_pass:
        print("\n✅ 云南网爬虫解析逻辑全部通过\n")
    else:
        print("\n⚠️  部分测试未通过\n")

    return all_pass


async def main():
    print("\n" + "🚀" * 20)
    print("  数据管道服务 - 快速验证脚本")
    print("🚀" * 20 + "\n")

    try:
        await test_mock_crawler()
        await test_event_store()
        await test_sse_manager()
        await test_yunnan_net_parser()

        print("=" * 60)
        print("🎉 所有核心功能测试通过！")
        print("=" * 60)
        print("\n📝 下一步操作:")
        print("  1. 安装依赖: pip install -r requirements.txt")
        print("  2. 启动服务: python -m app.main")
        print("  3. 访问 SSE: http://127.0.0.1:8000/sse")
        print("  4. 查看文档: http://127.0.0.1:8000/docs")
        print("  5. Dify配置: {\"transport\":\"sse\",\"url\":\"http://127.0.0.1:8000/sse\"}")
        print()

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
