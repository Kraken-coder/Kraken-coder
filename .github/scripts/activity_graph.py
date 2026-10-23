"""Render recent GitHub contribution totals as a self-contained SVG."""
import datetime
import html
import json
import os
from pathlib import Path
import sys
import urllib.request

user = os.environ.get('GITHUB_USER', 'Kraken-coder')
query = '''query($login:String!){user(login:$login){contributionsCollection{contributionCalendar{weeks{contributionDays{date contributionCount}}}}}}'''
if len(sys.argv) > 1:
    payload = json.loads(Path(sys.argv[1]).read_text())
else:
    body = json.dumps({'query': query, 'variables': {'login': user}}).encode()
    request = urllib.request.Request('https://api.github.com/graphql', data=body, headers={
        'Authorization': 'Bearer ' + os.environ['GITHUB_TOKEN'],
        'Content-Type': 'application/json', 'User-Agent': 'profile-activity-chart',
    })
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.load(response)
if payload.get('errors'):
    raise RuntimeError('GitHub did not return contribution data: ' + '; '.join(e.get('message', '') for e in payload['errors']))
calendar = payload['data']['user']['contributionsCollection']['contributionCalendar']
days = [day for week in calendar['weeks'] for day in week['contributionDays']][-31:]
if len(days) < 2:
    raise RuntimeError('At least two contribution days are required.')

width, height = 880, 265
left, right, top, bottom = 55, 847, 70, 207
maximum = max(4, max(d['contributionCount'] for d in days))
maximum = ((maximum + 3) // 4) * 4
coords = [(left + (right-left)*i/(len(days)-1), bottom-(bottom-top)*d['contributionCount']/maximum) for i,d in enumerate(days)]
points = ' '.join(f'{x:.1f},{y:.1f}' for x,y in coords)
area = f'{left},{bottom} ' + points + f' {right},{bottom}'
total = sum(day['contributionCount'] for day in days)
subtitle = f'{days[0]["date"]} to {days[-1]["date"]} · {total} contributions'
svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
    '<title id="title">Recent GitHub contribution activity</title>',
    f'<desc id="desc">{html.escape(subtitle)}. Daily contribution totals from GitHub.</desc>',
    '<rect x=".5" y=".5" width="879" height="264" rx="8" fill="#0d1117" stroke="#26354a"/>',
    '<g font-family="Arial, sans-serif">',
    '<text x="27" y="30" fill="#38bdf8" font-size="18" font-weight="600">Recent contribution activity</text>',
    f'<text x="27" y="51" fill="#8b949e" font-size="12">{html.escape(subtitle)}</text>']
for i in range(5):
    value = maximum*i//4
    y = bottom-(bottom-top)*i/4
    svg.extend([f'<line x1="{left}" y1="{y}" x2="{right}" y2="{y}" stroke="#212b38" stroke-dasharray="3 5"/>',
                f'<text x="43" y="{y+4}" fill="#8b949e" font-size="11" text-anchor="end">{value}</text>'])
svg.extend([f'<polygon points="{area}" fill="#38bdf8" opacity="0.10"/>',
            f'<polyline points="{points}" fill="none" stroke="#38bdf8" stroke-width="2.5" stroke-linejoin="round"/>'])
for (x,y), day in zip(coords, days):
    svg.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2.6" fill="#c9f1ff"><title>{day["date"]}: {day["contributionCount"]} contributions</title></circle>')
for i in [0, len(days)//4, len(days)//2, 3*len(days)//4, len(days)-1]:
    x = coords[i][0]
    label = datetime.date.fromisoformat(days[i]['date']).strftime('%d %b')
    svg.append(f'<text x="{x:.1f}" y="234" fill="#8b949e" font-size="11" text-anchor="middle">{label}</text>')
svg.append('</g></svg>')
out = Path('profile/activity.svg')
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text('\n'.join(svg))
print(f'Generated {out} from {len(days)} days of GitHub contribution data.')
