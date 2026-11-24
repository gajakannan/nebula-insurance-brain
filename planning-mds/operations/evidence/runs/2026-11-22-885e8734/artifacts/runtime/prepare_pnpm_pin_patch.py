"""Stage a reviewable build-harness correction without editing product source."""
import difflib
from pathlib import Path

root = Path('/home/gajap/uSandbox/repos/nebula/nebula-insurance-brain')
folder = Path(__file__).resolve().parent
source = root / 'docker/contracts/Dockerfile'
original = source.read_text()
old_env = 'ENV XDG_CACHE_HOME=/tmp/cache COREPACK_HOME=/tmp/corepack PNPM_HOME=/tmp/pnpm'
old_run = 'RUN corepack pnpm --dir experience install --frozen-lockfile --store-dir /tmp/pnpm-store'
if original.count(old_env) != 1 or original.count(old_run) != 1:
    raise RuntimeError('Unexpected Dockerfile; patch requires review')
proposed = original.replace(old_env, old_env + ' COREPACK_DEFAULT_TO_LATEST=0').replace(
    old_run, 'RUN corepack prepare pnpm@12.21.0 --activate \\\n+    && corepack pnpm --dir experience install --frozen-lockfile --store-dir /tmp/pnpm-store')
(folder/'Dockerfile.pnpm-pin-proposal').write_text(proposed)
(folder/'pnpm-selection.patch').write_text(''.join(difflib.unified_diff(
    original.splitlines(keepends=True), proposed.splitlines(keepends=True),
    fromfile='a/docker/contracts/Dockerfile', tofile='b/docker/contracts/Dockerfile')))
print(folder/'pnpm-selection.patch')
