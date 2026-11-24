import { createHash } from 'node:crypto';
import { readFileSync, realpathSync } from 'node:fs';
import { createRequire } from 'node:module';
import { isIP } from 'node:net';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import Ajv2020 from 'ajv/dist/2020.js';
import addFormats from 'ajv-formats';
import { visit } from 'jsonc-parser';

const require = createRequire(import.meta.url);
const DIALECT = 'https://json-schema.org/draft/2020-12/schema';
const PROFILE = 'portable-json/v1';
const MAX_BYTES = 16 * 1024 * 1024;
const MAX_DEPTH = 128;
const MAX_NODES = 1_000_000;
const MAX_RESOURCES = 256;
const RESOURCE_PATH = /^[a-z][a-z0-9-]*\.schema\.json$/;
const ANNOTATIONS = {
  title: 'string', description: 'string', default: 'json', examples: 'array',
  'x-nebula-concept': 'string', 'x-nebula-display-name': 'string',
  'x-nebula-evidence-required': 'boolean', 'x-nebula-relationship': 'string',
  'x-nebula-security-scope': 'string', 'x-nebula-extraction-hint': 'string',
  'x-nebula-line-of-business': 'string', 'x-nebula-document-profile': 'string',
};
const VALIDATION_KEYWORDS = [
  'type', 'const', 'enum', 'properties', 'required', 'additionalProperties',
  'propertyNames', 'maxProperties', 'items', 'minItems', 'maxItems', 'uniqueItems',
  'contains', 'minContains', 'maxContains', 'minimum', 'maximum', 'exclusiveMinimum',
  'minLength', 'maxLength', 'pattern', 'format', 'allOf', 'anyOf', 'oneOf',
  'if', 'then', 'else', 'not',
];
const CORE_KEYWORDS = ['$schema', '$id', '$ref', '$defs'];
const TOOLCHAIN_KEYS = ['builder', 'python', 'jsonschema', 'referencing', 'pydantic', 'datamodel_code_generator', 'ajv', 'ajv_formats', 'jsonc_parser'];
const ALLOWED = new Set([...VALIDATION_KEYWORDS, ...CORE_KEYWORDS, ...Object.keys(ANNOTATIONS)]);
const SINGLE_SCHEMA = new Set([
  'additionalProperties', 'propertyNames', 'items', 'contains', 'if', 'then', 'else', 'not',
]);
const ARRAY_SCHEMA = new Set(['allOf', 'anyOf', 'oneOf']);
export const AJV_OPTIONS = Object.freeze({
  strictSchema: true, strictNumbers: true, strictTypes: false, strictRequired: false,
  allowUnionTypes: true, allErrors: false, validateFormats: true,
  useDefaults: false, coerceTypes: false, removeAdditional: false, ownProperties: true,
});

export class ContractError extends Error {
  constructor(code, contractId = '', schemaPointer = '') {
    super(code);
    this.name = 'ContractError';
    this.code = code;
    this.contract_id = contractId;
    this.schema_pointer = schemaPointer;
  }
}

function fail(code, contractId, schemaPointer) {
  throw new ContractError(code, contractId, schemaPointer);
}

function pairedUnicode(value) {
  for (let index = 0; index < value.length; index += 1) {
    const unit = value.charCodeAt(index);
    if (unit >= 0xd800 && unit <= 0xdbff) {
      const next = value.charCodeAt(++index);
      if (!(next >= 0xdc00 && next <= 0xdfff)) return false;
    } else if (unit >= 0xdc00 && unit <= 0xdfff) return false;
  }
  return true;
}

function scalar(value) {
  if (typeof value === 'string' && !pairedUnicode(value)) fail('CONTRACT_JSON_UNSUPPORTED');
  if (typeof value === 'number'
      && (!Number.isFinite(value) || (Number.isInteger(value) && !Number.isSafeInteger(value)))) {
    fail('CONTRACT_JSON_UNSUPPORTED');
  }
}

/** Strict decoding precedes AJV; the visitor never repairs malformed input. */
export function decodePortableJson(raw) {
  let source;
  try {
    if (typeof raw === 'string') source = raw;
    else if (raw instanceof Uint8Array) {
      source = new TextDecoder('utf-8', { fatal: true, ignoreBOM: true }).decode(raw);
    } else fail('CONTRACT_JSON_INVALID');
  } catch (error) {
    if (error instanceof ContractError) throw error;
    fail('CONTRACT_JSON_INVALID');
  }
  if (Buffer.byteLength(source, 'utf8') > MAX_BYTES) fail('CONTRACT_JSON_UNSUPPORTED');
  let depth = 0;
  let nodes = 0;
  const objects = [];
  const count = () => {
    nodes += 1;
    if (nodes > MAX_NODES) fail('CONTRACT_JSON_UNSUPPORTED');
  };
  const begin = () => {
    count();
    depth += 1;
    if (depth > MAX_DEPTH) fail('CONTRACT_JSON_UNSUPPORTED');
  };
  try {
    visit(source, {
      onObjectBegin() { begin(); objects.push(new Set()); },
      onObjectEnd() { depth -= 1; objects.pop(); },
      onArrayBegin: begin,
      onArrayEnd() { depth -= 1; },
      onObjectProperty(key) {
        scalar(key);
        const keys = objects.at(-1);
        if (!keys || keys.has(key)) fail('CONTRACT_JSON_INVALID');
        keys.add(key);
      },
      onLiteralValue(value) {
        count();
        if (depth + 1 > MAX_DEPTH) fail('CONTRACT_JSON_UNSUPPORTED');
        scalar(value);
      },
      onError() { fail('CONTRACT_JSON_INVALID'); },
    }, { disallowComments: true, allowTrailingComma: false, allowEmptyContent: false });
    return JSON.parse(source);
  } catch (error) {
    if (error instanceof ContractError) throw error;
    fail('CONTRACT_JSON_INVALID');
  }
}

/** Admit already-decoded JSON without invoking getters or serializing away data. */
export function admitPortableJson(value) {
  let nodes = 0;
  const ancestors = new Set();
  function walk(current, depth) {
    nodes += 1;
    if (nodes > MAX_NODES || depth > MAX_DEPTH) fail('CONTRACT_JSON_UNSUPPORTED');
    scalar(current);
    if (current === null || ['string', 'boolean', 'number'].includes(typeof current)) return;
    if (typeof current !== 'object' || ancestors.has(current)) fail('CONTRACT_JSON_UNSUPPORTED');
    const array = Array.isArray(current);
    const prototype = Object.getPrototypeOf(current);
    if (!array && prototype !== Object.prototype && prototype !== null) fail('CONTRACT_JSON_UNSUPPORTED');
    if (Object.getOwnPropertySymbols(current).length) fail('CONTRACT_JSON_UNSUPPORTED');
    ancestors.add(current);
    const descriptors = Object.getOwnPropertyDescriptors(current);
    if (array) {
      if (Object.keys(descriptors).length !== current.length + 1) fail('CONTRACT_JSON_UNSUPPORTED');
      for (let index = 0; index < current.length; index += 1) {
        const item = descriptors[index];
        if (!item || !Object.hasOwn(item, 'value')) fail('CONTRACT_JSON_UNSUPPORTED');
        walk(item.value, depth + 1);
      }
    } else {
      for (const [key, descriptor] of Object.entries(descriptors)) {
        scalar(key);
        if (!descriptor.enumerable || !Object.hasOwn(descriptor, 'value')) fail('CONTRACT_JSON_UNSUPPORTED');
        walk(descriptor.value, depth + 1);
      }
    }
    ancestors.delete(current);
  }
  walk(value, 1);
  if (Buffer.byteLength(JSON.stringify(value), 'utf8') > MAX_BYTES) fail('CONTRACT_JSON_UNSUPPORTED');
}

export function portableDate(value) {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(value);
  if (!match) return false;
  const [, yearText, monthText, dayText] = match;
  const year = Number(yearText);
  const month = Number(monthText);
  const day = Number(dayText);
  if (!year || month < 1 || month > 12 || day < 1) return false;
  const leap = year % 4 === 0 && (year % 100 !== 0 || year % 400 === 0);
  return day <= [31, leap ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1];
}

export function portableDateTime(value) {
  const match = /^(\d{4}-\d{2}-\d{2})[tT](\d{2}):(\d{2}):(\d{2})(?:\.\d+)?(?:[zZ]|([+-])(\d{2}):(\d{2}))$/.exec(value);
  return Boolean(match && portableDate(match[1]) && Number(match[2]) <= 23
    && Number(match[3]) <= 59 && Number(match[4]) <= 59
    && (match[6] === undefined || (Number(match[6]) <= 23 && Number(match[7]) <= 59)));
}

export function portableUriReference(value) {
  // RFC3986 grammar is deliberately independent of WHATWG URL repair/normalization.
  if (/[^\x21-\x7e]/.test(value) || /%(?![0-9A-Fa-f]{2})/.test(value)) return false;
  const parts = /^([^?#]*)(?:\?([^#]*))?(?:#([^#]*))?$/.exec(value);
  if (!parts) return false;
  const pchar = /^[A-Za-z0-9\-._~!$&'()*+,;=:@%/]*$/;
  const queryOrFragment = /^[A-Za-z0-9\-._~!$&'()*+,;=:@%/?]*$/;
  if ((parts[2] !== undefined && !queryOrFragment.test(parts[2]))
      || (parts[3] !== undefined && !queryOrFragment.test(parts[3]))) return false;
  const scheme = /^[A-Za-z][A-Za-z0-9+.-]*:/.exec(parts[1]);
  let hierarchical = scheme ? parts[1].slice(scheme[0].length) : parts[1];
  if (hierarchical.startsWith('//')) {
    const slash = hierarchical.indexOf('/', 2);
    const authority = slash === -1 ? hierarchical.slice(2) : hierarchical.slice(2, slash);
    hierarchical = slash === -1 ? '' : hierarchical.slice(slash);
    const at = authority.lastIndexOf('@');
    const userinfo = at === -1 ? '' : authority.slice(0, at);
    const hostport = authority.slice(at + 1);
    if (!/^[A-Za-z0-9\-._~!$&'()*+,;=:%]*$/.test(userinfo)) return false;
    if (hostport.startsWith('[')) {
      const match = /^\[([^\]]+)\](?::([0-9]*))?$/.exec(hostport);
      if (!match || (isIP(match[1]) !== 6
          && !/^v[0-9A-Fa-f]+\.[A-Za-z0-9\-._~!$&'()*+,;=:]+$/i.test(match[1]))) return false;
    } else if (!/^[A-Za-z0-9\-._~!$&'()*+,;=%]*(?::[0-9]*)?$/.test(hostport)) return false;
  } else if (!scheme && !hierarchical.startsWith('/') && hierarchical.split('/', 1)[0].includes(':')) return false;
  if (!pchar.test(hierarchical)) return false;
  return true;
}

function portablePatternSource(value) {
  if (typeof value !== 'string') fail('CONTRACT_SCHEMA_UNSUPPORTED');
  let escaped = false;
  let characterClass = false;
  for (let index = 0; index < value.length; index += 1) {
    const character = value[index];
    if (escaped) { escaped = false; continue; }
    if (character === '\\') { escaped = true; continue; }
    if (character === '[') characterClass = true;
    else if (character === ']') characterClass = false;
    else if (character === '$' && !characterClass && index !== value.length - 1) {
      fail('CONTRACT_SCHEMA_UNSUPPORTED');
    }
  }
  return value;
}

const escapePointer = (key) => key.replaceAll('~', '~0').replaceAll('/', '~1');
const exactKeys = (value, keys) => value !== null && typeof value === 'object' && !Array.isArray(value)
  && Object.keys(value).length === keys.length && keys.every((key) => Object.hasOwn(value, key));
const canonical = (value) => JSON.stringify(value, (_key, current) => current !== null
  && typeof current === 'object' && !Array.isArray(current)
  ? Object.fromEntries(Object.entries(current).sort(([left], [right]) => left.localeCompare(right, 'en'))) : current);

function pointer(root, fragment) {
  if (!fragment) return root;
  if (!fragment.startsWith('/') || /~(?![01])/.test(fragment)) fail('CONTRACT_REFERENCE_UNRESOLVED');
  let target = root;
  for (const encoded of fragment.slice(1).split('/')) {
    const key = encoded.replaceAll('~1', '/').replaceAll('~0', '~');
    if (target === null || typeof target !== 'object' || !Object.hasOwn(target, key)) fail('CONTRACT_REFERENCE_UNRESOLVED');
    target = target[key];
  }
  if (typeof target !== 'boolean' && (target === null || typeof target !== 'object' || Array.isArray(target))) {
    fail('CONTRACT_REFERENCE_UNRESOLVED');
  }
  return target;
}

function schemaChildren(schema, at) {
  const children = [];
  for (const [key, value] of Object.entries(schema)) {
    const location = `${at}/${escapePointer(key)}`;
    if (key === 'properties' || key === '$defs') {
      if (value === null || typeof value !== 'object' || Array.isArray(value)) fail('CONTRACT_SCHEMA_UNSUPPORTED');
      for (const [name, child] of Object.entries(value)) children.push([child, `${location}/${escapePointer(name)}`]);
    } else if (SINGLE_SCHEMA.has(key)) children.push([value, location]);
    else if (ARRAY_SCHEMA.has(key)) {
      if (!Array.isArray(value)) fail('CONTRACT_SCHEMA_UNSUPPORTED');
      value.forEach((child, index) => children.push([child, `${location}/${index}`]));
    }
  }
  return children;
}

export function consumerVersions() {
  return {
    node: process.versions.node,
    ajv: require('ajv/package.json').version,
    ajv_formats: require('ajv-formats/package.json').version,
    jsonc_parser: require('jsonc-parser/package.json').version,
  };
}

/** Immutable, closed local bundle. No loadSchema callback or network retrieval exists. */
export class ContractBundle {
  #resources;
  #byId;
  #metadata;
  #schemaPositions;
  #ajv;
  #validators = new Map();

  static load(directory) {
    try { return new ContractBundle(directory); }
    catch (error) {
      if (error instanceof ContractError) throw error;
      fail('CONTRACT_BUNDLE_INVALID');
    }
  }

  constructor(directory) {
    const base = realpathSync(directory);
    const read = (name) => {
      const file = realpathSync(path.join(base, name));
      if (path.dirname(file) !== base) fail('CONTRACT_BUNDLE_INVALID');
      return readFileSync(file);
    };
    const manifestBytes = read('manifest.json');
    const manifest = decodePortableJson(manifestBytes);
    if (!exactKeys(manifest, ['bundle', 'profile', 'resources', 'toolchain'])
        || manifest.bundle !== 'brain-contracts/v1' || manifest.profile !== 'nebula-json-schema/1'
        || !Array.isArray(manifest.resources) || !manifest.resources.length
        || manifest.resources.length > MAX_RESOURCES || !exactKeys(manifest.toolchain, TOOLCHAIN_KEYS)
        || Object.values(manifest.toolchain).some((version) => typeof version !== 'string' || !version)) {
      fail('CONTRACT_BUNDLE_INVALID');
    }
    this.digest = createHash('sha256').update(manifestBytes).digest('hex');
    const profile = decodePortableJson(read('profile.json'));
    if (profile.id !== 'nebula-json-schema/1' || profile.dialect !== DIALECT
        || Object.entries(AJV_OPTIONS).some(([key, value]) => profile.ajv_options?.[key] !== value)
        || VALIDATION_KEYWORDS.some((key) => !profile.validation_keywords?.includes(key))
        || profile.validation_keywords.length !== VALIDATION_KEYWORDS.length) fail('CONTRACT_BUNDLE_INVALID');
    this.#metadata = decodePortableJson(read('ui-metadata.json'));
    this.#resources = new Map();
    this.#byId = new Map();
    for (const resource of manifest.resources) {
      if (!exactKeys(resource, ['id', 'version', 'path', 'sha256'])
          || typeof resource.path !== 'string' || !RESOURCE_PATH.test(resource.path)
          || typeof resource.version !== 'string' || !/^[1-9][0-9]*$/.test(resource.version)
          || typeof resource.sha256 !== 'string' || !/^[0-9a-f]{64}$/.test(resource.sha256)
          || typeof resource.id !== 'string' || !resource.id) fail('CONTRACT_BUNDLE_INVALID');
      const name = resource.path.replace(/\.schema\.json$/, '');
      if (this.#resources.has(name) || this.#byId.has(resource.id)) fail('CONTRACT_BUNDLE_INVALID');
      const bytes = read(resource.path);
      if (createHash('sha256').update(bytes).digest('hex') !== resource.sha256) fail('CONTRACT_BUNDLE_INVALID');
      const schema = decodePortableJson(bytes);
      if (schema.$id !== resource.id || schema.$schema !== DIALECT) fail('CONTRACT_BUNDLE_INVALID');
      const entry = { ...resource, schema };
      this.#resources.set(name, entry);
      this.#byId.set(resource.id, entry);
    }
    if (canonical(this.#admitSchemas()) !== canonical(this.#metadata)) fail('CONTRACT_BUNDLE_INVALID');
    this.#ajv = new Ajv2020({ ...AJV_OPTIONS, logger: false });
    addFormats(this.#ajv, ['uuid', 'date', 'date-time', 'uri-reference']);
    this.#ajv.addFormat('uuid', /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i);
    this.#ajv.addFormat('date', portableDate);
    this.#ajv.addFormat('date-time', portableDateTime);
    this.#ajv.addFormat('uri-reference', portableUriReference);
    for (const [keyword, type] of Object.entries(ANNOTATIONS)) {
      if (keyword.startsWith('x-nebula-')) this.#ajv.addKeyword({ keyword, schemaType: type, valid: true });
    }
    try {
      for (const { schema } of this.#resources.values()) this.#ajv.addSchema(schema);
      for (const { id } of this.#resources.values()) this.#ajv.getSchema(id);
    } catch { fail('CONTRACT_SCHEMA_UNSUPPORTED'); }
    Object.freeze(this);
  }

  #admitSchemas() {
    const nodes = new Map();
    const metadata = Object.fromEntries([...this.#byId.keys()].map((id) => [id, {}]));
    const visitSchema = (schema, id, location) => {
      const key = `${id}#${location}`;
      if (typeof schema === 'boolean') { nodes.set(key, []); return; }
      if (schema === null || typeof schema !== 'object' || Array.isArray(schema)) fail('CONTRACT_SCHEMA_UNSUPPORTED');
      for (const [keyword, value] of Object.entries(schema)) {
        if (!ALLOWED.has(keyword)) fail('CONTRACT_SCHEMA_UNSUPPORTED', id, location);
        const annotationType = ANNOTATIONS[keyword];
        if (annotationType && annotationType !== 'json'
            && (annotationType === 'array' ? !Array.isArray(value) : typeof value !== annotationType)) {
          fail('CONTRACT_SCHEMA_UNSUPPORTED', id, location);
        }
        if (keyword === 'format' && !['uuid', 'date', 'date-time', 'uri-reference'].includes(value)) fail('CONTRACT_SCHEMA_UNSUPPORTED', id, location);
        if (keyword === 'pattern') portablePatternSource(value);
        if (keyword === '$schema' && value !== DIALECT) fail('CONTRACT_SCHEMA_UNSUPPORTED', id, location);
        if (keyword === '$id' && (location || value !== id)) fail('CONTRACT_SCHEMA_UNSUPPORTED', id, location);
      }
      const annotations = Object.fromEntries(Object.entries(schema).filter(([keyword]) => keyword === 'title'
        || keyword === 'description' || keyword.startsWith('x-nebula-')));
      if (Object.keys(annotations).length) metadata[id][location] = annotations;
      const children = schemaChildren(schema, location);
      const edges = children.map(([, childLocation]) => `${id}#${childLocation}`);
      if (Object.hasOwn(schema, '$ref')) {
        if (typeof schema.$ref !== 'string') fail('CONTRACT_REFERENCE_UNRESOLVED', id, location);
        let uri;
        let fragment;
        try {
          const target = new URL(schema.$ref, id);
          fragment = decodeURIComponent(target.hash.slice(1));
          target.hash = '';
          uri = target.href;
        } catch { fail('CONTRACT_REFERENCE_UNRESOLVED', id, location); }
        const resource = this.#byId.get(uri);
        if (!resource) fail('CONTRACT_REFERENCE_UNRESOLVED', id, location);
        pointer(resource.schema, fragment);
        edges.push(`${uri}#${fragment}`);
      }
      nodes.set(key, edges);
      for (const [child, childLocation] of children) visitSchema(child, id, childLocation);
    };
    for (const { schema, id } of this.#resources.values()) visitSchema(schema, id, '');
    const active = new Set();
    const done = new Set();
    const checkCycle = (key) => {
      if (active.has(key)) fail('CONTRACT_REFERENCE_UNRESOLVED');
      if (done.has(key)) return;
      if (!nodes.has(key)) fail('CONTRACT_REFERENCE_UNRESOLVED');
      active.add(key);
      for (const edge of nodes.get(key)) checkCycle(edge);
      active.delete(key);
      done.add(key);
    };
    for (const key of nodes.keys()) checkCycle(key);
    this.#schemaPositions = new Set(nodes.keys());
    return metadata;
  }

  #resolve(ref) {
    if (!ref || typeof ref.name !== 'string') fail('CONTRACT_VERSION_UNSUPPORTED');
    const resource = this.#resources.get(ref.name.replace(/\.schema\.json$/, ''));
    if (!resource || resource.version !== ref.version) fail('CONTRACT_VERSION_UNSUPPORTED');
    const fragment = ref.pointer ?? '';
    if (typeof fragment !== 'string') fail('CONTRACT_REFERENCE_UNRESOLVED');
    if (!this.#schemaPositions.has(`${resource.id}#${fragment}`)) fail('CONTRACT_REFERENCE_UNRESOLVED');
    pointer(resource.schema, fragment);
    return { resource, fragment };
  }

  schema(ref) {
    const { resource, fragment } = this.#resolve(ref);
    return structuredClone(pointer(resource.schema, fragment));
  }

  metadata(ref) {
    const { resource, fragment } = this.#resolve(ref);
    return structuredClone(this.#metadata[resource.id]?.[fragment] ?? {});
  }

  decode(raw, { profile = PROFILE } = {}) {
    if (profile !== PROFILE) fail('CONTRACT_JSON_UNSUPPORTED');
    return decodePortableJson(raw);
  }

  validate(ref, value, { profile = PROFILE } = {}) {
    if (profile !== PROFILE) fail('CONTRACT_JSON_UNSUPPORTED');
    admitPortableJson(value);
    const { resource, fragment } = this.#resolve(ref);
    const key = `${this.digest}:${resource.id}#${fragment}:${profile}`;
    let validator = this.#validators.get(key);
    if (!validator) {
      try { validator = this.#ajv.compile({ $ref: `${resource.id}#${fragment}` }); }
      catch { fail('CONTRACT_REFERENCE_UNRESOLVED', resource.id, fragment); }
      this.#validators.set(key, validator);
    }
    if (!validator(value)) {
      fail('CONTRACT_INSTANCE_INVALID', resource.id, validator.errors?.[0]?.schemaPath ?? fragment);
    }
  }
}

let defaultBundle;
export function installedBundle() {
  defaultBundle ??= ContractBundle.load(fileURLToPath(new URL('../../src/generated/contracts/v1/', import.meta.url)));
  return defaultBundle;
}

export function validateContract(ref, value) {
  installedBundle().validate(ref, value);
}
