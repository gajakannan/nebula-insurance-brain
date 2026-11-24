import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { mkdtempSync, readFileSync, rmSync, symlinkSync, writeFileSync } from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { afterEach, test } from 'node:test';
import { fileURLToPath } from 'node:url';
import {
  AJV_OPTIONS, ContractBundle, ContractError, admitPortableJson, consumerVersions,
  decodePortableJson, portableDate, portableDateTime, portableUriReference,
} from './runtime.mjs';
import { runCases } from './check.mjs';
import { rawForCase } from './case-data.mjs';

const temporary = [];
afterEach(() => { while (temporary.length) rmSync(temporary.pop(), { recursive: true, force: true }); });
const DIALECT = 'https://json-schema.org/draft/2020-12/schema';
const ID = 'https://nebula.local/schemas/test.schema.json';
const keywords = [
  'type', 'const', 'enum', 'properties', 'required', 'additionalProperties',
  'propertyNames', 'maxProperties', 'items', 'minItems', 'maxItems', 'uniqueItems',
  'contains', 'minContains', 'maxContains', 'minimum', 'maximum', 'exclusiveMinimum',
  'minLength', 'maxLength', 'pattern', 'format', 'allOf', 'anyOf', 'oneOf', 'if', 'then', 'else', 'not',
];
const baseSchema = () => ({
  $id: ID, $schema: DIALECT, title: 'Synthetic test contract',
  'x-nebula-concept': 'test', 'x-nebula-evidence-required': true,
  type: 'object', required: ['name', 'amount'], additionalProperties: true,
  properties: {
    name: { type: 'string', minLength: 1 },
    amount: { type: 'string', pattern: '^[0-9]+\\.[0-9]{2}$' },
    count: { type: 'integer', minimum: 0, default: 10 },
    default: { type: 'string' },
    nullable: { type: ['string', 'null'] },
    date: { type: 'string', format: 'date' },
    uuid: { type: 'string', format: 'uuid' },
    timestamp: { type: 'string', format: 'date-time' },
    uri: { type: 'string', format: 'uri-reference' },
  },
  $defs: { alias: { type: 'string' } },
});
const ref = (pointer = '') => ({ name: 'test', version: '1', pointer });
const good = () => ({ name: 'same', amount: '900719925474099312345.01' });
const digest = (bytes) => createHash('sha256').update(bytes).digest('hex');
const encode = (value) => `${JSON.stringify(value, null, 2)}\n`;
const code = (expected) => (error) => error instanceof ContractError && error.code === expected && error.message === expected;

function bundleDirectory(schemas = [baseSchema()]) {
  const directory = mkdtempSync(path.join(os.tmpdir(), 'f0011-js-'));
  temporary.push(directory);
  const resources = schemas.map((schema, index) => {
    const filename = index ? `alias-${index}.schema.json` : 'test.schema.json';
    const bytes = encode(schema);
    writeFileSync(path.join(directory, filename), bytes);
    return { id: schema.$id, version: '1', path: filename, sha256: digest(bytes) };
  });
  writeFileSync(path.join(directory, 'manifest.json'), encode({
    bundle: 'brain-contracts/v1', profile: 'nebula-json-schema/1', resources,
    toolchain: {
      builder: 'synthetic', python: '3.13', jsonschema: 'test', referencing: 'test', pydantic: 'test', datamodel_code_generator: 'test',
      ajv: consumerVersions().ajv, ajv_formats: consumerVersions().ajv_formats, jsonc_parser: consumerVersions().jsonc_parser,
    },
  }));
  writeFileSync(path.join(directory, 'profile.json'), encode({
    id: 'nebula-json-schema/1', dialect: DIALECT, validation_keywords: keywords,
    ajv_options: AJV_OPTIONS,
  }));
  writeFileSync(path.join(directory, 'ui-metadata.json'), encode(Object.fromEntries(schemas.map((schema) => [
    schema.$id, schema.$id === ID ? { '': { title: 'Synthetic test contract', 'x-nebula-concept': 'test', 'x-nebula-evidence-required': true } } : {},
  ]))));
  return directory;
}

function update(directory, filename, edit) {
  const target = path.join(directory, filename);
  const value = JSON.parse(readFileSync(target, 'utf8'));
  edit(value);
  writeFileSync(target, encode(value));
}

test('portable decoder preserves opaque keys, supplementary characters and exact strings', () => {
  const value = decodePortableJson(Buffer.from('{"__proto__":{"safe":true},"a":"𝄞","money":"999999999999999999.99"}'));
  assert.equal(Object.hasOwn(value, '__proto__'), true);
  assert.equal(value.__proto__.safe, true);
  assert.equal(Object.getPrototypeOf(value), Object.prototype);
  assert.equal(value.a, '𝄞');
  assert.equal(value.money, '999999999999999999.99');
  assert.equal(decodePortableJson('9007199254740991'), Number.MAX_SAFE_INTEGER);
  assert.equal(decodePortableJson('1.2345'), 1.2345);
});

test('malformed JSON and duplicate keys cannot be repaired by the scanner', () => {
  for (const raw of ['', '{} {}', '{"a":1,"a":2}', '{"a":1,"\\u0061":2}', '{"a":1,}', '[1,]', '/*x*/{}', '//x\n{}', 'undefined', 'NaN', '\ufeff{}']) {
    assert.throws(() => decodePortableJson(raw), code('CONTRACT_JSON_INVALID'), raw);
  }
  assert.throws(() => decodePortableJson(Uint8Array.from([0xc3, 0x28])), code('CONTRACT_JSON_INVALID'));
  assert.throws(() => decodePortableJson({}), code('CONTRACT_JSON_INVALID'));
});

test('portable decoder refuses unsafe numbers, surrogates and resource overflows', () => {
  for (const raw of ['9007199254740992', '-9007199254740992', '1e400', '"\\ud800"', '"\\udc00"', '{"\\ud800":true}']) {
    assert.throws(() => decodePortableJson(raw), code('CONTRACT_JSON_UNSUPPORTED'));
  }
  assert.doesNotThrow(() => decodePortableJson(`${'['.repeat(127)}0${']'.repeat(127)}`));
  assert.throws(() => decodePortableJson(`${'['.repeat(128)}0${']'.repeat(128)}`), code('CONTRACT_JSON_UNSUPPORTED'));
  assert.throws(() => decodePortableJson(`"${'x'.repeat(16 * 1024 * 1024)}"`), code('CONTRACT_JSON_UNSUPPORTED'));
  assert.throws(() => decodePortableJson(`[${'0,'.repeat(1_000_000)}0]`), code('CONTRACT_JSON_UNSUPPORTED'));
});

test('root depth is one for every scalar and nested array/object value', () => {
  for (const scalar of [null, false, 0, 'x']) {
    assert.equal(decodePortableJson(JSON.stringify(scalar)), scalar);
    admitPortableJson(scalar);
    for (const [open, close] of [['[', ']'], ['{"v":', '}']]) {
      for (const containers of [127, 128, 129]) {
        const raw = open.repeat(containers) + JSON.stringify(scalar) + close.repeat(containers);
        const value = JSON.parse(raw);
        if (containers === 127) {
          assert.deepEqual(decodePortableJson(raw), value);
          assert.doesNotThrow(() => admitPortableJson(value));
        } else {
          assert.throws(() => decodePortableJson(raw), code('CONTRACT_JSON_UNSUPPORTED'));
          assert.throws(() => admitPortableJson(value), code('CONTRACT_JSON_UNSUPPORTED'));
        }
      }
    }
  }
  for (const [open, empty, close] of [['[', '[]', ']'], ['{"v":', '{}', '}']]) {
    const raw = open.repeat(127) + empty + close.repeat(127);
    assert.doesNotThrow(() => decodePortableJson(raw));
    assert.doesNotThrow(() => admitPortableJson(JSON.parse(raw)));
  }
});

test('direct value admission rejects lossy/non-JSON values without invoking getters', () => {
  const cyclic = {}; cyclic.self = cyclic;
  let getterRan = false;
  const accessor = { get value() { getterRan = true; return 1; } };
  const hidden = {}; Object.defineProperty(hidden, 'secret', { value: 1 });
  const symbolic = { [Symbol('x')]: 1 };
  for (const value of [undefined, () => {}, BigInt(1), NaN, Infinity, Number.MAX_SAFE_INTEGER + 1,
    '\ud800', new Date(), cyclic, accessor, hidden, symbolic, [undefined], Array(1)]) {
    assert.throws(() => admitPortableJson(value), code('CONTRACT_JSON_UNSUPPORTED'));
  }
  assert.equal(getterRan, false);
  admitPortableJson(Object.freeze({ a: Object.freeze([null, true, 1.25]) }));
  const opaque = JSON.parse('{"__proto__":null}'); admitPortableJson(opaque);
});

test('portable date/time formats bind Gregorian years and exact RFC3339 boundaries', () => {
  for (const value of ['0001-01-01', '2000-02-29', '9999-12-31']) assert.equal(portableDate(value), true, value);
  for (const value of ['0000-01-01', '1900-02-29', '2024-02-30', '2024-00-01', '2024-01-00', '2024-13-01', '24-01-01']) assert.equal(portableDate(value), false, value);
  for (const value of ['0001-01-01T00:00:00Z', '2024-02-29t23:59:59.123z', '2024-01-01T01:02:03+23:59']) assert.equal(portableDateTime(value), true, value);
  for (const value of ['2024-01-01T00:00:00', '2024-01-01T00:00:60Z', '2024-01-01T24:00:00Z', '2024-01-01T00:60:00Z', '2024-01-01T00:00:00+24:00', '1900-02-29T00:00:00Z']) assert.equal(portableDateTime(value), false, value);
});

test('portable URI references follow ASCII RFC3986 without WHATWG repair', () => {
  for (const value of ['', '../x', '#', '?q=x', 'https://example.test/a%20b?q=1#c', '//user:p@[::1]:80/a', 'http://[v1.example]/', 'urn:example:x']) assert.equal(portableUriReference(value), true, value);
  for (const value of ['x y', 'https://example.test/%zz', 'https://例え.test/', 'http://[bad]/', 'http://[::1', 'http://x:bad/', '1x:bad', '#a#b', 'http://u@u@host/', 'relative[x]', '?q=[x]']) assert.equal(portableUriReference(value), false, value);
});

test('bundle uses real AJV without coercion/defaults/removal or input mutation', () => {
  const bundle = ContractBundle.load(bundleDirectory());
  const value = Object.freeze({ ...good(), nullable: null, opaque: Object.freeze({ a: true }), default: 'property name' });
  const before = JSON.stringify(value);
  bundle.validate(ref(), value);
  assert.equal(JSON.stringify(value), before);
  assert.equal(Object.hasOwn(value, 'count'), false);
  for (const value of [{ ...good(), count: '1' }, { ...good(), count: -1 }, { name: '', amount: '1.00' }, { ...good(), amount: 1.25 }, { ...good(), date: '1900-02-29' }, { ...good(), uuid: 'bad' }, { ...good(), timestamp: '2024-01-01T00:00:60Z' }, { ...good(), uri: 'x y' }]) {
    assert.throws(() => bundle.validate(ref(), value), code('CONTRACT_INSTANCE_INVALID'));
  }
  bundle.validate(ref(), { ...good(), uuid: 'ABCDEF01-0000-0000-0000-000000000001', date: '0001-01-01', timestamp: '2024-01-01t00:00:00z', uri: '../x' });
  assert.equal(bundle.decode('{"x":1}').x, 1);
  assert.throws(() => bundle.decode('{}', { profile: 'native-compat/v1' }), code('CONTRACT_JSON_UNSUPPORTED'));
  assert.throws(() => bundle.validate(ref(), value, { profile: 'native-compat/v1' }), code('CONTRACT_JSON_UNSUPPORTED'));
  assert.match(bundle.digest, /^[0-9a-f]{64}$/);
});

test('bundle schema and metadata views cannot modify cached validators', () => {
  const bundle = ContractBundle.load(bundleDirectory());
  const schema = bundle.schema(ref()); schema.properties.amount.type = 'number';
  const metadata = bundle.metadata(ref()); metadata.title = 'changed';
  assert.equal(bundle.metadata(ref()).title, 'Synthetic test contract');
  assert.equal(bundle.schema(ref()).properties.amount.type, 'string');
  assert.deepEqual(bundle.metadata(ref('/properties/name')), {});
  bundle.validate(ref('/$defs/alias'), 'x');
  bundle.validate({ name: 'test.schema.json', version: '1' }, good());
  assert.throws(() => bundle.validate(ref('/$defs/alias'), 1), code('CONTRACT_INSTANCE_INVALID'));
  for (const bad of [{ name: 'missing', version: '1' }, { name: 'test', version: '2' }, {}]) {
    assert.throws(() => bundle.schema(bad), code('CONTRACT_VERSION_UNSUPPORTED'));
  }
  for (const bad of ['/missing', '/title', '/~bad', 'not-pointer']) assert.throws(() => bundle.schema(ref(bad)), code('CONTRACT_REFERENCE_UNRESOLVED'));
});

test('public bundle APIs admit schema positions and refuse schema-looking annotation data', () => {
  const schema = baseSchema();
  schema.default = { type: 'integer' };
  schema.examples = [{ type: 'string' }, true];
  const bundle = ContractBundle.load(bundleDirectory([schema]));
  for (const fragment of ['/default', '/examples/0', '/examples/1', '/properties', '/$defs', '/properties/count/default']) {
    assert.throws(() => bundle.schema(ref(fragment)), code('CONTRACT_REFERENCE_UNRESOLVED'));
    assert.throws(() => bundle.metadata(ref(fragment)), code('CONTRACT_REFERENCE_UNRESOLVED'));
    assert.throws(() => bundle.validate(ref(fragment), 1), code('CONTRACT_REFERENCE_UNRESOLVED'));
  }
  assert.deepEqual(bundle.schema(ref('/properties/default')), { type: 'string' });
  assert.deepEqual(bundle.metadata(ref('/properties/default')), {});
  bundle.validate(ref('/properties/default'), 'a property named default is a schema position');
  assert.throws(() => bundle.validate(ref('/properties/default'), 1), code('CONTRACT_INSTANCE_INVALID'));
});

test('registered refs resolve and dormant/external/cyclic refs fail before instances', () => {
  const main = baseSchema();
  const alias = { $id: 'https://nebula.local/schemas/alias.schema.json', $schema: DIALECT, $ref: `${ID}#/$defs/alias` };
  const bundle = ContractBundle.load(bundleDirectory([main, alias]));
  bundle.validate({ name: 'alias-1', version: '1' }, 'x');
  for (const target of [`${ID}#/missing`, 'https://external.invalid/schema', 'file:///etc/passwd', '#']) {
    const schema = baseSchema(); schema.$defs.never = { if: false, then: { $ref: target } };
    assert.throws(() => ContractBundle.load(bundleDirectory([schema])), code('CONTRACT_REFERENCE_UNRESOLVED'));
  }
});

test('schema admission rejects unsupported instructions rather than data property names', () => {
  for (const mutate of [
    (schema) => { schema.typo = true; },
    (schema) => { schema['x-nebula-unknown'] = 'x'; },
    (schema) => { schema['x-nebula-evidence-required'] = 'yes'; },
    (schema) => { schema.properties.bad = { format: 'email' }; },
    (schema) => { schema.$dynamicRef = '#x'; },
    (schema) => { schema.properties.bad = { $id: 'https://nebula.local/nested' }; },
    (schema) => { schema.properties.bad = { $schema: 'http://json-schema.org/draft-07/schema#' }; },
    (schema) => { schema.properties.bad = null; },
    (schema) => { schema.allOf = {}; },
  ]) {
    const schema = baseSchema(); mutate(schema);
    assert.throws(() => ContractBundle.load(bundleDirectory([schema])), code('CONTRACT_SCHEMA_UNSUPPORTED'));
  }
});

test('pattern admission distinguishes terminal anchors from escaped and character-class dollars', () => {
  for (const pattern of ['a$b', 'a\\\\$b']) {
    const schema = baseSchema(); schema.properties.name.pattern = pattern;
    assert.throws(() => ContractBundle.load(bundleDirectory([schema])), code('CONTRACT_SCHEMA_UNSUPPORTED'));
  }
  for (const [pattern, name] of [['^a$', 'a'], ['^a\\$b$', 'a$b'], ['^[a$]+$', 'a$a'], ['a', 'cat'], ['\\$', '$']]) {
    const schema = baseSchema(); schema.properties.name.pattern = pattern;
    const bundle = ContractBundle.load(bundleDirectory([schema]));
    bundle.validate(ref(), { ...good(), name });
  }
});

test('corrupt or incomplete bundles cannot create a usable partial runtime', () => {
  for (const mutate of [
    (manifest) => { manifest.bundle = 'other'; },
    (manifest) => { manifest.profile = 'other'; },
    (manifest) => { manifest.resources = []; },
    (manifest) => { manifest.resources.push(manifest.resources[0]); },
    (manifest) => { manifest.resources[0].path = '../outside.schema.json'; },
    (manifest) => { manifest.resources[0].sha256 = '0'.repeat(64); },
    (manifest) => { manifest.resources[0].id = 'wrong'; },
    (manifest) => { manifest.toolchain.python = null; },
  ]) {
    const directory = bundleDirectory(); update(directory, 'manifest.json', mutate);
    assert.throws(() => ContractBundle.load(directory), code('CONTRACT_BUNDLE_INVALID'));
  }
  const missing = bundleDirectory(); rmSync(path.join(missing, 'test.schema.json'));
  assert.throws(() => ContractBundle.load(missing), code('CONTRACT_BUNDLE_INVALID'));
  const tampered = bundleDirectory(); writeFileSync(path.join(tampered, 'test.schema.json'), '{}');
  assert.throws(() => ContractBundle.load(tampered), code('CONTRACT_BUNDLE_INVALID'));
  const profile = bundleDirectory(); update(profile, 'profile.json', (value) => { value.ajv_options.coerceTypes = true; });
  assert.throws(() => ContractBundle.load(profile), code('CONTRACT_BUNDLE_INVALID'));
  const metadata = bundleDirectory(); update(metadata, 'ui-metadata.json', (value) => { value[ID][''].title = 'tampered'; });
  assert.throws(() => ContractBundle.load(metadata), code('CONTRACT_BUNDLE_INVALID'));
  const linked = bundleDirectory(); rmSync(path.join(linked, 'test.schema.json'));
  symlinkSync('/etc/hosts', path.join(linked, 'test.schema.json'));
  assert.throws(() => ContractBundle.load(linked), code('CONTRACT_BUNDLE_INVALID'));
});

function caseFile(directory, cases) {
  const target = path.join(directory, 'cases.json');
  writeFileSync(target, encode({ format: 'schema-conformance-cases/v2', cases }));
  return target;
}
const validCase = (id = 'safe-case') => ({ id, contract: 'test', version: '1', kind: 'instance', input: good(), valid: true });

test('compact raw fixtures expand only exact bounded recipes or one explicit raw string', () => {
  const entry = (raw_repeat) => ({ kind: 'raw-json', raw_repeat });
  const recipe = { prefix: 'prefix', character: 'x', suffix: 'suffix', count: 3 };
  assert.equal(rawForCase({ kind: 'raw-json', raw: '{}' }), '{}');
  assert.equal(rawForCase(entry(recipe)), 'prefixxxxsuffix');
  assert.equal(rawForCase(entry({ ...recipe, count: 0 })), 'prefixsuffix');
  for (const character of ['[', ']', '{', '}']) {
    assert.equal(rawForCase(entry({ ...recipe, character })), `prefix${character.repeat(3)}suffix`);
  }
  assert.equal(rawForCase(entry({ prefix: '', character: 'x', suffix: '', count: 16_777_217 })).length, 16_777_217);
  for (const invalid of [null, [], {}, { ...recipe, extra: true }, { ...recipe, prefix: 1 },
    { ...recipe, suffix: null }, { ...recipe, character: '' }, { ...recipe, character: 'xx' },
    { ...recipe, character: '😀' }, { ...recipe, character: 'a' }, { ...recipe, count: -1 },
    { ...recipe, count: 1.5 }, { ...recipe, count: true }, { ...recipe, count: '1' },
    { ...recipe, count: 16_777_218 }, { ...recipe, count: Infinity }, { ...recipe, count: NaN }]) {
    assert.throws(() => rawForCase(entry(invalid)), code('CONTRACT_CASE_INVENTORY_INVALID'));
  }
  for (const invalid of [null, [], {}, { kind: 'instance', raw: '{}' }, { kind: 'raw-json', raw: 1 },
    { kind: 'raw-json', raw: '{}', raw_repeat: recipe }]) {
    assert.throws(() => rawForCase(invalid), code('CONTRACT_CASE_INVENTORY_INVALID'));
  }
});

test('runner executes positive and limit-refused compact raw cases through the real decoder', () => {
  const directory = bundleDirectory();
  const bundle = ContractBundle.load(directory);
  const recipe = { prefix: '{"name":"', character: 'x', suffix: '","amount":"1.00"}', count: 3 };
  const compact = { id: 'compact', contract: 'test', version: '1', kind: 'raw-json', raw_repeat: recipe, valid: true };
  const oversized = { ...compact, id: 'oversized', raw_repeat: { ...recipe, count: 16_777_217 }, valid: false };
  const report = runCases(caseFile(directory, [compact, oversized]), null, { bundle });
  assert.equal(report.total, 2);
  assert.equal(report.failed, 0);
  assert.equal(report.cases[1].code, 'CONTRACT_JSON_UNSUPPORTED');
  assert.throws(() => runCases(caseFile(directory, [{ ...compact, raw_repeat: { ...recipe, count: true }, valid: false }]), null, { bundle }), code('CONTRACT_CASE_INVENTORY_INVALID'));
  assert.throws(() => runCases(caseFile(directory, [{ ...validCase(), raw_repeat: recipe }]), null, { bundle }), code('CONTRACT_CASE_INVENTORY_INVALID'));
});

test('runner joins expectations and persists only safe case identities/results', () => {
  const directory = bundleDirectory();
  const bundle = ContractBundle.load(directory);
  const cases = [validCase(), { ...validCase('invalid'), input: { secret: 'do-not-log' }, valid: false },
    { id: 'raw', contract: 'test', version: '1', kind: 'raw-json', raw: '{"a":1,"a":2}', valid: false }];
  const output = path.join(directory, 'results.json');
  const report = runCases(caseFile(directory, cases), output, { bundle });
  assert.equal(report.total, 3); assert.equal(report.failed, 0);
  assert.equal(report.cases[1].code, 'CONTRACT_INSTANCE_INVALID');
  assert.equal(report.versions.ajv, consumerVersions().ajv);
  assert.equal(readFileSync(output, 'utf8').includes('do-not-log'), false);
  assert.equal(runCases(caseFile(directory, [{ ...validCase(), valid: false }]), null, { bundle }).failed, 1);
});

test('runner refuses missing, duplicate, unsupported or malformed inventory entries', () => {
  const directory = bundleDirectory(); const bundle = ContractBundle.load(directory);
  for (const cases of [[], [validCase(), validCase()], [{ ...validCase(), profile: 'native-compat/v1' }],
    [{ ...validCase(), valid: 'yes' }], [{ ...validCase(), kind: 'unknown' }],
    [{ ...validCase(), id: 'bad\nprotected' }], [{ ...validCase(), input: undefined }]]) {
    assert.throws(() => runCases(caseFile(directory, cases), null, { bundle }), code('CONTRACT_CASE_INVENTORY_INVALID'));
  }
  assert.throws(() => runCases(caseFile(directory, [{ ...validCase(), version: '9' }]), null, { bundle }), code('CONTRACT_VERSION_UNSUPPORTED'));
  const malformed = path.join(directory, 'bad-cases.json'); writeFileSync(malformed, '{bad}');
  assert.throws(() => runCases(malformed, null, { bundle }), code('CONTRACT_CASE_INVENTORY_INVALID'));
});

test('real CLI exposes exit status and safe summaries for complete, mismatched and broken runs', () => {
  const directory = bundleDirectory();
  const check = fileURLToPath(new URL('./check.mjs', import.meta.url));
  const casesPath = caseFile(directory, [validCase()]);
  const output = path.join(directory, 'cli-results.json');
  const invoke = (...args) => spawnSync(process.execPath, [check, '--bundle', directory, ...args], { encoding: 'utf8' });
  const passed = invoke('--cases', casesPath, '--output', output);
  assert.equal(passed.status, 0, passed.stderr);
  assert.equal(JSON.parse(passed.stdout).total, 1);
  assert.equal(JSON.parse(readFileSync(output, 'utf8')).failed, 0);
  caseFile(directory, [{ ...validCase(), valid: false }]);
  assert.equal(invoke('--cases', casesPath).status, 1);
  for (const args of [['--unexpected', 'secret-do-not-print'], ['--cases'], ['--cases', casesPath, '--cases', casesPath]]) {
    const failed = invoke(...args);
    assert.equal(failed.status, 2);
    assert.equal(failed.stderr.trim(), 'CONTRACT_CASE_INVENTORY_INVALID');
    assert.equal(failed.stderr.includes('secret-do-not-print'), false);
  }
});
