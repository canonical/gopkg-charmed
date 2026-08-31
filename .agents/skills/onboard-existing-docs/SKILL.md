---
description: |
    Onboards a downstream repository that already has unmanaged documentation tooling files (Sphinx config, Makefile, requirements, etc.) into the Copier-based platform-engineering-documentation-files management solution. Preserves downstream customizations while bringing tooling under central management. WHEN: onboard pre-existing docs repo, migrate unmanaged Sphinx docs to Copier template, bring existing documentation tooling under central management, convert standalone docs to platform-engineering-docs scaffold.
license: Apache-2.0
metadata:
    author: Canonical/platform-engineering
    github-path: skills/onboard-existing-docs
    github-ref: refs/heads/main
    github-repo: https://github.com/canonical/platform-engineering-documentation-files
    github-tree-sha: 93e3003061e0909a51389a013d21811d4d09c295
    summary: Onboard a downstream repo with pre-existing documentation tooling into the Copier-based central management solution
    tags:
        - canonical
        - platform-engineering
        - documentation
        - copier
        - sphinx
        - onboarding
    version: 1.0.0
name: onboard-existing-docs
---
# Onboard Existing Documentation

Inspect first. Preserve downstream customizations. Generate only after
understanding what exists.

## Description

This skill onboards a downstream repository that already has unmanaged
documentation tooling files (Sphinx config, Makefile, requirements, etc.)
into the Copier-based
[platform-engineering-documentation-files](https://github.com/canonical/platform-engineering-documentation-files)
management solution. It audits the existing files, extracts project-specific
values, backs up and removes overlapping tooling files, runs Copier to
generate the scaffold, re-applies downstream customizations, and validates
the build.

The work is split into eight sequential phases. Execute each phase in order
using `read_file` to load the sub-skill instructions.

## Assumptions

- The downstream repository has Python 3.10+, Git 2.27+, and Copier installed.
- Documentation already lives in `docs/` in the downstream repository.
- The downstream repo contains unmanaged copies of one or more files that
  overlap with the template's generated output.
- You are working in the downstream repository's workspace (not this template
  repo).

---

## Execution order

| Phase | Sub-skill file | Scope |
|---|---|---|
| 1 | [`phase-1-audit.md`](references/phase-1-audit.md) | Audit existing files, identify overlaps with template |
| 2 | [`phase-2-extract-values.md`](references/phase-2-extract-values.md) | Extract project-specific values from `conf.py`, map to Copier variables |
| 3 | [`phase-3-identify-customizations.md`](references/phase-3-identify-customizations.md) | Identify downstream-only customizations in Makefile, requirements, .gitignore |
| 4 | [`phase-4-backup-remove.md`](references/phase-4-backup-remove.md) | Back up and remove overlapping tooling files |
| 5 | [`phase-5-run-copier.md`](references/phase-5-run-copier.md) | Run Copier with confirmed values |
| 6 | [`phase-6-reapply-customizations.md`](references/phase-6-reapply-customizations.md) | Re-apply downstream customizations via diff |
| 7 | [`phase-7-validate-commit.md`](references/phase-7-validate-commit.md) | Validate build, diagnose failures, commit |
| 8 | [`phase-8-post-onboarding.md`](references/phase-8-post-onboarding.md) | Post-onboarding guidance and cleanup |

### Hand-off between phases

Each phase produces shared state that later phases depend on. Carry these
values forward:

| State key | Produced by | Consumed by | Description |
|---|---|---|---|
| `overlapping_files` | Phase 1 | Phases 2, 3, 4 | List of files that overlap with the template |
| `content_files` | Phase 1 | Phases 3, 4, 6 | List of documentation content files to preserve |
| `extracted_values` | Phase 2 | Phases 3, 4, 5, 6, 7, 8 | Dict of Copier variable → confirmed value |
| `template_uncovered_values` | Phase 2 | Phases 3, 6 | Custom config not covered by the template |
| `downstream_customizations` | Phase 3 | Phases 4, 6 | Structured list of customizations to re-apply |
| `backup_path` | Phase 4 | Phases 6, 7, 8 | Path to the backup directory (`/tmp/docs-backup/`) |

---

## Reference files

| File | Purpose |
|---|---|
| [`question-bank.md`](references/question-bank.md) | Structured questions for user prompts at key decision points |
| [`extract_conf_values.py`](assets/extract_conf_values.py) | Python script to automate Phase 2 value extraction from `conf.py` |
| [`PR-GUIDE.md`](assets/PR-GUIDE.md) | PR description structure, reviewer priority tiers, and human action checklist |

---

## After all phases complete

Read [`PR-GUIDE.md`](assets/PR-GUIDE.md) and use it to structure the PR
description, including:
- The `## For reviewers` section with high/medium/low priority file tiers
- The `## Items requiring human action` checklist

## Non-Negotiables

- Never delete documentation content files (`.md`, `.rst`, `_static/`,
  images). Only remove tooling/config files that overlap with the template.
- Always back up before removing anything.
- Always confirm extracted values with the user before running Copier.
- Always test the build (`make html`) before considering the onboarding
  complete.
- Never edit `.copier-answers.yml` manually after generation.
