import httpx

BASE_URL = "http://127.0.0.1:8050"

# 测试知识库列表
print('=== 知识库列表 ===')
try:
    r = httpx.get(f'{BASE_URL}/knowledge-base/list', timeout=10)
    print(r.status_code)
    print(r.json())
except Exception as e:
    print(f'错误: {e}')
print()

# 测试上传文档到调度知识库
print('=== 上传文档到调度知识库 ===')
try:
    with open('tests/test_doc.txt', 'rb') as f:
        files = {'file': ('test_doc.txt', f, 'text/plain')}
        data = {'kb_name': '优化调度'}
        r2 = httpx.post(f'{BASE_URL}/knowledge-base/upload', files=files, data=data, timeout=60)
        print(r2.status_code)
        print(r2.json())
except Exception as e:
    print(f'错误: {e}')
print()

# 测试上传文档到风险评估知识库
print('=== 上传文档到风险评估知识库 ===')
try:
    with open('tests/test_doc.txt', 'rb') as f:
        files = {'file': ('test_doc.txt', f, 'text/plain')}
        data = {'kb_name': '风险评估'}
        r3 = httpx.post(f'{BASE_URL}/knowledge-base/upload', files=files, data=data, timeout=60)
        print(r3.status_code)
        print(r3.json())
except Exception as e:
    print(f'错误: {e}')