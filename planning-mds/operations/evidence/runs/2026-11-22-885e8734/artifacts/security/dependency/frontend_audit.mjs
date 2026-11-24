import fs from 'node:fs';
import crypto from 'node:crypto';
import {spawnSync} from 'node:child_process';
const out='/app/brain/planning-mds/operations/evidence/runs/2026-11-22-885e8734/artifacts/security/dependency';
const digest=()=>crypto.createHash('sha256').update(fs.readFileSync('pnpm-lock.yaml')).digest('hex');
const before=digest();
const argv=['pnpm','audit','--json'];
const result=spawnSync('corepack',argv,{encoding:'utf8',maxBuffer:16*1024*1024});
fs.writeFileSync(`${out}/frontend.json`,result.stdout??'');
fs.writeFileSync(`${out}/frontend-auditor.log`,result.stderr??'');
const after=digest();
const record={workspace:'experience',recorded_at_utc:new Date().toISOString(),tool:'pnpm 12.21.0 audit',
 argv:['corepack',...argv],audit_exit_code:result.status,lock_sha256_before:before,lock_sha256_after:after,
 lock_unchanged:before===after,product_fix_requested:false};
fs.writeFileSync(`${out}/frontend-execution.json`,JSON.stringify(record,null,2)+'\n');
console.log(JSON.stringify({workspace:'experience',audit_exit_code:result.status,lock_unchanged:before===after}));
process.exit(before===after?(result.status??2):2);
