import { readFileSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import {
  ContractBundle, ContractError, consumerVersions, decodePortableJson, installedBundle,
} from './runtime.mjs';
import { rawForCase } from './case-data.mjs';

const SAFE_ID = /^[A-Za-z0-9][A-Za-z0-9_.:/-]{0,159}$/;

/** Every declared portable case produces exactly one safe result or the run fails. */
export function runCases(casesPath, outputPath, { bundle = installedBundle() } = {}) {
  let inventory;
  try { inventory = decodePortableJson(readFileSync(casesPath)); }
  catch { throw new ContractError('CONTRACT_CASE_INVENTORY_INVALID'); }
  if (!Array.isArray(inventory.cases) || !inventory.cases.length) {
    throw new ContractError('CONTRACT_CASE_INVENTORY_INVALID');
  }
  const ids = new Set();
  for (const entry of inventory.cases) {
    if (!entry || typeof entry.id !== 'string' || !SAFE_ID.test(entry.id) || ids.has(entry.id)
        || typeof entry.contract !== 'string' || !/^[a-z][a-z0-9-]*(?:\.schema\.json)?$/.test(entry.contract)
        || typeof entry.version !== 'string' || !/^[1-9][0-9]*$/.test(entry.version)
        || typeof entry.valid !== 'boolean' || !['instance', 'raw-json'].includes(entry.kind)
        || (entry.profile ?? 'portable-json/v1') !== 'portable-json/v1'
        || (entry.kind === 'instance' && (!Object.hasOwn(entry, 'input') || Object.hasOwn(entry, 'raw') || Object.hasOwn(entry, 'raw_repeat')))
        || (entry.kind === 'raw-json' && (Object.hasOwn(entry, 'input')
          || Object.hasOwn(entry, 'raw') === Object.hasOwn(entry, 'raw_repeat')))) {
      throw new ContractError('CONTRACT_CASE_INVENTORY_INVALID');
    }
    ids.add(entry.id);
  }
  const results = inventory.cases.map((entry) => {
    const ref = { name: entry.contract, version: entry.version, pointer: entry.pointer ?? '' };
    // A missing schema/version is a broken runner, never an expected invalid instance.
    bundle.schema(ref);
    let accepted = true;
    let code;
    try {
      const value = entry.kind === 'raw-json' ? bundle.decode(rawForCase(entry)) : entry.input;
      bundle.validate(ref, value);
    } catch (error) {
      if (!(error instanceof ContractError)
          || !['CONTRACT_INSTANCE_INVALID', 'CONTRACT_JSON_INVALID', 'CONTRACT_JSON_UNSUPPORTED'].includes(error.code)) throw error;
      accepted = false;
      code = error.code;
    }
    return {
      id: entry.id, accepted, contract: entry.contract, version: entry.version,
      consumer: 'ajv', profile: 'portable-json/v1', ...(code ? { code } : {}),
    };
  });
  const failed = results.filter((result, index) => result.accepted !== inventory.cases[index].valid).length;
  const report = {
    format: 'schema-conformance-results/v1', consumer: 'ajv',
    bundle_digest: bundle.digest, versions: consumerVersions(),
    cases: results, total: results.length, failed,
  };
  if (outputPath) writeFileSync(outputPath, `${JSON.stringify(report, null, 2)}\n`);
  return report;
}

function main(args) {
  const options = {};
  for (let index = 0; index < args.length; index += 2) {
    if (!['--cases', '--output', '--bundle'].includes(args[index]) || !args[index + 1] || options[args[index]]) {
      throw new ContractError('CONTRACT_CASE_INVENTORY_INVALID');
    }
    options[args[index]] = args[index + 1];
  }
  const casesPath = options['--cases'] ?? fileURLToPath(new URL('../../../scripts/contracts/cases.json', import.meta.url));
  const bundle = options['--bundle'] ? ContractBundle.load(options['--bundle']) : installedBundle();
  const report = runCases(casesPath, options['--output'], { bundle });
  process.stdout.write(`${JSON.stringify({ consumer: report.consumer, total: report.total, failed: report.failed, bundle_digest: report.bundle_digest })}\n`);
  process.exitCode = report.failed ? 1 : 0;
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  try { main(process.argv.slice(2)); }
  catch (error) {
    // Never print exception text from a parser/compiler or any instance content.
    process.stderr.write(`${error instanceof ContractError ? error.code : 'CONTRACT_CHECK_FAILED'}\n`);
    process.exitCode = 2;
  }
}
