---
name: phase-2-extract-values
description: "Phase 2 of the onboard-existing-docs skill. Extracts project-specific values from the downstream conf.py and maps them to Copier variables."
---

# Phase 2: Extract Project-Specific Values

**Prerequisites:** Phase 1 (`phase-1-audit`) must be complete. You should already have the `overlapping_files` list.

---

## Instructions

### Step 1: Run the extraction script

Run the automated extraction script to parse the downstream `docs/conf.py`:

```bash
python3 skills/onboard-existing-docs/assets/extract_conf_values.py docs/conf.py
```

This outputs a JSON object with two keys:

- `copier_values` — Copier variable → extracted value (for `extracted_values`)
- `template_uncovered` — config NOT covered by the template (for `template_uncovered_values`)

If the script cannot be run (e.g., the downstream repo doesn't have Python available), proceed with manual extraction in Step 2.

### Step 2: Manual extraction (fallback)

If the script is unavailable, manually read `docs/conf.py` and extract each value. Map to the corresponding Copier question variable:

| In existing `conf.py` | Copier variable | Notes |
|---|---|---|
| `project = "..."` | `project` | |
| `author = "..."` | `author` | |
| `copyright = ...` | (not a direct variable) | Template uses `datetime.date.today().year` |
| `ogp_image = "..."` | `ogp_image` | |
| `html_favicon = "..."` | `html_favicon` | May be absent |
| `html_context["product_page"]` | `product_page` | |
| `html_context["product_tag"]` | `product_tag` | May be absent |
| `html_context["discourse"]` | `discourse` | |
| `html_context["mattermost"]` | `mattermost` | |
| `html_context["matrix"]` | `matrix` | |
| `html_context["github_url"]` | `github_url` | |
| `html_context["repo_default_branch"]` | `repo_default_branch` | |
| `html_context["repo_folder"]` | `repo_folder` | |
| `html_context["display_contributors"]` | `display_contributors` | Boolean |

### Step 3: Identify values NOT covered by the template

The extraction script's `template_uncovered` output already captures most non-Copier config. Review it and supplement with manual inspection for any additional values.

Common non-Copier config to look for:
- Custom Sphinx `extensions = [...]` entries beyond what the template provides
- `intersphinx_mapping` for cross-referencing external docs
- `rst_prolog` with custom substitutions (e.g., `|charm|`)
- `exclude_patterns`, `html_css_files`, `html_js_files`
- `html_static_path`, `templates_path`
- `linkcheck_retries`, `linkcheck_timeout`
- `sitemap_filename`
- Extra `html_context` keys not covered by Copier variables
- Custom `html_theme_options`

These will be re-applied in Phase 6.

**Important — values the template intentionally replaces:**

- **`ogp_site_url` / `html_baseurl`**: The template replaces hardcoded URLs with `os.environ.get("READTHEDOCS_CANONICAL_URL", "/")`. Do **not** preserve the original hardcoded values — the template's environment-variable-based lookup is the intended pattern.
- **`version` variable**: The template removes the `version = f"{os.environ.get('READTHEDOCS_VERSION', 'local')}"` pattern. If the downstream project uses `version` for purposes beyond `ogp_site_url`/`html_baseurl`, flag it as a customization to re-apply.

### Step 4: Extract RTD slug (if applicable)

If the downstream repo has a `.readthedocs.yaml`, read it and extract the RTD project slug for the `rtd_slug` Copier variable.

### Step 5: Confirm values with the user

Present the extracted values to the user using the question bank (see [`question-bank.md`](question-bank.md), Section "Confirm Extracted Values"). Ask them to confirm or correct each one before proceeding.

Do not proceed to Phase 3 until the user has confirmed all values.

### Hand-off to Phase 3

Carry forward:
- `extracted_values` — dict of Copier variable → confirmed value
- `template_uncovered_values` — list of custom config not covered by the template
- `overlapping_files` — from Phase 1
- `content_files` — from Phase 1