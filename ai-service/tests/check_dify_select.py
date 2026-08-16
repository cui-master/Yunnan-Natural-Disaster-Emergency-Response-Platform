import httpx
import json

# 查询完整参数（包括 select 选项）
print('=== 风险评估完整参数 ===')
r = httpx.get('http://127.0.0.1:8080/v1/parameters',
              headers={'Authorization': 'Bearer app-xDyGdKhY52NJPCUfqPRayEo2'}, timeout=10)
data = r.json()
for item in data.get('user_input_form', []):
    for k, v in item.items():
        if k == 'select':
            print(f"  select: variable={v.get('variable')}, options={v.get('options')}, default={v.get('default')}")
        else:
            print(f"  {k}: variable={v.get('variable')}, default={v.get('default','')}")

print()
print('=== 调度方案完整参数 ===')
r2 = httpx.get('http://127.0.0.1:8080/v1/parameters',
               headers={'Authorization': 'Bearer app-ELApZzN6iN2LXRfEU2ckM62R'}, timeout=10)
data2 = r2.json()
for item in data2.get('user_input_form', []):
    for k, v in item.items():
        if k == 'select':
            print(f"  select: variable={v.get('variable')}, options={v.get('options')}, default={v.get('default')}")
        else:
            print(f"  {k}: variable={v.get('variable')}, default={v.get('default','')}")
