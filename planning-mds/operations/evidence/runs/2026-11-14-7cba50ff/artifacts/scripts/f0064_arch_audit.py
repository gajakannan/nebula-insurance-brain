import ast
import json
from pathlib import Path
import yaml

root = Path('/home/gajap/uSandbox/repos/nebula/nebula-insurance-brain')
binding = yaml.safe_load((root/'planning-mds/kg-source/bindings/f0064.yaml').read_text())['bindings']
code = yaml.safe_load((root/'planning-mds/knowledge-graph/code-index.yaml').read_text())
symbols_doc = yaml.safe_load((root/'planning-mds/knowledge-graph/symbol-index.yaml').read_text())
print(json.dumps({'code_index_keys':list(code), 'symbol_index_keys':list(symbols_doc)}))
by_id = {item['id']:item for item in code['node_bindings']}
symbols = [s for s in symbols_doc['symbols'] if s['node']=='capability:plan-readiness-validation']
for item in binding:
    assert item['id'] in by_id, item['id']
    assert {key:sorted(paths) for key,paths in item['paths'].items()} == {key:sorted(paths) for key,paths in by_id[item['id']]['paths'].items()}
    for paths in item['paths'].values():
        for path in paths:
            assert (root/path).is_file(), path
for symbol in symbols:
    tree=ast.parse((root/symbol['file']).read_text())
    assert any(isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)) and node.name==symbol['name'] and node.lineno==symbol['line'] for node in ast.walk(tree)),symbol
assert len(symbols)==14,len(symbols)
print(json.dumps({'status':'pass','capabilities':len(binding),'bound_paths':sum(len(paths) for item in binding for paths in item['paths'].values()),'symbol_definitions_verified':len(symbols)},indent=2))
