"""Read-only probe of the actual commit-response model for S0002 AC7."""
from datetime import UTC, datetime
import json
from pathlib import Path
import sys
from uuid import UUID

root = Path('/home/gajap/uSandbox/repos/nebula/nebula-insurance-brain')
for source in sorted((root / 'engine/packages').glob('*/src')):
    sys.path.insert(0, str(source))
sys.path.insert(0, str(root / 'engine/apps/api/src'))

from brain_api.schemas.facts import CommitResponseOut
from brain_domain.facts import CommitResult

result = CommitResult(
    commit_id=UUID(int=1),
    fact_version_ids=(UUID(int=2),),
    canonical_accepted_at=datetime(2026, 8, 5, tzinfo=UTC),
)
response = CommitResponseOut.from_domain(result).model_dump(mode='json')
print(json.dumps({
    'model': 'brain_api.schemas.facts.CommitResponseOut',
    'response': response,
    'properties': list(CommitResponseOut.model_json_schema()['properties']),
    'AC7_fields_missing': sorted({'valid_to_state', 'attested_from', 'attested_to', 'valid_from_basis'} - set(response)),
    'temporal_block_present': 'temporal' in response,
}, indent=2))
