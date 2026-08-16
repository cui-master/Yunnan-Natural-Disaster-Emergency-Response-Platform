import httpx
import json

# 查询风险评估工作流的输入参数
print('=== 风险评估工作流参数 ===')
r = httpx.get('http://127.0.0.1:8080/v1/parameters',
              headers={'Authorization': 'Bearer app-xDyGdKhY52NJPCUfqPRayEo2'}, timeout=10)
print(r.status_code)
data = r.json()
if 'user_input_form' in data:
    for item in data['user_input_form']:
        for k, v in item.items():
            var = v.get('variable', '?')
            label = v.get('label', '')
            req = v.get('required', False)
            print(f'  {k}: variable={var}, label={label}, required={req}')
else:
    print(json.dumps(data, ensure_ascii=False, indent=2)[:1000])

print()

# 查询调度方案工作流的输入参数
print('=== 调度方案工作流参数 ===')
r2 = httpx.get('http://127.0.0.1:8080/v1/parameters',
               headers={'Authorization': 'Bearer app-ELApZzN6iN2LXRfEU2ckM62R'}, timeout=10)
print(r2.status_code)
data2 = r2.json()
if 'user_input_form' in data2:
    for item in data2['user_input_form']:
        for k, v in item.items():
            var = v.get('variable', '?')
            label = v.get('label', '')
            req = v.get('required', False)
            print(f'  {k}: variable={var}, label={label}, required={req}')
else:
    print(json.dumps(data2, ensure_ascii=False, indent=2)[:1000])
