import argparse
from pathlib import Path
import json
from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

parser = argparse.ArgumentParser()
parser.add_argument('--product-root', required=True)
args = parser.parse_args()
root = Path(args.product_root).resolve()
schemas = root / 'planning-mds/schemas'
names = ['interpretation-result', 'assertion-record-v2', 'interpretation-result-v2',
         'assertion-admission-result-v1']
documents = {name: json.loads((schemas / (name + '.schema.json')).read_text()) for name in names}
for name, document in documents.items():
    Draft202012Validator.check_schema(document)
registry = Registry().with_resources((document['$id'], Resource.from_contents(document))
                                     for document in documents.values())
fixtures_path = root / 'planning-mds/features/F0006-assertion-plane-origin-and-interpretation-basis/contract-examples.json'
fixtures = json.loads(fixtures_path.read_text())
for case in fixtures['cases']:
    name = Path(case['schema']).name.removesuffix('.schema.json')
    validator = Draft202012Validator(documents[name], registry=registry,
                                    format_checker=FormatChecker())
    errors = list(validator.iter_errors(case['input']))
    valid = not errors
    if valid != case['valid']:
        raise AssertionError((case['id'], 'unexpected validity', [e.message for e in errors]))
    print(case['id'], 'PASS', 'expected valid' if valid else 'expected invalid')
print(json.dumps({'status': 'pass', 'schema_documents': len(documents),
                  'contract_cases': len(fixtures['cases']),
                  'scope': 'offline design schema and example validation only; no runtime proof'}))
