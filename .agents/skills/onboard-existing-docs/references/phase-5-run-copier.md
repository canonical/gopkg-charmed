---
name: phase-5-run-copier
description: "Phase 5 of the onboard-existing-docs skill. Runs Copier with the confirmed values to generate the documentation scaffold."
---

# Phase 5: Run Copier

**Prerequisites:** Phase 4 (`phase-4-backup-remove`) must be complete. Overlapping files must be removed and backed up.

---

## Instructions

### Step 1: Determine execution mode

Check whether the user wants interactive or non-interactive Copier execution.

- **Interactive**: Copier prompts for each value. Use this when the user wants to review each value as it's entered.
- **Non-interactive**: Pass all values via `--data` flags. Use this when all values have been confirmed and the user wants a single command.

Ask the user which mode they prefer (see [`question-bank.md`](question-bank.md), Section "Copier Execution Mode").

### Step 2: Run Copier interactively

From the downstream repo root:

```bash
copier copy gh:canonical/platform-engineering-documentation-files.git .
```

Answer each prompt with the values from `extracted_values` (confirmed in Phase 2).

### Step 3: Run Copier non-interactively (alternative)

Construct the command using `--data` flags for each confirmed value. Use `--defaults` to skip prompts for unspecified values and `--overwrite` to allow Copier to write into the existing `docs/` directory (which still contains content files):

```bash
copier copy --defaults --overwrite \
  --data "project=MyProject" \
  --data "author=Canonical Ltd." \
  --data "product_page=charmhub.io/my-charm" \
  --data "discourse=https://discourse.charmhub.io" \
  --data "github_url=https://github.com/canonical/my-repo" \
  --data "repo_default_branch=main" \
  --data "repo_folder=/docs/" \
  --data "display_contributors=False" \
  ... \
  gh:canonical/platform-engineering-documentation-files.git .
```

Only include `--data` flags for non-default values. Omit flags for variables where the default is acceptable.

### Step 4: Verify generation

After Copier completes, verify that the expected files were generated:

```bash
ls docs/conf.py docs/Makefile docs/requirements.txt docs/.gitignore
ls docs/_dev/
ls docs/_templates/
ls docs/release-notes/template/
ls .readthedocs.yaml .copier-answers.yml
```

### Step 5: Verify `.copier-answers.yml`

Read `.copier-answers.yml` and confirm it contains the correct values matching `extracted_values`. If any value is wrong, do not edit `.copier-answers.yml` manually — re-run `copier copy` with corrected `--data` flags.

### Hand-off to Phase 6

Carry forward:
- `backup_path` — from Phase 4
- `extracted_values` — from Phase 2
- `template_uncovered_values` — from Phase 2
- `downstream_customizations` — from Phase 3
- `content_files` — from Phase 1