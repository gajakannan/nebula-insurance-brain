"""Read-only installed-source inventory for the four SoupSieve advisories.

This is a source reachability aid, not a vulnerability scan or runtime proof.
It neither constructs selectors nor parses attacker input.
"""

from __future__ import annotations

import ast
import importlib.metadata
import json
from datetime import UTC, datetime


report = {"recorded_at_utc": datetime.now(UTC).isoformat(), "scope": "installed Docling-family source and BeautifulSoup wrappers; static aid, not a complete dynamic call graph", "packages": []}
for name in ("soupsieve", "beautifulsoup4", "docling", "docling-slim", "docling-graph", "docling-core", "docling-parse", "docling-ibm-models"):
    distribution = importlib.metadata.distribution(name)
    package = {"name": name, "version": distribution.version, "python_source_files": 0, "source_files_parsed": 0, "read_or_parse_failures": [], "imports_and_selector_calls": []}
    for file in distribution.files or ():
        if not str(file).endswith(".py"):
            continue
        package["python_source_files"] += 1
        path = distribution.locate_file(file)
        try:
            source = path.read_text()
            tree = ast.parse(source)
            package["source_files_parsed"] += 1
        except (OSError, UnicodeError, SyntaxError) as exc:
            package["read_or_parse_failures"].append({"file": str(file), "error_type": type(exc).__name__})
            continue
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names if alias.name.split(".")[0] in {"bs4", "soupsieve"})
            elif isinstance(node, ast.ImportFrom) and (node.module or "").split(".")[0] in {"bs4", "soupsieve"}:
                imports.append(node.module)
        if not imports:
            continue
        lines = source.splitlines()
        calls = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr in {"select", "select_one", "compile", "match", "filter", "closest", "iselect"}:
                calls.append({"line": node.lineno, "source": lines[node.lineno - 1].strip()})
        package["imports_and_selector_calls"].append({"file": str(file), "imports": imports, "candidate_calls": calls})
    report["packages"].append(package)
print(json.dumps(report, indent=2))
