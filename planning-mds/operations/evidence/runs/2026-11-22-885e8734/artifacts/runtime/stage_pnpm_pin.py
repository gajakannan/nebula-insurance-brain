"""Stage the exact pnpm pin correction as a reviewable two-line patch."""
import difflib
from pathlib import Path

root = Path('/home/gajap/uSandbox/repos/nebula/nebula-insurance-brain')
folder = Path(__file__).resolve().parent
original = (root/'docker/contracts/Dockerfile').read_text()
old_env = 'ENV XDG_CACHE_HOME=/tmp/cache COREPACK_HOME=/tmp/corepack PNPM_HOME=/tmp/pnpm'
old_run = 'RUN corepack pnpm --dir experience install --frozen-lockfile --store-dir /tmp/pnpm-store'
assert original.count(old_env) == original.count(old_run) == 1
new_run = 'RUN corepack prepare pnpm@12.21.0 --activate && corepack pnpm --dir experience install --frozen-lockfile --store-dir /tmp/pnpm-store'
proposed = original.replace(old_env, old_env+' COREPACK_DEFAULT_TO_LATEST=0').replace(old_run,new_run)
(folder/'Dockerfile.pnpm-pin-proposal').write_text(proposed)
(folder/'pnpm-selection.patch').write_text(''.join(difflib.unified_diff(
    original.splitlines(keepends=True), proposed.splitlines(keepends=True),
    fromfile='a/docker/contracts/Dockerfile', tofile='b/docker/contracts/Dockerfile')))
print(folder/'pnpm-selection.patch')
