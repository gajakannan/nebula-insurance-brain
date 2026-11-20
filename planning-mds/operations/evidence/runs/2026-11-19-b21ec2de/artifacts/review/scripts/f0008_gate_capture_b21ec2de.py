"""Run the unmodified gate driver with its supported stream-capture parameters."""
import copy
import json
from pathlib import Path
import runpy
import sys

FRAMEWORK=Path('/home/gajap/uSandbox/repos/nebula/nebula-agents')
ROOT=Path('/home/gajap/uSandbox/repos/nebula/nebula-insurance-brain')
RUN=ROOT/'planning-mds/operations/evidence/runs/2026-11-19-b21ec2de'
sys.path.insert(0,str(FRAMEWORK/'agents/scripts'))
import gate_runtime
original = gate_runtime.run_operation

def capture(op, **kwargs):
    op = copy.deepcopy(op)
    body = op['run']
    name = body.get('id', 'validator')
    # Bind the product-aware tracker explicitly; all other argv remain unchanged.
    if 'agents/product-manager/scripts/validate-trackers.py' in body.get('argv',[]) and '--product-root' not in body['argv']:
        body['argv'] += ['--product-root', str(ROOT)]
    kwargs['stdout_path'] = RUN/'artifacts/validators'/f'{name}.stdout.txt'
    kwargs['stderr_path'] = RUN/'artifacts/validators'/f'{name}.stderr.txt'
    result = original(op, **kwargs)
    meta = {k:v for k,v in result.items() if k not in ('stdout','stderr')}
    (RUN/'artifacts/validators'/f'{name}.result.json').write_text(json.dumps(meta,indent=2)+'\n')
    return result

gate_runtime.run_operation = capture
sys.argv = [str(FRAMEWORK/'agents/scripts/run-gate.py'), *sys.argv[1:]]
runpy.run_path(sys.argv[0],run_name='__main__')
