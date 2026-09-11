#!/usr/bin/env python3
"""Validate Brain planning structure; architectural judgment belongs to reviewers."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CHECK_ID = "plan-readiness"
FEATURE = re.compile(r"F\d{4}")
CHECKLIST_COLUMNS = ["Rule ID", "Owner", "Criterion", "Governing source", "Planning evidence to inspect"]
RULES = {"BRAIN-SCOPE", "BRAIN-AUTHORITY", "BRAIN-EVIDENCE", "BRAIN-PARSE-ONCE", "BRAIN-TEMPORAL", "BRAIN-AUTHORIZATION", "BRAIN-BUILDABILITY", "BRAIN-EXAMPLES"}


def local_path(root: Path, value: str) -> Path:
    path = (root / value).resolve()
    if not path.is_relative_to(root) or ".." in Path(value).parts:
        raise ValueError(f"Path escapes product: {value}")
    return path


def validate(root: Path, scope: str, target: str) -> list[dict[str, str]]:
    findings = []

    def fail(rule: str, message: str, path: str):
        findings.append({"rule_id": rule, "message": message, "path": path})

    def read(value: str) -> str:
        path = local_path(root, value)
        if not path.is_file():
            fail("BRAIN-ARTIFACT", "Required planning artifact is missing.", value)
            return ""
        text = path.read_text(encoding="utf-8")
        if not re.sub(r"[#\s|:*-]", "", text):
            fail("BRAIN-ARTIFACT", "Required planning artifact is empty.", value)
        return text

    def sections(text: str, required: list[str], path: str):
        headings = list(re.finditer(r"^##\s+(.+?)\s*$", text, re.M))
        bodies = {m.group(1).lower(): text[m.end():headings[i + 1].start() if i + 1 < len(headings) else len(text)].strip()
                  for i, m in enumerate(headings)}
        for heading in required:
            body = bodies.get(heading.lower(), "")
            if not body or re.fullmatch(r"[\s#*_-]*(?:TODO|TBD|Pending|\.\.\.)[\s.*_-]*", body, re.I):
                fail("BRAIN-SECTIONS", f"Missing or placeholder section: {heading}", path)

    for required in ["planning-mds/BLUEPRINT.md", "docs/agent-instructions.md"]:
        read(required)
    checklist_path = "docs/plan-review-checklist.md"
    checklist = read(checklist_path)
    rows = [[c.strip().strip("`") for c in line.strip().strip("|").split("|")]
            for line in checklist.splitlines() if line.startswith("|")]
    if not rows or rows[0] != CHECKLIST_COLUMNS:
        fail("BRAIN-CHECKLIST", "Review checklist is missing its required columns.", checklist_path)
    present = set()
    for row in rows[2:]:
        if len(row) != len(CHECKLIST_COLUMNS) or any(not cell for cell in row):
            fail("BRAIN-CHECKLIST", "Every checklist entry needs an owner, criterion, governing source, and planning evidence guidance.", checklist_path)
            continue
        rule, owner, _, source, _ = row
        if rule in present:
            fail("BRAIN-CHECKLIST", f"Duplicate checklist rule: {rule}", checklist_path)
        present.add(rule)
        if owner not in {"product-manager", "architect", "security", "code-reviewer"}:
            fail("BRAIN-CHECKLIST", f"Unknown review owner: {owner}", checklist_path)
        read(source)
    for missing in sorted(RULES - present):
        fail("BRAIN-CHECKLIST", f"Required local review criterion missing: {missing}", checklist_path)

    registry_path = "planning-mds/features/REGISTRY.md"
    registry = read(registry_path)
    entries = {}
    active = set()
    for line in registry.splitlines():
        cells = [c.strip().strip("`") for c in line.strip().strip("|").split("|")]
        if cells and FEATURE.fullmatch(cells[0]):
            folders = [c for c in cells[1:] if re.fullmatch(r"(?:archive/)?F\d{4}-[a-z0-9-]+/?", c)]
            if len(folders) != 1 or cells[0] in entries:
                fail("BRAIN-REGISTRY", f"Invalid or duplicate registry entry: {cells[0]}", registry_path)
                continue
            entries[cells[0]] = "planning-mds/features/" + folders[0].rstrip("/")
            if "Active" in cells or "In Progress" in cells:
                active.add(cells[0])
    if scope == "project":
        if target != "project":
            raise ValueError("Project scope requires target 'project'.")
        targets = sorted(k for k, p in entries.items()
                         if "/archive/" not in p and (k in active or (local_path(root, p) / "PRD.md").exists()))
    else:
        targets = [t.strip() for t in target.split(",")]
        if scope not in {"feature", "feature-set"} or (scope == "feature" and len(targets) != 1):
            raise ValueError("Scope does not match the requested targets.")
        if len(set(targets)) != len(targets) or any(not FEATURE.fullmatch(t) for t in targets):
            raise ValueError("Targets must be distinct feature IDs.")
    for feature in targets:
        if feature not in entries:
            fail("BRAIN-TARGET", f"Target is not registered: {feature}", registry_path)
            continue
        folder = entries[feature]
        for filename in ["README.md", "STATUS.md"]:
            read(f"{folder}/{filename}")
        prd_path = f"{folder}/PRD.md"
        prd = read(prd_path)
        sections(prd, ["Feature Statement", "Scope & Boundaries", "Acceptance Criteria Overview", "Dependencies"], prd_path)
        stories = sorted(local_path(root, folder).glob(f"{feature}-S[0-9][0-9][0-9][0-9]-*.md"))
        if not stories:
            fail("BRAIN-STORIES", "Planned feature has no story artifacts.", prd_path)
        planning_documents = [(prd_path, prd)]
        for path in stories:
            relative = path.relative_to(root).as_posix()
            text = read(relative)
            sections(text, ["User Story", "Acceptance Criteria"], relative)
            planning_documents.append((relative, text))
        # Links to authored planning files must resolve. Inline code naming future
        # runtime files is intentionally not interpreted as an existence claim.
        for source, text in planning_documents:
            for match in re.finditer(r"\]\(([^)]+)\)", text):
                link = match.group(1).split("#", 1)[0]
                if not link or "://" in link or link.startswith("mailto:"):
                    continue
                candidate = (root / source).parent / link
                resolved = candidate.resolve()
                if not resolved.is_relative_to(root):
                    fail("BRAIN-REFERENCE", f"Planning link escapes product: {link}", source)
                elif resolved.is_relative_to(root / "planning-mds") and not resolved.exists():
                    fail("BRAIN-REFERENCE", f"Required planning reference does not resolve: {link}", source)
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--product-root", type=Path, default=ROOT)
    parser.add_argument("--plan-scope", choices=["feature", "feature-set", "project"], required=True)
    parser.add_argument("--target", required=True)
    args = parser.parse_args(argv)
    try:
        findings = validate(args.product_root.resolve(), args.plan_scope, args.target)
        rc = 1 if findings else 0
    except (OSError, ValueError) as exc:
        findings = [{"rule_id": "BRAIN-INVOCATION", "message": str(exc), "path": "planning-mds/BLUEPRINT.md"}]
        rc = 2
    print(json.dumps({"schema_version": 1, "check_id": CHECK_ID, "status": "fail" if rc else "pass", "findings": findings}, indent=2))
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
