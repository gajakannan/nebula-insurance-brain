// Line coverage for authored contract runtime scripts from raw NODE_V8_COVERAGE data.
// A line counts as covered when the innermost V8 block range at its first non-blank
// character has a nonzero count in any process (max across processes).
import { readFileSync, readdirSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
const [, , v8Dir, srcRoot, out] = process.argv;
const files = ['case-data.mjs', 'check.mjs', 'runtime.mjs'];
const prefix = 'file:///app/brain/experience/scripts/contracts/';
const rows = [];
for (const name of files) {
  const src = readFileSync(join(srcRoot, name), 'utf8');
  const best = new Int32Array(src.length).fill(-1);
  for (const f of readdirSync(v8Dir)) {
    for (const script of JSON.parse(readFileSync(join(v8Dir, f), 'utf8')).result) {
      if (script.url !== prefix + name) continue;
      const counts = new Int32Array(src.length).fill(-1);
      const widths = new Int32Array(src.length).fill(2 ** 30);
      for (const fn of script.functions) for (const r of fn.ranges) {
        const w = r.endOffset - r.startOffset;
        for (let i = r.startOffset; i < Math.min(r.endOffset, src.length); i++)
          if (w <= widths[i]) { widths[i] = w; counts[i] = r.count; }
      }
      for (let i = 0; i < src.length; i++) best[i] = Math.max(best[i], counts[i]);
    }
  }
  let offset = 0, total = 0, covered = 0; const missing = [];
  src.split('\n').forEach((line, idx) => {
    const t = line.trim();
    const code = t && !t.startsWith('//') && !t.startsWith('*') && !t.startsWith('/*') && !/^[})\];,]+$/.test(t);
    if (code) { total++; const i = offset + line.indexOf(t[0]); if (best[i] > 0) covered++; else missing.push(idx + 1); }
    offset += line.length + 1;
  });
  rows.push({ path: 'experience/scripts/contracts/' + name, lines: total, covered, pct: +(100 * covered / total).toFixed(2), missing_lines: missing });
}
const lines = rows.reduce((a, r) => a + r.lines, 0), cov = rows.reduce((a, r) => a + r.covered, 0);
const result = { language: 'JavaScript', source: v8Dir, method: 'innermost V8 block range at first non-blank character, max across processes; comment and bare-delimiter lines excluded', lines, covered: cov, coverage_pct: +(100 * cov / lines).toFixed(2), contract_min_pct: 80, status: 100 * cov / lines >= 80 ? 'pass' : 'fail', files: rows };
writeFileSync(out, JSON.stringify(result, null, 2) + '\n');
console.log(JSON.stringify({ ...result, files: rows.map(r => [r.path, r.pct]) }));
