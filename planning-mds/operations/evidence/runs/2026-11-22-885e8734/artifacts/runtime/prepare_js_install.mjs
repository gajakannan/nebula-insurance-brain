import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {createRequire} from 'node:module';

const root='/app/brain';
const out=`${root}/planning-mds/operations/evidence/runs/2026-11-22-885e8734/artifacts/install-final/javascript`;
fs.mkdirSync(out,{recursive:true});
for(const relative of ['experience/scripts/contracts','experience/src/generated/contracts/v1']){
  fs.cpSync(`${root}/${relative}`,`${out}/${relative}`,{recursive:true,dereference:true});
}
fs.copyFileSync(`${root}/scripts/contracts/cases.json`,`${out}/cases.json`);
const req=createRequire(`${root}/experience/package.json`);
const copied=new Map();
function copyPackage(name,from){
  let directory=path.dirname(fs.realpathSync(req.resolve(name,{paths:[from]})));
  let info;
  while(directory!==path.dirname(directory)){
    const manifest=path.join(directory,'package.json');
    if(fs.existsSync(manifest)){
      const value=JSON.parse(fs.readFileSync(manifest,'utf8'));
      if(value.name===name){info=value;break;}
    }
    directory=path.dirname(directory);
  }
  if(!info)throw new Error('Installed package root not found');
  if(copied.has(name)){
    if(copied.get(name)!==info.version)throw new Error('Conflicting installed package versions');
    return;
  }
  copied.set(name,info.version);
  fs.cpSync(directory,`${out}/experience/node_modules/${name}`,{recursive:true,dereference:true});
  for(const child of Object.keys(info.dependencies??{}))copyPackage(child,directory);
}
for(const name of ['ajv','ajv-formats','jsonc-parser'])copyPackage(name,`${root}/experience`);
const digest=crypto.createHash('sha256').update(fs.readFileSync(`${root}/schemas/contracts/v1/manifest.json`)).digest('hex');
const preparation={node:process.versions.node,bundle_digest:digest,packages:Object.fromEntries(copied),
  cases:JSON.parse(fs.readFileSync(`${out}/cases.json`,'utf8')).cases.length,
  scripts:fs.readdirSync(`${out}/experience/scripts/contracts`).sort()};
fs.writeFileSync(`${out}/preparation.json`,JSON.stringify(preparation,null,2)+'\n');
const probe=`import fs from 'node:fs';
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
fs.writeFileSync('/output/installed-js-results.json',JSON.stringify(report,null,2)+'\\n');
console.log(JSON.stringify(report));
`;
fs.writeFileSync(`${out}/installed_js_probe.mjs`,probe);
console.log(JSON.stringify(preparation));
