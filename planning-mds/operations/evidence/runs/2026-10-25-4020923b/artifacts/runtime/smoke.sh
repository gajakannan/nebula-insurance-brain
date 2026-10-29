#!/bin/sh
# F0005 deployability smoke: start both validation services and check the F0005 surface.
cd /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain
F=planning-mds/operations/evidence/runs/2026-10-25-4020923b/artifacts/runtime/compose.yaml
c() { docker compose -f "$F" "$@"; }
c up -d engine-validation neuron-validation
for i in $(seq 1 36); do
  e=$(docker inspect -f '{{.State.Health.Status}}' brain-f0005-4020923b-engine-validation-1)
  n=$(docker inspect -f '{{.State.Health.Status}}' brain-f0005-4020923b-neuron-validation-1)
  [ "$e" != starting ] && [ "$n" != starting ] && break; sleep 5
done
echo "health engine=$e neuron=$n"
echo "== neuron: F0005 modules, pins and committed config"
c exec -T -e BRAIN_LOCAL_CONFIG_PATH=/app/brain/config/local.yaml neuron-validation python -c "
import importlib.metadata as m
from brain_ingestion import worker_guard, provider_supervisor, conversion_process, document_worker, worker_cli
from brain_ingestion.item_provenance import ocr_asset_pins
from brain_content.config import load_extraction_config, load_job_queue_config, load_content_writer_config
print('docling', m.version('docling'), 'docling-graph', m.version('docling-graph'), 'rapidocr', m.version('rapidocr'))
print('conversion deadline', conversion_process.CONVERSION_DEADLINE_SECONDS)
print('ocr pins loaded', bool(ocr_asset_pins()))
print('pipeline', load_extraction_config().pipeline, 'max_queue_depth', load_job_queue_config().max_queue_depth)
print('writer', load_content_writer_config())
"; echo "exit=$?"
echo "== neuron: worker CLI"; c exec -T neuron-validation python -m brain_ingestion.worker_cli --help >/dev/null; echo "exit=$?"
echo "== neuron: provider supervisor CLI"; c exec -T neuron-validation python -m brain_ingestion.provider_supervisor --help >/dev/null; echo "exit=$?"
echo "== engine: migration heads"; c exec -T engine-validation sh -c 'cd engine/migrations && python -m alembic -c alembic.ini heads'; echo "exit=$?"
echo "== engine: health"; c exec -T engine-validation python -c "import urllib.request;print(urllib.request.urlopen('http://localhost:8000/health',timeout=5).read().decode())"; echo "exit=$?"
