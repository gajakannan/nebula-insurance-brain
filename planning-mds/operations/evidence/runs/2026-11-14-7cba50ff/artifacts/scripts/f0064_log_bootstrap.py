import datetime
import json
from pathlib import Path
from f0064_review_exec import append_json

run = Path('/home/gajap/uSandbox/repos/nebula/nebula-insurance-brain/planning-mds/operations/evidence/runs/2026-11-14-7cba50ff')
source = json.loads((run / 'artifacts/bootstrap-commands.json').read_text())
stamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
for command in source['commands']:
    append_json(run / 'commands.log', dict(schema_version=1, timestamp=stamp,
        **command, artifacts=[], redactions=[], phase='bootstrap-backfill',
        timestamp_semantics='recorded after setup; original execution timestamp not captured'))
with (run / 'artifact-trace.md').open('a') as stream:
    stream.write('\n## Bootstrap telemetry\n\nartifacts/bootstrap-commands.json backfills exact pre-initialization command blocks and exits. Their command-log timestamps are recording times; original execution timestamps were not captured. Gate operations and subsequent review commands have direct execution timestamps.\n')
print('Backfilled', len(source['commands']), 'pre-logger command blocks; timestamp semantics explicit.')
