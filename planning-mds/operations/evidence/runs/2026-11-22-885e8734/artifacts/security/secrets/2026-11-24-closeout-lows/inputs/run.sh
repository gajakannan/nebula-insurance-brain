#!/bin/sh
set -eu
stage=/tmp/f0011-secrets-source
mkdir -p "$stage"
while IFS= read -r relative; do
    [ -n "$relative" ] || continue
    parent=$(dirname "$relative")
    mkdir -p "$stage/$parent"
    cp "/scan/$relative" "$stage/$relative"
done < /inputs/paths.txt
sh /framework/agents/security/scripts/check-secrets.sh --path "$stage" --mode filesystem --report-dir /reports -- --no-git
