import httpx

r = httpx.get('http://127.0.0.1:8050/api/v1/graph/visualization', params={'limit': 500}, timeout=30)
data = r.json()

spots = [n for n in data['nodes'] if n['group'] in ('受灾点', 'DisasterSpot')]
print('受灾点:')
for s in spots:
    print(f"  name={s['properties'].get('name', 'N/A')}  label={s['label']}")
    print(f"    props={s['properties']}")

# 也列出所有一级实体
print("\n一级实体统计:")
for label, count in data['stats']['by_label'].items():
    print(f"  {label}: {count}")
