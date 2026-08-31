---
name: question-bank
description: "Structured questions for the onboard-existing-docs skill. Used at key decision points across all phases."
---

# Question Bank

This file contains structured questions the agent should ask the user at key
decision points during the onboarding process. Each section maps to a specific
phase and step.

---

## Confirm Extracted Values (Phase 2, Step 5)

Present the extracted values and ask the user to confirm or correct each one.

> I've extracted the following values from your existing `docs/conf.py`.
> Please confirm or correct each one:

| Copier variable | Extracted value | Description |
|---|---|---|
| `project` | `{value}` | Official project/product name |
| `author` | `{value}` | Copyright footer author name |
| `product_page` | `{value}` | Product website URL |
| `discourse` | `{value}` | Discourse instance URL |
| `mattermost` | `{value}` | Mattermost channel URL |
| `matrix` | `{value}` | Matrix channel URL |
| `github_url` | `{value}` | GitHub repository URL |
| `repo_default_branch` | `{value}` | Default branch name |
| `repo_folder` | `{value}` | Path to docs folder in repo |
| `ogp_image` | `{value}` | Open Graph preview image |
| `html_favicon` | `{value}` | Custom favicon path |
| `product_tag` | `{value}` | Product tag image path |
| `display_contributors` | `{value}` | Show contributors on each page |
| `rtd_slug` | `{value}` | Read the Docs project slug |

> Are these values correct? Would you like to change any of them?

---

## Confirm Customizations (Phase 3, Step 4)

Present the identified downstream customizations and ask which should be
re-applied.

> I've identified the following downstream-only customizations that are not
> part of the standard template. Which of these should be re-applied after
> generation?

### Custom Sphinx extensions (from `conf.py`)
- `{extension_name}` — {description if available}

### Custom Makefile targets (from `docs/Makefile`)
- `{target_name}` — {description if available}

### Extra Python dependencies (from `docs/requirements.txt`)
- `{package_name}=={version}`

### Custom `.gitignore` patterns
- `{pattern}`

> Should I re-apply all of these, or would you like to drop any?

---

## Copier Execution Mode (Phase 5, Step 1)

Ask the user whether to run Copier interactively or non-interactively.

> All values have been confirmed. How would you like to run Copier?
>
> - **Interactive**: Copier will prompt you for each value one at a time.
>   You can review and adjust each value as it's entered.
> - **Non-interactive**: I'll construct a single command with all values
>   passed via `--data` flags. Faster, but you won't see each prompt.

---

## Build Failure Diagnosis (Phase 7, Step 2)

If the build fails, ask targeted questions to narrow down the cause.

> The build failed with the following error:
> ```
> {error_output}
> ```
>
> This is likely caused by:
> - {likely_cause_1}
> - {likely_cause_2}
>
> Would you like me to attempt the suggested fix?

---

## Post-Onboarding Confirmation (Phase 8, Step 4)

Confirm the onboarding is complete and working.

> The onboarding is complete. Here's a summary:
> - **Files generated**: {count} files from the template
> - **Customizations re-applied**: {count} downstream customizations
> - **Build status**: {pass/fail}
>
> Is everything working as expected? Do you need any adjustments?