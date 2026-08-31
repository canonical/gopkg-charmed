---
name: phase-6-reapply-customizations
description: "Phase 6 of the onboard-existing-docs skill. Re-applies downstream customizations by diffing generated files against backups."
---

# Phase 6: Re-Apply Downstream Customizations

**Prerequisites:** Phase 5 (`phase-5-run-copier`) must be complete. Copier must have generated all files successfully.

---

## Instructions

### Step 1: Diff generated files against backups

Run diffs for each file that had downstream customizations:

```bash
diff /tmp/docs-backup/conf.py docs/conf.py
diff /tmp/docs-backup/Makefile docs/Makefile
diff /tmp/docs-backup/requirements.txt docs/requirements.txt
diff /tmp/docs-backup/.gitignore docs/.gitignore
```

### Step 2: Re-apply `conf.py` customizations

The generated `conf.py` has a `######################## Configuration extras ########################`
section at the end with commented-out scaffolds for common customizations.
**This section is added from scratch** — the generated file has no `extensions`
list, `intersphinx_mapping`, `rst_prolog`, etc. by default.

Using the `template_uncovered_values` from Phase 2, uncomment and fill in the
relevant sections. Add any additional config that doesn't fit the scaffolds.

**Do not overwrite Copier-managed values.** Only add entries that are NOT
covered by the template's Copier variables.

#### What to re-apply

| Original `conf.py` entry | Where to add it in generated `conf.py` |
|---|---|
| `extensions = [...]` | Uncomment `extensions` in the Configuration extras section |
| `intersphinx_mapping = {...}` | Uncomment `intersphinx_mapping` in the Configuration extras section |
| `rst_prolog = "..."` | Uncomment `rst_prolog` in the Configuration extras section |
| `exclude_patterns = [...]` | Uncomment `exclude_patterns` in the Configuration extras section |
| `html_css_files = [...]` | Uncomment `html_css_files` in the Configuration extras section |
| `html_js_files = [...]` | Uncomment `html_js_files` in the Configuration extras section |
| Extra `html_context` keys | Add to the `html_context` dict (after the license block) |
| Custom `html_theme_options` | Merge into the existing `html_theme_options` dict (or add if absent) |

#### Concrete example: typical Juju charm project

Here is what the Configuration extras section looks like after re-applying
customizations for a typical Juju charm documentation project:

```python
########################
# Configuration extras #
########################

# Custom Sphinx extensions beyond what the template provides.
extensions = [
    "sphinx.ext.intersphinx",
]

# Patterns to exclude from the build.
exclude_patterns = [
    "release-notes/index.rst",
]

# A string of reStructuredText included at the beginning of every source file.
rst_prolog = """
.. |charm| replace:: MyCharm
"""

# Intersphinx mappings for cross-referencing external documentation.
intersphinx_mapping = {
    "juju": ("https://canonical-juju.readthedocs-hosted.com/en/latest/", None),
}
```

**Important — values the template intentionally replaces:**

- **`ogp_site_url` / `html_baseurl`**: Do **not** re-apply hardcoded URLs.
  The template uses `os.environ.get("READTHEDOCS_CANONICAL_URL", "/")` which
  is the intended pattern.
- **`version` variable**: The template removes this. Only re-add it if the
  downstream project uses `version` for purposes beyond `ogp_site_url` /
  `html_baseurl`.

### Step 3: Re-apply `Makefile` customizations

Using `downstream_customizations.makefile_targets` from Phase 3, re-add any custom Makefile targets. Append them after the existing targets, preserving the template's standard targets.

### Step 4: Re-apply `requirements.txt` customizations

Using `downstream_customizations.extra_dependencies` from Phase 3, add any extra Python dependencies. Append them at the end of the file with a comment:

```
# Downstream-specific dependencies
my-extra-package==1.2.3
```

### Step 5: Merge `.gitignore` customizations

Using `downstream_customizations.gitignore_patterns` from Phase 3, merge any custom ignore patterns. Append them at the end of the file with a comment:

```
# Downstream-specific ignores
my-custom-pattern/
```

### Step 6: Verify no content files were affected

Confirm that documentation content files from `content_files` (Phase 1) are still present and unchanged:

```bash
ls docs/*.md docs/*.rst docs/_static/ 2>/dev/null
```

### Hand-off to Phase 7

Carry forward:
- `backup_path` — from Phase 4
- `extracted_values` — from Phase 2
- `content_files` — from Phase 1