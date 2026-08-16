import httpx
import json

r = httpx.get('http://127.0.0.1:8050/api/v1/dispatch/graph/dispatch-triples',
              params={'disaster_name': '墨江县联珠镇受灾点'}, timeout=60)
print(r.status_code)
data = r.json()
print('success:', data.get('success'))
print('triples:', data.get('total_triples', 0))
ents = data.get('entities', {})
print('disaster:', ents.get('disaster', {}).get('name', 'N/A'))
print('teams:', len(ents.get('rescue_teams', [])))
print('warehouses:', len(ents.get('warehouses', [])))
print('shelters:', len(ents.get('shelters', [])))
print('roads:', len(ents.get('roads', [])))
print()
print('前10条三元组:')
for t in data.get('triples', [])[:10]:
    subj = t.get('subject', '')
    pred = t.get('predicate', '')
    obj = t.get('object', '')
    otype = t.get('object_type', '')
    level = t.get('level', '')
    print(f'  [{level}] {subj} -[{pred}]-> {obj} ({otype})')
