#!/usr/bin/env python3
"""Hash every git-tracked file of a repo, anchored at <root>. Symlinks hash their target string (no follow).
Usage: tree-hash.py <root>  -> prints '<sha256>  <path>' lines plus a final 'TOTAL n' line."""
import hashlib, os, subprocess, sys
root = os.path.abspath(sys.argv[1])
files = subprocess.run(["git", "-C", root, "ls-files", "-z"], capture_output=True, check=True).stdout.split(b"\0")
n = 0
for f in filter(None, files):
    p = os.path.join(root, f.decode())
    if os.path.islink(p):
        h = "link:" + hashlib.sha256(os.readlink(p).encode()).hexdigest()
    elif os.path.isfile(p):
        h = hashlib.sha256(open(p, "rb").read()).hexdigest()
    else:
        h = "MISSING"
    print(f"{h}  {f.decode()}"); n += 1
print(f"TOTAL {n}")
