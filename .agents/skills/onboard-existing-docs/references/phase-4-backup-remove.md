---
name: phase-4-backup-remove
description: "Phase 4 of the onboard-existing-docs skill. Backs up existing tooling files and removes only those that overlap with the template."
---

# Phase 4: Back Up and Remove Overlapping Files

**Prerequisites:** Phase 3 (`phase-3-identify-customizations`) must be complete. All values must be confirmed by the user.

---

## Instructions

### Step 1: Create the backup

Run the following from the downstream repo root:

```bash
mkdir /tmp/docs-backup
cp -r docs/ /tmp/docs-backup/
cp .readthedocs.yaml /tmp/docs-backup/ 2>/dev/null || true
```

Verify the backup was created:

```bash
ls /tmp/docs-backup/docs/
```

### Step 2: Remove only the tooling files that overlap with the template

**CRITICAL: Do NOT remove documentation content files** (`.md`, `.rst`, `_static/`, images, custom CSS, etc.).

Using the `overlapping_files` list from Phase 1, remove only those files:

```bash
rm -rf docs/conf.py docs/Makefile docs/requirements.txt \
       docs/.gitignore docs/_dev docs/_templates \
       docs/release-notes/template .readthedocs.yaml
```

### Step 3: Verify content files are still present

Confirm that documentation content files were not accidentally removed:

```bash
ls docs/*.md docs/*.rst docs/_static/ 2>/dev/null
```

If any content files are missing, restore them from the backup immediately:

```bash
cp -r /tmp/docs-backup/docs/<missing-file> docs/
```

### Step 4: Confirm readiness

Tell the user: "Backup created at `/tmp/docs-backup/`. Tooling files removed. Content files preserved. Ready to run Copier."

### Hand-off to Phase 5

Carry forward:
- `backup_path` — `/tmp/docs-backup/`
- `extracted_values` — from Phase 2
- `template_uncovered_values` — from Phase 2
- `downstream_customizations` — from Phase 3
- `content_files` — from Phase 1