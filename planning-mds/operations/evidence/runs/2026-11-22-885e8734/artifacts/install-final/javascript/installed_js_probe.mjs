import fs from 'node:fs';
import assert from 'node:assert/strict';
import {installedBundle,consumerVersions} from './experience/scripts/contracts/runtime.mjs';
import {runCases} from './experience/scripts/contracts/check.mjs';
assert.equal(fs.existsSync('/app/brain/experience'),false);
assert.equal(fs.existsSync('/app/brain/planning-mds'),false);
const expected=JSON.parse(fs.readFileSync('/packages/preparation.json','utf8'));
const bundle=installedBundle();
assert.equal(bundle.digest,expected.bundle_digest);
const cases=runCases('/packages/cases.json','/output/installed-js-cases.json',{bundle});
assert.equal(cases.total,expected.cases);
assert.equal(cases.failed,0);
const report={status:'pass',total_cases:cases.total,failed:cases.failed,bundle_digest:bundle.digest,
 versions:consumerVersions(),checkout_unavailable:true,network:'none',copied_scripts:expected.scripts};
fs.writeFileSync('/output/installed-js-results.json',JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify(report));
