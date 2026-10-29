# F0005 qualification corpus (synthetic development data)

**Synthetic development data.** Thirteen fictional US commercial general liability
declarations documents with independently authored expected values for the
`gl-limits-a` and `gl-limits-b` extraction profiles. Every name, address, policy number
and form number is invented. This corpus is not `golden-corpus/` and not the frozen holdout.

## Regenerate

From the product repo root:

```
neuron/.venv/bin/python neuron/fixtures/qualification/build_corpus.py
cd neuron/fixtures/qualification && sha256sum -c CORPUS-HASHES.txt
```

The generator is deterministic (fixed seeds, `reportlab.rl_config.invariant = 1`,
fixed JPEG settings), so a rerun reproduces every file byte for byte. It deletes and
rewrites `documents/` and `expectations/`, and rewrites `corpus.yaml`,
`CORPUS-HASHES.txt` and this README.

## Contents

- 6 `native` documents (text layer), 4 `scanned` documents (each page is a
  200 dpi grayscale JPEG with slight skew and speckle, and no text layer),
  2 `mixed` documents (text layer plus one pixel-only image region holding some
  expected values), and 1 `partial` document (text layer; page 2 has a corrupted
  content stream and holds no expected values).
- Distractors in every document: Products-Completed Operations Aggregate, Personal and
  Advertising Injury, Damage to Premises Rented, Medical Expense, issue/retroactive
  dates, producer/insurer/additional-insured names. A distractor amount never
  equals the target value in the same document.
- `expectations/<id>.json` holds, for each profile field, `value` (verbatim as printed,
  or `null` when absent) and `evidence` (`page`, exact printed `text`, `region`).
  A `split-across-regions` value is the two printed parts joined by one space, and both
  parts are listed as evidence.

| id | kind | pages | layout | damaged page |
|---|---|---|---|---|
| gl-q-001 | native | 1 | label-value-lines | - |
| gl-q-002 | native | 2 | header-box-and-limits-table | - |
| gl-q-003 | native | 2 | two-column | - |
| gl-q-004 | native | 1 | dollar-sign-column-table | - |
| gl-q-005 | native | 1 | supplemental-declarations | - |
| gl-q-006 | native | 2 | insured-schedule-table-plus-recap | - |
| gl-q-007 | scanned | 2 | label-value-lines-scanned | - |
| gl-q-008 | scanned | 2 | tables-scanned | - |
| gl-q-009 | scanned | 1 | continuation-declarations-scanned | - |
| gl-q-010 | scanned | 2 | insured-tables-wrapped-dates-scanned | - |
| gl-q-011 | mixed | 1 | image-header-native-limits | - |
| gl-q-012 | mixed | 1 | native-header-image-limits-table | - |
| gl-q-013 | partial | 3 | three-page-with-damaged-page | 2 |

## Case-tag coverage (document numbers, gl-q-NNN)

| field | unique | repeated | table-borne | split-across-regions | absent |
|---|---|---|---|---|---|
| `each_occurrence_limit` | 001, 002, 007, 008, 010, 011, 012, 013 | 003, 006, 009 | 002, 004, 006, 008, 011, 012 | 004 | 005 |
| `general_aggregate_limit` | 001, 002, 005, 007, 009, 012, 013 | 006, 008, 011 | 002, 004, 006, 008, 012 | 004 | 003, 010 |
| `named_insured` | 001, 004, 006, 008, 011, 012, 013 | 002, 005, 010 | 006, 010 | 003, 007 | 009 |
| `policy_period_start` | 001, 003, 005, 006, 008, 009, 011, 013 | 002, 007 | 003, 008 | 004, 010 | 012 |
| `policy_period_end` | 001, 003, 006, 008, 009, 011, 013 | 002, 007 | 003, 008 | 004, 010 | 005, 012 |

Every field x tag cell is non-empty. Per-document tags are in `corpus.yaml`.

## Independence

`build_corpus.py` takes expected values from its own layout specifications only. It
does not import, run or read any conversion or extraction code (Docling,
docling-graph, brain_extraction, brain_ingestion, model servers). pypdf is used only
outside the generator, to check text-layer presence and the damaged page.
