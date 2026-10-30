import urllib.request, json, sys

endpoints = [
    ('GET', 'http://localhost:8000/api/health'),
    ('GET', 'http://localhost:8000/api/config'),
    ('GET', 'http://localhost:8000/api/baseline'),
]

for method, url in endpoints:
    try:
        req = urllib.request.Request(url)
        resp = urllib.request.urlopen(req, timeout=5)
        data = json.loads(resp.read())
        key = url.split('/api/')[1]
        print(f'OK  {key}: {str(data)[:80]}')
    except Exception as e:
        print(f'ERR {url}: {e}')

body = json.dumps({
    'land_ha': 1000, 'water_budget_m3': 8000000,
    'water_change_pct': -20, 'rainfall_scenario': 'Deficit'
}).encode()
req = urllib.request.Request(
    'http://localhost:8000/api/optimize',
    data=body,
    headers={'Content-Type': 'application/json'},
    method='POST'
)
resp = urllib.request.urlopen(req, timeout=10)
data = json.loads(resp.read())
plan = data['plan']
print(f'OK  optimize: status={plan["status"]}, water={plan["total_water_m3"]:,.0f} m3')
print(f'    income=Rs{plan["total_income_inr"]:,.0f}, food={plan["total_production_tonnes"]:.0f}t')

# Test stress test
body2 = json.dumps({'land_ha': 1000, 'water_budget_m3': 8000000, 'rainfall_scenario': 'Normal'}).encode()
req2 = urllib.request.Request(
    'http://localhost:8000/api/stress-test',
    data=body2,
    headers={'Content-Type': 'application/json'},
    method='POST'
)
resp2 = urllib.request.urlopen(req2, timeout=10)
data2 = json.loads(resp2.read())
bottlenecks = [(b['constraint'], b['severity']) for b in data2['bottlenecks']]
print(f'OK  stress-test: strict={data2["strict_status"]}, bottlenecks={bottlenecks}')
