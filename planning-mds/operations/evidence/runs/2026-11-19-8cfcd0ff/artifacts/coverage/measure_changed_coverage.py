"""Changed executable-line coverage: lines added/modified vs origin/main in engine
source (not tests) intersected with coverage.py's executable statements."""
import json, re, subprocess, sys, pathlib
P = pathlib.Path('/home/gajap/uSandbox/repos/nebula/nebula-insurance-brain')
cov = json.loads(pathlib.Path(sys.argv[1]).read_text())
files = {}
for name, data in cov['files'].items():
    full = (P / 'engine' / name).resolve() if not name.startswith('/') else pathlib.Path(name)
    rel = str(full.relative_to(P))
    files[rel] = (set(data['executed_lines']), set(data['missing_lines']))
diff = subprocess.run(['git', '-C', str(P), 'diff', '-U0', 'origin/main', '--', 'engine'], capture_output=True, text=True).stdout
untracked = subprocess.run(['git', '-C', str(P), 'ls-files', '--others', '--exclude-standard', 'engine'], capture_output=True, text=True).stdout.split()
changed = {}
cur = None
for line in diff.splitlines():
    if line.startswith('+++ b/'):
        cur = line[6:]; changed.setdefault(cur, set())
    m = re.match(r'@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@', line)
    if m and cur:
        start, n = int(m.group(1)), int(m.group(2) or 1)
        changed[cur].update(range(start, start + n))
for f in untracked:
    if f.endswith('.py'):
        changed[f] = set(range(1, sum(1 for _ in open(P / f)) + 1))
rows = []
tot_hit = tot_exec = 0
for f, lines in sorted(changed.items()):
    if '/tests/' in f or not f.endswith('.py') or '/migrations/' in f and False:
        continue
    if f not in files:
        rows.append((f, None, None, 'not measured')); continue
    executed, missing = files[f]
    ex = lines & (executed | missing)
    hit = lines & executed
    tot_hit += len(hit); tot_exec += len(ex)
    rows.append((f, len(hit), len(ex), sorted(lines & missing)))
for r in rows:
    print(r[0], f"{r[1]}/{r[2]}" if r[1] is not None else '', r[3] if r[3] else '')
print(f"TOTAL changed executable lines covered: {tot_hit}/{tot_exec} = {100*tot_hit/max(tot_exec,1):.2f}%")
