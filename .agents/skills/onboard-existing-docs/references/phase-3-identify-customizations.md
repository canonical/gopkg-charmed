---
name: phase-3-identify-customizations
description: "Phase 3 of the onboard-existing-docs skill. Identifies downstream-only customizations in Makefile, requirements.txt, and .gitignore."
---

# Phase 3: Identify Downstream-Only Customizations

**Prerequisites:** Phase 2 (`phase-2-extract-values`) must be complete. You should already have `extracted_values` and `template_uncovered_values`.

---

## Instructions

### Step 1: Read the downstream tooling files

Read the following files from the downstream repo:
- `docs/Makefile`
- `docs/requirements.txt`
- `docs/.gitignore` (if it exists)

### Step 2: Read the template versions for comparison

Read the corresponding template files from this repository:
- `template/docs/Makefile`
- `template/docs/requirements.txt`
- `template/docs/.gitignore`

### Step 3: Diff and identify customizations

For each file, compare the downstream version against the template version:

#### `docs/Makefile`
- Identify any custom targets not present in the template
- Note any modified variable defaults (e.g., `SPHINX_PORT`, `DOCS_VENVDIR`)

#### `docs/requirements.txt`
- Identify any extra Python dependencies not in the template
- Note any version pin differences for shared dependencies

#### `docs/.gitignore`
- Identify any custom ignore patterns not in the template

### Step 4: Report to the user

Report: "These customizations will need to be re-applied after generation."

List each customization with its source file and a brief description. Use the question bank (see [`question-bank.md`](question-bank.md), Section "Confirm Customizations") to confirm which customizations should be re-applied.

### Hand-off to Phase 4

Carry forward:
- `downstream_customizations` — structured list of customizations to re-apply:
  - `makefile_targets` — list of custom Makefile targets
  - `extra_dependencies` — list of extra Python packages
  - `gitignore_patterns` — list of custom ignore patterns
- `extracted_values` — from Phase 2
- `template_uncovered_values` — from Phase 2
- `overlapping_files` — from Phase 1
- `content_files` — from Phase 1