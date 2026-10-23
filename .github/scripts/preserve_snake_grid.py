"""Keep contribution colors visible while Platane's snake follows its route."""
from pathlib import Path
import xml.etree.ElementTree as ET

OVERRIDE_ID = 'preserve-contribution-grid'
OVERRIDE = f'''<style id="{OVERRIDE_ID}">
/* Preserve each cell's original contribution color throughout the loop. */
.c {{ animation: none !important; }}
/* The collected-contributions bar is unnecessary when nothing disappears. */
.u {{ display: none; }}
@media (prefers-reduced-motion: reduce) {{
  .s {{ animation: none !important; }}
}}
</style>'''

for name in ['contribution-snake.svg', 'contribution-snake-dark.svg']:
    path = Path('profile') / name
    svg = path.read_text()
    root = ET.fromstring(svg)
    ns = '{http://www.w3.org/2000/svg}'
    cells = [e for e in root.iter() if 'c' in e.get('class', '').split()]
    snake = [e for e in root.iter() if 's' in e.get('class', '').split()]
    if not cells or not snake:
        raise RuntimeError(f'{name}: unexpected upstream snake SVG structure')
    if root.find(f"{ns}style[@id='{OVERRIDE_ID}']") is None:
        svg = svg.replace('</svg>', OVERRIDE + '</svg>')
    ET.fromstring(svg)
    path.write_text(svg)
    print(f'{name}: preserved {len(cells)} contribution cells; kept {len(snake)} animated snake segments.')
