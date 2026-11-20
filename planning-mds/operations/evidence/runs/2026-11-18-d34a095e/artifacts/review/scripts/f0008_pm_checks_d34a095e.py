import json
import re
import sys
from pathlib import Path
sys.path.insert(0, '/tmp')
from f0008_review_exec_d34a095e import ROOT, RUN

feature = ROOT / 'planning-mds/features/archive/F0008-bitemporal-canonical-facts'
evidence = ROOT / 'planning-mds/operations/evidence/runs/2026-11-17-1a4ae2f0'
stories = []
for path in sorted(feature.glob('F0008-S*.md')):
    text = path.read_text()
    rows = [(n, line) for n, line in enumerate(text.splitlines(), 1) if '**AC' in line or '**Status:**' in line]
    print(str(path.relative_to(ROOT)))
    for n, line in rows:
        print(f'{n}: {line}')
    stories.append({'path': str(path.relative_to(ROOT)), 'done': '**Status:** Done' in text,
                    'checked_acs': len(re.findall(r'^- \[x\] \*\*AC\d+:', text, re.M))})
status = (feature / 'STATUS.md').read_text()
ledger = (evidence / 'signoff-ledger.md').read_text()
status_rows = []
for line in status.splitlines():
    if not line.startswith('| F0008-S'):
        continue
    cells = [x.strip() for x in line.strip('|').split('|')]
    if len(cells) == 7:
        story, role, reviewer, verdict, ref, date, note = cells
        ref = ref.strip('`')
        mirror = f'- {story} / {role}: {verdict} by {reviewer} on {date} ({ref})'
        status_rows.append({'story': story, 'role': role, 'reviewer': reviewer,
                            'verdict': verdict, 'date': date, 'path': ref,
                            'exists': (ROOT / ref).is_file(), 'matches_ledger': mirror in ledger})
assert len(status_rows) == 35
assert len({(r['story'], r['role']) for r in status_rows}) == 35
assert all(r['exists'] and r['matches_ledger'] and r['reviewer'] and r['date'] for r in status_rows)
print(f'\nSignoff rows: {len(status_rows)} unique, all match ledger; referenced role files exist.')
print(f'Stories: {len(stories)}, checked AC boxes: {sum(s["checked_acs"] for s in stories)}. Checked boxes are claims, not observed AC fulfillment.')
(RUN / 'artifacts/review/pm-source-checks.json').write_text(json.dumps({'stories': stories, 'signoffs': status_rows}, indent=2)+'\n')
