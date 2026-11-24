import { createHash } from 'node:crypto';
import { mkdtempSync, readFileSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { ContractBundle, admitPortableJson, installedBundle } from '/app/brain/experience/scripts/contracts/runtime.mjs';

const bundle = installedBundle(), results = {};
function outcome(operation) { try { operation(); return 'accepted'; } catch (error) { return error.code; } }
const deep = '['.repeat(128) + '0' + ']'.repeat(128);
results.depth128_decode = outcome(() => bundle.decode(deep));
results.depth128_direct = outcome(() => admitPortableJson(JSON.parse(deep)));
results.money_newline_ajv = outcome(() => bundle.validate({ name: 'qualified-money-v1', version: '1' }, { type: 'money', amount: '1\n', currency: 'USD' }));
const head = '{"n":1e-7,"p":"', tail = '"}';
const raw = head + 'x'.repeat(16777216 - head.length - tail.length) + tail;
const value = bundle.decode(raw);
results.max_bytes_decode = raw.length === 16777216;
results.max_bytes_ajv = outcome(() => bundle.validate({ name: 'assertion-record-v2', version: '2', pointer: '/$defs/qualifiers/additionalProperties' }, value));
const identity = 'https://nebula.local/schemas/reviewer-test.schema.json';
const schema = { $schema: 'https://json-schema.org/draft/2020-12/schema', $id: identity, default: {}, examples: [{}], properties: { default: {} } };
const schemaRaw = JSON.stringify(schema), root = '/app/brain/experience/src/generated/contracts/v1/';
const originalManifest = JSON.parse(readFileSync(root + 'manifest.json'));
const manifest = { bundle: 'brain-contracts/v1', profile: 'nebula-json-schema/1', toolchain: originalManifest.toolchain,
  resources: [{ id: identity, version: '1', path: 'reviewer-test.schema.json', sha256: createHash('sha256').update(schemaRaw).digest('hex') }] };
const directory = mkdtempSync(path.join(tmpdir(), 'f0011-reviewer-'));
writeFileSync(path.join(directory, 'manifest.json'), JSON.stringify(manifest));
writeFileSync(path.join(directory, 'reviewer-test.schema.json'), schemaRaw);
writeFileSync(path.join(directory, 'profile.json'), readFileSync(root + 'profile.json'));
writeFileSync(path.join(directory, 'ui-metadata.json'), JSON.stringify({ [identity]: {} }));
const synthetic = ContractBundle.load(directory);
for (const pointer of ['/default', '/examples/0']) {
  const selected = { name: 'reviewer-test', version: '1', pointer };
  results['annotation_schema:' + pointer] = outcome(() => synthetic.schema(selected));
  results['annotation_metadata:' + pointer] = outcome(() => synthetic.metadata(selected));
  results['annotation_validate:' + pointer] = outcome(() => synthetic.validate(selected, 1));
}
results.real_default_property = outcome(() => synthetic.validate({ name: 'reviewer-test', version: '1', pointer: '/properties/default' }, 1));
const expected = { depth128_decode: 'CONTRACT_JSON_UNSUPPORTED', depth128_direct: 'CONTRACT_JSON_UNSUPPORTED',
  money_newline_ajv: 'CONTRACT_INSTANCE_INVALID', max_bytes_decode: true, max_bytes_ajv: 'accepted' };
for (const pointer of ['/default', '/examples/0']) {
  for (const action of ['schema', 'metadata', 'validate']) expected['annotation_' + action + ':' + pointer] = 'CONTRACT_REFERENCE_UNRESOLVED';
}
expected.real_default_property = 'accepted';
const report = { status: JSON.stringify(results) === JSON.stringify(expected) ? 'pass' : 'fail',
  reviewer: 'Codex / independent Code Reviewer', bundle_digest: bundle.digest, results };
writeFileSync(fileURLToPath(new URL('code-review-reprobe-javascript.json', import.meta.url)), JSON.stringify(report, null, 2) + '\n');
console.log(JSON.stringify(report));
process.exitCode = report.status === 'pass' ? 0 : 1;
