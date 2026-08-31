---
name: phase-1-audit
description: "Phase 1 of the onboard-existing-docs skill. Audits the downstream repo for files that overlap with the template."
---

# Phase 1: Audit Existing Files

**Prerequisites:** This is Phase 1 of the `onboard-existing-docs` skill. See the parent [SKILL.md](../SKILL.md) for the full workflow overview.

---

## Instructions

### Step 1: List the downstream `docs/` directory

Run the following to inventory the downstream repo's documentation directory:

```bash
find docs/ -type f | sort
```

Also check for root-level config files:

```bash
ls -la .readthedocs.yaml 2>/dev/null || echo "No .readthedocs.yaml found"
```

### Step 2: Compare against the template's generated file list

The template generates these files in the downstream repo:

| Template source | Downstream output |
|---|---|
| `conf.py.jinja` | `docs/conf.py` |
| `Makefile` | `docs/Makefile` |
| `requirements.txt` | `docs/requirements.txt` |
| `.gitignore` | `docs/.gitignore` |
| `_dev/*` | `docs/_dev/*` |
| `_templates/*` | `docs/_templates/*` |
| `release-notes/template/*` | `docs/release-notes/template/*` |
| `.readthedocs.yaml` | `.readthedocs.yaml` |
| `{{ _copier_conf.answers_file }}.jinja` | `.copier-answers.yml` |

### Step 3: Identify overlapping files

For each file in the template's output list, check if it exists in the downstream repo. Build a list of overlapping files.

### Step 4: Report to the user

Report: "I found N files that overlap with the template. These will be overwritten during onboarding."

List each overlapping file with its path.

### Step 5: Identify documentation content files to preserve

List all files under `docs/` that are **not** in the overlapping list — these are documentation content files (`.md`, `.rst`, `_static/`, images, custom CSS, etc.) that must be preserved.

### Hand-off to Phase 2

Carry forward:
- `overlapping_files` — list of files that will be overwritten
- `content_files` — list of documentation content files to preserve