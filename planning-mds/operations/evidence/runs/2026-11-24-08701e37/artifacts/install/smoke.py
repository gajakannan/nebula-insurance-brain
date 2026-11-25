"""Installed-package smoke (S0006 AC3): run from /tmp, outside the source checkout."""
import json, sys
from pathlib import Path
import brain_provenance, brain_contracts
from brain_contracts.schema_runtime import ContractBundle, ContractRef
from brain_domain.provenance import ProvenanceQuery, RecordRef
from brain_domain.authx import ResourceKey, ResourceType
from uuid import uuid4
assert "/app/brain" not in brain_provenance.__file__ and "/app/brain" not in brain_contracts.__file__
bundle = ContractBundle.installed()
for name in ("provenance-query-v1", "provenance-result-v1", "learning-candidate-reservation-v1",
             "review-submission-attempt-v1", "review-decision"):
    bundle.schema(ContractRef(name, "1"))
query = ProvenanceQuery(RecordRef("fact_version", uuid4()), ResourceKey(ResourceType.FACT_SLOT, uuid4()))
bundle.validate(ContractRef("provenance-query-v1", "1"), query.to_json(), profile="portable-json/v1")
print(json.dumps({"status": "pass", "reader": brain_provenance.ProvenanceReader.__name__,
                  "bundle_digest": bundle.digest, "python": sys.version.split()[0],
                  "brain_provenance": brain_provenance.__file__}))
