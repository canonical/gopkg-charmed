.. _ci-workflows:

CI workflows for documentation validation
=========================================

Automatic docs checks
---------------------

Workflow: ``.github/workflows/automatic-doc-checks.yml``

Purpose:

- run documentation checks when docs-related files change
- avoid unnecessary CI usage for unrelated code changes

Check removed URLs
------------------

Workflow: ``.github/workflows/automatic-doc-checks.yml``

Purpose:

- detect removed documentation URLs in pull requests to ``main``
- protect release-path documentation links from accidental breakage

Documentation tests
-------------------

Workflow: ``.github/workflows/documentation-tests.yml``

Purpose:

- execute literal shell commands from tutorials and how-to guides when their
  content or deployment inputs change
- validate the complete build, deploy, integrate, configure, and verify flow
  in a provisioned Ubuntu environment

Where it comes from:

- The workflow file lives in this repository:
  ``.github/workflows/documentation-tests.yml``
- The job itself reuses Canonical's shared documentation test workflow:
  ``canonical/charm-ci/.github/workflows/doc-test.yml`` pinned to a
  specific commit for reproducibility.

Current behavior:

- triggers on tutorial, how-to, Spread task, artifact recipe, provisioning,
  and workflow changes
- uses ``opcli tutorial expand`` to extract commands directly from the RST
- executes the generated shell script through the ``docs-ci`` Spread backend
- provisions MicroK8s and Juju, then builds the rock and charm from source
- composes dependent how-to guides in prerequisite order; the hostname test
  extracts setup, deployment, and hostname configuration commands

Automatic vs manual linkage
---------------------------

Command synchronization is content-aware; workflow triggering is path-based.

- Automatic part:
  commands are extracted from tutorials and how-to guides, so edits to their
  executable code blocks change the tested scripts without duplicate tests.
- Manual part:
  if you move documentation files to new paths, you must update the Spread
  task inputs and the workflow's ``paths`` list.

