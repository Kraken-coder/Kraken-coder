"""Render the GitHub contribution calendar total, without an arbitrary grade."""
import html
import json
import os
from pathlib import Path
import sys
import urllib.request

user = os.environ.get('GITHUB_USER', 'Kraken-coder')
query = '''query($login:String!){user(login:$login){contributionsCollection{contributionCalendar{totalContributions weeks{contributionDays{date contributionCount}}}}}}'''
if len(sys.argv) > 1:
    payload = json.loads(Path(sys.argv[1]).read_text())
else:
    request = urllib.request.Request(
        'https://api.github.com/graphql',
        data=json.dumps({'query': query, 'variables': {'login': user}}).encode(),
        headers={'Authorization': 'Bearer ' + os.environ['GITHUB_TOKEN'],
                 'Content-Type': 'application/json', 'User-Agent': 'profile-contribution-summary'},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.load(response)
if payload.get('errors'):
    raise RuntimeError('GitHub contribution query failed.')
calendar = payload['data']['user']['contributionsCollection']['contributionCalendar']
days = [day for week in calendar['weeks'] for day in week['contributionDays']]
if not days or sum(day['contributionCount'] for day in days) != calendar['totalContributions']:
    raise RuntimeError('Contribution calendar is incomplete or inconsistent.')
total = calendar['totalContributions']
active = sum(day['contributionCount'] > 0 for day in days)
recent = sum(day['contributionCount'] for day in days[-30:])
best = max(day['contributionCount'] for day in days)
period = f'{days[0]["date"]} to {days[-1]["date"]}'
description = f'{total} contributions; {active} active days; {recent} contributions in the last 30 calendar days; busiest day {best}. Period: {period}.'
svg = [
    '<svg xmlns="http://www.w3.org/2000/svg" width="495" height="245" viewBox="0 0 495 245" role="img" aria-labelledby="title desc">',
    '<title id="title">GitHub contribution summary</title>',
    f'<desc id="desc">{html.escape(description)}</desc>',
    '<rect x=".5" y=".5" width="494" height="244" rx="6" fill="#0d1117" stroke="#26354a"/>',
    '<g font-family="Arial, sans-serif">',
    '<text x="25" y="35" fill="#38bdf8" font-size="18" font-weight="600">GitHub contribution activity</text>',
    f'<text x="25" y="57" fill="#8b949e" font-size="11">Calendar period: {period}</text>',
    f'<text x="25" y="112" fill="#e6edf3" font-size="43" font-weight="700">{total:,}</text>',
    '<text x="25" y="135" fill="#c9d1d9" font-size="13">Total calendar contributions</text>',
    '<line x1="25" y1="155" x2="470" y2="155" stroke="#26354a"/>',
]
for x, value, label in [(25, active, 'Active days'), (185, recent, 'Last 30 days'), (345, best, 'Busiest day')]:
    svg.extend([
        f'<text x="{x}" y="190" fill="#38bdf8" font-size="25" font-weight="600">{value:,}</text>',
        f'<text x="{x}" y="212" fill="#c9d1d9" font-size="12">{label}</text>',
    ])
svg.extend(['</g>', '</svg>'])
out = Path('profile/contributions.svg')
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text('\n'.join(svg))
print(f'Generated {out}: {total} calendar contributions ({period}).')
